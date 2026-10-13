"""Checkout page: delivery details, then place the order (cash on delivery)."""
import re

import streamlit as st

import database
import routes
import state
import ui

user = ui.require_login("Log in to check out.")
user_id = user["user_id"]
items, total = database.get_cart_items(user_id)

ui.section_title("Checkout")

if not items:
    ui.empty_state(
        "Your cart is empty",
        "Add a product before checking out.",
        "Browse products",
        "shop",
        key="empty_checkout",
        symbol="🛒",
    )
    ui.stop_page()

form_column, summary_column = st.columns([3, 2], gap="large")

with form_column:
    with st.form("checkout_form", border=True):
        st.html('<h3 class="sum-title">Delivery details</h3>')
        full_name = st.text_input("Full name", value=user["name"], max_chars=60, key="checkout_name")
        phone = st.text_input("Phone number", placeholder="03001234567", max_chars=20, key="checkout_phone")
        address = st.text_area(
            "Delivery address", placeholder="House, street, area and city", max_chars=300, height=110,
            key="checkout_address",
        )
        st.html(
            f'<div class="pay-box">{ui.icon("cash")}<div><b>Cash on delivery</b><br>'
            "<span>Pay when your order arrives.</span></div></div>"
        )
        place_order = st.form_submit_button("Place order", type="primary", width="stretch")

with summary_column:
    with st.container(border=True, key="checkout_summary"):
        lines = "".join(
            f'<div class="sum-row"><span>{ui.esc(item["product"]["name"])} &times; {item["quantity"]}</span>'
            f'<span>{ui.money(item["subtotal"])}</span></div>'
            for item in items
        )
        st.html(
            f'<h3 class="sum-title">Your items</h3>{lines}'
            f'<div class="sum-row sum-total"><span>Total</span><span>{ui.money(total)}</span></div>'
        )
        if st.button("Change your cart", key="back_to_cart", width="stretch"):
            routes.go("cart")

if place_order:
    full_name, phone, address = full_name.strip(), phone.strip(), address.strip()
    digits = re.sub(r"\D", "", phone)
    problem = None
    if not 2 <= len(full_name) <= 60:
        problem = "Enter your full name (2 to 60 characters)."
    elif not re.fullmatch(r"[0-9+\-\s()]+", phone) or not 10 <= len(digits) <= 15:
        problem = "Enter a valid phone number with 10 to 15 digits."
    elif not 10 <= len(address) <= 300:
        problem = "Enter your full delivery address (10 to 300 characters)."

    if problem:
        st.error(problem)
    else:
        try:
            with st.spinner("Placing your order..."):
                database.place_order(user_id, user["email"], full_name, phone, address)
        except database.StoreError as store_problem:
            st.error(str(store_problem))
        else:
            state.set_cart_count(0)
            state.refresh_products()  # the stock changed
            state.flash("success", "Order placed. Thank you for shopping with us!")
            routes.go("orders")
