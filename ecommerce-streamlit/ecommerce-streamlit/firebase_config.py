"""Connects to Firebase once, when the app starts.

Other files import `db` (the Firestore database) and `bucket` (Storage) from here.
"""
import firebase_admin
from firebase_admin import credentials, firestore, storage

import config


class SetupError(RuntimeError):
    """Raised when the Firebase secrets are missing or wrong. The message explains what to fix."""


def start_firebase():
    """Starts the Firebase connection (only once, even if Streamlit reloads this file)."""
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass  # not started yet

    key = config.firebase_key()
    if not key:
        raise SetupError("The [firebase] secret is missing. Add your Firebase service account key to the secrets.")
    try:
        certificate = credentials.Certificate(key)
    except (ValueError, KeyError, TypeError) as error:
        raise SetupError(
            "The [firebase] secret looks incomplete. Copy every value from the service account JSON file."
        ) from error

    options = {"storageBucket": config.storage_bucket()} if config.storage_bucket() else {}
    return firebase_admin.initialize_app(certificate, options)


start_firebase()

db = firestore.client()  # the Firestore database

# The Storage bucket is optional. Without it, admins paste image links instead of uploading files.
bucket = storage.bucket() if config.storage_bucket() else None
