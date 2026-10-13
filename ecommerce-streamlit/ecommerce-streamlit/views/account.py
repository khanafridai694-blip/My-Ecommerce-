"""Account page: log in or create an account (admins log in here too)."""
import streamlit as st

import accounts
import routes
import state
import ui

user = state.current_user()
_, middle, _ = st.columns([1, 1.8, 1])


def finish_login(profile, message):
    """Saves the login and opens the right page on the next run (admins go to their dashboard)."""
    state.sign_in(profile)
    state.flash("success", message)
    state.go_after_login("admin" if profile["role"] == "admin" else "home")
    st.rerun()


with middle:
    if user:
        ui.section_title(f"Hi, {ui.first_name(user['name'])}", user["email"])
        st.html(f"<p>{ui.chip('Admin' if user['role'] == 'admin' else 'Customer', 'brand')}</p>")
        if st.button("My orders", icon=":material/receipt_long:", key="account_orders", width="stretch"):
            routes.go("orders")
        if user["role"] == "admin" and st.button(
            "Admin dashboard", icon=":material/dashboard:", key="account_admin", width="stretch"
        ):
            routes.go("admin")
        if st.button("Log out", icon=":material/logout:", key="account_logout", width="stretch"):
            state.sign_out()
            state.flash("info", "You have been logged out.")
            st.rerun()
        ui.stop_page()

    ui.section_title("Welcome", "Log in to use your cart and follow your orders.")
    login_tab, register_tab = st.tabs(["Log in", "Create account"])

    with login_tab:
        with st.form("login_form", border=True):
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            login_clicked = st.form_submit_button("Log in", type="primary", width="stretch")
        if login_clicked:
            try:
                profile = accounts.login(login_email, login_password)
            except accounts.AccountError as problem:
                st.error(str(problem))
            else:
                finish_login(profile, f"Welcome back, {profile['name']}!")

    with register_tab:
        with st.form("register_form", border=True):
            register_name = st.text_input("Name", max_chars=60, key="register_name")
            register_email = st.text_input("Email", key="register_email")
            register_password = st.text_input("Password", type="password", key="register_password",
                                              help="At least 8 characters.")
            register_confirm = st.text_input("Confirm password", type="password", key="register_confirm")
            register_clicked = st.form_submit_button("Create account", type="primary", width="stretch")
        if register_clicked:
            try:
                profile = accounts.register(register_name, register_email, register_password, register_confirm)
            except accounts.AccountError as problem:
                st.error(str(problem))
            else:
                finish_login(profile, f"Welcome to the store, {profile['name']}!")
