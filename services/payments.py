from __future__ import annotations

from db.database import execute, fetch_all, now_iso

PAYMENT_METHODS = ("cash", "card", "upi")


def record_payment(
    user_id: int,
    amount: float,
    method: str,
    membership_id: int | None = None,
    notes: str = "",
) -> tuple[bool, str]:
    if amount < 0:
        return False, "Amount cannot be negative."
    if method not in PAYMENT_METHODS:
        return False, "Choose cash, card, or UPI."
    execute(
        """
        INSERT INTO payments (user_id, membership_id, amount, method, paid_at, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, membership_id, amount, method, now_iso(), notes.strip()),
    )
    return True, "Payment recorded."


def list_payments(limit: int = 200) -> list[dict]:
    return fetch_all(
        """
        SELECT
            p.id, p.amount, p.method, p.paid_at, p.notes,
            u.name AS member_name, u.email,
            mp.name AS plan_name
        FROM payments p
        JOIN users u ON u.id = p.user_id
        LEFT JOIN memberships m ON m.id = p.membership_id
        LEFT JOIN membership_plans mp ON mp.id = m.plan_id
        ORDER BY p.paid_at DESC
        LIMIT ?
        """,
        (limit,),
    )
