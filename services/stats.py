from __future__ import annotations

from db.database import fetch_all, fetch_one, today_iso


def admin_kpis() -> dict:
    active = fetch_one(
        """
        SELECT COUNT(*) AS n FROM memberships
        WHERE status = 'active' AND date(end_date) >= date(?)
        """,
        (today_iso(),),
    )["n"]
    checkins = fetch_one(
        "SELECT COUNT(*) AS n FROM attendance WHERE date(check_in_at) = date(?)",
        (today_iso(),),
    )["n"]
    revenue = fetch_one(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM payments
        WHERE strftime('%Y-%m', paid_at) = strftime('%Y-%m', ?)
        """,
        (today_iso(),),
    )["total"]
    return {
        "active_members": active,
        "checkins_today": checkins,
        "revenue_month": float(revenue or 0),
    }


def revenue_by_method() -> list[dict]:
    return fetch_all(
        """
        SELECT method, SUM(amount) AS total
        FROM payments
        WHERE strftime('%Y-%m', paid_at) = strftime('%Y-%m', ?)
        GROUP BY method
        ORDER BY total DESC
        """,
        (today_iso(),),
    )


def membership_mix() -> list[dict]:
    return fetch_all(
        """
        SELECT COALESCE(p.name, 'No plan') AS plan, COUNT(*) AS members
        FROM users u
        LEFT JOIN memberships m ON m.id = (
            SELECT m2.id FROM memberships m2
            WHERE m2.user_id = u.id
            ORDER BY m2.start_date DESC, m2.id DESC
            LIMIT 1
        )
        LEFT JOIN membership_plans p ON p.id = m.plan_id
        WHERE u.role = 'member' AND u.is_active = 1
        GROUP BY plan
        ORDER BY members DESC
        """
    )
