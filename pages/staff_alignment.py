import streamlit as st
import pandas as pd
import gspread
import re
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    layout="wide",
    page_title="Staff Dashboard"
)

# =========================
# AUTH CHECK
# =========================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠ Session expired. Please login again.")
    if st.button("⬅ Back to Login"):
        st.switch_page("app.py")
    st.stop()

# =========================
# CONFIG
# =========================
SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
TAB_NAME = "StaffSchedule"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# =========================
# GOOGLE CLIENT
# =========================
@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["GOOGLE_CREDS_JSON"],
        scopes=SCOPES
    )
    return gspread.authorize(creds)

client = get_client()
sheet = client.open_by_key(SHEET_ID)

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=300)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame()

    headers = [str(h).strip() for h in raw[0]]

    seen = {}
    clean_headers = []
    for h in headers:
        if h in seen:
            seen[h] += 1
            h = f"{h}_{seen[h]}"
        else:
            seen[h] = 0
        clean_headers.append(h)

    return pd.DataFrame(raw[1:], columns=clean_headers)

df = load_data()

# =========================
# OT CALC
# =========================
def extract_ot(row):
    total = 0
    for d in DAYS:
        val = str(row.get(d, ""))
        match = re.search(r"\(OT\s+(\d+(?:\.\d+)?)\s*h\)", val)
        if match:
            total += float(match.group(1))
    return total

# =========================
# HEADER
# =========================
st.title("📊 Staff Management Dashboard")

branches = sorted(df["Branch"].dropna().unique()) if not df.empty else []
selected_branch = st.selectbox("🏢 Select Branch", ["All"] + branches)

selected_date = st.date_input("📅 Week", datetime.today())

week_start = selected_date - timedelta(days=(selected_date.weekday() + 1) % 7)
st.caption(f"Week Start: {week_start.strftime('%d %b %Y')}")

# =========================
# FILTER DATA
# =========================
data = df.copy()
if selected_branch != "All":
    data = data[data["Branch"] == selected_branch]

# =========================
# KPI CALC
# =========================
staff_count = len(data)

data["OT"] = data.apply(extract_ot, axis=1)
total_ot = round(data["OT"].sum(), 2)

# =========================
# KPI CARDS (MODERN HEADER)
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("👥 Staff Count", staff_count)

with col2:
    st.metric("⏱ Total OT Hours", f"{total_ot} hrs")

with col3:
    active_branch = selected_branch if selected_branch != "All" else "All Branches"
    st.metric("🏢 View Mode", active_branch)

st.divider()

# =========================
# MINI TABLE (ONLY ESSENTIAL)
# =========================
st.subheader("👨‍💼 Staff List (Compact View)")

if not data.empty:
    mini_df = data[["Branch", "Name", "Role"]].copy()
    mini_df["OT Hours"] = data["OT"].astype(float).round(2)

    st.dataframe(
        mini_df,
        use_container_width=True,
        height=420
    )
else:
    st.info("No staff found for selected branch")

# =========================
# QUICK INSIGHT CHART
# =========================
st.subheader("📈 OT Overview")

if not data.empty:
    chart_df = data.groupby("Name")["OT"].sum().sort_values(ascending=False).head(10)
    st.bar_chart(chart_df)

# =========================
# REFRESH
# =========================
if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
