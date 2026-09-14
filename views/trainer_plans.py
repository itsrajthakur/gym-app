import pandas as pd
import streamlit as st

from services.members import list_members
from services.ui import empty, flash, page_header, set_flash
from services.workouts import add_exercise, create_plan, delete_exercise, list_plans_for_member, plan_exercises

flash()
page_header("Workout plans", "Assign exercise plans to members you train.", ":material/fitness_center:")

members = list_members()
if not members:
    empty("No members in the gym yet.", ":material/groups:")
    st.stop()

member = st.selectbox("Member", members, format_func=lambda m: f"{m['name']} · {m['email']}")
plans = list_plans_for_member(member["id"])

st.subheader(":material/note_add: New plan")
with st.form("new_plan", border=True):
    title = st.text_input("Title", value=f"{member['name']} — training plan")
    notes = st.text_area("Notes")
    if st.form_submit_button("Create plan", type="primary", icon=":material/add:"):
        ok, message, _ = create_plan(member["id"], st.session_state.user["id"], title, notes)
        if ok:
            set_flash(message)
            st.rerun()
        st.error(message, icon=":material/error:")

if not plans:
    empty("This member does not have a plan yet. Create one above.", ":material/fitness_center:")
    st.stop()

selected = st.selectbox("Existing plans", plans, format_func=lambda p: f"{p['title']} · {p['created_at'][:10]}")
st.caption(selected["notes"] or "No notes.")

exercises = plan_exercises(selected["id"])
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
    to_delete = st.selectbox("Remove exercise", exercises, format_func=lambda e: e["exercise_name"])
    if st.button("Remove selected exercise", icon=":material/delete:"):
        delete_exercise(to_delete["id"])
        set_flash("Exercise removed.")
        st.rerun()
else:
    empty("No exercises on this plan yet.", ":material/fitness_center:")

st.subheader(":material/add: Add exercise")
with st.form("add_exercise", border=True):
    exercise_name = st.text_input("Exercise")
    day_label = st.text_input("Day label", value="Day A")
    sets = st.number_input("Sets", min_value=1, value=3)
    reps = st.number_input("Reps", min_value=1, value=10)
    rest = st.number_input("Rest (seconds)", min_value=0, value=60)
    if st.form_submit_button("Add exercise", type="primary", icon=":material/add:"):
        ok, message = add_exercise(selected["id"], exercise_name, int(sets), int(reps), int(rest), day_label)
        if ok:
            set_flash(message)
            st.rerun()
        st.error(message, icon=":material/error:")
