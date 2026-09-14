import pandas as pd
import streamlit as st

from services.members import current_membership, list_members
from services.payments import list_payments, record_payment
from services.ui import empty, flash, inr, page_header, set_flash, show_image

flash()
page_header("Payments", "Manual records for cash, card, and UPI. No online checkout in this version.", ":material/payments:")
show_image("hero-login.png")

members = list_members()
with st.form("record_payment", border=True):
    if not members:
        st.info("Add a member before recording a payment.", icon=":material/info:")
        st.form_submit_button("Record payment", disabled=True, icon=":material/payments:")
    else:
        member = st.selectbox("Member", members, format_func=lambda m: f"{m['name']} · {m['email']}")
        amount = st.number_input("Amount (₹)", min_value=0.0, value=1499.0, step=100.0)
        method = st.selectbox("Method", ["upi", "card", "cash"])
        notes = st.text_input("Notes")
        if st.form_submit_button("Record payment", type="primary", icon=":material/payments:"):
            membership = current_membership(member["id"])
            membership_id = membership["id"] if membership else None
            ok, message = record_payment(member["id"], float(amount), method, membership_id, notes)
            if ok:
                set_flash(message)
                st.rerun()
            st.error(message, icon=":material/error:")

payments = list_payments()
if not payments:
    empty("No payments recorded yet.", ":material/receipt_long:")
else:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "When": p["paid_at"],
                    "Member": p["member_name"],
                    "Amount": inr(p["amount"]),
                    "Method": p["method"].upper(),
                    "Plan": p["plan_name"] or "—",
                    "Notes": p["notes"] or "",
                }
                for p in payments
            ]
        ),
        hide_index=True,
        width="stretch",
    )
