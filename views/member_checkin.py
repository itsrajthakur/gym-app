import pandas as pd
import streamlit as st

from services.attendance import member_history, source_label
from services.members import membership_access
from services.ui import empty, flash, page_header, render_self_checkin, show_image, status_badge

flash()
page_header("Check in", "Mark your visit when you arrive at the gym. One check-in per day.", ":material/how_to_reg:")

user = st.session_state.user
allowed, reason, membership = membership_access(user["id"])
if membership:
    status_badge(membership["status"])

photo, action = st.columns([1, 1.6], vertical_alignment="center")
with photo:
    show_image("hero-floor.png")
with action, st.container(border=True):
    st.markdown("### :material/login: Gym register")
    st.caption("Use this instead of writing your name in the paper register.")
    render_self_checkin(user["id"], allowed, reason, "checkin_page")

history = member_history(user["id"])
st.subheader(":material/history: Recent visits")
if not history:
    empty("No visits in the last 14 days.", ":material/how_to_reg:")
else:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "When": row["check_in_at"],
                    "Source": source_label(row.get("source")),
                }
                for row in history
            ]
        ),
        hide_index=True,
        width="stretch",
    )
