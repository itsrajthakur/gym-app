from __future__ import annotations

from db.database import execute, fetch_all, fetch_one, today_iso


def list_users(role: str | None = None, search: str = "", include_inactive: bool = True) -> list[dict]:
    clauses = ["1=1"]
    params: list = []
    if role:
        clauses.append("u.role = ?")
        params.append(role)
    if not include_inactive:
        clauses.append("u.is_active = 1")
    search = search.strip()
    if search:
        clauses.append("(u.name LIKE ? OR u.email LIKE ? OR IFNULL(u.phone, '') LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like])
    where = " AND ".join(clauses)
    return fetch_all(
        f"""
        SELECT
            u.id, u.name, u.email, u.role, u.phone, u.is_active, u.created_at,
            m.status AS membership_status,
            m.end_date AS membership_end,
            p.name AS plan_name
        FROM users u
        LEFT JOIN memberships m ON m.id = (
            SELECT m2.id FROM memberships m2
            WHERE m2.user_id = u.id
            ORDER BY m2.start_date DESC, m2.id DESC
            LIMIT 1
        )
        LEFT JOIN membership_plans p ON p.id = m.plan_id
        WHERE {where}
        ORDER BY u.role, u.name
        """,
        tuple(params),
    )


def list_members(search: str = "") -> list[dict]:
    return list_users(role="member", search=search)


def list_trainers(active_only: bool = True) -> list[dict]:
    return list_users(role="trainer", include_inactive=not active_only)


def get_user(user_id: int) -> dict | None:
    return fetch_one(
        """
        SELECT id, name, email, role, phone, is_active, created_at
        FROM users WHERE id = ?
        """,
        (user_id,),
    )


def update_user(user_id: int, name: str, phone: str, is_active: bool) -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "Name is required."
    execute(
        "UPDATE users SET name = ?, phone = ?, is_active = ? WHERE id = ?",
        (name, phone.strip(), 1 if is_active else 0, user_id),
    )
    return True, "Profile updated."


def current_membership(user_id: int) -> dict | None:
    return fetch_one(
        """
        SELECT m.*, p.name AS plan_name, p.price AS plan_price, p.duration_days
        FROM memberships m
        JOIN membership_plans p ON p.id = m.plan_id
        WHERE m.user_id = ?
        ORDER BY m.start_date DESC, m.id DESC
        LIMIT 1
        """,
        (user_id,),
    )


def membership_access(user_id: int) -> tuple[bool, str, dict | None]:
    membership = current_membership(user_id)
    if not membership:
        return False, "No membership assigned. Ask the front desk to assign a plan.", None
    if membership["status"] == "frozen":
        return False, "Membership is frozen. Check-ins and class booking are paused.", membership
    if membership["status"] == "expired" or membership["end_date"] < today_iso():
        return False, "Membership has expired. Renew at the front desk to continue.", membership
    if membership["status"] != "active":
        return False, f"Membership is {membership['status']}.", membership
    return True, "", membership
