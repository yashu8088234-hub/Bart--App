import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ---------------- Page Config ----------------
st.set_page_config(layout="wide", page_title="Manager Dashboard")

# ---------------- Hide Streamlit UI ----------------
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets Connection ----------------
scope = [
"https://spreadsheets.google.com/feeds",
"https://www.googleapis.com/auth/drive"
]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Master Inventory").worksheet("Daily Sales")
except Exception as e:
    st.error(f"Google Sheets connection failed: {e}")
    st.stop()

# ---------------- Load Data ----------------
@st.cache_data(ttl=30)
def load_data():
    try:
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
    except Exception as e:
        st.error(f"Error loading sheet data: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    # Convert numeric columns safely
    if "Quantity" in df.columns:
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)

    if "Unit Price (SAR)" in df.columns:
        df["Unit Price (SAR)"] = pd.to_numeric(df["Unit Price (SAR)"], errors="coerce").fillna(0)

    if "Total (SAR)" in df.columns:
        df["Total (SAR)"] = pd.to_numeric(df["Total (SAR)"], errors="coerce").fillna(0)
    else:
        df["Total (SAR)"] = df["Quantity"] * df["Unit Price (SAR)"]

    return df

df = load_data()

# ---------------- Title ----------------
st.markdown("<h1 style='text-align:center;color:red;'>Manager Dashboard</h1>", unsafe_allow_html=True)

if df.empty:
    st.warning("No sales data found.")
    st.stop()

# ---------------- Date Filter ----------------
selected_date = st.date_input("Select Date", datetime.today())
date_str = selected_date.strftime("%Y-%m-%d")

df_date = df[df["Date"] == date_str]

if df_date.empty:
    st.info(f"No sales found for {date_str}")
    st.stop()

# ---------------- Summary ----------------
total_revenue = df_date["Total (SAR)"].sum()
total_items = df_date["Quantity"].sum()

col1, col2 = st.columns(2)

col1.metric("Total Revenue (SAR)", f"{total_revenue:.2f}")
col2.metric("Total Items Sold", int(total_items))

# ---------------- Table ----------------
st.markdown("### Sales Table")
st.dataframe(df_date[["Item", "Quantity", "Unit Price (SAR)", "Total (SAR)"]], use_container_width=True)

# ---------------- Charts ----------------
chart1, chart2 = st.columns(2)

# Bar Chart
with chart1:

    bar_data = df_date.groupby("Item")["Quantity"].sum()

    fig1, ax1 = plt.subplots(figsize=(6,4))
    ax1.bar(bar_data.index, bar_data.values)
    ax1.set_title("Items Sold")
    ax1.set_ylabel("Quantity")
    ax1.tick_params(axis='x', rotation=45)

    st.pyplot(fig1)

# Pie Chart
with chart2:

    pie_data = df_date.groupby("Item")["Total (SAR)"].sum()

    fig2, ax2 = plt.subplots(figsize=(5,4))
    ax2.pie(pie_data.values, labels=pie_data.index, autopct="%1.1f%%")
    ax2.set_title("Revenue Distribution")

    st.pyplot(fig2)

# ---------------- Back Button ----------------
if st.button("⬅ Back"):
    st.switch_page("pages/staff_dashboard.py")