from __future__ import annotations

from datetime import date, datetime, timedelta

from db.database import execute, execute_many, fetch_one, get_conn, now_iso, today_iso
from services.auth import hash_password


def _dt(days_ago: int, hour: int, minute: int = 0) -> str:
    moment = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    moment = moment - timedelta(days=days_ago)
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def seed_if_empty() -> None:
    if fetch_one("SELECT COUNT(*) AS n FROM users")["n"] > 0:
        return

    created = now_iso()
    admin_hash = hash_password("admin123")
    demo_hash = hash_password("demo123")

    users = [
        ("Maya Rao", "admin@pulsegym.local", admin_hash, "admin", "9000000001", 1, created),
        ("Priya Shah", "priya.trainer@pulsegym.local", demo_hash, "trainer", "9000000002", 1, created),
        ("Arjun Mehta", "arjun.trainer@pulsegym.local", demo_hash, "trainer", "9000000003", 1, created),
        ("Ananya Iyer", "ananya@example.com", demo_hash, "member", "9000001001", 1, created),
        ("Rohan Das", "rohan@example.com", demo_hash, "member", "9000001002", 1, created),
        ("Meera Kapoor", "meera@example.com", demo_hash, "member", "9000001003", 1, created),
        ("Kabir Singh", "kabir@example.com", demo_hash, "member", "9000001004", 1, created),
        ("Nisha Patel", "nisha@example.com", demo_hash, "member", "9000001005", 1, created),
        ("Vikram Rao", "vikram@example.com", demo_hash, "member", "9000001006", 1, created),
    ]
    execute_many(
        """
        INSERT INTO users (name, email, password_hash, role, phone, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        users,
    )

    plans = [
        ("Monthly", 30, 1499.0, "Gym floor access and group classes for 30 days."),
        ("Quarterly", 90, 3999.0, "Best value for consistent training over 3 months."),
        ("Annual", 365, 12999.0, "Year-round access with priority class booking."),
    ]
    execute_many(
        "INSERT INTO membership_plans (name, duration_days, price, description) VALUES (?, ?, ?, ?)",
        plans,
    )

    ids = {
        row["email"]: row["id"]
        for row in _all("SELECT id, email FROM users")
    }
    plan_ids = {row["name"]: row["id"] for row in _all("SELECT id, name FROM membership_plans")}

    today = date.today()

    def iso(d: date) -> str:
        return d.isoformat()

    memberships = [
        (ids["ananya@example.com"], plan_ids["Monthly"], iso(today - timedelta(days=10)), iso(today + timedelta(days=20)), "active", created),
        (ids["rohan@example.com"], plan_ids["Quarterly"], iso(today - timedelta(days=20)), iso(today + timedelta(days=70)), "active", created),
        (ids["meera@example.com"], plan_ids["Monthly"], iso(today - timedelta(days=45)), iso(today - timedelta(days=15)), "expired", created),
        (ids["kabir@example.com"], plan_ids["Monthly"], iso(today - timedelta(days=5)), iso(today + timedelta(days=25)), "frozen", created),
        (ids["vikram@example.com"], plan_ids["Annual"], iso(today - timedelta(days=40)), iso(today + timedelta(days=325)), "active", created),
    ]
    execute_many(
        """
        INSERT INTO memberships (user_id, plan_id, start_date, end_date, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        memberships,
    )
    membership_by_email = {
        row["email"]: row["mid"]
        for row in _all(
            """
            SELECT u.email, m.id AS mid
            FROM memberships m
            JOIN users u ON u.id = m.user_id
            """
        )
    }

    payments = [
        (ids["ananya@example.com"], membership_by_email["ananya@example.com"], 1499.0, "upi", _dt(10, 10, 15), "Monthly signup"),
        (ids["rohan@example.com"], membership_by_email["rohan@example.com"], 3999.0, "card", _dt(20, 11, 0), "Quarterly signup"),
        (ids["vikram@example.com"], membership_by_email["vikram@example.com"], 12999.0, "cash", _dt(40, 9, 30), "Annual signup"),
        (ids["meera@example.com"], membership_by_email["meera@example.com"], 1499.0, "upi", _dt(45, 16, 20), "Expired monthly"),
        (ids["ananya@example.com"], membership_by_email["ananya@example.com"], 500.0, "cash", _dt(3, 18, 5), "Personal training add-on"),
    ]
    execute_many(
        """
        INSERT INTO payments (user_id, membership_id, amount, method, paid_at, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        payments,
    )

    attendance = []
    for days_ago in range(13, -1, -1):
        attendance.append((ids["ananya@example.com"], _dt(days_ago, 7, 10)))
        if days_ago % 2 == 0:
            attendance.append((ids["rohan@example.com"], _dt(days_ago, 18, 40)))
        if days_ago % 3 == 0:
            attendance.append((ids["vikram@example.com"], _dt(days_ago, 6, 50)))
    execute_many("INSERT INTO attendance (user_id, check_in_at) VALUES (?, ?)", attendance)

    classes = [
        ("Sunrise HIIT", ids["priya.trainer@pulsegym.local"], 0, "07:00", 45, 12, "High-intensity intervals to start the week."),
        ("Yoga flow", ids["priya.trainer@pulsegym.local"], 1, "18:00", 60, 15, "Mobility and breath work."),
        ("Sunrise HIIT", ids["priya.trainer@pulsegym.local"], 2, "07:00", 45, 12, "Mid-week conditioning."),
        ("Yoga flow", ids["priya.trainer@pulsegym.local"], 3, "18:00", 60, 15, "Restore and stretch."),
        ("Strength circuit", ids["arjun.trainer@pulsegym.local"], 0, "19:00", 50, 10, "Compound lifts and accessories."),
        ("Strength circuit", ids["arjun.trainer@pulsegym.local"], 4, "19:00", 50, 10, "Friday strength finisher."),
        ("Weekend spin", ids["arjun.trainer@pulsegym.local"], 5, "09:00", 40, 8, "Indoor cycling."),
        ("Express abs", ids["priya.trainer@pulsegym.local"], today.weekday(), "12:00", 20, 1, "Short core blast — limited spots."),
    ]
    execute_many(
        """
        INSERT INTO gym_classes (name, trainer_id, weekday, start_time, duration_min, capacity, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        classes,
    )

    class_rows = _all("SELECT id, name, weekday FROM gym_classes")
    express = next(c for c in class_rows if c["name"] == "Express abs")
    strength_fri = next((c for c in class_rows if c["name"] == "Strength circuit" and c["weekday"] == 4), None)
    hiit_mon = next(c for c in class_rows if c["name"] == "Sunrise HIIT" and c["weekday"] == 0)

    next_monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
    bookings = [
        (express["id"], ids["vikram@example.com"], today_iso(), "booked", created),
        (hiit_mon["id"], ids["ananya@example.com"], next_monday.isoformat(), "booked", created),
        (hiit_mon["id"], ids["rohan@example.com"], next_monday.isoformat(), "booked", created),
    ]
    if strength_fri:
        next_friday = today + timedelta(days=(4 - today.weekday()) % 7)
        if next_friday == today:
            bookings.append((strength_fri["id"], ids["rohan@example.com"], today_iso(), "booked", created))
    execute_many(
        """
        INSERT INTO class_bookings (class_id, user_id, session_date, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        bookings,
    )

    plan_id = execute(
        """
        INSERT INTO workout_plans (member_id, trainer_id, title, notes, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            ids["ananya@example.com"],
            ids["priya.trainer@pulsegym.local"],
            "Ananya — 4 week strength",
            "Focus on hinge and squat patterns. Rest 90 seconds between compounds.",
            created,
        ),
    )
    execute_many(
        """
        INSERT INTO plan_exercises (plan_id, exercise_name, sets, reps, rest_sec, day_label, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (plan_id, "Goblet squat", 3, 10, 90, "Day A", 1),
            (plan_id, "Romanian deadlift", 3, 8, 90, "Day A", 2),
            (plan_id, "Lat pulldown", 3, 10, 75, "Day A", 3),
            (plan_id, "Push-up", 3, 12, 60, "Day B", 4),
            (plan_id, "Walking lunge", 3, 10, 75, "Day B", 5),
            (plan_id, "Plank", 3, 40, 45, "Day B", 6),
        ],
    )

    logs = []
    for days_ago, exercise, sets, reps, weight in [
        (6, "Goblet squat", 3, 10, 16),
        (6, "Romanian deadlift", 3, 8, 30),
        (4, "Goblet squat", 3, 10, 18),
        (4, "Push-up", 3, 12, 0),
        (2, "Lat pulldown", 3, 10, 25),
        (2, "Plank", 3, 40, 0),
        (0, "Goblet squat", 3, 8, 20),
    ]:
        logs.append(
            (
                ids["ananya@example.com"],
                (today - timedelta(days=days_ago)).isoformat(),
                exercise,
                sets,
                reps,
                float(weight),
                "",
            )
        )
    execute_many(
        """
        INSERT INTO workout_logs (user_id, logged_on, exercise_name, sets, reps, weight, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        logs,
    )


def seed_ad_plans_if_empty() -> None:
    row = fetch_one("SELECT COUNT(*) AS n FROM ad_plans")
    if row and row["n"] > 0:
        return
    execute_many(
        "INSERT INTO ad_plans (name, duration_days, price, description) VALUES (?, ?, ?, ?)",
        [
            ("1 Day", 1, 199.0, "Banner on member pages for one day."),
            ("1 Week", 7, 999.0, "Banner on member pages for seven days."),
            ("1 Month", 30, 2999.0, "Banner on member pages for 30 days."),
            ("1 Year", 365, 24999.0, "Banner on member pages for a full year."),
        ],
    )


def _all(sql: str) -> list[dict]:
    with get_conn() as conn:
        return [dict(row) for row in conn.execute(sql).fetchall()]
