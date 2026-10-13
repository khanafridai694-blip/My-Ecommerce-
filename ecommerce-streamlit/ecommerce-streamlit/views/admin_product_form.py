"""Add a new product, or edit one. The product to edit comes from the address: /admin-product?id=..."""
import streamlit as st
from google.api_core.exceptions import GoogleAPIError

import config
import database
import routes
import state
import ui

ui.require_admin()

product_id = st.query_params.get("id", "")
editing = bool(product_id)
product = database.get_product(product_id) if editing else {}

if editing and product is None:
    ui.empty_state(
        "We could not find that product",
        "It may have been deleted.",
        "Back to products",
        "admin_products",
        key="form_missing",
        symbol="🔍",
    )
    ui.stop_page()

ui.section_title("Edit product" if editing else "Add a product")
suffix = product_id or "new"  # keeps the form fields separate for each product

if editing and product.get("image_url"):
    st.html(f'<div class="thumb-box" style="width:140px">{ui.image_tag(product)}</div>')

category_index = config.CATEGORIES.index(product["category"]) if product.get("category") in config.CATEGORIES else 0

with st.form("product_form", border=True):
    name = st.text_input("Product name", value=product.get("name", ""), max_chars=100, key=f"form_name_{suffix}")
    category = st.selectbox("Category", config.CATEGORIES, index=category_index, key=f"form_category_{suffix}")
    price_column, stock_column = st.columns(2)
    with price_column:
        price = st.number_input(
            f"Price ({config.CURRENCY})", min_value=0.0, value=float(product.get("price", 0.0)), step=1.0,
            format="%.2f", key=f"form_price_{suffix}",
        )
    with stock_column:
        stock = st.number_input(
            "Stock", min_value=0, value=int(product.get("stock", 0)), step=1, key=f"form_stock_{suffix}"
        )
    description = st.text_area(
        "Description", value=product.get("description", ""), max_chars=1000, height=140, key=f"form_description_{suffix}"
    )
    image_url = st.text_input(
        "Image link", value=product.get("image_url", ""), placeholder="https://...", key=f"form_image_url_{suffix}"
    )
    upload = st.file_uploader(
        "Or upload an image",
        type=config.ALLOWED_IMAGE_TYPES,
        help=f"PNG, JPG or WebP, up to {config.MAX_IMAGE_MB} MB. Uploading needs Firebase Storage. "
             "An uploaded file replaces the image link.",
        key=f"form_upload_{suffix}",
    )
    saved = st.form_submit_button("Save changes" if editing else "Add product", type="primary")

if st.button("Cancel", key="form_cancel"):
    routes.go("admin_products")

if saved:
    name, description, image_url = name.strip(), description.strip(), image_url.strip()
    problem = None
    if not 2 <= len(name) <= 100:
        problem = "The product name needs 2 to 100 characters."
    elif not 10 <= len(description) <= 1000:
        problem = "The description needs 10 to 1000 characters."
    elif not 0 < price <= 10_000_000:
        problem = "The price must be more than 0."
    elif stock > 100_000:
        problem = "The stock can be at most 100,000."
    elif upload is None and not image_url.startswith(("http://", "https://")):
        problem = "Paste an image link that starts with https:// or upload an image."
    elif upload is not None and upload.size > config.MAX_IMAGE_MB * 1024 * 1024:
        problem = f"The image must be smaller than {config.MAX_IMAGE_MB} MB."

    if problem:
        st.error(problem)
    else:
        try:
            if upload is not None:
                with st.spinner("Uploading the image..."):
                    image_url = database.upload_product_image(upload.getvalue(), upload.name, upload.type)
            database.save_product(
                {
                    "name": name,
                    "description": description,
                    "category": category,
                    "price": round(float(price), 2),
                    "stock": int(stock),
                    "image_url": image_url,
                },
                product_id or None,
            )
        except database.StoreError as store_problem:
            st.error(str(store_problem))
        except GoogleAPIError:
            st.error("The product could not be saved. If you uploaded an image, check your Firebase Storage "
                     "setup or paste an image link instead.")
        else:
            state.refresh_products()
            state.flash("success", f"{name} was {'updated' if editing else 'added'}.")
            routes.go("admin_products")
