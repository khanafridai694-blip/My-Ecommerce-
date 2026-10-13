"""Product details page. The product comes from the address, for example /product?id=demo-01"""
import streamlit as st

import config
import database
import routes
import state
import ui

product_id = st.query_params.get("id", "")
product = database.get_product(product_id)  # a fresh read, so the stock is up to date

if product is None:
    ui.empty_state(
        "We could not find that product",
        "It may have been removed. Browse the shop to see what is available.",
        "Browse products",
        "shop",
        key="missing_product",
        symbol="🔍",
    )
    ui.stop_page()

if st.button("Back to shop", icon=":material/arrow_back:", type="tertiary", key="back_to_shop"):
    routes.go("shop", category=product["category"])

image_column, details_column = st.columns(2, gap="large")

with image_column:
    st.html(f'<div class="pdp-img">{ui.image_tag(product)}</div>')

with details_column:
    st.html(
        f'<p class="pdp-cat">{ui.esc(product["category"])}</p>'
        f'<h1 class="pdp-title">{ui.esc(product["name"])}</h1>'
        f'<div class="pdp-price">{ui.money(product["price"])}</div>'
        f'<div>{ui.stock_chip(product["stock"])}</div>'
        f'<p class="pdp-desc">{ui.esc(product["description"])}</p>'
    )

    if product["stock"] > 0:
        most = min(product["stock"], config.MAX_QUANTITY_PER_ITEM)
        quantity = st.number_input(
            "Quantity", min_value=1, max_value=most, value=1, step=1, key=f"quantity_{product_id}"
        )
        if st.button("Add to cart", type="primary", icon=":material/add_shopping_cart:", key="detail_add", width="stretch"):
            ui.add_to_cart(product, int(quantity))
    else:
        st.button("Out of stock", disabled=True, key="detail_sold_out", width="stretch")

    st.html(
        '<ul class="perks">'
        f'<li>{ui.icon("cash")}Pay in cash when your order arrives</li>'
        f'<li>{ui.icon("receipt")}Track the order from your account</li>'
        f'<li>{ui.icon("truck")}Delivered to the address you give at checkout</li>'
        "</ul>"
    )

related = [
    other for other in state.load_products()
    if other["category"] == product["category"] and other["id"] != product["id"]
][:4]
if related:
    ui.section_title(f"More in {product['category']}")
    ui.product_grid(related, "related")
