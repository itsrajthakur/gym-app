from __future__ import annotations

import re
import sqlite3

from passlib.hash import pbkdf2_sha256

from db.database import execute, fetch_one, now_iso

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pbkdf2_sha256.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def public_user(row: dict) -> dict:
    user = dict(row)
    user.pop("password_hash", None)
    return user


def get_user_by_email(email: str) -> dict | None:
    return fetch_one("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),))


def login(email: str, password: str) -> dict | None:
    user = get_user_by_email(email)
    if not user:
        return None
    if not user["is_active"]:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return public_user(user)


def register_member(name: str, email: str, password: str, phone: str = "") -> tuple[bool, str, dict | None]:
    name = name.strip()
    email = email.strip().lower()
    phone = phone.strip()
    if not name:
        return False, "Enter your name.", None
    if not EMAIL_RE.match(email):
        return False, "Enter a valid email address.", None
    if len(password) < 6:
        return False, "Password must be at least 6 characters.", None
    try:
        user_id = execute(
            """
            INSERT INTO users (name, email, password_hash, role, phone, is_active, created_at)
            VALUES (?, ?, ?, 'member', ?, 1, ?)
            """,
            (name, email, hash_password(password), phone, now_iso()),
        )
    except sqlite3.IntegrityError:
        return False, "That email is already registered.", None
    user = fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return True, "Account created. Ask the front desk to assign a membership.", public_user(user)


def create_user(
    name: str,
    email: str,
    password: str,
    role: str,
    phone: str = "",
) -> tuple[bool, str, dict | None]:
    name = name.strip()
    email = email.strip().lower()
    phone = phone.strip()
    if role not in {"admin", "trainer", "member"}:
        return False, "Invalid role.", None
    if not name:
        return False, "Name is required.", None
    if not EMAIL_RE.match(email):
        return False, "Enter a valid email address.", None
    if len(password) < 6:
        return False, "Password must be at least 6 characters.", None
    try:
        user_id = execute(
            """
            INSERT INTO users (name, email, password_hash, role, phone, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (name, email, hash_password(password), role, phone, now_iso()),
        )
    except sqlite3.IntegrityError:
        return False, "That email is already registered.", None
    return True, "User created.", fetch_one(
        "SELECT id, name, email, role, phone, is_active, created_at FROM users WHERE id = ?",
        (user_id,),
    )
