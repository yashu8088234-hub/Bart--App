import streamlit as st
import pandas as pd
import gspread
import re
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================
# PAGE
# =========================
st.set_page_config(layout="wide", page_title="Ops Control Center")

# =========================
# AUTH
# =========================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Session expired")
    st.stop()

# =========================
# SHEET CONFIG
# =========================
SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
TAB_NAME = "StaffSchedule"

DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

# =========================
# CLIENT
# =========================
@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["GOOGLE_CREDS_JSON"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    return gspread.authorize(creds)

client = get_client()
sheet = client.open_by_key(SHEET_ID)

# =========================
# LOAD SAFE DATA
# =========================
@st.cache_data(ttl=300)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(raw[1:], columns=raw[0])

    # clean NaN issues
    df = df.fillna("")

    return df

df = load_data()

# =========================
# SAFE SHIFT PARSER
# =========================
def parse_shift(cell):
    try:
        if not cell or str(cell).strip() == "":
            return None

        match = re.search(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", str(cell))
        if not match:
            return None

        start = datetime.strptime(match.group(1), "%H:%M").time()
        end = datetime.strptime(match.group(2), "%H:%M").time()

        return start, end

    except:
        return None

def is_active(cell, now_time):
    shift = parse_shift(cell)
    if not shift:
        return False
    start, end = shift
    return start <= now_time <= end

# =========================
# TIME
# =========================
now_time = datetime.now().time()

# =========================
# FILTER UI
# =========================
branches = sorted(df["Branch"].dropna().unique()) if not df.empty else []

selected_branch = st.selectbox("🏢 Branch", branches)

data = df[df["Branch"] == selected_branch].copy()

# =========================
# SAFE ACTIVE SPLIT
# =========================
active_rows = []
inactive_rows = []

if not data.empty:

    today = DAYS[(datetime.today().weekday() + 1) % 7]

    for _, row in data.iterrows():
        try:
            cell = row.get(today, "")
        except:
            cell = ""

        if is_active(cell, now_time):
            active_rows.append(row)
        else:
            inactive_rows.append(row)

active_df = pd.DataFrame(active_rows)
inactive_df = pd.DataFrame(inactive_rows)

# =========================
# TOP KPIs
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("👥 Total Workers", len(data))

with col2:
    st.metric("🔴 Active Now", len(active_df))

with col3:
    st.metric("⚪ Inactive", len(inactive_df))

st.divider()

# =========================
# ACTIVE LIST
# =========================
st.subheader("🔥 Active Staff")

if not active_df.empty:
    st.dataframe(active_df[["Name","Role","Branch"]], use_container_width=True)
else:
    st.info("No active staff right now")

# =========================
# FULL VIEW SAFE
# =========================
st.subheader("📊 Staff Overview")

combined = pd.concat([active_df, inactive_df], ignore_index=True)

if not combined.empty:
    combined["Status"] = ["ACTIVE"] * len(active_df) + ["INACTIVE"] * len(inactive_df)

    st.dataframe(
        combined[["Name","Role","Status"]],
        use_container_width=True
    )
else:
    st.warning("No data available")
