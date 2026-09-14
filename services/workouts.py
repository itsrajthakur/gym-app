from __future__ import annotations

from datetime import date

from db.database import execute, fetch_all, fetch_one, now_iso


def list_plans_for_member(member_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT p.*, u.name AS trainer_name
        FROM workout_plans p
        JOIN users u ON u.id = p.trainer_id
        WHERE p.member_id = ?
        ORDER BY p.created_at DESC
        """,
        (member_id,),
    )


def latest_plan(member_id: int) -> dict | None:
    plans = list_plans_for_member(member_id)
    return plans[0] if plans else None


def get_plan(plan_id: int) -> dict | None:
    return fetch_one(
        """
        SELECT p.*, m.name AS member_name, t.name AS trainer_name
        FROM workout_plans p
        JOIN users m ON m.id = p.member_id
        JOIN users t ON t.id = p.trainer_id
        WHERE p.id = ?
        """,
        (plan_id,),
    )


def plan_exercises(plan_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT * FROM plan_exercises
        WHERE plan_id = ?
        ORDER BY sort_order, id
        """,
        (plan_id,),
    )


def create_plan(member_id: int, trainer_id: int, title: str, notes: str = "") -> tuple[bool, str, int | None]:
    title = title.strip()
    if not title:
        return False, "Give the plan a title.", None
    member = fetch_one("SELECT id FROM users WHERE id = ? AND role = 'member'", (member_id,))
    if not member:
        return False, "Select a member.", None
    plan_id = execute(
        """
        INSERT INTO workout_plans (member_id, trainer_id, title, notes, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (member_id, trainer_id, title, notes.strip(), now_iso()),
    )
    return True, "Plan created.", plan_id


def add_exercise(
    plan_id: int,
    exercise_name: str,
    sets: int,
    reps: int,
    rest_sec: int | None,
    day_label: str,
) -> tuple[bool, str]:
    exercise_name = exercise_name.strip()
    if not exercise_name:
        return False, "Exercise name is required."
    if sets <= 0 or reps <= 0:
        return False, "Sets and reps must be greater than zero."
    current = plan_exercises(plan_id)
    sort_order = (current[-1]["sort_order"] + 1) if current else 1
    execute(
        """
        INSERT INTO plan_exercises (plan_id, exercise_name, sets, reps, rest_sec, day_label, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (plan_id, exercise_name, sets, reps, rest_sec, day_label.strip(), sort_order),
    )
    return True, "Exercise added."


def delete_exercise(exercise_id: int) -> None:
    execute("DELETE FROM plan_exercises WHERE id = ?", (exercise_id,))


def log_workout(
    user_id: int,
    logged_on: date,
    exercise_name: str,
    sets: int,
    reps: int,
    weight: float | None,
    notes: str = "",
) -> tuple[bool, str]:
    exercise_name = exercise_name.strip()
    if not exercise_name:
        return False, "Exercise name is required."
    if sets <= 0 or reps <= 0:
        return False, "Sets and reps must be greater than zero."
    if weight is not None and weight < 0:
        return False, "Weight cannot be negative."
    execute(
        """
        INSERT INTO workout_logs (user_id, logged_on, exercise_name, sets, reps, weight, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, logged_on.isoformat(), exercise_name, sets, reps, weight, notes.strip()),
    )
    return True, "Workout logged."


def list_logs(user_id: int, limit: int = 100) -> list[dict]:
    return fetch_all(
        """
        SELECT * FROM workout_logs
        WHERE user_id = ?
        ORDER BY logged_on DESC, id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )


def latest_log(user_id: int) -> dict | None:
    return fetch_one(
        """
        SELECT * FROM workout_logs
        WHERE user_id = ?
        ORDER BY logged_on DESC, id DESC
        LIMIT 1
        """,
        (user_id,),
    )


def volume_by_day(user_id: int, days: int = 14) -> list[dict]:
    return fetch_all(
        """
        SELECT logged_on, SUM(sets * reps * COALESCE(weight, 0)) AS volume
        FROM workout_logs
        WHERE user_id = ? AND logged_on >= date('now', 'localtime', ?)
        GROUP BY logged_on
        ORDER BY logged_on
        """,
        (user_id, f"-{days - 1} days"),
    )
