import streamlit as st
import pandas as pd
import gspread
import re
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

# =========================
# PAGE
# =========================
st.set_page_config(layout="wide", page_title="Ops Intelligence System")

# =========================
# AUTH
# =========================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Session expired")
    st.stop()

# =========================
# CONFIG
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
    df = pd.DataFrame(raw[1:], columns=raw[0]).fillna("")
    return df

df = load_data()

# =========================
# SHIFT PARSER (CORE ENGINE)
# =========================
def parse_shift(cell):
    match = re.search(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", str(cell))
    if not match:
        return None

    start = datetime.strptime(match.group(1), "%H:%M").time()
    end = datetime.strptime(match.group(2), "%H:%M").time()

    return start, end

def status(cell, now):
    shift = parse_shift(cell)
    if not shift:
        return "OFF"

    start, end = shift

    if start <= now <= end:
        return "ACTIVE"
    elif now < start:
        return "UPCOMING"
    else:
        return "DONE"

# =========================
# TIME ENGINE
# =========================
now = datetime.now().time()

# =========================
# UI FILTER
# =========================
branches = sorted(df["Branch"].unique())
branch = st.selectbox("🏢 Select Branch", branches)

data = df[df["Branch"] == branch].copy()

today = DAYS[(datetime.today().weekday() + 1) % 7]

# =========================
# INTELLIGENCE COMPUTE
# =========================
active = []
upcoming = []
late = []
off = []

for _, r in data.iterrows():

    cell = r.get(today, "")
    s = status(cell, now)

    row = r.to_dict()

    if s == "ACTIVE":
        active.append(row)
    elif s == "UPCOMING":
        upcoming.append(row)
    elif s == "DONE":
        late.append(row)
    else:
        off.append(row)

active_df = pd.DataFrame.from_records(active)
upcoming_df = pd.DataFrame.from_records(upcoming)
late_df = pd.DataFrame.from_records(late)

# =========================
# OPS KPI LAYER (CONTROL ROOM TOP BAR)
# =========================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("👥 Total Staff", len(data))

with col2:
    st.metric("🔴 Active Now", len(active_df))

with col3:
    st.metric("⏳ Upcoming", len(upcoming_df))

with col4:
    st.metric("⚠️ Late/Done", len(late_df))

st.divider()

# =========================
# ACTIVE OPS VIEW
# =========================
st.subheader("🔥 Live Active Staff")

if not active_df.empty:
    st.dataframe(active_df[["Name","Role","Branch"]], use_container_width=True)
else:
    st.info("No active staff right now")

# =========================
# UPCOMING VIEW (INTELLIGENCE)
# =========================
st.subheader("⏳ Next Staff (Upcoming Shifts)")

if not upcoming_df.empty:
    st.dataframe(upcoming_df[["Name","Role","Branch"]], use_container_width=True)
else:
    st.info("No upcoming shifts")

# =========================
# BRANCH HEALTH SCORE (SMART KPI)
# =========================
total = len(data)
score = 0

if total > 0:
    score = int((len(active_df) / total) * 100)

st.subheader("📊 Branch Health Score")

st.progress(score / 100)
st.write(f"Operational Efficiency: {score}%")

# =========================
# FULL INTELLIGENCE VIEW
# =========================
st.subheader("🧠 Full Ops Intelligence View")

full = pd.concat([
    pd.DataFrame.from_records(active).assign(Status="ACTIVE"),
    pd.DataFrame.from_records(upcoming).assign(Status="UPCOMING"),
    pd.DataFrame.from_records(late).assign(Status="DONE"),
    pd.DataFrame.from_records(off).assign(Status="OFF")
], ignore_index=True)

if not full.empty:
    st.dataframe(full[["Name","Role","Status"]], use_container_width=True)
