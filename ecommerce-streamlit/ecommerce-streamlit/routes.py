"""Where every page lives, and small helpers to move between pages.

Each page is a normal Python file inside the "views" folder. Streamlit runs the file of the
page the visitor opens. Admin pages are only added to the navigation for admin users, so
other visitors cannot open them, even by typing the address.
"""
import streamlit as st

import config

PAGES = {
    "home": "views/home.py",
    "shop": "views/shop.py",
    "product": "views/product.py",
    "cart": "views/cart.py",
    "checkout": "views/checkout.py",
    "orders": "views/orders.py",
    "account": "views/account.py",
    "admin": "views/admin_dashboard.py",
    "admin_products": "views/admin_products.py",
    "admin_product_form": "views/admin_product_form.py",
    "admin_orders": "views/admin_orders.py",
}

# name -> (title shown in the browser tab, address path). Home is the default page.
STORE_PAGES = {
    "home": ("Home", ""),
    "shop": ("Shop", "shop"),
    "product": ("Product", "product"),
    "cart": ("Cart", "cart"),
    "checkout": ("Checkout", "checkout"),
    "orders": ("My orders", "orders"),
    "account": ("Account", "account"),
}
ADMIN_PAGES = {
    "admin": ("Admin dashboard", "admin"),
    "admin_products": ("Admin products", "admin-products"),
    "admin_product_form": ("Product form", "admin-product"),
    "admin_orders": ("Admin orders", "admin-orders"),
}


def build_pages(user):
    """The pages this visitor may open."""
    names = dict(STORE_PAGES)
    if user and user["role"] == "admin":
        names.update(ADMIN_PAGES)
    return [
        st.Page(
            PAGES[name],
            title=f"{title} | {config.STORE_NAME}",
            url_path=path,
            default=(name == "home"),
        )
        for name, (title, path) in names.items()
    ]


def go(name, **query):
    """Opens a page. Extra keyword arguments become the address's query, e.g. go("shop", q="shoes")."""
    st.switch_page(PAGES[name], query_params=query or None)


def link(name, label, icon=None):
    """A clickable link to a page."""
    st.page_link(PAGES[name], label=label, icon=icon)
