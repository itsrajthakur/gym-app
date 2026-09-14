import streamlit as st

from services.classes import next_booking_for_member
from services.members import current_membership, membership_access
from services.ui import class_icon, empty, flash, membership_panel, page_header, show_class_art
from services.workouts import latest_log, latest_plan

flash()
user = st.session_state.user
page_header("Home", f"Welcome back, {user['name'].split()[0]}.", ":material/home:")

allowed, reason, membership = membership_access(user["id"])
membership = membership or current_membership(user["id"])
next_class = next_booking_for_member(user["id"])
last_workout = latest_log(user["id"])
plan = latest_plan(user["id"])

if membership:
    membership_panel(membership, user["name"])
    if not allowed:
        st.warning(reason, icon=":material/warning:")
else:
    st.warning(reason, icon=":material/info:")

col_a, col_b = st.columns(2)
with col_a:
    with st.container(border=True):
        st.subheader(":material/event: Next class")
        if next_class:
            show_class_art(next_class["name"])
            st.markdown(f"{class_icon(next_class['name'])} **{next_class['name']}**")
            st.caption(
                f":material/schedule: {next_class['session_date']} at {next_class['start_time']} "
                f"with {next_class['trainer_name']}"
            )
        else:
            empty("No upcoming class booked.", ":material/event_busy:")
with col_b:
    with st.container(border=True):
        st.subheader(":material/exercise: Last workout")
        if last_workout:
            weight = f" @ {last_workout['weight']} kg" if last_workout["weight"] else ""
            st.markdown(f":material/fitness_center: **{last_workout['exercise_name']}**")
            st.caption(f":material/calendar_today: {last_workout['logged_on']} · {last_workout['sets']}×{last_workout['reps']}{weight}")
        else:
            empty("No workouts logged yet.", ":material/fitness_center:")

if plan:
    with st.container(border=True):
        st.subheader(":material/assignment: Assigned plan")
        st.markdown(f"**{plan['title']}**")
        st.caption(f":material/sports: Coach {plan['trainer_name']}")
        if plan["notes"]:
            st.write(plan["notes"])
