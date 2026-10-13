"""Adds 30 demo products and the first admin account to Firebase.

Run it once from the project folder on your computer:   python seed_data.py
(It reads the same .streamlit/secrets.toml file as the app.)
It is safe to run again: products and accounts that already exist are skipped.

Demo images are placeholders from placehold.co (no copyrighted images). Replace them later
with real photos from Admin > Products > Edit.
"""
from datetime import timedelta
from urllib.parse import quote_plus

import config

try:
    from firebase_admin import auth

    from database import create_user_profile, now
    from firebase_config import db
except RuntimeError as problem:  # our SetupError: the Firebase secrets are missing or wrong
    raise SystemExit(f"Cannot connect to Firebase: {problem}")

# (name, short image label, category, price, stock, description)
# The list is mixed on purpose: the home page "Featured" section shows the 8 newest products,
# so mixing the categories makes Featured show a variety of products.
DEMO_PRODUCTS = [
    ("Wireless Bluetooth Earbuds", "Earbuds", "Electronics", 3499, 40,
     "Compact earbuds with clear sound, touch controls and up to 20 hours of play time with the charging case."),
    ("Printed Lawn 3-Piece Suit", "Lawn suit", "Fashion", 6500, 18,
     "Soft summer lawn shirt, dupatta and trouser set with a printed front and a relaxed, breathable fit."),
    ("Lightweight Running Shoes", "Running shoes", "Shoes", 5999, 25,
     "Breathable mesh running shoes with a cushioned sole for daily jogs and gym sessions."),
    ("Hydrating Face Moisturizer", "Moisturizer", "Beauty", 1299, 60,
     "Light daily moisturizer with hyaluronic acid for soft, fresh-feeling skin. 100 ml."),
    ("Classic Leather Strap Watch", "Leather watch", "Watches", 4999, 15,
     "Round analog watch with a brown leather strap, a date window and splash resistance."),
    ("Everyday Leather Handbag", "Handbag", "Bags", 6999, 10,
     "Roomy faux-leather handbag with a zip pocket, two inner compartments and a removable shoulder strap."),
    ("Non-Stick Frying Pan 28 cm", "Frying pan", "Home & Kitchen", 2499, 35,
     "Heavy-base frying pan with a non-stick coating that heats evenly and cleans up in seconds."),
    ("Yoga Mat 6 mm", "Yoga mat", "Sports", 1499, 50,
     "Non-slip, sweat-resistant mat with extra cushioning for yoga, stretching and floor workouts."),

    ("Power Bank 10000 mAh", "Power bank", "Electronics", 3999, 30,
     "Slim power bank with fast charging and two USB outputs. Charges most phones about two times."),
    ("Men's Cotton Polo Shirt", "Polo shirt", "Fashion", 1999, 45,
     "Pure cotton polo with a ribbed collar and a regular fit. Easy to wash and keeps its shape."),
    ("Casual Canvas Sneakers", "Sneakers", "Shoes", 3499, 30,
     "Low-top canvas sneakers with a flexible rubber sole. Easy to pair with jeans or shorts."),
    ("Matte Lipstick Set (3 shades)", "Lipstick set", "Beauty", 1899, 28,
     "Three long-wearing matte shades in nude, rose and berry with a smooth, comfortable finish."),
    ("Digital Sports Watch", "Sports watch", "Watches", 2999, 22,
     "Shock-resistant digital watch with stopwatch, alarm, backlight and water resistance."),
    ("Laptop Backpack 15.6 inch", "Backpack", "Bags", 3299, 20,
     "Padded laptop compartment, USB charging port and water-resistant fabric for school, office and travel."),
    ("Stainless Steel Water Bottle 750 ml", "Water bottle", "Home & Kitchen", 1199, 70,
     "Double-wall insulated bottle that keeps drinks cold for 12 hours and hot for 6 hours."),
    ("Adjustable Dumbbell Set 10 kg", "Dumbbells", "Sports", 6499, 12,
     "Pair of adjustable dumbbells with a secure locking collar for strength training at home."),

    ("LED Desk Lamp", "Desk lamp", "Electronics", 2799, 0,
     "Foldable desk lamp with three brightness levels and a flexible neck. Gentle on the eyes."),
    ("Wool Blend Winter Shawl", "Shawl", "Fashion", 3799, 14,
     "Warm, lightweight shawl with a soft feel and a classic border design."),
    ("Leather Formal Shoes", "Formal shoes", "Shoes", 7499, 9,
     "Classic lace-up shoes in genuine leather with a padded insole for all-day comfort."),
    ("Vitamin C Face Serum 30 ml", "Face serum", "Beauty", 2199, 33,
     "Brightening serum with vitamin C that absorbs quickly and layers well under sunscreen."),
    ("Stainless Steel Analog Watch", "Steel watch", "Watches", 6999, 11,
     "Slim steel watch with a scratch-resistant face and a secure folding clasp."),
    ("Travel Duffel Bag", "Duffel bag", "Bags", 4499, 4,
     "Spacious weekend duffel with a shoe compartment, padded straps and a sturdy zip."),
    ("Ceramic Dinner Set 24-Piece", "Dinner set", "Home & Kitchen", 8999, 8,
     "Dinner plates, side plates, bowls and mugs for six people. Microwave and dishwasher safe."),
    ("Football Size 5", "Football", "Sports", 1799, 38,
     "Machine-stitched match ball with a durable cover and a steady bounce. Pump not included."),

    ("Portable Bluetooth Speaker", "Speaker", "Electronics", 4499, 26,
     "Splash-proof speaker with deep bass and 10 hours of playtime. Pairs with phones and laptops."),
    ("Classic Denim Jacket", "Denim jacket", "Fashion", 4299, 17,
     "Mid-weight denim jacket with a button front and two chest pockets. A wardrobe staple."),
    ("Comfort Slide Sandals", "Sandals", "Shoes", 1599, 55,
     "Soft, flexible slides with a contoured footbed. Quick-drying and easy to clean."),
    ("Eau de Parfum 50 ml", "Perfume", "Beauty", 3499, 5,
     "Fresh floral-woody fragrance with long-lasting wear. Comes in a gift-ready box."),
    ("Smart Fitness Watch", "Fitness watch", "Watches", 8999, 19,
     "Tracks steps, heart rate and sleep, shows phone notifications and lasts up to 7 days per charge."),
    ("Electric Kettle 1.7 L", "Kettle", "Home & Kitchen", 3499, 32,
     "Stainless steel kettle with automatic shut-off and boil-dry protection. Boils in about 4 minutes."),
]

