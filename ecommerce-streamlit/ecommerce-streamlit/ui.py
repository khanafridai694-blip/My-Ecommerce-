"""Shared look and feel: styles, header, footer and small page pieces used by many pages.

Most pieces are small HTML snippets styled by assets/style.css. Buttons are normal Streamlit
buttons, because only Streamlit widgets can talk to the Python code.
IMPORTANT: every piece of text that came from a user or the database goes through esc()
before it is put into HTML.
"""
import html
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st
from firebase_admin.exceptions import FirebaseError
from google.api_core.exceptions import GoogleAPIError

import config
import database
import routes
import state

CSS_FILE = Path(__file__).parent / "assets" / "style.css"

STATUS_STYLES = {"Pending": "warn", "Confirmed": "info", "Shipped": "brand", "Delivered": "ok", "Cancelled": "bad"}
FLASH_ICONS = {"success": "✅", "info": "ℹ️"}

# Small line icons (24 x 24). They are drawn with the text colour of the element around them.
ICONS = {
    "bag": '<path d="M6 7h12l-1 13H7L6 7z"/><path d="M9 7V6a3 3 0 0 1 6 0v1"/>',
    "cash": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/><path d="M6 12h.01M18 12h.01"/>',
    "receipt": '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3z"/><path d="M9 8h6M9 12h6"/>',
    "shield": '<path d="M12 3l8 3v6c0 4.5-3.2 7.8-8 9-4.8-1.2-8-4.5-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/>',
    "truck": '<path d="M3 7h11v9H3z"/><path d="M14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
}


def icon(name):
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'
    )


class StopPage(Exception):
    """Ends the current page early. streamlit_app.py catches it, so the footer still shows."""


def stop_page():
    raise StopPage()


# ---------------------------------------------------------------- Small helpers
def load_css():
    css = CSS_FILE.read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")


def esc(value):
    """Makes text safe to put inside HTML."""
    return html.escape(str(value), quote=True)


def money(value):
    amount = float(value or 0)
    if amount == int(amount):
        return f"{config.CURRENCY} {int(amount):,}"
    return f"{config.CURRENCY} {amount:,.2f}"


def category_label(category):
    return f"{config.CATEGORY_ICONS.get(category, '')} {category}".strip()


def format_date(value):
    return value.strftime("%d %b %Y, %H:%M UTC") if value else ""


def first_name(name):
    return (name or "").split(" ")[0][:14] or "Account"


def image_tag(product):
    """The product picture. Shows a grey 'No image' box when the link is missing."""
    url = str(product.get("image_url", ""))
    if not url.startswith(("http://", "https://")):
        return '<div class="noimg">No image</div>'
    return f'<img src="{esc(url)}" alt="{esc(product["name"])}" loading="lazy">'


def chip(text, style):
    return f'<span class="chip chip-{style}">{esc(text)}</span>'


def stock_chip(stock):
    if stock <= 0:
        return chip("Out of stock", "bad")
    if stock <= config.LOW_STOCK_LIMIT:
        return chip(f"Only {stock} left", "warn")
    return chip("In stock", "ok")


def status_chip(status):
    return chip(status, STATUS_STYLES.get(status, "info"))


def section_title(title, subtitle=""):
    sub = f"<p>{esc(subtitle)}</p>" if subtitle else ""
    st.html(f'<div class="section-head"><h2>{esc(title)}</h2>{sub}</div>')


def empty_state(title, message, button_label=None, page=None, key="empty", symbol="🛍️"):
    """A friendly 'nothing here' box with an optional button that opens a page."""
    st.html(
        f'<div class="empty"><div class="empty-icon">{symbol}</div>'
        f"<h3>{esc(title)}</h3><p>{esc(message)}</p></div>"
    )
    if button_label and page:
        with st.container(horizontal=True, horizontal_alignment="center"):
            if st.button(button_label, key=f"empty_button_{key}", type="primary"):
                routes.go(page)


def require_login(message="Log in to see this page."):
    """Returns the logged-in user. Visitors who are not logged in see a login prompt instead."""
    user = state.current_user()
    if user is None:
        empty_state("Log in first", message, "Log in or create an account", "account", key="need_login", symbol="🔒")
        stop_page()
    return user


def require_admin():
    """Returns the admin user. Everyone else is blocked (the admin pages are also hidden from them)."""
    user = state.current_user()
    if user is None or user["role"] != "admin":
        empty_state("Access denied", "You need an admin account to open this page.", "Back to the shop", "home",
                    key="admin_denied", symbol="🚫")
        stop_page()
    return user


