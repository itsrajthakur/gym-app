from __future__ import annotations

from datetime import date, timedelta

from db.database import execute, fetch_all, fetch_one, get_conn, now_iso, today_iso
from services.members import membership_access

WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def list_classes() -> list[dict]:
    return fetch_all(
        """
        SELECT
            c.*,
            u.name AS trainer_name
        FROM gym_classes c
        JOIN users u ON u.id = c.trainer_id
        ORDER BY c.weekday, c.start_time, c.name
        """
    )


def classes_for_trainer(trainer_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT c.*, u.name AS trainer_name
        FROM gym_classes c
        JOIN users u ON u.id = c.trainer_id
        WHERE c.trainer_id = ?
        ORDER BY c.weekday, c.start_time
        """,
        (trainer_id,),
    )


def create_class(
    name: str,
    trainer_id: int,
    weekday: int,
    start_time: str,
    duration_min: int,
    capacity: int,
    description: str = "",
) -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "Class name is required."
    if weekday not in range(7):
        return False, "Pick a valid weekday."
    if duration_min <= 0:
        return False, "Duration must be greater than zero."
    if capacity <= 0:
        return False, "Capacity must be at least 1."
    trainer = fetch_one("SELECT id FROM users WHERE id = ? AND role = 'trainer' AND is_active = 1", (trainer_id,))
    if not trainer:
        return False, "Select an active trainer."
    execute(
        """
        INSERT INTO gym_classes (name, trainer_id, weekday, start_time, duration_min, capacity, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (name, trainer_id, weekday, start_time, duration_min, capacity, description.strip()),
    )
    return True, "Class added to the weekly schedule."


def booked_count(class_id: int, session_date: str) -> int:
    row = fetch_one(
        """
        SELECT COUNT(*) AS n FROM class_bookings
        WHERE class_id = ? AND session_date = ? AND status IN ('booked', 'attended')
        """,
        (class_id, session_date),
    )
    return int(row["n"]) if row else 0


def upcoming_sessions(days: int = 7, trainer_id: int | None = None) -> list[dict]:
    classes = classes_for_trainer(trainer_id) if trainer_id else list_classes()
    today = date.today()
    sessions = []
    for offset in range(days):
        session_day = today + timedelta(days=offset)
        for gym_class in classes:
            if gym_class["weekday"] != session_day.weekday():
                continue
            session_date = session_day.isoformat()
            taken = booked_count(gym_class["id"], session_date)
            sessions.append(
                {
                    **gym_class,
                    "session_date": session_date,
                    "weekday_name": WEEKDAYS[gym_class["weekday"]],
                    "booked": taken,
                    "spots_left": max(gym_class["capacity"] - taken, 0),
                }
            )
    sessions.sort(key=lambda row: (row["session_date"], row["start_time"]))
    return sessions


def booking_for(class_id: int, user_id: int, session_date: str) -> dict | None:
    return fetch_one(
        """
        SELECT * FROM class_bookings
        WHERE class_id = ? AND user_id = ? AND session_date = ?
        """,
        (class_id, user_id, session_date),
    )


def book_class(class_id: int, user_id: int, session_date: str) -> tuple[bool, str]:
    allowed, reason, _ = membership_access(user_id)
    if not allowed:
        return False, reason
    gym_class = fetch_one("SELECT * FROM gym_classes WHERE id = ?", (class_id,))
    if not gym_class:
        return False, "Class not found."
    if session_date < date.today().isoformat():
        return False, "That session has already passed."
    with get_conn() as conn:
        existing = conn.execute(
            """
            SELECT id, status FROM class_bookings
            WHERE class_id = ? AND user_id = ? AND session_date = ?
            """,
            (class_id, user_id, session_date),
        ).fetchone()
        if existing and existing["status"] in ("booked", "attended"):
            return False, "You already have a booking for this session."
        taken = conn.execute(
            """
            SELECT COUNT(*) AS n FROM class_bookings
            WHERE class_id = ? AND session_date = ? AND status IN ('booked', 'attended')
            """,
            (class_id, session_date),
        ).fetchone()["n"]
        if taken >= gym_class["capacity"]:
            return False, "This class is full."
        if existing and existing["status"] == "cancelled":
            conn.execute(
                "UPDATE class_bookings SET status = 'booked' WHERE id = ?",
                (existing["id"],),
            )
        else:
            conn.execute(
                """
                INSERT INTO class_bookings (class_id, user_id, session_date, status, created_at)
                VALUES (?, ?, ?, 'booked', ?)
                """,
                (class_id, user_id, session_date, now_iso()),
            )
    return True, "Class booked."


def cancel_booking(class_id: int, user_id: int, session_date: str) -> tuple[bool, str]:
    existing = booking_for(class_id, user_id, session_date)
    if not existing or existing["status"] == "cancelled":
        return False, "No active booking to cancel."
    if existing["status"] == "attended":
        return False, "This session was already marked attended."
    execute(
        "UPDATE class_bookings SET status = 'cancelled' WHERE id = ?",
        (existing["id"],),
    )
    return True, "Booking cancelled."


def roster(class_id: int, session_date: str) -> list[dict]:
    return fetch_all(
        """
        SELECT b.id, b.status, b.session_date, u.id AS user_id, u.name, u.email, u.phone
        FROM class_bookings b
        JOIN users u ON u.id = b.user_id
        WHERE b.class_id = ? AND b.session_date = ? AND b.status IN ('booked', 'attended')
        ORDER BY u.name
        """,
        (class_id, session_date),
    )


def mark_attended(booking_id: int) -> tuple[bool, str]:
    booking = fetch_one("SELECT * FROM class_bookings WHERE id = ?", (booking_id,))
    if not booking:
        return False, "Booking not found."
    if booking["status"] == "cancelled":
        return False, "Cancelled bookings cannot be marked attended."
    execute("UPDATE class_bookings SET status = 'attended' WHERE id = ?", (booking_id,))
    return True, "Marked attended."


def next_booking_for_member(user_id: int) -> dict | None:
    return fetch_one(
        """
        SELECT b.session_date, b.status, c.name, c.start_time, c.duration_min, u.name AS trainer_name
        FROM class_bookings b
        JOIN gym_classes c ON c.id = b.class_id
        JOIN users u ON u.id = c.trainer_id
        WHERE b.user_id = ? AND b.status = 'booked' AND b.session_date >= ?
        ORDER BY b.session_date, c.start_time
        LIMIT 1
        """,
        (user_id, today_iso()),
    )
