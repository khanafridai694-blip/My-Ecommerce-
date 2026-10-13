"""All Firestore (database) and Storage (images) code lives here.

This file does not use Streamlit, so the pages stay short and this logic is easy to test.

Firestore collections used:
  users     one document per user          (document id = Firebase user id)
  products  one document per product
  cart      one document per user          (document id = Firebase user id)
  orders    one document per order, with its items stored inside the order
"""
import re
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

import config
from firebase_config import bucket, db


class StoreError(Exception):
    """A problem that the shopper or admin can fix. The message is safe to show on screen."""


# ---------------------------------------------------------------- Small helpers
def now():
    return datetime.now(timezone.utc)


def is_valid_id(value):
    """Ids made by Firestore (and by seed_data.py) only contain letters, numbers and dashes."""
    return bool(re.fullmatch(r"[A-Za-z0-9-]{1,128}", value or ""))


def doc_to_dict(doc):
    """Turns a Firestore document into a normal dictionary and adds its id."""
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return data


def newest_first(items):
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    return sorted(items, key=lambda item: item.get("created_at") or oldest, reverse=True)


# ---------------------------------------------------------------- Users
def get_user(user_id):
    """Returns the user's profile, or None if there is none yet."""
    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        return None
    profile = doc_to_dict(doc)
    profile["user_id"] = user_id
    profile.setdefault("name", "Customer")
    profile.setdefault("email", "")
    if profile.get("role") != "admin":
        profile["role"] = "customer"  # anything that is not "admin" is treated as a customer
    return profile


def create_user_profile(user_id, name, email, role="customer"):
    """Saves the user's profile. (The password is NOT stored here - Firebase Authentication keeps it.)"""
    profile = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "role": role,
        "created_at": now(),
    }
    db.collection("users").document(user_id).set(profile)
    return profile


# ---------------------------------------------------------------- Products
def get_all_products():
    """Returns every product, newest first. A small store only has a few hundred products."""
    docs = db.collection("products").stream()
    return newest_first([doc_to_dict(doc) for doc in docs])


def get_product(product_id):
    """Returns one product, or None if it does not exist."""
    if not is_valid_id(product_id):
        return None
    doc = db.collection("products").document(product_id).get()
    return doc_to_dict(doc) if doc.exists else None


def save_product(product, product_id=None):
    """Adds a new product (no product_id) or updates an existing one."""
    if product_id is None:
        reference = db.collection("products").document()  # Firestore creates a new unique id
        reference.set({**product, "id": reference.id, "created_at": now()})
        return reference.id
    db.collection("products").document(product_id).update(product)
    return product_id


def delete_product(product_id):
    db.collection("products").document(product_id).delete()


def upload_product_image(data, filename, content_type):
    """Uploads an image (bytes) to Firebase Storage and returns a link that browsers can open."""
    if bucket is None:
        raise StoreError("Image upload is not set up yet. Paste an image link instead.")
    extension = filename.rsplit(".", 1)[-1].lower()
    path = f"products/{uuid.uuid4().hex}.{extension}"
    token = str(uuid.uuid4())  # this token lets anyone with the link view the image
    blob = bucket.blob(path)
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.upload_from_string(data, content_type=content_type)
    return (
        f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/"
        f"{quote(path, safe='')}?alt=media&token={token}"
    )


# ---------------------------------------------------------------- Cart
def get_cart(user_id):
    """Returns the cart as a dictionary: {product_id: quantity}."""
    doc = db.collection("cart").document(user_id).get()
    if not doc.exists:
        return {}
    return (doc.to_dict() or {}).get("items", {})


def save_cart(user_id, cart):
    """Saves the cart. An empty cart removes the document."""
    cart_ref = db.collection("cart").document(user_id)
    if cart:
        cart_ref.set({"user_id": user_id, "items": cart, "updated_at": now()})
    else:
        cart_ref.delete()


def cart_count(user_id):
    """How many items (counting quantities) are in the cart."""
    return sum(get_cart(user_id).values())


def add_to_cart(user_id, product_id, quantity=1):
    """Adds a product to the cart. Returns the new item count. Raises StoreError if it is not allowed."""
    product = get_product(product_id)
    if product is None:
        raise StoreError("That product is no longer available.")
    if not 1 <= quantity <= config.MAX_QUANTITY_PER_ITEM:
        raise StoreError(f"Choose a quantity from 1 to {config.MAX_QUANTITY_PER_ITEM}.")
    if product["stock"] <= 0:
        raise StoreError(f"{product['name']} is out of stock.")

    cart = get_cart(user_id)
    new_quantity = cart.get(product_id, 0) + quantity
    if new_quantity > product["stock"]:
        raise StoreError(f"Only {product['stock']} of {product['name']} are in stock.")
    if new_quantity > config.MAX_QUANTITY_PER_ITEM:
        raise StoreError(f"You can order up to {config.MAX_QUANTITY_PER_ITEM} of one product.")

    cart[product_id] = new_quantity
    save_cart(user_id, cart)
    return sum(cart.values())


