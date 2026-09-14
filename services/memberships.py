from __future__ import annotations

from datetime import date, timedelta

from db.database import execute, fetch_all, fetch_one, now_iso, today_iso
from services.members import current_membership


def list_plans() -> list[dict]:
    return fetch_all(
        """
        SELECT p.*, (
            SELECT COUNT(*) FROM memberships m
            WHERE m.plan_id = p.id AND m.status = 'active' AND date(m.end_date) >= date(?)
        ) AS active_members
        FROM membership_plans p
        ORDER BY p.duration_days
        """,
        (today_iso(),),
    )


def get_plan(plan_id: int) -> dict | None:
    return fetch_one("SELECT * FROM membership_plans WHERE id = ?", (plan_id,))


def create_plan(name: str, duration_days: int, price: float, description: str) -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "Plan name is required."
    if duration_days <= 0:
        return False, "Duration must be greater than zero."
    if price < 0:
        return False, "Price cannot be negative."
    execute(
        "INSERT INTO membership_plans (name, duration_days, price, description) VALUES (?, ?, ?, ?)",
        (name, duration_days, price, description.strip()),
    )
    return True, "Plan created."


def update_plan(plan_id: int, name: str, duration_days: int, price: float, description: str) -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "Plan name is required."
    if duration_days <= 0:
        return False, "Duration must be greater than zero."
    if price < 0:
        return False, "Price cannot be negative."
    execute(
        """
        UPDATE membership_plans
        SET name = ?, duration_days = ?, price = ?, description = ?
        WHERE id = ?
        """,
        (name, duration_days, price, description.strip(), plan_id),
    )
    return True, "Plan updated."


def delete_plan(plan_id: int) -> tuple[bool, str]:
    in_use = fetch_one("SELECT COUNT(*) AS n FROM memberships WHERE plan_id = ?", (plan_id,))
    if in_use and in_use["n"] > 0:
        return False, "This plan is assigned to members and cannot be deleted."
    execute("DELETE FROM membership_plans WHERE id = ?", (plan_id,))
    return True, "Plan deleted."


def assign_membership(user_id: int, plan_id: int, start: date | None = None) -> tuple[bool, str, int | None]:
    plan = get_plan(plan_id)
    if not plan:
        return False, "Select a valid plan.", None
    start = start or date.today()
    end = start + timedelta(days=int(plan["duration_days"]) - 1)
    current = current_membership(user_id)
    if current and current["status"] == "active":
        execute("UPDATE memberships SET status = 'expired' WHERE id = ?", (current["id"],))
    membership_id = execute(
        """
        INSERT INTO memberships (user_id, plan_id, start_date, end_date, status, created_at)
        VALUES (?, ?, ?, ?, 'active', ?)
        """,
        (user_id, plan_id, start.isoformat(), end.isoformat(), now_iso()),
    )
    return True, f"Assigned {plan['name']} until {end.isoformat()}.", membership_id


def freeze_membership(user_id: int) -> tuple[bool, str]:
    current = current_membership(user_id)
    if not current:
        return False, "This member has no membership to freeze."
    if current["status"] != "active":
        return False, "Only an active membership can be frozen."
    execute("UPDATE memberships SET status = 'frozen' WHERE id = ?", (current["id"],))
    return True, "Membership frozen."


def unfreeze_membership(user_id: int) -> tuple[bool, str]:
    current = current_membership(user_id)
    if not current:
        return False, "This member has no membership."
    if current["status"] != "frozen":
        return False, "Membership is not frozen."
    new_status = "expired" if current["end_date"] < today_iso() else "active"
    execute("UPDATE memberships SET status = ? WHERE id = ?", (new_status, current["id"]))
    return True, "Membership unfrozen." if new_status == "active" else "Unfrozen, but the plan has already expired."


def renew_membership(user_id: int, plan_id: int) -> tuple[bool, str, int | None]:
    current = current_membership(user_id)
    start = date.today()
    if current and current["status"] == "active" and current["end_date"] >= today_iso():
        start = date.fromisoformat(current["end_date"]) + timedelta(days=1)
    return assign_membership(user_id, plan_id, start=start)
