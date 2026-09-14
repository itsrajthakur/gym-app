import streamlit as st

from services.auth import create_user
from services.members import list_members, list_trainers, update_user
from services.memberships import (
    assign_membership,
    freeze_membership,
    list_plans,
    renew_membership,
    unfreeze_membership,
)
from services.payments import record_payment
from services.ui import empty, flash, inr, page_header, person_title, set_flash, status_badge

flash()
page_header("Members", "Search the roster, assign plans, and freeze or renew access.", ":material/groups:")

search = st.text_input(
    "Search name, email, or phone",
    placeholder="Start typing…",
    icon=":material/search:",
)
members = list_members(search)
plans = list_plans()
plan_labels = {f"{p['name']} · {inr(p['price'])} / {p['duration_days']} days": p["id"] for p in plans}

tab_list, tab_add = st.tabs([":material/groups: Roster", ":material/person_add: Add person"])

with tab_add:
    with st.form("add_person", border=True):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        role = st.selectbox("Role", ["member", "trainer"])
        password = st.text_input("Temporary password", type="password", value="demo123")
        submitted = st.form_submit_button("Create", type="primary", icon=":material/person_add:")
    if submitted:
        ok, message, _ = create_user(name, email, password, role, phone)
        if ok:
            set_flash(message)
            st.rerun()
        st.error(message, icon=":material/error:")

with tab_list:
    if not members:
        empty("No members match that search. Add a member to get started.", ":material/person_search:")
    else:
        for member in members:
            with st.container(border=True):
                top = st.container(horizontal=True, vertical_alignment="center")
                with top:
                    person_title(member["name"], "member")
                    status_badge(member["membership_status"])
                st.caption(f":material/mail: {member['email']} · :material/call: {member['phone'] or 'No phone'}")
                if member["plan_name"]:
                    st.caption(f":material/card_membership: {member['plan_name']} through {member['membership_end']}")
                else:
                    st.caption(":material/info: No membership assigned.")

                action = st.pills(
                    "Actions",
                    ["Edit", "Assign / renew", "Freeze", "Unfreeze"],
                    key=f"member_action_{member['id']}",
                    label_visibility="collapsed",
                )
                if action == "Edit":
                    with st.form(f"edit_{member['id']}"):
                        name = st.text_input("Name", value=member["name"])
                        phone = st.text_input("Phone", value=member["phone"] or "")
                        active = st.toggle("Active account", value=bool(member["is_active"]))
                        if st.form_submit_button("Save", type="primary", icon=":material/save:"):
                            ok, message = update_user(member["id"], name, phone, active)
                            if ok:
                                set_flash(message)
                                st.rerun()
                            st.error(message, icon=":material/error:")
                elif action == "Assign / renew":
                    if not plans:
                        st.warning("Create a membership plan first.", icon=":material/warning:")
                    else:
                        with st.form(f"assign_{member['id']}"):
                            plan_label = st.selectbox("Plan", list(plan_labels))
                            take_payment = st.checkbox("Record payment for plan price", value=True)
                            method = st.selectbox("Payment method", ["upi", "card", "cash"])
                            if st.form_submit_button("Assign plan", type="primary", icon=":material/card_membership:"):
                                plan_id = plan_labels[plan_label]
                                if member["membership_status"] == "active":
                                    ok, message, membership_id = renew_membership(member["id"], plan_id)
                                else:
                                    ok, message, membership_id = assign_membership(member["id"], plan_id)
                                if ok and take_payment:
                                    plan = next(p for p in plans if p["id"] == plan_id)
                                    record_payment(member["id"], plan["price"], method, membership_id, "Plan assignment")
                                if ok:
                                    set_flash(message)
                                    st.rerun()
                                st.error(message, icon=":material/error:")
                elif action == "Freeze":
                    st.warning(
                        f"Freeze membership for {member['name']}? They will not be able to check in or book classes.",
                        icon=":material/ac_unit:",
                    )
                    confirm, cancel = st.columns(2)
                    if confirm.button("Confirm freeze", type="primary", key=f"freeze_{member['id']}", icon=":material/ac_unit:"):
                        ok, message = freeze_membership(member["id"])
                        set_flash(message, "success" if ok else "error")
                        st.rerun()
                    if cancel.button("Not now", key=f"freeze_cancel_{member['id']}", icon=":material/close:"):
                        st.rerun()
                elif action == "Unfreeze":
                    if st.button("Unfreeze membership", key=f"unfreeze_{member['id']}", icon=":material/wb_sunny:"):
                        ok, message = unfreeze_membership(member["id"])
                        set_flash(message, "success" if ok else "error")
                        st.rerun()

st.subheader(":material/sports: Trainers")
trainers = list_trainers(active_only=False)
if not trainers:
    empty("No trainers yet. Add a trainer from the Add person tab.", ":material/sports:")
else:
    for trainer in trainers:
        with st.container(border=True):
            person_title(trainer["name"], "trainer")
            st.caption(f":material/mail: {trainer['email']} · :material/call: {trainer['phone'] or 'No phone'}")
            status_badge("active" if trainer["is_active"] else "expired")
