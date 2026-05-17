import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# =========================================================
# FIRESTORE INIT (SAFE + FIXED FOR STREAMLIT SECRETS)
# =========================================================
@st.cache_resource
def init_firestore():

    # 🔥 Get Firebase key from Streamlit secrets
    firebase_key = st.secrets["FIREBASE_KEY"]

    # 🔥 Convert string → dict (IMPORTANT FIX)
    if isinstance(firebase_key, str):
        firebase_key = json.loads(firebase_key)

    # 🔥 Prevent duplicate Firebase initialization
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_key)
        firebase_admin.initialize_app(cred)

    return firestore.client()


# Firestore client
db = init_firestore()


# =========================================================
# TEST WRITE FUNCTION
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

    return "✅ Test data written successfully"


# =========================================================
# ADD STOCK (REAL USE)
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

    return "✅ Stock added successfully"


# =========================================================
# READ STOCK BY DATE
# =========================================================
def get_stock_by_date(date_str):

    docs = db.collection("stock") \
        .where("date", "==", date_str) \
        .stream()

    data = [doc.to_dict() for doc in docs]

    return data


# =========================================================
# CLEAR COLLECTION (TEST ONLY)
# =========================================================
def clear_stock_collection():

    docs = db.collection("stock").stream()

    for doc in docs:
        doc.reference.delete()

    return "🗑️ All stock data deleted"
