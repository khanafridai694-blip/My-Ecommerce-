"""Session helpers: who is logged in, flash messages and the cached product list.

st.session_state belongs to one visitor's browser tab. It lives on the server, so visitors
cannot change it. Note: refreshing the browser page starts a new session (the visitor must
log in again). The cart, orders and account are saved in Firebase, so nothing is lost.
"""
import streamlit as st

import config
import database


# ---------------------------------------------------------------- Login
def current_user():
    """The logged-in user as a dictionary (user_id, name, email, role), or None."""
    return st.session_state.get("user")


def sign_in(profile):
    st.session_state["user"] = {key: profile[key] for key in ("user_id", "name", "email", "role")}
    st.session_state["cart_count"] = database.cart_count(profile["user_id"])


def sign_out():
    st.session_state.clear()


def go_after_login(page_name):
    """Remember which page to open on the next run. (Admin pages only exist once the user is logged in.)"""
    st.session_state["go_after_login"] = page_name


def pop_go_after_login():
    return st.session_state.pop("go_after_login", None)


# ---------------------------------------------------------------- Cart badge in the header
def cart_count():
    return st.session_state.get("cart_count", 0)


def set_cart_count(count):
    st.session_state["cart_count"] = count


# ---------------------------------------------------------------- Messages shown on the next page
def flash(kind, message):
    """Saves a message ("success", "info", "warning" or "error") to show after the next rerun."""
    st.session_state.setdefault("flashes", []).append((kind, message))


def pop_flashes():
    return st.session_state.pop("flashes", [])


# ---------------------------------------------------------------- Products (remembered for a short time)
@st.cache_data(ttl=config.CACHE_SECONDS, show_spinner=False)
def load_products():
    """All products, newest first. Cached so every click does not ask Firestore again."""
    return database.get_all_products()


def refresh_products():
    """Call this after a product or its stock changes."""
    load_products.clear()
