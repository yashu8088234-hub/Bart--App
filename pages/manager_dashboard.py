import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ---------------- Page Config ----------------
st.set_page_config(layout="wide", page_title="BART Manager Dashboard")

# ---------------- Hide Streamlit Default UI ----------------
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}
.block-container {padding:0 !important; margin:0 auto !important; max-width: 100% !important;}
.stApp {background: linear-gradient(135deg,#eef2f7,#d6e4ff);}
</style>
""", unsafe_allow_html=True)

# ---------------- BART Header ----------------
st.markdown("""
<div style="
    background: linear-gradient(90deg, #1f1f2e, #4b6cb7);
    padding: 20px;
    border-radius: 12px;
    text-align: center;
">
<h1 style='color:#ffffff; font-size:48px; margin:0;'>BART Manager Dashboard</h1>
<p style='color:#e0e0e0; font-size:20px; margin:0;'>Branch-wise Sales & Performance</p>
</div>
""", unsafe_allow_html=True)

# ---------------- Google Sheets Connection ----------------
try:
    creds_dict = dict(st.secrets["GOOGLE_CREDS_JSON"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"Error connecting to Google API: {e}")
    st.stop()

# ---------------- Branch Selection ----------------
try:
    master_sheet = client.open("MASTERBRANCHSHEET").sheet1
    branch_data = master_sheet.get_all_records()
    branches = [f"{b['BranchCode']} - {b['BranchName']}" for b in branch_data]
except Exception as e:
    st.error(f"Failed to load branches: {e}")
    st.stop()

st.markdown("<h3 style='text-align:center;'>Select Branch</h3>", unsafe_allow_html=True)
selected_branch = st.selectbox("Branch", ["-- Select Branch --"] + branches)

if selected_branch == "-- Select Branch --":
    st.warning("Please select a branch to view sales.")
    st.stop()

branch_info = next(b for b in branch_data if f"{b['BranchCode']} - {b['BranchName']}" == selected_branch)
sheet_id = branch_info["SheetID"]

# ---------------- Load Branch Sales Sheet ----------------
try:
    branch_sheet = client.open_by_key(sheet_id).worksheet("Daily Sales")
    records = branch_sheet.get_all_records()
    df = pd.DataFrame(records)
except Exception as e:
    st.error(f"Failed to load branch sales sheet: {e}")
    st.stop()

if df.empty:
    st.warning("No sales data found for this branch.")
    st.stop()

# Convert numeric columns safely
for col in ["Quantity", "Unit Price (SAR)"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
df["Total (SAR)"] = pd.to_numeric(df.get("Total (SAR)", df["Quantity"] * df["Unit Price (SAR)"]), errors="coerce").fillna(0)

# ---------------- Date Filter ----------------
selected_date = st.date_input("Select Date", datetime.today())
date_str = selected_date.strftime("%Y-%m-%d")
df_date = df[df["Date"] == date_str]

if df_date.empty:
    st.info(f"No sales found for {date_str}")
    st.stop()

# ---------------- Summary Metrics ----------------
total_revenue = df_date["Total (SAR)"].sum()
total_items = df_date["Quantity"].sum()
top_item = df_date.groupby("Item")["Quantity"].sum().idxmax()

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Revenue (SAR)", f"{total_revenue:.2f}")
col2.metric("📦 Total Items Sold", int(total_items))
col3.metric("🏆 Top Seller", top_item)

# ---------------- Revenue Growth vs Yesterday ----------------
prev_date = (selected_date - timedelta(days=1)).strftime("%Y-%m-%d")
prev_revenue = df[df["Date"] == prev_date]["Total (SAR)"].sum()
growth = total_revenue - prev_revenue
st.metric("Revenue Growth vs Yesterday", f"{growth:.2f}")

# ---------------- Sales Table ----------------
st.markdown("### Sales Table")
st.dataframe(df_date[["Item", "Quantity", "Unit Price (SAR)", "Total (SAR)"]], use_container_width=True)

# ---------------- Charts ----------------
chart1, chart2 = st.columns(2)

# Bar Chart - Items Sold
with chart1:
    bar_data = df_date.groupby("Item")["Quantity"].sum()
    fig1, ax1 = plt.subplots(figsize=(6,4))
    ax1.bar(bar_data.index, bar_data.values, color="#4CAF50")
    ax1.set_title("Items Sold")
    ax1.set_ylabel("Quantity")
    ax1.tick_params(axis='x', rotation=45)
    st.pyplot(fig1)

# Pie Chart - Revenue Distribution
with chart2:
    pie_data = df_date.groupby("Item")["Total (SAR)"].sum()
    fig2, ax2 = plt.subplots(figsize=(5,4))
    ax2.pie(pie_data.values, labels=pie_data.index, autopct="%1.1f%%", colors=plt.cm.Paired.colors)
    ax2.set_title("Revenue Distribution")
    st.pyplot(fig2)

# ---------------- Top N Items ----------------
top_n = st.slider("Top N items by quantity", 1, 20, 5)
top_items = df_date.groupby("Item")["Quantity"].sum().sort_values(ascending=False).head(top_n)
st.markdown(f"### Top {top_n} Items Sold")
st.table(top_items)

# ---------------- Export CSV ----------------
csv = df_date.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download CSV Report",
    data=csv,
    file_name=f"{selected_branch}_{date_str}_sales.csv",
    mime="text/csv"
)

# ---------------- Back Button ----------------
if st.button("⬅ Back"):
    st.switch_page("pages/staff_dashboard.py")