def show_flashes():
    """Shows the messages saved with state.flash(). Errors stay on the page; the others are toasts."""
    for kind, message in state.pop_flashes():
        if kind == "error":
            st.error(message)
        elif kind == "warning":
            st.warning(message)
        else:
            st.toast(message, icon=FLASH_ICONS.get(kind, "ℹ️"))


def error_page(error):
    """Friendly page for unexpected problems. The technical details stay in the server log."""
    if isinstance(error, (GoogleAPIError, FirebaseError, requests.RequestException)):
        title, message = "We can't reach the database", "Please try again in a moment."
    else:
        title, message = "Something went wrong", "Please try again. If it keeps happening, contact the store."
    empty_state(title, message, "Back to the shop", "home", key="error", symbol="⚠️")


# ---------------------------------------------------------------- Top bar and footer
def search_box():
    """Search field in the top bar. Press Enter or the button to see the results on the Shop page."""
    version = st.session_state.get("search_version", 0)  # a new number gives an empty box
    with st.form("search_form", border=False):
        box, button = st.columns([5, 1.6], vertical_alignment="center")
        with box:
            text = st.text_input(
                "Search products", key=f"header_search_{version}", placeholder="Search products",
                label_visibility="collapsed", max_chars=100,
            )
        with button:
            submitted = st.form_submit_button("Search", icon=":material/search:", width="stretch")
    if submitted:
        text = text.strip()
        if text:
            routes.go("shop", q=text)
        else:
            routes.go("shop")


def account_menu(user):
    if user is None:
        routes.link("account", "Log in", ":material/login:")
        return
    with st.popover(first_name(user["name"]), icon=":material/account_circle:"):
        st.caption(user["email"])
        routes.link("orders", "My orders", ":material/receipt_long:")
        if user["role"] == "admin":
            routes.link("admin", "Admin dashboard", ":material/dashboard:")
        if st.button("Log out", key="logout_button", icon=":material/logout:", width="stretch"):
            state.sign_out()
            state.flash("info", "You have been logged out.")
            st.rerun()


def nav_links(user):
    routes.link("home", "Home", ":material/home:")
    routes.link("shop", "Shop", ":material/storefront:")
    with st.popover("Categories", icon=":material/category:"):
        for category in config.CATEGORIES:
            if st.button(category_label(category), key=f"nav_category_{category}", width="stretch"):
                routes.go("shop", category=category)
    if user:
        routes.link("orders", "My orders", ":material/receipt_long:")
    if user and user["role"] == "admin":
        routes.link("admin", "Dashboard", ":material/dashboard:")
        routes.link("admin_products", "Products", ":material/inventory_2:")
        routes.link("admin_orders", "Orders", ":material/local_shipping:")


def header(user):
    """The top bar: brand, search, cart, account and the main links."""
    count = state.cart_count()
    with st.container(key="topbar"):
        brand_column, search_column, action_column = st.columns([2.2, 4.8, 3.2], vertical_alignment="center")
        with brand_column:
            st.html(
                f'<div class="brand"><span class="brand-mark">{icon("bag")}</span>'
                f'<span class="brand-name">{esc(config.STORE_NAME)}</span></div>'
            )
        with search_column:
            search_box()
        with action_column:
            with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center", gap="small"):
                routes.link("cart", f"Cart ({count})" if count else "Cart", ":material/shopping_cart:")
                account_menu(user)
        with st.container(horizontal=True, vertical_alignment="center", gap="small"):
            nav_links(user)


def footer():
    st.html(
        f'<div class="footer"><span class="footer-brand">{esc(config.STORE_NAME)}</span>'
        f"<span>&copy; {datetime.now().year} {esc(config.STORE_NAME)}. Demo store with cash on delivery.</span></div>"
    )


# ---------------------------------------------------------------- Home page pieces
def hero(featured, logged_in):
    """Big welcome panel with two buttons and a few featured products."""
    with st.container(key="hero"):
        left, right = st.columns([3, 2], gap="large", vertical_alignment="center")
        with left:
            st.html(
                '<h1 class="hero-title">Fashion, gadgets and kitchen finds, <span>delivered to your door.</span></h1>'
                f'<p class="hero-text">Browse {len(config.CATEGORIES)} categories, pay cash when your order '
                "arrives and follow every order from your account.</p>"
            )
            with st.container(horizontal=True, gap="small"):
                if st.button("Shop all products", type="primary", key="hero_shop"):
                    routes.go("shop")
                if not logged_in and st.button("Create an account", key="hero_signup"):
                    routes.go("account")
        with right:
            if featured:
                tiles = "".join(
                    f'<div class="tile">{image_tag(product)}<div class="tile-name">{esc(product["name"])}</div>'
                    f'<div class="tile-price">{money(product["price"])}</div></div>'
                    for product in featured
                )
                st.html(f'<div class="collage">{tiles}</div>')


