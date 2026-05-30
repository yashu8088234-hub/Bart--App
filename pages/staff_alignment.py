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
# SHEETS
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
# LOAD DATA
# =========================
@st.cache_data(ttl=300)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()

    df = pd.DataFrame(raw[1:], columns=raw[0])
    return df

df = load_data()

# =========================
# SHIFT PARSER (IMPORTANT)
# =========================
def parse_time_range(cell):
    """
    Extracts 09:00-18:00
    """
    match = re.search(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", str(cell))
    if not match:
        return None

    start = datetime.strptime(match.group(1), "%H:%M").time()
    end = datetime.strptime(match.group(2), "%H:%M").time()
    return start, end

def is_active(cell, now_time):
    shift = parse_time_range(cell)
    if not shift:
        return False
    start, end = shift
    return start <= now_time <= end

# =========================
# TIME NOW
# =========================
now = datetime.now().time()

# =========================
# FILTER
# =========================
branches = sorted(df["Branch"].dropna().unique())
selected_branch = st.selectbox("🏢 Select Branch", branches)

data = df[df["Branch"] == selected_branch].copy()

# =========================
# ACTIVE CALC
# =========================
active_staff = []
inactive_staff = []

for _, row in data.iterrows():
    today = DAYS[(datetime.today().weekday() + 1) % 7]

    cell = row.get(today, "")

    if is_active(cell, now):
        active_staff.append(row)
    else:
        inactive_staff.append(row)

active_df = pd.DataFrame(active_staff)
inactive_df = pd.DataFrame(inactive_staff)

# =========================
# TOP OPS BAR (IMPORTANT)
# =========================
col1, col2, col3 = st.columns([2,2,2])

with col1:
    st.metric("👥 Total Workers", len(data))

with col2:
    st.metric("🔴 Active Now", len(active_df))

with col3:
    st.metric("⚡ Inactive", len(inactive_df))

st.divider()

# =========================
# ACTIVE LIST (HIGHLIGHTED)
# =========================
st.subheader("🔥 Active Staff (Working Now)")

if not active_df.empty:
    st.dataframe(
        active_df[["Name","Role","Branch"]],
        use_container_width=True,
        height=250
    )
else:
    st.info("No staff currently active")

# =========================
# SORTED MASTER VIEW (ACTIVE FIRST)
# =========================
st.subheader("📊 Branch Staff Overview (Active Priority)")

combined = pd.concat([active_df, inactive_df])

if not combined.empty:

    combined["Status"] = ["ACTIVE"] * len(active_df) + ["INACTIVE"] * len(inactive_df)

    st.dataframe(
        combined[["Name","Role","Status"]],
        use_container_width=True,
        height=500
    )
