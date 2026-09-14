import pandas as pd
import streamlit as st

from services.attendance import recent_attendance
from services.classes import upcoming_sessions
from services.stats import admin_kpis, membership_mix, revenue_by_method
from services.ui import class_icon, empty, flash, hero, inr, page_header, show_class_art

flash()
page_header("Dashboard", "Live snapshot of memberships, visits, and classes.", ":material/dashboard:")
hero("hero-floor.png")

kpis = admin_kpis()
sessions = upcoming_sessions(7)
capacity = sum(row["capacity"] for row in sessions)
booked = sum(row["booked"] for row in sessions)
fill_rate = (booked / capacity * 100) if capacity else 0
trend = recent_attendance(14)
spark = [row["check_ins"] for row in trend] if trend else None

with st.container(horizontal=True):
    st.metric(":material/groups: Active members", kpis["active_members"], border=True)
    checkin_metric = {
        "label": ":material/how_to_reg: Check-ins today",
        "value": kpis["checkins_today"],
        "border": True,
    }
    if spark:
        checkin_metric["chart_data"] = spark
        checkin_metric["chart_type"] = "bar"
    st.metric(**checkin_metric)
    st.metric(":material/payments: Revenue this month", inr(kpis["revenue_month"]), border=True)
    st.metric(":material/event: Class fill (7 days)", f"{fill_rate:.0f}%", border=True)

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.subheader(":material/bar_chart: Check-ins")
        if trend:
            st.bar_chart(pd.DataFrame(trend), x="day", y="check_ins")
        else:
            empty("No check-ins recorded yet.", ":material/how_to_reg:")
with right:
    with st.container(border=True):
        st.subheader(":material/account_balance_wallet: Revenue by method")
        methods = revenue_by_method()
        if methods:
            st.bar_chart(pd.DataFrame(methods), x="method", y="total")
        else:
            empty("No payments this month.", ":material/payments:")

with st.container(border=True):
    st.subheader(":material/card_membership: Membership mix")
    mix = membership_mix()
    if mix:
        st.bar_chart(pd.DataFrame(mix), x="plan", y="members")
    else:
        empty("No members yet.", ":material/groups:")

if sessions:
    st.subheader(":material/event: Classes this week")
    preview = sessions[:4]
    cols = st.columns(len(preview))
    for col, session in zip(cols, preview):
        with col, st.container(border=True):
            show_class_art(session["name"])
            st.markdown(f"{class_icon(session['name'])} **{session['name']}**")
            st.caption(f":material/schedule: {session['session_date']} {session['start_time']}")
            st.caption(f":material/groups: {session['booked']}/{session['capacity']} booked")
