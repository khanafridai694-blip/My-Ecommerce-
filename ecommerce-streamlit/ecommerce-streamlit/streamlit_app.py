"""ShopEase - the entry point of the app.

Run it on your computer with:   streamlit run streamlit_app.py

Streamlit runs this file again every time a visitor clicks something. The steps are:
  1. check that the Firebase secrets are filled in
  2. work out which pages this visitor may open (admin pages only for admins)
  3. draw the top bar, then the page, then the footer
"""
import logging

import streamlit as st

import config

st.set_page_config(
    page_title=config.STORE_NAME,
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

logger = logging.getLogger("shopease")


def show_setup_help(problem, hint=None):
    """Shown instead of the store when Firebase is not connected yet."""
    st.title("Connect Firebase to start the store")
    st.error(problem)
    if hint:
        st.info(hint)
    st.markdown(
        "1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill it in.\n"
        "2. On Streamlit Community Cloud, paste the same text into **App settings > Secrets**.\n"
        "3. Restart the app.\n\n"
        "The README explains where to find each value in the Firebase console."
    )


def main():
    missing = config.missing_settings()
    if missing:
        show_setup_help("These secrets are missing or empty: " + ", ".join(missing), config.secrets_file_hint())
        st.stop()

    try:
        import firebase_config  # noqa: F401  (connects to Firebase the first time it is imported)
    except RuntimeError as error:  # our own SetupError, with a helpful message
        show_setup_help(str(error))
        st.stop()
    except Exception:
        logger.exception("Firebase could not start")
        show_setup_help("Firebase could not start. Check that the secrets are correct (the app log has details).")
        st.stop()

    import routes
    import state
    import ui

    ui.load_css()
    user = state.current_user()
    page = st.navigation(routes.build_pages(user), position="hidden")

    after_login = state.pop_go_after_login()
    if after_login:  # a visitor just logged in, so open the page they should see first
        routes.go(after_login)

    ui.header(user)
    ui.show_flashes()
    try:
        page.run()
    except ui.StopPage:
        pass  # the page ended early on purpose (for example: "log in first")
    except Exception as error:
        logger.exception("A page failed")  # full details go to the server log only
        ui.error_page(error)
    ui.footer()


main()

