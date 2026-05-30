import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG
# =========================
SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
TAB_NAME = "StaffSchedule"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# =========================
# GOOGLE SHEETS AUTH
# =========================
@st.cache_resource
def connect_gsheet():
    creds = Credentials.from_service_account_file(
        "service_account.json", scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    return sheet

@st.cache_data(ttl=60)
def load_data():
    sheet = connect_gsheet()
    ws = sheet.worksheet(TAB_NAME)

    data = ws.get_all_records()
    df = pd.DataFrame(data)

    return df


# =========================
# UI
# =========================
st.set_page_config(page_title="Staff Live Dashboard", layout="wide")

st.title("📊 Staff Live Schedule Dashboard")

df = load_data()

# =========================
# CLEAN COLUMNS
# =========================
df.columns = [c.strip() for c in df.columns]

# =========================
# FILTERS
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    branch = st.selectbox("🏢 Branch", ["All"] + sorted(df["Branch"].dropna().unique().tolist()))

with col2:
    role = st.selectbox("👨‍💼 Role", ["All"] + sorted(df["Role"].dropna().unique().tolist()))

with col3:
    name = st.selectbox("👤 Name", ["All"] + sorted(df["Name"].dropna().unique().tolist()))

# =========================
# FILTER LOGIC
# =========================
filtered = df.copy()

if branch != "All":
    filtered = filtered[filtered["Branch"] == branch]

if role != "All":
    filtered = filtered[filtered["Role"] == role]

if name != "All":
    filtered = filtered[filtered["Name"] == name]

# =========================
# SHOW RAW TABLE
# =========================
st.subheader("📅 Raw Schedule Data")
st.dataframe(filtered, use_container_width=True)

# =========================
# LIVE SUMMARY VIEW
# =========================
st.subheader("🔥 Live Staff Status View")

days = [col for col in df.columns if "(" in col or "Friday" in col or "Saturday" in col]

view_df = filtered[["Branch", "Name", "Role"] + days + ["Over-Time"]]

st.dataframe(view_df, use_container_width=True)

# =========================
# OT ANALYSIS
# =========================
st.subheader("⏱ Overtime Summary")

ot_col = "Over-Time"

if ot_col in df.columns:
    df["OT_Hours"] = (
        df[ot_col].astype(str)
        .str.replace("h", "", regex=False)
        .replace("", "0")
    )
    df["OT_Hours"] = pd.to_numeric(df["OT_Hours"], errors="coerce").fillna(0)

    ot_summary = df.groupby("Branch")["OT_Hours"].sum().reset_index()

    st.dataframe(ot_summary, use_container_width=True)

    st.bar_chart(ot_summary.set_index("Branch"))
