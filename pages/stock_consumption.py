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
.block-container {padding:0 !important; margin:0 auto !important; max-width: 100% !important;}
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets Setup ----------------
try:
    creds_dict = dict(st.secrets["GOOGLE_CREDS_JSON"])  # Use your TOML secret
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"Error connecting to Google API: {e}")
    st.stop()

# ---------------- Load Branches ----------------
@st.cache_data
def load_branches():
    try:
        sheet = client.open("MASTERBRANCHSHEET").sheet1
        return sheet.get_all_records()
    except Exception as e:
        st.error(f"Error loading master branch sheet: {e}")
        st.stop()

branch_data = load_branches()
branches = [f"{b['BranchCode']} - {b['BranchName']}" for b in branch_data]

# ---------------- Branch Selection ----------------
if 'selected_branch' not in st.session_state:
    st.session_state.selected_branch = "-- Select Branch --"

st.session_state.selected_branch = st.selectbox(
    "Select Branch",
    ["-- Select Branch --"] + branches,
    index=branches.index(st.session_state.selected_branch) + 1
    if st.session_state.selected_branch != "-- Select Branch --" else 0
)
selected_branch = st.session_state.selected_branch

if selected_branch == "-- Select Branch --":
    st.info("Please select a branch to view sales.")
    st.stop()

# ---------------- Branch Sheet Setup ----------------
branch_info = next(b for b in branch_data if f"{b['BranchCode']} - {b['BranchName']}" == selected_branch)
try:
    branch_sheet = client.open_by_key(branch_info['SheetID'])
    sheet = branch_sheet.worksheet("Daily Sales")  # assuming tab name
except Exception as e:
    st.error(f"Error opening branch sheet: {e}")
    st.stop()

# ---------------- Load Sales Data ----------------
@st.cache_data(ttl=300)
def load_sales(sheet):
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    if not df.empty:
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
        df["Unit Price (SAR)"] = pd.to_numeric(df["Unit Price (SAR)"], errors="coerce").fillna(0)
        if "Total (SAR)" in df.columns:
            df["Total (SAR)"] = pd.to_numeric(df["Total (SAR)"], errors="coerce").fillna(0)
        else:
            df["Total (SAR)"] = df["Quantity"] * df["Unit Price (SAR)"]
    return df

df = load_sales(sheet)

# ---------------- Page Title ----------------
st.markdown(f"<h1 style='text-align:center;color:red;'>{selected_branch} - Manager Dashboard</h1>", unsafe_allow_html=True)

if df.empty:
    st.warning("No sales data found for this branch.")
    st.stop()

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
col1, col2 = st.columns(2)
col1.metric("Total Revenue (SAR)", f"{total_revenue:.2f}")
col2.metric("Total Items Sold", int(total_items))

# ---------------- Sales Table ----------------
st.markdown("### Sales Table")
st.dataframe(df_date[["Item", "Quantity", "Unit Price (SAR)", "Total (SAR)"]], use_container_width=True)

# ---------------- Charts ----------------
chart1, chart2 = st.columns(2)

# Bar Chart: Quantity Sold
with chart1:
    bar_data = df_date.groupby("Item")["Quantity"].sum()
    fig1, ax1 = plt.subplots(figsize=(6,4))
    ax1.bar(bar_data.index, bar_data.values, color="#4CAF50")
    ax1.set_title("Items Sold")
    ax1.set_ylabel("Quantity")
    ax1.tick_params(axis='x', rotation=45)
    st.pyplot(fig1)

# Pie Chart: Revenue Distribution
with chart2:
    pie_data = df_date.groupby("Item")["Total (SAR)"].sum()
    fig2, ax2 = plt.subplots(figsize=(5,4))
    ax2.pie(pie_data.values, labels=pie_data.index, autopct="%1.1f%%")
    ax2.set_title("Revenue Distribution")
    st.pyplot(fig2)

# ---------------- Back Button ----------------
if st.button("⬅ Back"):
    st.session_state.selected_branch = "-- Select Branch --"
    st.experimental_rerun()
