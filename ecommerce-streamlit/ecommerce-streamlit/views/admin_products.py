"""Admin products: find, edit and delete products."""
import streamlit as st

import config
import database
import routes
import state
import ui

ui.require_admin()

PAGE_SIZE = 25


@st.dialog("Delete this product?")
def confirm_delete(product):
    """A small pop-up that asks before anything is deleted."""
    st.html(f"<p><b>{ui.esc(product['name'])}</b> will be removed from the store. This cannot be undone.</p>")
    cancel_column, delete_column = st.columns(2)
    with cancel_column:
        if st.button("Cancel", key="delete_cancel", width="stretch"):
            st.rerun()
    with delete_column:
        if st.button("Delete", type="primary", key="delete_confirm", width="stretch"):
            database.delete_product(product["id"])
            state.refresh_products()
            state.flash("info", f"Deleted: {product['name']}")
            st.rerun()


ui.section_title("Products", "Add, edit or delete the products in your store.")

filter_column, add_column = st.columns([3, 1], vertical_alignment="bottom")
with filter_column:
    filter_text = st.text_input(
        "Filter products", placeholder="Type a product name or category", key="admin_filter",
        label_visibility="collapsed",
    )
with add_column:
    if st.button("Add product", type="primary", icon=":material/add:", key="products_add", width="stretch"):
        routes.go("admin_product_form")

products = state.load_products()
needle = filter_text.strip().lower()
shown = [p for p in products if needle in f"{p['name']} {p['category']}".lower()] if needle else products
st.caption(f"{len(shown)} of {len(products)} products")

if not shown:
    ui.empty_state("No products found", "Try another word, or add a new product.", key="no_admin_products", symbol="📦")
    ui.stop_page()

limit = st.session_state.get("admin_products_limit", PAGE_SIZE)
for product in shown[:limit]:
    product_id = product["id"]
    with st.container(border=True, key=f"admin_row_{product_id}"):
        image_column, name_column, price_column, stock_column, edit_column, delete_column = st.columns(
            [0.9, 3.2, 1.5, 1.6, 1, 1.2], vertical_alignment="center"
        )
        with image_column:
            st.html(f'<div class="thumb-box">{ui.image_tag(product)}</div>')
        with name_column:
            st.html(
                f'<div class="row-name">{ui.esc(product["name"])}</div>'
                f'<div class="row-meta">{ui.esc(product["category"])}</div>'
            )
        with price_column:
            st.html(f'<div class="row-name">{ui.money(product["price"])}</div>')
        with stock_column:
            st.html(f'<div>{ui.stock_chip(product["stock"])}</div>')
        with edit_column:
            if st.button("Edit", key=f"edit_{product_id}", icon=":material/edit:", width="stretch"):
                routes.go("admin_product_form", id=product_id)
        with delete_column:
            if st.button("Delete", key=f"delete_{product_id}", icon=":material/delete:", width="stretch"):
                confirm_delete(product)

if len(shown) > limit:
    with st.container(horizontal=True, horizontal_alignment="center"):
        if st.button(f"Show more ({len(shown) - limit} left)", key="admin_products_more", type="primary"):
            st.session_state["admin_products_limit"] = limit + PAGE_SIZE
            st.rerun()
