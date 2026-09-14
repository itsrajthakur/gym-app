import streamlit as st

from db.database import expire_memberships, init_db
from services.ui import ROLE_ICONS, inject_css, show_brand

st.set_page_config(
    page_title="Pulse Gym",
    page_icon=":material/exercise:",
    layout="wide",
)

init_db()
expire_memberships()
inject_css()
show_brand()
st.session_state.setdefault("user", None)

if not st.session_state.user:
    page = st.navigation(
        [st.Page("views/login.py", title="Sign in", icon=":material/login:")],
        position="hidden",
    )
    page.run()
    st.stop()

user = st.session_state.user
role = user["role"]

with st.sidebar:
    st.markdown(f"{ROLE_ICONS.get(role, ':material/person:')} **{user['name']}**")
    st.caption(role.title())
    if st.button("Log out", icon=":material/logout:", width="stretch"):
        st.session_state.clear()
        st.rerun()

if role == "admin":
    navigation = {
        "Gym": [
            st.Page("views/admin_dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
            st.Page("views/admin_members.py", title="Members", icon=":material/groups:"),
            st.Page("views/admin_plans.py", title="Plans", icon=":material/card_membership:"),
            st.Page("views/admin_payments.py", title="Payments", icon=":material/payments:"),
            st.Page("views/admin_attendance.py", title="Attendance", icon=":material/how_to_reg:"),
            st.Page("views/admin_classes.py", title="Classes", icon=":material/calendar_month:"),
        ]
    }
elif role == "trainer":
    navigation = [
        st.Page("views/trainer_dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
        st.Page("views/trainer_roster.py", title="Roster", icon=":material/list:"),
        st.Page("views/trainer_plans.py", title="Plans", icon=":material/fitness_center:"),
    ]
elif role == "member":
    navigation = [
        st.Page("views/member_home.py", title="Home", icon=":material/home:", default=True),
        st.Page("views/member_classes.py", title="Classes", icon=":material/event:"),
        st.Page("views/member_workouts.py", title="Workouts", icon=":material/exercise:"),
        st.Page("views/member_profile.py", title="Profile", icon=":material/person:"),
    ]
else:
    st.error("Unknown account role. Contact the gym admin.", icon=":material/error:")
    st.stop()

page = st.navigation(navigation, position="sidebar")
page.run()
