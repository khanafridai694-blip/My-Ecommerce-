# ShopEase - a Streamlit + Firebase online store

A small, professional online store written in Python. Customers browse products, search, fill a
cart and place cash-on-delivery orders. Admins manage products and orders from a dashboard.
The code is short and plain on purpose, so it is easy to read and expand.

## Features

**Customers:** register, log in, log out, home page, categories, product list with search and
sorting, product details, add to cart, change quantity, remove from cart, checkout, place order,
view my orders with a progress tracker.

**Admin:** log in, dashboard (key numbers, orders by status, low stock), add / edit / delete
products, view products, view orders, update order status (Pending, Confirmed, Shipped,
Delivered, Cancelled). Cancelling an order puts its items back in stock.

## Requirements

- Python 3.10 or newer
- A free Firebase account (https://console.firebase.google.com)
- A GitHub account (to deploy on Streamlit Community Cloud)
- Packages in `requirements.txt`: streamlit, firebase-admin, requests

## Project structure

```
ecommerce-streamlit/
├── streamlit_app.py     entry point: top bar, page, footer
├── views/               one file per page (home, shop, product, cart, checkout, orders,
│                        account, admin_dashboard, admin_products, admin_product_form, admin_orders)
├── ui.py                header, footer, product cards and other shared page pieces
├── state.py             logged-in user, flash messages, cached product list
├── routes.py            page list and helpers to open pages
├── accounts.py          register and log in with Firebase Authentication
├── database.py          all Firestore and Storage code
├── firebase_config.py   connects to Firebase
├── config.py            store name, currency, categories, secrets
├── seed_data.py         adds 30 demo products and the admin account
├── assets/style.css     styles for the custom HTML pieces
├── .streamlit/config.toml            colours and fonts (theme)
├── .streamlit/secrets.toml.example   copy this to secrets.toml
└── requirements.txt, README.md, .gitignore
```

## Installation

```bash
python -m venv venv
venv\Scripts\activate            # Windows
source venv/bin/activate         # macOS / Linux
pip install -r requirements.txt
```

## Firebase setup

1. Open the Firebase console and click **Add project**.
2. **Authentication > Sign-in method:** turn on **Email/Password**.
3. **Firestore Database > Create database.** Choose a location and start in **production mode**.
   Keep the default locked rules. Only this app talks to Firestore (through the Admin SDK, which
   rules do not block), so browsers never touch the database directly.
4. **Project settings > Service accounts > Generate new private key.** A JSON file is downloaded.
   Its values go into the secrets below. Never commit this file.
5. **Project settings > General:** copy the **Web API Key**. It is used to check passwords at login.
6. **Optional - image uploads:** open **Storage > Get started** and copy the bucket name
   (for example `your-project-id.firebasestorage.app`). Cloud Storage for Firebase needs the
   pay-as-you-go **Blaze** plan. If you skip this step, everything still works: admins paste
   an image link instead of uploading a file.

The collections `users`, `products`, `cart` and `orders` are created automatically.
Orders keep their items inside the order, so there is no separate `order_items` collection.

## Secrets

All secrets live in one place. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
and fill it in:

| Secret | Needed | What it is |
|---|---|---|
| `firebase_web_api_key` | yes | Web API Key from Project settings |
| `[firebase]` table | yes | Every value from the service account JSON file (keep `private_key` in double quotes) |
| `storage_bucket` | optional | Turns on image uploads |
| `[admin]` table | for `seed_data.py` | Email, password and name of the first admin account |

`.streamlit/secrets.toml` is in `.gitignore`, so it is never committed.

## Run locally

```bash
python seed_data.py              # adds 30 demo products and creates the admin account
streamlit run streamlit_app.py   # opens the store at http://localhost:8501
```

- Run both commands from the project folder, so the secrets file is found.
- Log in on the normal **Account** page with the admin email and password. Admins are sent to
  the dashboard.
- You can also register a normal account first, put that email in `[admin]` and run
  `python seed_data.py` again. It turns that account into an admin.
- Demo images are placeholders from placehold.co. Replace them in **Admin > Products > Edit**.
- Prices use `Rs.`. Change `CURRENCY` and `STORE_NAME` in `config.py`.
- Customers must log in to use the cart.

## Deploy on Streamlit Community Cloud

1. Push the project to a GitHub repository. Check that `.streamlit/secrets.toml` is **not** in it.
2. Go to https://share.streamlit.io, sign in with GitHub and click **Create app**.
3. Choose your repository and branch. Set **Main file path** to `streamlit_app.py`.
4. Open **Advanced settings**. Pick a Python version (3.10 or newer) and paste the content of your
   `secrets.toml` into the **Secrets** box.
5. Click **Deploy**.

Run `python seed_data.py` on your own computer. It writes to the same Firebase project, so the
live site sees the demo products and the admin account right away.

## Good to know

- **Refreshing the browser page logs you out.** Streamlit starts a new session on every page
  refresh. The cart, orders and account are saved in Firebase, so nothing is lost: just log in again.
- The product list is remembered for 30 seconds (`CACHE_SECONDS` in `config.py`), so other
  visitors may see a stock change after a short delay. Orders always check the real stock.
- Passwords are only handled by Firebase Authentication. They are never stored by this app.
- Admin pages exist only for admin accounts. Other visitors cannot open them, even by typing the address.
- Visitors see friendly messages. Technical errors are written to the app log only.