# Background colour of the placeholder image for each category
CATEGORY_COLORS = {
    "Electronics": "1d4e89",
    "Fashion": "a14b6b",
    "Shoes": "b8581e",
    "Beauty": "8e4a9b",
    "Watches": "3b4a57",
    "Bags": "7a5a3a",
    "Home & Kitchen": "2f7d5b",
    "Sports": "b8342f",
}


def make_image_url(category, label):
    return f"https://placehold.co/600x600/{CATEGORY_COLORS[category]}/ffffff.png?text={quote_plus(label)}"


def seed_products():
    started_at = now()
    added = 0
    for number, (name, label, category, price, stock, description) in enumerate(DEMO_PRODUCTS, start=1):
        product_id = f"demo-{number:02d}"
        reference = db.collection("products").document(product_id)
        if reference.get().exists:
            continue
        reference.set({
            "id": product_id,
            "name": name,
            "description": description,
            "price": price,
            "category": category,
            "image_url": make_image_url(category, label),
            "stock": stock,
            # Later products get a slightly later time, so the last ones count as "newest"
            "created_at": started_at - timedelta(seconds=len(DEMO_PRODUCTS) - number),
        })
        added += 1
    print(f"Products: {added} added, {len(DEMO_PRODUCTS) - added} already existed.")


def create_admin():
    """Creates the admin account from the [admin] section of your secrets."""
    settings = config.admin_settings()
    email = str(settings.get("email", "")).strip().lower()
    password = str(settings.get("password", ""))
    name = str(settings.get("name", "Store Admin"))
    if not email:
        print("Admin: [admin] email is empty in the secrets, so no admin account was created.")
        return

    try:
        user = auth.get_user_by_email(email)  # the account already exists, e.g. registered on the site
    except auth.UserNotFoundError:
        if len(password) < config.MIN_PASSWORD_LENGTH:
            print(f"Admin: set a password of at least {config.MIN_PASSWORD_LENGTH} characters in [admin] and run this again.")
            return
        user = auth.create_user(email=email, password=password, display_name=name)

    profile_ref = db.collection("users").document(user.uid)
    if profile_ref.get().exists:
        profile_ref.update({"role": "admin"})
    else:
        create_user_profile(user.uid, user.display_name or name, email, role="admin")
    print(f"Admin: {email} can now log in as an admin.")


if __name__ == "__main__":
    seed_products()
    create_admin()
