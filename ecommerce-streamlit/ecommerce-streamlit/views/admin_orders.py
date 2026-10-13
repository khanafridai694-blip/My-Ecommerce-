"""Admin orders: see every order and move it through the statuses."""
import streamlit as st

import config
import database
import state
import ui

ui.require_admin()

PAGE_SIZE = 20

ui.section_title("Orders", "Update the status as an order moves along.")
orders = database.get_all_orders()

if not orders:
    ui.empty_state(
        "No orders yet",
        "They will show up here when customers check out.",
        key="no_admin_orders",
        symbol="📦",
    )
    ui.stop_page()

limit = st.session_state.get("admin_orders_limit", PAGE_SIZE)
for order in orders[:limit]:
    order_id = order["id"]
    current = order["order_status"]
    cancelled = current == "Cancelled"
    with st.container(border=True, key=f"admin_order_{order_id}"):
        st.html(ui.order_card_html(order, show_customer=True))
        select_column, button_column = st.columns([3, 1.4], vertical_alignment="bottom")
        with select_column:
            new_status = st.selectbox(
                "Status",
                config.ORDER_STATUSES,
                index=config.ORDER_STATUSES.index(current) if current in config.ORDER_STATUSES else 0,
                key=f"status_{order_id}",
                disabled=cancelled,
            )
        with button_column:
            update = st.button(
                "Update status", key=f"update_{order_id}", type="primary", disabled=cancelled, width="stretch"
            )
        if cancelled:
            st.caption("Cancelled orders cannot be changed.")
        if update:
            try:
                database.update_order_status(order_id, new_status)
            except database.StoreError as problem:
                state.flash("error", str(problem))
            else:
                state.refresh_products()  # cancelling puts items back in stock
                state.flash("success", f"Order #{order_id[:8].upper()} is now {new_status}.")
            st.rerun()

if len(orders) > limit:
    with st.container(horizontal=True, horizontal_alignment="center"):
        if st.button(f"Show more ({len(orders) - limit} left)", key="admin_orders_more", type="primary"):
            st.session_state["admin_orders_limit"] = limit + PAGE_SIZE
            st.rerun()
