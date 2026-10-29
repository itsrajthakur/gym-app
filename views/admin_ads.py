import pandas as pd
import streamlit as st

from services.ads import (
    ad_image_path,
    create_ad,
    expire_ad,
    list_ads,
    list_plans,
    pause_ad,
    resume_ad,
)
from services.ui import empty, flash, inr, page_header, set_flash, status_badge

flash()
page_header("Ads", "Take payment from an advertiser, then run their banner until the plan ends.", ":material/campaign:")

plans = list_plans()
st.subheader(":material/add: Run an advertisement")
if not plans:
    st.warning("Create an ad plan first (1 Day, 1 Week, 1 Month, or 1 Year).", icon=":material/warning:")
else:
    with st.form("create_ad", border=True):
        advertiser_name = st.text_input("Advertiser name")
        advertiser_phone = st.text_input("Advertiser phone")
        title = st.text_input("Ad title")
        body = st.text_area("Short text")
        link_url = st.text_input("Website (optional)", placeholder="https://example.com")
        upload = st.file_uploader("Banner image", type=["png", "jpg", "jpeg", "webp"])
        plan = st.selectbox(
            "Plan",
            plans,
            format_func=lambda p: f"{p['name']} · {inr(p['price'])} / {p['duration_days']} day{'s' if p['duration_days'] != 1 else ''}",
        )
        amount = st.number_input("Amount received (₹)", min_value=0.0, value=float(plan["price"]), step=100.0)
        method = st.selectbox("Payment method", ["upi", "card", "cash"])
        if st.form_submit_button("Start ad", type="primary", icon=":material/campaign:"):
            ok, message = create_ad(
                advertiser_name,
                advertiser_phone,
                title,
                body,
                link_url,
                plan["id"],
                float(amount),
                method,
                upload,
            )
            if ok:
                set_flash(message)
                st.rerun()
            st.error(message, icon=":material/error:")

ads = list_ads()
live = [row for row in ads if row["status"] == "active"]
paused = [row for row in ads if row["status"] == "paused"]
expired = [row for row in ads if row["status"] == "expired"]

tab_live, tab_paused, tab_expired = st.tabs(
    [
        f":material/campaign: Live ({len(live)})",
        f":material/pause_circle: Paused ({len(paused)})",
        f":material/event_busy: Expired ({len(expired)})",
    ]
)


def _ad_card(ad: dict, *, actions: str) -> None:
    with st.container(border=True):
        photo, body = st.columns([1, 2.4], vertical_alignment="center")
        with photo:
            image = ad_image_path(ad)
            if image:
                st.image(str(image), width="stretch")
        with body:
            st.subheader(ad["title"])
            status_badge(ad["status"])
            st.caption(
                f":material/store: {ad['advertiser_name']}"
                + (f" · :material/call: {ad['advertiser_phone']}" if ad.get("advertiser_phone") else "")
            )
            if ad.get("body"):
                st.write(ad["body"])
            st.caption(
                f":material/sell: {ad['plan_name']} · {ad['start_date']} → {ad['end_date']} · "
                f"{inr(ad['amount'])} {ad['method'].upper()}"
            )
            if ad.get("link_url"):
                st.caption(ad["link_url"])
            if actions == "live":
                pause, stop = st.columns(2)
                if pause.button("Pause", key=f"pause_{ad['id']}", icon=":material/pause:"):
                    ok, message = pause_ad(ad["id"])
                    set_flash(message, "success" if ok else "error")
                    st.rerun()
                if stop.button("Expire now", key=f"expire_{ad['id']}", icon=":material/event_busy:"):
                    ok, message = expire_ad(ad["id"])
                    set_flash(message, "success" if ok else "error")
                    st.rerun()
            elif actions == "paused":
                play, stop = st.columns(2)
                if play.button("Resume", key=f"resume_{ad['id']}", type="primary", icon=":material/play_arrow:"):
                    ok, message = resume_ad(ad["id"])
                    set_flash(message, "success" if ok else "error")
                    st.rerun()
                if stop.button("Expire now", key=f"expire_paused_{ad['id']}", icon=":material/event_busy:"):
                    ok, message = expire_ad(ad["id"])
                    set_flash(message, "success" if ok else "error")
                    st.rerun()


with tab_live:
    if not live:
        empty("No live ads. Start one above after taking payment.", ":material/campaign:")
    else:
        for ad in live:
            _ad_card(ad, actions="live")

with tab_paused:
    if not paused:
        empty("No paused ads.", ":material/pause_circle:")
    else:
        for ad in paused:
            _ad_card(ad, actions="paused")

with tab_expired:
    if not expired:
        empty("No expired ads yet.", ":material/event_busy:")
    else:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Advertiser": row["advertiser_name"],
                        "Title": row["title"],
                        "Plan": row["plan_name"],
                        "Ran": f"{row['start_date']} → {row['end_date']}",
                        "Paid": inr(row["amount"]),
                    }
                    for row in expired
                ]
            ),
            hide_index=True,
            width="stretch",
        )
