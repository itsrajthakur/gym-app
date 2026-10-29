import pandas as pd
import streamlit as st

from services.attendance import check_in, source_label, todays_attendance
from services.members import list_members
from services.ui import empty, flash, page_header, set_flash, show_image

flash()
page_header("Attendance", "Front-desk gym check-in. Frozen or expired members are blocked.", ":material/how_to_reg:")

members = list_members()
if not members:
    empty("Add a member before taking attendance.", ":material/person_off:")
else:
    photo, desk = st.columns([1, 1.8], vertical_alignment="center")
    with photo:
        show_image("hero-floor.png")
    with desk, st.container(border=True):
        st.markdown("### :material/login: Front desk")
        member = st.selectbox("Member", members, format_func=lambda m: f"{m['name']} · {m['email']}")
        if st.button("Check in", type="primary", icon=":material/login:"):
            ok, message = check_in(member["id"], source="desk")
            set_flash(message, "success" if ok else "error")
            st.rerun()

rows = todays_attendance()
st.subheader(":material/today: Today")
if not rows:
    empty("No check-ins yet today.", ":material/how_to_reg:")
else:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Time": r["check_in_at"],
                    "Member": r["name"],
                    "Email": r["email"],
                    "Source": source_label(r.get("source")),
                }
                for r in rows
            ]
        ),
        hide_index=True,
        width="stretch",
    )
