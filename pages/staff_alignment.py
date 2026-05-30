import streamlit as st
import pandas as pd
import gspread
import re
from google.oauth2.service_account import Credentials
from datetime import datetime

# =========================
# APP
# =========================
st.set_page_config(layout="wide", page_title="Ops Intelligence System")

st.title("⚡ Ops Intelligence Control Center")

# =========================
# SHEET CONFIG
# =========================
SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
TAB_NAME = "StaffSchedule"

# =========================
# GOOGLE CLIENT
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
@st.cache_data(ttl=60)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame()

    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

df = load_data()

# =========================
# CLEAN ENGINE
# =========================
def clean(text):
    text = str(text)
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# =========================
# SHIFT PARSER (ROBUST)
# =========================
def extract_times(text):
    return re.findall(r"(\d{1,2})\s*(AM|PM)", text, re.IGNORECASE)

def to_24(h, ap):
    h = int(h)
    ap = ap.upper()
    if ap == "AM":
        return 0 if h == 12 else h
    return 12 if h == 12 else h + 12

def parse_shift(cell):
    if not cell:
        return None

    text = clean(cell)

    if "OFF" in text.upper():
        return None

    text = re.sub(r"\(.*?\)", "", text)

    times = extract_times(text)

    if len(times) < 2:
        return None

    start = to_24(*times[0])
    end = to_24(*times[1])

    return start, end

def is_active(cell):
    shift = parse_shift(cell)
    if not shift:
        return False

    start, end = shift
    now = datetime.now().hour

    if start < end:
        return start <= now <= end

    return now >= start or now <= end

# =========================
# AUTO DETECT SHIFT COLUMN (IMPORTANT FIX)
# =========================
exclude_cols = ["Branch", "Name", "Role"]
shift_columns = [c for c in df.columns if c not in exclude_cols]

if not shift_columns:
    st.error("No shift columns found in sheet")
    st.stop()

selected_col = st.selectbox("📅 Select Shift Column", shift_columns)

# =========================
# FILTER BRANCH
# =========================
branches = sorted(df["Branch"].unique()) if not df.empty else []
selected_branch = st.selectbox("🏢 Select Branch", branches)

data = df[df["Branch"] == selected_branch].copy()

# =========================
# OPS ENGINE
# =========================
active = []
inactive = []
broken = []

for _, row in data.iterrows():
    cell = row.get(selected_col, "")

    parsed = parse_shift(cell)

    if cell and not parsed and "OFF" not in str(cell).upper():
        broken.append(cell)

    if is_active(cell):
        active.append(row.to_dict())
    else:
        inactive.append(row.to_dict())

active_df = pd.DataFrame(active)
inactive_df = pd.DataFrame(inactive)

# =========================
# KPI HEADER
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("👥 Total Staff", len(data))

with col2:
    st.metric("🔴 Active Now", len(active_df))

with col3:
    st.metric("⚪ Inactive", len(inactive_df))

st.divider()

# =========================
# ACTIVE VIEW
# =========================
st.subheader("🔥 Active Staff (LIVE)")

if not active_df.empty:
    st.dataframe(active_df[["Name", "Role"]], use_container_width=True)
else:
    st.warning("No active staff right now")

# =========================
# FULL OPS VIEW
# =========================
st.subheader("📊 Full Ops View")

final_df = pd.concat([
    active_df.assign(Status="ACTIVE"),
    inactive_df.assign(Status="INACTIVE")
], ignore_index=True)

if not final_df.empty:
    st.dataframe(final_df[["Name", "Role", "Status"]], use_container_width=True)

# =========================
# DEBUG PANEL
# =========================
with st.expander("🧠 Debug (Unparsed Rows)"):
    st.write(broken)
