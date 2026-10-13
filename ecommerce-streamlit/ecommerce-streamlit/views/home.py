"""Home page: hero, categories, featured products and a preview of all products."""
import streamlit as st

import config
import routes
import state
import ui

products = state.load_products()  # newest first
user = state.current_user()

ui.hero(products[:3], logged_in=user is not None)
ui.benefits()

ui.section_title("Shop by category", "Pick a category to see its products.")
picked = st.pills(
    "Category", config.CATEGORIES, format_func=ui.category_label, key="home_category", label_visibility="collapsed"
)
if picked:
    routes.go("shop", category=picked)

if not products:
    ui.empty_state(
        "No products yet",
        "Run python seed_data.py to add demo products, or add the first product from the admin dashboard.",
        key="no_products",
        symbol="📦",
    )
    ui.stop_page()

featured = products[:8]
ui.section_title("Featured products", "The newest arrivals in the store.")
ui.product_grid(featured, "featured")

# "All products" continues where Featured stops, so no product is shown twice on this page.
featured_ids = {product["id"] for product in featured}
rest = sorted((p for p in products if p["id"] not in featured_ids), key=lambda product: product["name"].lower())
if rest:
    ui.section_title("All products", f"{len(rest)} more to explore. The shop has {len(products)} products in total.")
    ui.product_grid(rest[:config.PRODUCTS_PER_PAGE], "all")

if len(rest) > config.PRODUCTS_PER_PAGE:
    with st.container(horizontal=True, horizontal_alignment="center"):
        if st.button(f"See all {len(products)} products", key="home_see_all", type="primary"):
            routes.go("shop")
