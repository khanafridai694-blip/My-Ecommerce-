"""Store settings and secrets.

Secrets are read from Streamlit secrets:
  - on your computer: the file  .streamlit/secrets.toml
  - on Streamlit Community Cloud: the "Secrets" box in the app settings
"""
import streamlit as st

# ---------- Store ----------
STORE_NAME = "ShopEase"
CURRENCY = "Rs."

CATEGORIES = [
    "Electronics",
    "Fashion",
    "Shoes",
    "Beauty",
    "Watches",
    "Bags",
    "Home & Kitchen",
    "Sports",
]

CATEGORY_ICONS = {
    "Electronics": "📱",
    "Fashion": "👗",
    "Shoes": "👟",
    "Beauty": "💄",
    "Watches": "⌚",
    "Bags": "👜",
    "Home & Kitchen": "🍳",
    "Sports": "⚽",
}

ORDER_STATUSES = ["Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"]
ORDER_STEPS = ["Pending", "Confirmed", "Shipped", "Delivered"]  # steps shown in the order tracker

MAX_QUANTITY_PER_ITEM = 10
MIN_PASSWORD_LENGTH = 8
LOW_STOCK_LIMIT = 5  # "Only N left" is shown at or below this number
PRODUCTS_PER_PAGE = 12
CACHE_SECONDS = 30  # how long the product list is remembered before Firestore is asked again

ALLOWED_IMAGE_TYPES = ["png", "jpg", "jpeg", "webp"]
MAX_IMAGE_MB = 3


# ---------- Secrets ----------
def get_secret(name, default=None):
    """Reads one value from Streamlit secrets. Returns `default` when it is missing."""
    try:
        return st.secrets[name]
    except (KeyError, FileNotFoundError):  # no such secret, or no secrets file at all
        return default


def firebase_key():
    """The Firebase service account key as a normal dictionary, or None if it is missing."""
    key = get_secret("firebase")
    if not key:
        return None
    key = dict(key)
    if "private_key" in key:  # tolerate a key that was pasted with a literal "\n"
        key["private_key"] = key["private_key"].replace("\\n", "\n")
    return key


def web_api_key():
    return str(get_secret("firebase_web_api_key", "") or "")


def storage_bucket():
    return str(get_secret("storage_bucket", "") or "")


def admin_settings():
    return dict(get_secret("admin", {}) or {})


def missing_settings():
    """Names of required secrets that are not filled in yet (empty list = all good)."""
    missing = []
    key = firebase_key() or {}
    if not key.get("private_key") or not key.get("client_email"):
        missing.append("[firebase] service account key")
    if not web_api_key():
        missing.append("firebase_web_api_key")
    return missing
