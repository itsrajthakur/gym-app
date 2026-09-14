from __future__ import annotations

from db.database import execute, fetch_all, fetch_one, now_iso, today_iso
from services.members import membership_access


def check_in(user_id: int) -> tuple[bool, str]:
    allowed, reason, _ = membership_access(user_id)
    if not allowed:
        return False, reason
    already = fetch_one(
        """
        SELECT id FROM attendance
        WHERE user_id = ? AND date(check_in_at) = date(?)
        """,
        (user_id, today_iso()),
    )
    if already:
        return False, "Already checked in today."
    execute("INSERT INTO attendance (user_id, check_in_at) VALUES (?, ?)", (user_id, now_iso()))
    return True, "Checked in."


def todays_attendance() -> list[dict]:
    return fetch_all(
        """
        SELECT a.id, a.check_in_at, u.name, u.email
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
