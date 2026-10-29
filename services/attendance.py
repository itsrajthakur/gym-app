from __future__ import annotations

from db.database import execute, fetch_all, fetch_one, now_iso, today_iso
from services.members import membership_access

SOURCES = {"self", "desk"}


def source_label(source: str | None) -> str:
    return "Self" if source == "self" else "Desk"


def check_in_time(row: dict) -> str:
    stamp = row.get("check_in_at") or ""
    parts = stamp.split(" ")
    return parts[1][:5] if len(parts) > 1 else stamp


def todays_check_in(user_id: int) -> dict | None:
    return fetch_one(
        """
        SELECT id, user_id, check_in_at, source
        FROM attendance
        WHERE user_id = ? AND date(check_in_at) = date(?)
        """,
        (user_id, today_iso()),
    )


def member_history(user_id: int, days: int = 14) -> list[dict]:
    return fetch_all(
        """
        SELECT id, check_in_at, source
        FROM attendance
        WHERE user_id = ? AND date(check_in_at) >= date(?, ?)
        ORDER BY check_in_at DESC
        """,
        (user_id, today_iso(), f"-{days - 1} days"),
    )


def check_in(user_id: int, source: str = "desk") -> tuple[bool, str]:
    if source not in SOURCES:
        return False, "Invalid check-in source."
    allowed, reason, _ = membership_access(user_id)
    if not allowed:
        return False, reason
    already = todays_check_in(user_id)
    if already:
        return False, "Already checked in today."
    execute(
        "INSERT INTO attendance (user_id, check_in_at, source) VALUES (?, ?, ?)",
        (user_id, now_iso(), source),
    )
    return True, "Checked in."


def todays_attendance() -> list[dict]:
    return fetch_all(
        """
        SELECT a.id, a.check_in_at, a.source, u.name, u.email
        FROM attendance a
        JOIN users u ON u.id = a.user_id
        WHERE date(a.check_in_at) = date(?)
        ORDER BY a.check_in_at DESC
        """,
        (today_iso(),),
    )


def recent_attendance(days: int = 14) -> list[dict]:
    return fetch_all(
        """
        SELECT date(check_in_at) AS day, COUNT(*) AS check_ins
        FROM attendance
        WHERE date(check_in_at) >= date(?, ?)
        GROUP BY date(check_in_at)
        ORDER BY day
        """,
        (today_iso(), f"-{days - 1} days"),
    )
