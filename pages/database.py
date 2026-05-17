import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# =========================================================
# FIRESTORE INIT (SAFE + STREAMLIT CLOUD READY)
# =========================================================
@st.cache_resource
def init_firestore():

    raw_key = st.secrets["FIREBASE_KEY"]

    # -------------------------------------------------
    # Convert secrets into dict safely
    # -------------------------------------------------
    if isinstance(raw_key, str):
        try:
            key_dict = json.loads(raw_key)
        except Exception:
            raise ValueError(
                "❌ FIREBASE_KEY is not valid JSON. Fix Streamlit secrets format."
            )
    else:
        key_dict = raw_key

    # -------------------------------------------------
    # Prevent duplicate Firebase initialization
    # -------------------------------------------------
    if not firebase_admin._apps:
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)

    return firestore.client()


# Firestore client
db = init_firestore()

# =========================================================
# TEST WRITE
# =========================================================
def add_test_stock():
    db.collection("stock").add({
        "branch": "Jeddah",
        "item": "Rice",
        "sku": "R01",
        "uom": "KG",
        "date": "2026-05-17",
        "qty": 10
    })
    return "✅ Test data written"


# =========================================================
# ADD STOCK
# =========================================================
def add_stock(branch, item, sku, uom, date, qty):

    db.collection("stock").add({
        "branch": branch,
        "item": item,
        "sku": sku,
        "uom": uom,
        "date": date,
        "qty": float(qty)
    })

    return "✅ Stock added"


# =========================================================
# GET STOCK BY DATE
# =========================================================
def get_stock_by_date(date_str):

    docs = db.collection("stock") \
        .where("date", "==", date_str) \
        .stream()

    return [doc.to_dict() for doc in docs]


# =========================================================
# DELETE ALL STOCK (TEST ONLY)
# =========================================================
def clear_stock():

    docs = db.collection("stock").stream()

    for doc in docs:
        doc.reference.delete()

    return "🗑️ All stock cleared"
