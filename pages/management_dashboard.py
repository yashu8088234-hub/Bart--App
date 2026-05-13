import streamlit as st
import pandas as pd
import psycopg2
from st_aggrid import AgGrid

# =========================================================
# PAGE
# =========================================================

st.set_page_config(layout="wide")
st.title("🧪 STOCK TEST (PostgreSQL Check)")

# =========================================================
# DB CONNECTION TEST
# =========================================================

try:
    conn = psycopg2.connect(
        dbname="mydatabase",
        user="postgres",
        host="localhost",
        port=5432
    )
    st.success("✅ PostgreSQL Connected")

except Exception as e:
    st.error(e)
    st.stop()

# =========================================================
# FAKE DATA (JUST FOR TEST)
# =========================================================

data = pd.DataFrame([
    ["Jeddah", "Chicken", "SKU1", "KG", "daily", "2026-01-01", 10],
    ["Jeddah", "Chicken", "SKU1", "KG", "daily", "2026-01-01", 15],
    ["Riyadh", "Chicken", "SKU1", "KG", "daily", "2026-01-01", 20],
    ["Jeddah", "Rice", "SKU2", "KG", "weekly", "2026-01-01", 5],
], columns=[
    "branch_name",
    "item_name",
    "sku",
    "uom",
    "stock_type",
    "stock_date",
    "quantity"
])

st.subheader("📦 Dummy Stock Data")
AgGrid(data)

# =========================================================
# TEST QUERY FROM DB (REAL CHECK)
# =========================================================

try:
    df = pd.read_sql("SELECT * FROM stock_data LIMIT 5", conn)
    st.subheader("📊 Data from PostgreSQL")
    st.dataframe(df)

except Exception as e:
    st.warning("Table is empty or not accessible yet")
    st.text(e)
