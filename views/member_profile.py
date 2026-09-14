import streamlit as st

from services.members import current_membership, get_user, membership_access, update_user
from services.ui import flash, membership_panel, page_header, set_flash

flash()
page_header("Profile", "Your membership card and contact details.", ":material/person:")
user = get_user(st.session_state.user["id"]) or st.session_state.user
allowed, reason, membership = membership_access(user["id"])
membership = membership or current_membership(user["id"])

if membership:
    membership_panel(membership, user["name"])
    if not allowed:
        st.warning(reason, icon=":material/warning:")
else:
    st.info(reason, icon=":material/info:")

with st.form("profile", border=True):
    name = st.text_input("Name", value=user["name"])
    st.text_input("Email", value=user["email"], disabled=True)
    phone = st.text_input("Phone", value=user.get("phone") or "")
    if st.form_submit_button("Save profile", type="primary", icon=":material/save:"):
        ok, message = update_user(user["id"], name, phone, bool(user.get("is_active", True)))
        if ok:
            st.session_state.user["name"] = name.strip()
            st.session_state.user["phone"] = phone.strip()
            set_flash(message)
            st.rerun()
        st.error(message, icon=":material/error:")
