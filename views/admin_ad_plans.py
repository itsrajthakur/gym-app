import streamlit as st

from services.ads import create_plan, delete_plan, list_plans, update_plan
from services.ui import empty, flash, inr, page_header, set_flash

flash()
page_header("Ad plans", "Prices for running a banner on member pages.", ":material/sell:")

plans = list_plans()
if plans:
    cols = st.columns(min(4, len(plans)))
    for col, plan in zip(cols, plans):
        with col, st.container(border=True):
            st.subheader(f":material/schedule: {plan['name']}")
            st.metric("Price", inr(plan["price"]))
            st.caption(
                f":material/calendar_today: {plan['duration_days']} day{'s' if plan['duration_days'] != 1 else ''} · "
                f":material/campaign: {plan['live_ads']} live"
            )
            st.write(plan["description"] or "")
else:
    empty("No ad plans yet. Create 1 Day, 1 Week, 1 Month, and 1 Year.", ":material/sell:")

st.subheader(":material/add: Create plan")
with st.form("create_ad_plan", border=True):
    name = st.text_input("Name", placeholder="1 Week")
    duration = st.number_input("Duration (days)", min_value=1, value=7)
    price = st.number_input("Price (₹)", min_value=0.0, value=999.0, step=100.0)
    description = st.text_area("Description")
    if st.form_submit_button("Create plan", type="primary", icon=":material/add:"):
        ok, message = create_plan(name, int(duration), float(price), description)
        if ok:
            set_flash(message)
            st.rerun()
        st.error(message, icon=":material/error:")

if plans:
    st.subheader(":material/edit: Edit or delete")
    selected = st.selectbox("Plan", plans, format_func=lambda p: f"{p['name']} · {inr(p['price'])}")
    with st.form("edit_ad_plan", border=True):
        name = st.text_input("Name", value=selected["name"])
        duration = st.number_input("Duration (days)", min_value=1, value=int(selected["duration_days"]))
        price = st.number_input("Price (₹)", min_value=0.0, value=float(selected["price"]), step=100.0)
        description = st.text_area("Description", value=selected["description"] or "")
        save = st.form_submit_button("Save changes", type="primary", icon=":material/save:")
        delete = st.form_submit_button("Delete plan", icon=":material/delete:")
    if save:
        ok, message = update_plan(selected["id"], name, int(duration), float(price), description)
        set_flash(message, "success" if ok else "error")
        st.rerun()
    if delete:
        ok, message = delete_plan(selected["id"])
        set_flash(message, "success" if ok else "error")
        st.rerun()
