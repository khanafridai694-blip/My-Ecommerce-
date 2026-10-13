"""Sign up and log in with Firebase Authentication.

Passwords are only ever handled by Firebase. We never store them.
"""
import re

import requests
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError
from google.api_core.exceptions import GoogleAPIError

import config
import database

LOGIN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AccountError(Exception):
    """A problem with signing up or logging in. The message is safe to show on screen."""


def register(name, email, password, confirm_password):
    """Creates the account and returns the user's profile."""
    name = name.strip()
    email = email.strip().lower()

    if not 2 <= len(name) <= 60:
        raise AccountError("Enter your name (2 to 60 characters).")
    if not EMAIL_PATTERN.match(email):
        raise AccountError("Enter a valid email address.")
    if len(password) < config.MIN_PASSWORD_LENGTH:
        raise AccountError(f"Your password needs at least {config.MIN_PASSWORD_LENGTH} characters.")
    if password != confirm_password:
        raise AccountError("The two passwords do not match.")

    try:
        # Firebase Authentication stores the password safely (hashed). We never see it again.
        firebase_user = auth.create_user(email=email, password=password, display_name=name)
    except auth.EmailAlreadyExistsError:
        raise AccountError("An account with this email already exists. Log in instead.")
    except ValueError:
        raise AccountError("Check your email and password, then try again.")
    except (FirebaseError, GoogleAPIError, requests.RequestException):
        raise AccountError("We could not create your account right now. Try again in a moment.")

    try:
        return database.create_user_profile(firebase_user.uid, name, email)
    except GoogleAPIError:
        raise AccountError("Your account was created, but we could not finish setting it up. Log in to continue.")


def login(email, password):
    """Checks the password with Firebase and returns the user's profile."""
    email = email.strip().lower()
    if not email or not password:
        raise AccountError("Enter your email and password.")
    if not config.web_api_key():
        raise AccountError("Login is not available right now. Try again later.")

    try:
        response = requests.post(
            LOGIN_URL,
            params={"key": config.web_api_key()},
            json={"email": email, "password": password, "returnSecureToken": True},
            timeout=10,
        )
    except requests.RequestException:
        raise AccountError("We could not reach the login service. Try again in a moment.")

    if not response.ok:
        try:
            error_code = response.json().get("error", {}).get("message", "")
        except ValueError:
            error_code = ""
        if "TOO_MANY_ATTEMPTS" in error_code:
            raise AccountError("Too many failed attempts. Wait a few minutes, then try again.")
        if "USER_DISABLED" in error_code:
            raise AccountError("This account has been disabled. Contact the store for help.")
        if response.status_code >= 500:
            raise AccountError("The login service is busy. Try again in a moment.")
        raise AccountError("The email or password is wrong. Check them and try again.")

    firebase_user = response.json()
    user_id = firebase_user["localId"]
    try:
        profile = database.get_user(user_id)
        if profile is None:  # the account was made in the Firebase console, so add a profile
            name = firebase_user.get("displayName") or email.split("@")[0]
            profile = database.create_user_profile(user_id, name, email)
    except GoogleAPIError:
        raise AccountError("We could not load your account. Try again in a moment.")
    return profile
