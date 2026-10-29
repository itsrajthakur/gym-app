from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import streamlit as st

from db.database import ROOT, execute, fetch_all, fetch_one, now_iso, today_iso

ADS_DIR = ROOT / "data" / "ads"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
METHODS = ("upi", "card", "cash")


def expire_ads() -> None:
    execute(
        """
        UPDATE advertisements
        SET status = 'expired'
        WHERE status IN ('active', 'paused') AND date(end_date) < date(?)
        """,
        (today_iso(),),
    )


def list_plans() -> list[dict]:
    return fetch_all(
        """
        SELECT p.*, (
            SELECT COUNT(*) FROM advertisements a
            WHERE a.plan_id = p.id AND a.status = 'active' AND date(a.end_date) >= date(?)
        ) AS live_ads
        FROM ad_plans p
        ORDER BY p.duration_days
        """,
        (today_iso(),),
    )


def get_plan(plan_id: int) -> dict | None:
    return fetch_one("SELECT * FROM ad_plans WHERE id = ?", (plan_id,))


def create_plan(name: str, duration_days: int, price: float, description: str) -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "Plan name is required."
    if duration_days <= 0:
        return False, "Duration must be greater than zero."
    if price < 0:
        return False, "Price cannot be negative."
    execute(
        "INSERT INTO ad_plans (name, duration_days, price, description) VALUES (?, ?, ?, ?)",
        (name, duration_days, price, description.strip()),
    )
    return True, "Ad plan created."


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
        UPDATE ad_plans
        SET name = ?, duration_days = ?, price = ?, description = ?
        WHERE id = ?
        """,
        (name, duration_days, price, description.strip(), plan_id),
    )
    return True, "Ad plan updated."


def delete_plan(plan_id: int) -> tuple[bool, str]:
    in_use = fetch_one("SELECT COUNT(*) AS n FROM advertisements WHERE plan_id = ?", (plan_id,))
    if in_use and in_use["n"] > 0:
        return False, "This plan is used by advertisements and cannot be deleted."
    execute("DELETE FROM ad_plans WHERE id = ?", (plan_id,))
    return True, "Ad plan deleted."


def save_ad_image(upload) -> tuple[str | None, str]:
    if upload is None:
        return None, "Upload an advertisement image."
    ext = Path(upload.name).suffix.lower()
    if ext not in IMAGE_EXTS:
        return None, "Use a PNG, JPG, or WEBP image."
    ADS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{ext}"
    path = ADS_DIR / filename
    path.write_bytes(upload.getvalue())
    return f"data/ads/{filename}", ""


def create_ad(
    advertiser_name: str,
    advertiser_phone: str,
    title: str,
    body: str,
    link_url: str,
    plan_id: int,
    amount: float,
    method: str,
    upload,
) -> tuple[bool, str]:
    advertiser_name = advertiser_name.strip()
    title = title.strip()
    body = body.strip()
    link_url = link_url.strip()
    advertiser_phone = advertiser_phone.strip()
    if not advertiser_name:
        return False, "Advertiser name is required."
    if not title:
        return False, "Ad title is required."
    if method not in METHODS:
        return False, "Choose cash, card, or UPI."
    plan = get_plan(plan_id)
    if not plan:
        return False, "Select a valid ad plan."
    if amount < 0:
        return False, "Amount cannot be negative."
    image_path, image_error = save_ad_image(upload)
    if image_error:
        return False, image_error
    start = date.today()
    end = start + timedelta(days=int(plan["duration_days"]) - 1)
    execute(
        """
        INSERT INTO advertisements (
            advertiser_name, advertiser_phone, title, body, image_path, link_url,
            plan_id, start_date, end_date, status, amount, method, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
        """,
        (
            advertiser_name,
            advertiser_phone,
            title,
            body,
            image_path,
            link_url,
            plan_id,
            start.isoformat(),
            end.isoformat(),
            float(amount),
            method,
            now_iso(),
        ),
    )
    return True, f"Ad live until {end.isoformat()}."


def list_ads(status: str | None = None) -> list[dict]:
    sql = """
        SELECT a.*, p.name AS plan_name, p.duration_days
        FROM advertisements a
        JOIN ad_plans p ON p.id = a.plan_id
    """
    params: tuple = ()
    if status:
        sql += " WHERE a.status = ?"
        params = (status,)
    sql += " ORDER BY a.created_at DESC"
    return fetch_all(sql, params)


def get_ad(ad_id: int) -> dict | None:
    return fetch_one(
        """
        SELECT a.*, p.name AS plan_name, p.duration_days
        FROM advertisements a
        JOIN ad_plans p ON p.id = a.plan_id
        WHERE a.id = ?
        """,
        (ad_id,),
    )


def active_ads() -> list[dict]:
    return fetch_all(
        """
        SELECT a.*, p.name AS plan_name
        FROM advertisements a
        JOIN ad_plans p ON p.id = a.plan_id
        WHERE a.status = 'active'
          AND date(a.start_date) <= date(?)
          AND date(a.end_date) >= date(?)
        ORDER BY a.id
        """,
        (today_iso(), today_iso()),
    )


def pause_ad(ad_id: int) -> tuple[bool, str]:
    ad = get_ad(ad_id)
    if not ad:
        return False, "Advertisement not found."
    if ad["status"] != "active":
        return False, "Only a live ad can be paused."
    execute("UPDATE advertisements SET status = 'paused' WHERE id = ?", (ad_id,))
    return True, "Ad paused. Members will not see it."


def resume_ad(ad_id: int) -> tuple[bool, str]:
    ad = get_ad(ad_id)
    if not ad:
        return False, "Advertisement not found."
    if ad["status"] != "paused":
        return False, "Only a paused ad can be resumed."
    if ad["end_date"] < today_iso():
        execute("UPDATE advertisements SET status = 'expired' WHERE id = ?", (ad_id,))
        return False, "This ad has already expired."
    execute("UPDATE advertisements SET status = 'active' WHERE id = ?", (ad_id,))
    return True, "Ad is live again."


def expire_ad(ad_id: int) -> tuple[bool, str]:
    ad = get_ad(ad_id)
    if not ad:
        return False, "Advertisement not found."
    if ad["status"] == "expired":
        return False, "This ad is already expired."
    execute("UPDATE advertisements SET status = 'expired' WHERE id = ?", (ad_id,))
    return True, "Ad expired. Members will not see it."


def ad_image_path(ad: dict) -> Path | None:
    relative = ad.get("image_path") or ""
    if not relative:
        return None
    path = ROOT / relative
    return path if path.exists() else None


def pick_ad(ads: list[dict], page_title: str) -> dict | None:
    if not ads:
        return None
    day = date.today().toordinal()
    index = (day + sum(ord(ch) for ch in page_title)) % len(ads)
    return ads[index]


def render_member_ads(page_title: str = "Home") -> None:
    ads = active_ads()
    ad = pick_ad(ads, page_title)
    if not ad:
        return
    with st.container(border=True):
        photo, copy = st.columns([1, 2.2], vertical_alignment="center")
        with photo:
            image = ad_image_path(ad)
            if image:
                st.image(str(image), width="stretch")
        with copy:
            st.caption(":material/campaign: Advertisement")
            st.subheader(ad["title"])
            if ad.get("body"):
                st.write(ad["body"])
            st.caption(ad["advertiser_name"])
            link = (ad.get("link_url") or "").strip()
            if link:
                if not link.startswith(("http://", "https://")):
                    link = f"https://{link}"
                st.link_button("Visit site", link, icon=":material/open_in_new:")
