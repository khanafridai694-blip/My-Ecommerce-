"""Shop page: search results, category filter, sorting and a product grid."""
import streamlit as st

import config
import routes
import state
import ui

# name -> (what to sort by, biggest first?). "Newest first" keeps the order we already have.
SORT_OPTIONS = {
    "Newest first": None,
    "Price: low to high": (lambda product: product["price"], False),
    "Price: high to low": (lambda product: product["price"], True),
    "Name: A to Z": (lambda product: product["name"].lower(), False),
}

search_text = st.query_params.get("q", "").strip()[:100]
start_category = st.query_params.get("category", "")
if start_category not in config.CATEGORIES:
    start_category = None

# A widget with a new key starts fresh. The key changes when the address changes (a new category link
# or a new search) and when "Reset filters" is pressed, so old filter choices never stick around.
filter_version = st.session_state.get("filter_version", 0)
filter_key = f"{filter_version}_{start_category or 'all'}_{search_text}"

products = state.load_products()

title_column, sort_column = st.columns([3, 1.4], vertical_alignment="bottom")
with title_column:
    heading = f'Results for "{search_text}"' if search_text else "All products"
    ui.section_title(heading)
with sort_column:
    sort_name = st.selectbox("Sort by", list(SORT_OPTIONS), key="shop_sort")

category = st.pills(
    "Category",
    config.CATEGORIES,
    default=start_category,
    format_func=ui.category_label,
    key=f"shop_category_{filter_key}",
    label_visibility="collapsed",
)

# ---- filter and sort
results = products
if category:
    results = [product for product in results if product["category"] == category]
if search_text:
    needle = search_text.lower()
    results = [
        product for product in results
        if needle in f"{product['name']} {product['description']} {product['category']}".lower()
    ]
rule = SORT_OPTIONS[sort_name]
if rule:
    results = sorted(results, key=rule[0], reverse=rule[1])

count_column, reset_column = st.columns([4, 1.5], vertical_alignment="center")
with count_column:
    st.caption(f"{len(results)} product{'' if len(results) == 1 else 's'} found")
with reset_column:
    if (search_text or category) and st.button("Reset filters", icon=":material/close:", key="reset_filters", width="stretch"):
        st.session_state["filter_version"] = filter_version + 1
        st.session_state["search_version"] = st.session_state.get("search_version", 0) + 1
        routes.go("shop")

if not results:
    ui.empty_state(
        "No products found",
        "Try another word or choose a different category.",
        key="no_results",
        symbol="🔍",
    )
    ui.stop_page()

# ---- show a page of products at a time
signature = (category, search_text, sort_name)
if st.session_state.get("shop_signature") != signature:
    st.session_state["shop_signature"] = signature
    st.session_state["shop_limit"] = config.PRODUCTS_PER_PAGE
limit = st.session_state.get("shop_limit", config.PRODUCTS_PER_PAGE)

ui.product_grid(results[:limit], "shop")

if len(results) > limit:
    with st.container(horizontal=True, horizontal_alignment="center"):
        if st.button(f"Show more ({len(results) - limit} left)", key="shop_more", type="primary"):
            st.session_state["shop_limit"] = limit + config.PRODUCTS_PER_PAGE
            st.rerun()
