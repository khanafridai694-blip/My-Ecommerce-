"""Cart page: change quantities, remove items and go to checkout."""
import streamlit as st

import config
import database
import routes
import state
import ui

user = ui.require_login("Log in to see your cart.")
user_id = user["user_id"]
items, total = database.get_cart_items(user_id)

# If the stock dropped below what is in the cart, lower the quantity to what is left.
lowered = False
for item in items:
    product = item["product"]
    limit = min(product["stock"], config.MAX_QUANTITY_PER_ITEM)
    if 0 < limit < item["quantity"]:
        database.set_cart_quantity(user_id, product["id"], limit)
        state.flash("warning", f"Only {limit} of {product['name']} are left, so we lowered the quantity.")
        lowered = True
if lowered:
    st.rerun()

state.set_cart_count(sum(item["quantity"] for item in items))
ui.section_title("Your cart")

if not items:
    ui.empty_state(
        "Your cart is empty",
        "Add a few products and they will show up here.",
        "Browse products",
        "shop",
        key="empty_cart",
        symbol="🛒",
    )
    ui.stop_page()

has_sold_out_item = False
list_column, summary_column = st.columns([2.2, 1], gap="large")

with list_column:
    for item in items:
        product = item["product"]
        product_id = product["id"]
        with st.container(border=True, key=f"line_{product_id}"):
            image_column, name_column, quantity_column, total_column = st.columns(
                [1.1, 3, 1.5, 1.6], vertical_alignment="center"
            )
            with image_column:
                st.html(f'<div class="thumb-box">{ui.image_tag(product)}</div>')
            with name_column:
                st.html(
                    f'<div class="line-name">{ui.esc(product["name"])}</div>'
                    f'<div class="line-meta">{ui.esc(product["category"])}</div>'
                    f'<div class="line-meta">{ui.money(product["price"])} each</div>'
                )
            with quantity_column:
                if product["stock"] <= 0:
                    has_sold_out_item = True
                    st.html(f'<div>{ui.chip("Out of stock", "bad")}</div>')
                else:
                    most = min(product["stock"], config.MAX_QUANTITY_PER_ITEM)
                    new_quantity = st.number_input(
                        "Quantity", min_value=1, max_value=most, value=item["quantity"], step=1,
                        key=f"cart_quantity_{product_id}", label_visibility="collapsed",
                    )
                    if new_quantity != item["quantity"]:
                        try:
                            state.set_cart_count(database.set_cart_quantity(user_id, product_id, int(new_quantity)))
                        except database.StoreError as problem:
                            state.flash("error", str(problem))
                        st.rerun()
            with total_column:
                st.html(f'<div class="line-total">{ui.money(item["subtotal"])}</div>')
                if st.button("Remove", key=f"remove_{product_id}", type="tertiary", icon=":material/delete:"):
                    state.set_cart_count(database.remove_from_cart(user_id, product_id))
                    state.flash("info", f"Removed from your cart: {product['name']}")
                    st.rerun()

with summary_column:
    with st.container(border=True, key="cart_summary"):
        st.html(
            '<h3 class="sum-title">Order summary</h3>'
            f'<div class="sum-row"><span>Items</span><span>{state.cart_count()}</span></div>'
            '<div class="sum-row"><span>Payment</span><span>Cash on delivery</span></div>'
            f'<div class="sum-row sum-total"><span>Total</span><span>{ui.money(total)}</span></div>'
        )
        if has_sold_out_item:
            st.warning("Remove the sold-out item to check out.")
        if st.button("Go to checkout", type="primary", width="stretch", disabled=has_sold_out_item, key="go_checkout"):
            routes.go("checkout")
        if st.button("Continue shopping", width="stretch", key="continue_shopping"):
            routes.go("shop")
