import streamlit as st

from services.auth import login, register_member
from services.ui import set_flash, show_image

visual, form = st.columns([1.15, 0.95], gap="large", vertical_alignment="center")

with visual:
    show_image("hero-login.png")
    st.markdown("### :material/exercise: Train with intent")
    st.caption("Check in, book classes, and track every session from one dark-mode gym desk.")

with form:
    show_image("pulse-logo.png", width=88)
    st.header("Pulse Gym")
    st.caption("Welcome back. Sign in or create a member account.")

    mode = st.segmented_control(
        "Account",
        options=["Sign in", "Create member account"],
        default="Sign in",
        key="auth_mode",
        label_visibility="collapsed",
    )

    if mode == "Sign in":
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@email.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Sign in",
                type="primary",
                width="stretch",
                icon=":material/login:",
            )
        if submitted:
            user = login(email, password)
            if not user:
                st.error("Invalid email, password, or inactive account.", icon=":material/lock:")
            else:
                st.session_state.user = user
                st.rerun()
    else:
        with st.form("register_form"):
            name = st.text_input("Full name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Create account",
                type="primary",
                width="stretch",
                icon=":material/person_add:",
            )
        if submitted:
            ok, message, user = register_member(name, email, password, phone)
            if not ok:
                st.error(message, icon=":material/error:")
            else:
                st.session_state.user = user
                set_flash(message)
                st.rerun()

    with st.expander("Demo accounts", icon=":material/key:"):
        st.markdown(
            """
            | Role | Email | Password |
            | --- | --- | --- |
            | :material/admin_panel_settings: Admin | `admin@pulsegym.local` | `admin123` |
            | :material/sports: Trainer | `priya.trainer@pulsegym.local` | `demo123` |
            | :material/person: Member (active) | `ananya@example.com` | `demo123` |
            | :material/event_busy: Member (expired) | `meera@example.com` | `demo123` |
            | :material/ac_unit: Member (frozen) | `kabir@example.com` | `demo123` |
            """
        )
