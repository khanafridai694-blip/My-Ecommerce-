"""My orders: every order the customer placed, with a progress tracker."""
import streamlit as st

import database
import ui

user = ui.require_login("Log in to see your orders.")

ui.section_title("My orders", "Follow each order until it arrives.")
orders = database.get_user_orders(user["user_id"])

if not orders:
    ui.empty_state(
        "No orders yet",
        "When you place an order it will show up here.",
        "Start shopping",
        "shop",
        key="no_orders",
        symbol="📦",
    )
    ui.stop_page()

for order in orders:
    with st.container(border=True, key=f"order_{order['id']}"):
        st.html(ui.order_card_html(order))
