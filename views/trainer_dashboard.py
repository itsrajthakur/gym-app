import streamlit as st

from services.classes import WEEKDAYS, upcoming_sessions
from services.ui import class_icon, empty, flash, page_header, show_class_art

flash()
page_header("Dashboard", "Your classes for the next week.", ":material/dashboard:")

user = st.session_state.user
sessions = upcoming_sessions(7, trainer_id=user["id"])

if not sessions:
    empty("You have no classes on the schedule. Ask an admin to assign one.", ":material/event_busy:")
else:
    with st.container(horizontal=True):
        st.metric(":material/calendar_month: Sessions this week", len(sessions), border=True)
        st.metric(":material/groups: Booked seats", sum(s["booked"] for s in sessions), border=True)
        st.metric(":material/event_available: Open spots", sum(s["spots_left"] for s in sessions), border=True)

    for session in sessions:
        with st.container(border=True):
            photo, body = st.columns([1, 2.6], vertical_alignment="center")
            with photo:
                show_class_art(session["name"])
            with body:
                st.subheader(f"{class_icon(session['name'])} {session['name']}")
                st.caption(
                    f":material/schedule: {WEEKDAYS[session['weekday']]} {session['session_date']} · "
                    f"{session['start_time']} · {session['booked']}/{session['capacity']} booked"
                )