def set_cart_quantity(user_id, product_id, quantity):
    """Changes how many of a product are in the cart. Returns the new item count."""
    cart = get_cart(user_id)
    if product_id not in cart:
        raise StoreError("That item is not in your cart.")
    if not 1 <= quantity <= config.MAX_QUANTITY_PER_ITEM:
        raise StoreError(f"Choose a quantity from 1 to {config.MAX_QUANTITY_PER_ITEM}.")
    product = get_product(product_id)
    if product is None:
        raise StoreError("That product is no longer available.")
    if quantity > product["stock"]:
        raise StoreError(f"Only {product['stock']} of {product['name']} are in stock.")
    cart[product_id] = quantity
    save_cart(user_id, cart)
    return sum(cart.values())


def remove_from_cart(user_id, product_id):
    """Takes a product out of the cart. Returns the new item count."""
    cart = get_cart(user_id)
    cart.pop(product_id, None)
    save_cart(user_id, cart)
    return sum(cart.values())


def get_cart_items(user_id):
    """Returns (items, total) for the cart page. Products that were deleted are dropped."""
    cart = get_cart(user_id)
    items = []
    total = 0
    for product_id, quantity in cart.items():
        product = get_product(product_id)
        if product is None:
            continue
        subtotal = round(product["price"] * quantity, 2)
        items.append({"product": product, "quantity": quantity, "subtotal": subtotal})
        total += subtotal
    if len(items) != len(cart):  # some products no longer exist, so clean up the cart
        save_cart(user_id, {item["product"]["id"]: item["quantity"] for item in items})
    return items, round(total, 2)


# ---------------------------------------------------------------- Orders
def place_order(user_id, email, full_name, phone, address):
    """Turns the user's cart into an order and lowers the stock. Raises StoreError if it fails."""
    order_ref = db.collection("orders").document()  # new unique order id
    return _place_order(db.transaction(), order_ref, user_id, email, full_name, phone, address)


@firestore.transactional
def _place_order(transaction, order_ref, user_id, email, full_name, phone, address):
    """Runs as ONE all-or-nothing step, so two shoppers can never buy the same last item."""
    cart_ref = db.collection("cart").document(user_id)
    cart_doc = cart_ref.get(transaction=transaction)
    cart = (cart_doc.to_dict() or {}).get("items", {}) if cart_doc.exists else {}
    if not cart:
        raise StoreError("Your cart is empty. Add a product first.")

    # Step 1: read every product. (Firestore needs all reads to happen before any write.)
    order_items = []
    stock_updates = []
    total = 0
    for product_id, quantity in cart.items():
        product_ref = db.collection("products").document(product_id)
        product_doc = product_ref.get(transaction=transaction)
        if not product_doc.exists:
            raise StoreError("A product in your cart is no longer available. Check your cart and try again.")
        product = product_doc.to_dict()
        if product["stock"] == 0:
            raise StoreError(f"{product['name']} is out of stock. Remove it from your cart to continue.")
        if product["stock"] < quantity:
            raise StoreError(
                f"Only {product['stock']} of {product['name']} are left. Lower the quantity in your cart."
            )
        order_items.append({
            "product_id": product_id,
            "name": product["name"],
            "price": product["price"],
            "quantity": quantity,
            "image_url": product["image_url"],
        })
        stock_updates.append((product_ref, product["stock"] - quantity))
        total += product["price"] * quantity

    # Step 2: write everything.
    for product_ref, new_stock in stock_updates:
        transaction.update(product_ref, {"stock": new_stock})
    order = {
        "order_id": order_ref.id,
        "user_id": user_id,
        "customer_name": full_name,
        "customer_email": email,
        "phone": phone,
        "items": order_items,
        "total_price": round(total, 2),
        "delivery_address": address,
        "order_status": "Pending",
        "created_at": now(),
    }
    transaction.set(order_ref, order)
    transaction.delete(cart_ref)  # the cart is empty after ordering
    return order


def get_user_orders(user_id):
    """Returns one customer's orders, newest first."""
    docs = db.collection("orders").where(filter=FieldFilter("user_id", "==", user_id)).stream()
    return newest_first([doc_to_dict(doc) for doc in docs])


def get_all_orders():
    """Returns every order, newest first (for the admin)."""
    return newest_first([doc_to_dict(doc) for doc in db.collection("orders").stream()])


def update_order_status(order_id, new_status):
    """Changes an order's status. Cancelling an order puts its items back in stock."""
    if not is_valid_id(order_id):
        raise StoreError("That order could not be found.")
    order_ref = db.collection("orders").document(order_id)
    _change_order_status(db.transaction(), order_ref, new_status)


@firestore.transactional
def _change_order_status(transaction, order_ref, new_status):
    order_doc = order_ref.get(transaction=transaction)
    if not order_doc.exists:
        raise StoreError("That order could not be found.")
    order = order_doc.to_dict()
    if order["order_status"] == "Cancelled":
        raise StoreError("A cancelled order cannot be changed.")

    if new_status == "Cancelled":
        # Read all the products first, then write.
        product_refs = [db.collection("products").document(item["product_id"]) for item in order["items"]]
        product_docs = [product_ref.get(transaction=transaction) for product_ref in product_refs]
        for item, product_ref, product_doc in zip(order["items"], product_refs, product_docs):
            if product_doc.exists:  # the product may have been deleted since the order
                transaction.update(product_ref, {"stock": product_doc.to_dict()["stock"] + item["quantity"]})

    transaction.update(order_ref, {"order_status": new_status})
