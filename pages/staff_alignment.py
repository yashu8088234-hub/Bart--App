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

DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

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
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

df = load_data()

# =========================
# CLEAN ENGINE (VERY IMPORTANT)
# =========================
def clean(text):
    text = str(text)
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# =========================
# SELF-HEALING SHIFT PARSER
# =========================
def extract_time_pairs(text):
    """
    Extracts ALL time patterns like:
    5 PM, 12 AM, etc.
    """
    return re.findall(r"(\d{1,2})\s*(AM|PM)", text, re.IGNORECASE)

def to_24(h, ap):
    h = int(h)
    ap = ap.upper()
    if ap == "AM":
        return 0 if h == 12 else h
    return 12 if h == 12 else h + 12

def parse_shift(cell):
    try:
        if not cell:
            return None

        text = clean(cell)

        if "OFF" in text.upper():
            return None

        # remove OT safely
        text = re.sub(r"\(.*?\)", "", text)

        times = extract_time_pairs(text)

        if len(times) < 2:
            return None

        start_h, start_ap = times[0]
        end_h, end_ap = times[1]

        start = to_24(start_h, start_ap)
        end = to_24(end_h, end_ap)

        return start, end

    except:
        return None

# =========================
# ACTIVE ENGINE (REAL INTELLIGENCE)
# =========================
def is_active(cell):
    shift = parse_shift(cell)

    if not shift:
        return False

    start, end = shift
    now = datetime.now().hour

    # normal shift
    if start < end:
        return start <= now <= end

    # overnight shift
    return now >= start or now <= end

# =========================
# UI
# =========================
branches = sorted(df["Branch"].unique()) if not df.empty else []
branch = st.selectbox("🏢 Select Branch", branches)

data = df[df["Branch"] == branch].copy()

today = DAYS[(datetime.today().weekday() + 1) % 7]

# =========================
# DEBUG (SELF HEALING INSIGHT)
# =========================
broken_rows = []

# =========================
# OPS COMPUTE
# =========================
active = []
inactive = []

for _, row in data.iterrows():
    cell = row.get(today, "")

    parsed = parse_shift(cell)
    if cell and not parsed and "OFF" not in str(cell).upper():
        broken_rows.append(cell)

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
st.subheader("🔥 Active Staff (LIVE OPS)")

if not active_df.empty:
    st.dataframe(active_df[["Name","Role"]], use_container_width=True)
else:
    st.error("No active staff detected (check debug below)")

# =========================
# FULL OPS VIEW
# =========================
st.subheader("📊 Full Ops Intelligence View")

combined = pd.concat([
    active_df.assign(Status="ACTIVE"),
    inactive_df.assign(Status="INACTIVE")
], ignore_index=True)

if not combined.empty:
    st.dataframe(combined[["Name","Role","Status"]], use_container_width=True)

# =========================
# SELF HEALING DEBUG PANEL
# =========================
with st.expander("🧠 Debug: Unparsed Shift Rows"):
    st.write(broken_rows)def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

df = load_data()

# =========================
# SUPER ROBUST SHIFT PARSER
# =========================
def parse_shift(cell):
    try:
        if not cell:
            return None

        text = str(cell)

        # normalize everything
        text = text.replace("–", "-").replace("—", "-")
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)

        if "OFF" in text.upper():
            return None

        # REMOVE OT
        text = re.sub(r"\(.*?\)", "", text)

        # 🔥 VERY FLEXIBLE MATCH (KEY FIX)
        match = re.search(
            r"(\d{1,2})\s*(AM|PM)\s*-\s*(\d{1,2})\s*(AM|PM)",
            text,
            re.IGNORECASE
        )

        if not match:
            return None

        sh, sap, eh, eap = match.groups()

        def to24(h, ap):
            h = int(h)
            ap = ap.upper()
            if ap == "AM":
                return 0 if h == 12 else h
            return 12 if h == 12 else h + 12

        start = to24(sh, sap)
        end = to24(eh, eap)

        return start, end

    except:
        return None

# =========================
# ACTIVE CHECK
# =========================
def is_active(cell):
    shift = parse_shift(cell)
    if not shift:
        return False

    start, end = shift
    now = datetime.now().hour

    # normal shift
    if start < end:
        return start <= now <= end

    # overnight shift
    return now >= start or now <= end

# =========================
# UI
# =========================
st.title("⚡ Ops Intelligence Control Center")

branches = sorted(df["Branch"].unique()) if not df.empty else []
branch = st.selectbox("Select Branch", branches)

data = df[df["Branch"] == branch]

today = DAYS[(datetime.today().weekday() + 1) % 7]

# =========================
# OPS ENGINE
# =========================
active = []
inactive = []

debug_fail = []

for _, row in data.iterrows():
    cell = row.get(today, "")

    if parse_shift(cell) is None and cell and "OFF" not in cell.upper():
        debug_fail.append(cell)

    if is_active(cell):
        active.append(row.to_dict())
    else:
        inactive.append(row.to_dict())

# =========================
# DEBUG (IMPORTANT)
# =========================
with st.expander("🔍 Debug Unparsed Shifts"):
    st.write(debug_fail)

# =========================
# KPI
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total", len(data))

with col2:
    st.metric("Active", len(active))

with col3:
    st.metric("Inactive", len(inactive))

st.divider()

# =========================
# ACTIVE
# =========================
st.subheader("🔥 Active Staff")

if active:
    st.dataframe(pd.DataFrame(active)[["Name","Role"]], use_container_width=True)
else:
    st.error("❌ STILL NO ACTIVE → check debug panel above")

# =========================
# FULL VIEW
# =========================
st.subheader("📊 Full View")

all_df = pd.DataFrame(active + inactive)
if not all_df.empty:
    st.dataframe(all_df[["Name","Role"]])
