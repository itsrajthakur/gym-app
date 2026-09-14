import pandas as pd
import streamlit as st

from services.classes import WEEKDAYS, mark_attended, roster, upcoming_sessions
from services.ui import class_icon, empty, flash, page_header, set_flash, show_class_art

flash()
page_header("Roster", "See who booked your class and mark attendance.", ":material/list:")

user = st.session_state.user
sessions = upcoming_sessions(14, trainer_id=user["id"])
if not sessions:
    empty("No upcoming classes assigned to you.", ":material/event_busy:")
    st.stop()

labels = {
    f"{s['session_date']} {s['start_time']} · {s['name']} ({s['booked']}/{s['capacity']})": s
    for s in sessions
}
choice = st.selectbox("Session", list(labels))
session = labels[choice]
people = roster(session["id"], session["session_date"])

photo, meta = st.columns([1, 2.4], vertical_alignment="center")
with photo:
    show_class_art(session["name"])
with meta:
    st.subheader(f"{class_icon(session['name'])} {session['name']}")
    st.caption(f":material/schedule: {WEEKDAYS[session['weekday']]} {session['session_date']} at {session['start_time']}")
    st.caption(f":material/groups: {session['booked']} booked of {session['capacity']}")

if not people:
    empty("Nobody is booked for this session yet.", ":material/person_off:")
else:
    st.dataframe(
        pd.DataFrame(
            [
                {"Member": p["name"], "Email": p["email"], "Phone": p["phone"] or "—", "Status": p["status"]}
                for p in people
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    pending = [p for p in people if p["status"] == "booked"]
    if pending:
        person = st.selectbox("Mark attended", pending, format_func=lambda p: p["name"])
        if st.button("Mark attended", type="primary", icon=":material/how_to_reg:"):
            ok, message = mark_attended(person["id"])
            set_flash(message, "success" if ok else "error")
            st.rerun()
