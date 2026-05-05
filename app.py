import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ---------------- Page Config ----------------
st.set_page_config(layout="wide", page_title="BART Manager Dashboard")

# ---------------- Clean Modern UI ----------------
st.markdown("""
<style>

/* Hide Streamlit UI */
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}

/* App background */
.stApp {
    background: #f6f8fb;
    font-family: 'Segoe UI', sans-serif;
}

/* Layout spacing */
.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 1400px;
}

/* Header Card */
.dashboard-header {
    background: white;
    padding: 25px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    margin-bottom: 25px;
    text-align: center;
    border-left: 6px solid #4b6cb7;
}

.dashboard-header h1 {
    margin: 0;
    font-size: 38px;
    color: #1f1f2e;
}

.dashboard-header p {
    margin: 5px 0 0;
    color: #666;
    font-size: 16px;
}

/* Section title */
.section-title {
    font-size: 20px;
    font-weight: 600;
    margin: 20px 0 10px;
    color: #1f1f2e;
}

/* Metrics cards */
[data-testid="metric-container"] {
    background: white;
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    border: 1px solid #eee;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    background: white;
}

/* Buttons */
.stButton > button {
    background: #4b6cb7;
    color: white;
    border-radius: 10px;
    padding: 10px 18px;
    border: none;
    font-weight: 500;
    transition: 0.2s;
}

.stButton > button:hover {
    background: #3a56a0;
    transform: translateY(-2px);
}

</style>
""", unsafe_allow_html=True)

# ---------------- Header ----------------
st.markdown("""
<div class="dashboard-header">
    <h1>🍩 BART Manager Dashboard</h1>
    <p>Branch-wise Sales & Performance Analytics</p>
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

st.markdown("<div class='section-title'>Select Branch</div>", unsafe_allow_html=True)
selected_branch = st.selectbox("Branch", ["-- Select Branch --"] + branches)

if selected_branch == "-- Select Branch --":
    st.warning("Please select a branch to view sales.")
    st.stop()

branch_info = next(b for b in branch_data if f"{b['BranchCode']} - {b['BranchName']}" == selected_branch)
sheet_id = branch_info["SheetID"]

# ---------------- Load Branch Sales ----------------
try:
    branch_sheet = client.open_by_key(sheet_id).worksheet("Sales")
    records = branch_sheet.get_all_records()
    df = pd.DataFrame(records)
except Exception as e:
    st.error(f"Failed to load branch sales sheet: {e}")
    st.stop()

if df.empty:
    st.warning("No sales data found for this branch.")
    st.stop()

# ---------------- Convert numeric ----------------
for col in ["Quantity", "Unit Price (SAR)"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df["Total (SAR)"] = pd.to_numeric(
    df.get("Total (SAR)", df["Quantity"] * df["Unit Price (SAR)"]),
    errors="coerce"
).fillna(0)

# ---------------- Date Filter ----------------
selected_date = st.date_input("Select Date", datetime.today())
date_str = selected_date.strftime("%Y-%m-%d")
df_date = df[df["Date"] == date_str]

if df_date.empty:
    st.info(f"No sales found for {date_str}")
    st.stop()

# ---------------- Metrics ----------------
total_revenue = df_date["Total (SAR)"].sum()
total_items = df_date["Quantity"].sum()
top_item = df_date.groupby("Item")["Quantity"].sum().idxmax()
low_item = df_date.groupby("Item")["Quantity"].sum().idxmin()

st.markdown("<div class='section-title'>📊 Daily Performance</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Revenue (SAR)", f"{total_revenue:.2f}")

with col2:
    st.metric("Items Sold", int(total_items))

with col3:
    st.metric("Top Seller", top_item)

# ---------------- Growth ----------------
prev_date = (selected_date - timedelta(days=1)).strftime("%Y-%m-%d")
prev_revenue = df[df["Date"] == prev_date]["Total (SAR)"].sum()
growth = total_revenue - prev_revenue
st.metric("Revenue Growth vs Yesterday", f"{growth:.2f} SAR")

# ---------------- Table ----------------
st.markdown("<div class='section-title'>🧾 Sales Table</div>", unsafe_allow_html=True)
st.dataframe(df_date[["Item", "Quantity", "Unit Price (SAR)", "Total (SAR)"]],
             use_container_width=True)

# ---------------- Charts ----------------
st.markdown("<div class='section-title'>📈 Analytics</div>", unsafe_allow_html=True)

chart1, chart2 = st.columns(2)

with chart1:
    top10_items = df_date.groupby("Item")["Quantity"].sum().sort_values(ascending=False).head(10)
    fig1, ax1 = plt.subplots()
    ax1.barh(top10_items.index[::-1], top10_items.values[::-1])
    ax1.set_title("Top 10 Items Sold")
    ax1.set_xlabel("Quantity")
    st.pyplot(fig1)

with chart2:
    last_7_days = [(selected_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    revenue_trend = [df[df["Date"] == d]["Total (SAR)"].sum() for d in last_7_days]

    fig2, ax2 = plt.subplots()
    ax2.plot(last_7_days, revenue_trend, marker="o")
    ax2.set_title("Last 7 Days Revenue Trend")
    ax2.tick_params(axis='x', rotation=45)
    st.pyplot(fig2)

# ---------------- Lowest item ----------------
st.markdown(f"**Lowest Selling Item Today:** {low_item}")

# ---------------- Download ----------------
csv = df_date.to_csv(index=False).encode('utf-8')

st.download_button(
    label="⬇ Download CSV Report",
    data=csv,
    file_name=f"{selected_branch}_{date_str}_sales.csv",
    mime="text/csv"
)

# ---------------- Back ----------------
if st.button("⬅ Back"):
    st.switch_page("pages/staff_dashboard.py")