def benefits():
    items = [
        ("cash", "Cash on delivery", "Pay when your order arrives."),
        ("receipt", "Order tracking", "Follow each order from Pending to Delivered."),
        ("shield", "Secure accounts", "Passwords are handled by Firebase Authentication."),
    ]
    cards = "".join(
        f'<div class="benefit"><div class="benefit-icon">{icon(name)}</div><div><b>{esc(title)}</b>'
        f"<span>{esc(text)}</span></div></div>"
        for name, title, text in items
    )
    st.html(f'<div class="benefits">{cards}</div>')


# ---------------------------------------------------------------- Products
def add_to_cart(product, quantity=1):
    """Used by every 'Add to cart' button. Guests are sent to the login page."""
    user = state.current_user()
    if user is None:
        state.flash("info", "Log in to add items to your cart.")
        routes.go("account")
    try:
        count = database.add_to_cart(user["user_id"], product["id"], quantity)
    except database.StoreError as problem:
        state.flash("error", str(problem))
    else:
        state.set_cart_count(count)
        state.flash("success", f"Added to your cart: {product['name']}")
    st.rerun()


def product_card(product, section):
    """One product: picture, details and two buttons. `section` keeps button keys unique on a page."""
    product_id = product["id"]
    sold_out = product["stock"] <= 0
    ribbon = '<span class="pc-ribbon">Sold out</span>' if sold_out else ""
    with st.container(border=True, key=f"card_{section}_{product_id}"):
        st.html(
            f'<div class="pc-img">{image_tag(product)}{ribbon}</div>'
            f'<div class="pc-cat">{esc(product["category"])}</div>'
            f'<div class="pc-name">{esc(product["name"])}</div>'
            f'<div class="pc-row"><span class="pc-price">{money(product["price"])}</span>'
            f'{stock_chip(product["stock"])}</div>'
        )
        if st.button("Add to cart", key=f"add_{section}_{product_id}", type="primary",
                     icon=":material/add_shopping_cart:", disabled=sold_out, width="stretch"):
            add_to_cart(product)
        if st.button("View details", key=f"view_{section}_{product_id}", width="stretch"):
            routes.go("product", id=product_id)


def product_grid(products, section, columns=4):
    """Shows products in rows of `columns` cards."""
    with st.container(key=f"grid_{section}"):
        for start in range(0, len(products), columns):
            row = products[start:start + columns]
            for column, product in zip(st.columns(columns), row):
                with column:
                    product_card(product, section)


# ---------------------------------------------------------------- Orders
def tracker_html(status):
    """Progress dots: Pending, Confirmed, Shipped, Delivered. Cancelled orders show a red note."""
    if status == "Cancelled":
        return '<div class="tracker-cancelled">This order was cancelled. Its items went back into stock.</div>'
    steps = config.ORDER_STEPS
    current = steps.index(status) if status in steps else 0
    dots = []
    for index, step in enumerate(steps):
        if status == "Delivered" or index < current:
            style = "done"
        elif index == current:
            style = "current"
        else:
            style = ""
        dots.append(f'<li class="{style}"><span class="dot"></span>{esc(step)}</li>')
    return f'<ol class="tracker">{"".join(dots)}</ol>'


def order_card_html(order, show_customer=False):
    """One order as an HTML card. Admins also see who ordered."""
    status = order.get("order_status", "Pending")
    lines = "".join(
        f'<li><span>{esc(item["name"])} &times; {item["quantity"]}</span>'
        f'<span>{money(item["price"] * item["quantity"])}</span></li>'
        for item in order["items"]
    )
    customer = ""
    if show_customer:
        customer = (
            f'<div class="oc-info"><b>{esc(order.get("customer_name", ""))}</b><br>'
            f'{esc(order.get("customer_email", ""))}<br>{esc(order.get("phone", ""))}</div>'
        )
    return (
        f'<div class="oc-head"><div><div class="oc-id">Order #{esc(order["id"][:8].upper())}</div>'
        f'<div class="oc-date">{esc(format_date(order.get("created_at")))}</div></div>{status_chip(status)}</div>'
        f"{tracker_html(status)}"
        f'<ul class="oc-lines">{lines}</ul>'
        f'<div class="oc-total"><span>Total</span><span>{money(order["total_price"])}</span></div>'
        f"{customer}"
        f'<div class="oc-info"><b>Delivery address</b><br>{esc(order.get("delivery_address", ""))}</div>'
    )
