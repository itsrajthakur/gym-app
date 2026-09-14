import streamlit as st

from services.classes import WEEKDAYS, book_class, booking_for, cancel_booking, upcoming_sessions
from services.members import membership_access
from services.ui import class_icon, empty, flash, page_header, set_flash, show_class_art, status_badge

flash()
page_header("Classes", "Book a session in the next 7 days. Capacity is first-come, first-served.", ":material/event:")

user = st.session_state.user
allowed, reason, membership = membership_access(user["id"])
if membership:
    status_badge(membership["status"])
if not allowed:
    st.warning(reason, icon=":material/warning:")

sessions = upcoming_sessions(7)
if not sessions:
    empty("No classes are scheduled this week.", ":material/event_busy:")
    st.stop()

for session in sessions:
    existing = booking_for(session["id"], user["id"], session["session_date"])
    active = existing and existing["status"] in ("booked", "attended")
    with st.container(border=True):
        photo, body = st.columns([1, 2.3], vertical_alignment="center")
        with photo:
            show_class_art(session["name"])
        with body:
            st.subheader(f"{class_icon(session['name'])} {session['name']}")
            st.caption(
                f":material/schedule: {WEEKDAYS[session['weekday']]} {session['session_date']} · "
                f"{session['start_time']} · {session['trainer_name']}"
            )
            st.caption(
                f":material/groups: {session['booked']}/{session['capacity']} booked · "
                f"{session['spots_left']} spots left"
            )
            if session.get("description"):
                st.write(session["description"])
            key = f"{session['id']}_{session['session_date']}"
            if active:
                status_badge(existing["status"])
                if existing["status"] == "booked":
                    confirm_key = f"confirm_cancel_{key}"
                    if st.session_state.get(confirm_key):
                        st.warning(
                            "Cancel this booking? The spot will open for someone else.",
                            icon=":material/warning:",
                        )
                        yes, no = st.columns(2)
                        if yes.button("Yes, cancel", key=f"yes_{key}", icon=":material/cancel:"):
                            st.session_state.pop(confirm_key, None)
                            ok, message = cancel_booking(session["id"], user["id"], session["session_date"])
                            set_flash(message, "success" if ok else "error")
                            st.rerun()
                        if no.button("Keep booking", key=f"no_{key}", icon=":material/event_available:"):
                            st.session_state.pop(confirm_key, None)
                            st.rerun()
                    elif st.button("Cancel booking", key=f"cancel_{key}", icon=":material/event_busy:"):
                        st.session_state[confirm_key] = True
                        st.rerun()
            else:
                disabled = (not allowed) or session["spots_left"] <= 0
                label = "Class full" if session["spots_left"] <= 0 else "Book"
                icon = ":material/block:" if disabled else ":material/event_available:"
                if st.button(label, key=f"book_{key}", type="primary", disabled=disabled, icon=icon):
                    ok, message = book_class(session["id"], user["id"], session["session_date"])
                    set_flash(message, "success" if ok else "error")
                    st.rerun()
                if not allowed:
                    st.caption(reason)
                elif session["spots_left"] <= 0:
                    st.caption("This class is full.")
