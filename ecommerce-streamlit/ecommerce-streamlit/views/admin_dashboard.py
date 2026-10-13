"""Admin dashboard: key numbers, orders by status, low stock and recent orders."""
import streamlit as st

import config
import database
import routes
import state
import ui

ui.require_admin()

products = state.load_products()
orders = database.get_all_orders()

ui.section_title("Admin dashboard", "A quick look at the store.")

with st.container(horizontal=True, gap="small"):
    if st.button("Add product", type="primary", icon=":material/add:", key="dash_add"):
        routes.go("admin_product_form")
    if st.button("Manage products", icon=":material/inventory_2:", key="dash_products"):
        routes.go("admin_products")
    if st.button("View orders", icon=":material/local_shipping:", key="dash_orders"):
        routes.go("admin_orders")

# ---- key numbers
sales = sum(order["total_price"] for order in orders if order["order_status"] != "Cancelled")
pending = sum(1 for order in orders if order["order_status"] == "Pending")
first, second, third, fourth = st.columns(4)
first.metric("Products", len(products), border=True)
second.metric("Orders", len(orders), border=True)
third.metric("Pending orders", pending, border=True)
fourth.metric("Sales (without cancelled)", ui.money(sales), border=True)

# ---- orders by status and low stock
status_column, stock_column = st.columns(2, gap="large")

with status_column:
    with st.container(border=True, key="dash_status"):
        counts = {status: 0 for status in config.ORDER_STATUSES}
        for order in orders:
            counts[order["order_status"]] = counts.get(order["order_status"], 0) + 1
        biggest = max(counts.values()) or 1
        bars = "".join(
            f'<div class="bar-row"><span>{ui.esc(status)}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{count / biggest * 100:.0f}%"></div></div>'
            f'<span class="bar-count">{count}</span></div>'
            for status, count in counts.items()
        )
        st.html(f'<h3 class="sum-title">Orders by status</h3><div class="bars">{bars}</div>')

with stock_column:
    with st.container(border=True, key="dash_low_stock"):
        low = sorted(
            (product for product in products if product["stock"] <= config.LOW_STOCK_LIMIT),
            key=lambda product: product["stock"],
        )
        rows = "".join(
            f'<tr><td><div class="row-name">{ui.esc(product["name"])}</div></td>'
            f'<td class="num">{ui.stock_chip(product["stock"])}</td></tr>'
            for product in low[:6]
        )
        body = (
            f'<div class="tbl-wrap"><table class="tbl"><tbody>{rows}</tbody></table></div>'
            if rows else '<p class="row-meta">Every product has enough stock.</p>'
        )
        st.html(f'<h3 class="sum-title">Low stock</h3>{body}')

# ---- recent orders
with st.container(border=True, key="dash_recent"):
    rows = "".join(
        f'<tr><td><div class="row-name">#{ui.esc(order["id"][:8].upper())}</div>'
        f'<div class="row-meta">{ui.esc(ui.format_date(order.get("created_at")))}</div></td>'
        f'<td>{ui.esc(order.get("customer_name", ""))}</td>'
        f'<td class="num">{ui.money(order["total_price"])}</td>'
        f'<td class="num">{ui.status_chip(order["order_status"])}</td></tr>'
        for order in orders[:5]
    )
    body = (
        '<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Order</th><th>Customer</th>'
        f'<th class="num">Total</th><th class="num">Status</th></tr></thead><tbody>{rows}</tbody></table></div>'
        if rows else '<p class="row-meta">No orders yet. They will show up here.</p>'
    )
    st.html(f'<h3 class="sum-title">Recent orders</h3>{body}')
