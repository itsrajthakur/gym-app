from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "gym.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_iso() -> str:
    return date.today().isoformat()


@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    with get_conn() as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def fetch_one(sql: str, params: tuple = ()) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None


def execute(sql: str, params: tuple = ()) -> int:
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        return int(cur.lastrowid)


def execute_many(sql: str, seq_of_params: list[tuple]) -> None:
    with get_conn() as conn:
        conn.executemany(sql, seq_of_params)


def _migrate(conn: sqlite3.Connection) -> None:
    attendance_cols = {row[1] for row in conn.execute("PRAGMA table_info(attendance)")}
    if "source" not in attendance_cols:
        conn.execute("ALTER TABLE attendance ADD COLUMN source TEXT NOT NULL DEFAULT 'desk'")


def init_db() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_conn() as conn:
        conn.executescript(schema)
        _migrate(conn)
    from db.seed import seed_ad_plans_if_empty, seed_if_empty

    seed_if_empty()
    seed_ad_plans_if_empty()


def expire_memberships() -> None:
    execute(
        """
        UPDATE memberships
        SET status = 'expired'
        WHERE status = 'active' AND date(end_date) < date(?)
        """,
        (today_iso(),),
    )
