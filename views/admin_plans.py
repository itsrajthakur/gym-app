import streamlit as st

from services.memberships import create_plan, delete_plan, list_plans, update_plan
from services.ui import empty, flash, inr, page_header, set_flash, show_image

flash()
page_header("Plans", "Membership products sold at the front desk.", ":material/card_membership:")

plans = list_plans()
if plans:
    for start in range(0, len(plans), 3):
        cards = st.columns(3)
        for col, plan in zip(cards, plans[start : start + 3]):
            with col, st.container(border=True):
                if plan["duration_days"] <= 40:
                    show_image("class-hiit.png")
                elif plan["duration_days"] <= 120:
                    show_image("class-strength.png")
                else:
                    show_image("class-yoga.png")
                st.subheader(f":material/badge: {plan['name']}")
                st.metric("Price", inr(plan["price"]))
                st.caption(f":material/schedule: {plan['duration_days']} days · :material/groups: {plan['active_members']} active")
                st.write(plan["description"] or "")
else:
    empty("No plans yet. Create Monthly, Quarterly, or Annual access.", ":material/card_membership:")

st.subheader(":material/add: Create plan")
with st.form("create_plan", border=True):
    name = st.text_input("Name", placeholder="Monthly")
    duration = st.number_input("Duration (days)", min_value=1, value=30)
    price = st.number_input("Price (₹)", min_value=0.0, value=1499.0, step=100.0)
    description = st.text_area("Description")
    if st.form_submit_button("Create plan", type="primary", icon=":material/add:"):
        ok, message = create_plan(name, int(duration), float(price), description)
        if ok:
            set_flash(message)
            st.rerun()
        st.error(message, icon=":material/error:")

if plans:
    st.subheader(":material/edit: Edit or delete")
    selected = st.selectbox("Plan", plans, format_func=lambda p: p["name"])
    with st.form("edit_plan", border=True):
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
