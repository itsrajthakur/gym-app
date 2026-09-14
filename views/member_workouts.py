from datetime import date

import pandas as pd
import streamlit as st

from services.ui import empty, flash, page_header, set_flash, show_image
from services.workouts import latest_plan, list_logs, log_workout, plan_exercises, volume_by_day

flash()
page_header("Workouts", "Log what you lifted and follow the plan your trainer assigned.", ":material/exercise:")
show_image("class-strength.png")

user = st.session_state.user
plan = latest_plan(user["id"])

if plan:
    with st.container(border=True):
        st.subheader(f":material/assignment: {plan['title']}")
        st.caption(f":material/sports: Coach {plan['trainer_name']}")
        exercises = plan_exercises(plan["id"])
        if exercises:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Day": e["day_label"] or "—",
                            "Exercise": e["exercise_name"],
                            "Sets": e["sets"],
                            "Reps": e["reps"],
                            "Rest (sec)": e["rest_sec"] or "—",
                        }
                        for e in exercises
                    ]
                ),
                hide_index=True,
                width="stretch",
            )
        else:
            empty("Your plan has no exercises yet.", ":material/fitness_center:")
else:
    empty("No workout plan assigned yet. Your trainer can add one.", ":material/assignment:")

st.subheader(":material/edit_note: Log a set")
with st.form("log_workout", border=True):
    exercise_name = st.text_input("Exercise")
    logged_on = st.date_input("Date", value=date.today())
    sets = st.number_input("Sets", min_value=1, value=3)
    reps = st.number_input("Reps", min_value=1, value=10)
    weight = st.number_input("Weight (kg)", min_value=0.0, value=0.0, step=2.5)
    notes = st.text_input("Notes")
    if st.form_submit_button("Save log", type="primary", icon=":material/save:"):
        ok, message = log_workout(
            user["id"],
            logged_on,
            exercise_name,
            int(sets),
            int(reps),
            float(weight) if weight else 0.0,
            notes,
        )
        if ok:
            set_flash(message)
            st.rerun()
        st.error(message, icon=":material/error:")

volume = volume_by_day(user["id"], 14)
st.subheader(":material/monitoring: Volume")
if volume:
    st.bar_chart(pd.DataFrame(volume), x="logged_on", y="volume")
else:
    empty("Log a workout to see volume over time.", ":material/show_chart:")

logs = list_logs(user["id"])
st.subheader(":material/history: History")
if not logs:
    empty("No workout history yet.", ":material/history:")
else:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Date": row["logged_on"],
                    "Exercise": row["exercise_name"],
                    "Sets": row["sets"],
                    "Reps": row["reps"],
                    "Weight": row["weight"] or 0,
                    "Notes": row["notes"] or "",
                }
                for row in logs
            ]
        ),
        hide_index=True,
        width="stretch",
    )
