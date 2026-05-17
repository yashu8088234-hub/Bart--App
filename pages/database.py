import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

# =========================================================
# INIT FIRESTORE (SAFE SINGLETON)
# =========================================================
@st.cache_resource
def init_firestore():

    # Load Firebase credentials from Streamlit secrets
    cred = credentials.Certificate(st.secrets["FIREBASE_KEY"])

    # Prevent duplicate initialization
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    return firestore.client()


db = init_firestore()

# =========================================================
# TEST WRITE FUNCTION
# =========================================================
def add_test_stock():
    """
    Writes a sample document to Firestore
    """
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
# WRITE STOCK (REAL FUNCTION YOU WILL USE LATER)
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
# READ STOCK BY DATE
# =========================================================
def get_stock_by_date(date_str):

    docs = db.collection("stock") \
        .where("date", "==", date_str) \
        .stream()

    data = []

    for doc in docs:
        data.append(doc.to_dict())

    return data


# =========================================================
# CLEAR COLLECTION (FOR TESTING ONLY)
# =========================================================
def clear_stock_collection():

    docs = db.collection("stock").stream()

    for doc in docs:
        doc.reference.delete()

    return "🗑️ All stock data deleted"
