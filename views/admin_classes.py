import pandas as pd
import streamlit as st

from services.classes import WEEKDAYS, create_class, list_classes, roster, upcoming_sessions
from services.members import list_trainers
from services.ui import class_icon, empty, flash, page_header, set_flash, show_class_art

flash()
page_header("Classes", "Weekly recurring classes. Bookings are per session date.", ":material/calendar_month:")

trainers = list_trainers(active_only=True)
with st.form("create_class", border=True):
    name = st.text_input("Class name")
    if trainers:
        trainer = st.selectbox("Trainer", trainers, format_func=lambda t: t["name"])
    else:
        trainer = None
        st.warning("Add a trainer before creating a class.", icon=":material/warning:")
    weekday = st.selectbox("Weekday", list(enumerate(WEEKDAYS)), format_func=lambda item: item[1])
    start_time = st.time_input("Start time")
    duration = st.number_input("Duration (minutes)", min_value=10, value=45, step=5)
    capacity = st.number_input("Capacity", min_value=1, value=12)
    description = st.text_area("Description")
    submitted = st.form_submit_button("Add class", type="primary", disabled=trainer is None, icon=":material/add:")
    if submitted and trainer:
        ok, message = create_class(
            name,
            trainer["id"],
            weekday[0],
            start_time.strftime("%H:%M"),
            int(duration),
            int(capacity),
            description,
        )
        if ok:
            set_flash(message)
            st.rerun()
        st.error(message, icon=":material/error:")

classes = list_classes()
if not classes:
    empty("No classes on the schedule yet.", ":material/event_busy:")
else:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Class": c["name"],
                    "Trainer": c["trainer_name"],
                    "Day": WEEKDAYS[c["weekday"]],
                    "Time": c["start_time"],
                    "Minutes": c["duration_min"],
                    "Capacity": c["capacity"],
                }
                for c in classes
            ]
        ),
        hide_index=True,
        width="stretch",
    )

st.subheader(":material/event: Upcoming bookings")
sessions = upcoming_sessions(7)
if not sessions:
    empty("No sessions in the next 7 days.", ":material/event_busy:")
else:
    for session in sessions:
        with st.expander(
            f"{class_icon(session['name'])} {session['session_date']} · {session['start_time']} · {session['name']} "
            f"({session['booked']}/{session['capacity']})",
            icon=":material/event:",
        ):
            photo, details = st.columns([1, 2.4], vertical_alignment="center")
            with photo:
                show_class_art(session["name"])
            with details:
                people = roster(session["id"], session["session_date"])
                if not people:
                    empty("No bookings yet.", ":material/person_off:")
                else:
                    st.dataframe(
                        pd.DataFrame(
                            [{"Member": p["name"], "Email": p["email"], "Status": p["status"]} for p in people]
                        ),
                        hide_index=True,
                        width="stretch",
                    )
