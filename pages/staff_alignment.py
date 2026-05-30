import streamlit as st
import pandas as pd
import gspread
import re
from google.oauth2.service_account import Credentials
from datetime import datetime

# =========================
# APP CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Ops Intelligence System")

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
# LOAD DATA SAFE
# =========================
@st.cache_data(ttl=300)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(raw[1:], columns=raw[0]).fillna("")
    return df

df = load_data()

# =========================
# CLEANING ENGINE (IMPORTANT)
# =========================
def clean_text(text):
    text = str(text)

    # normalize weird dashes
    text = text.replace("–", "-").replace("—", "-")

    # remove hidden unicode spaces
    text = text.replace("\xa0", " ")

    # collapse spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()

# =========================
# SHIFT PARSER (ROBUST CORE)
# =========================
def parse_shift(cell):
    try:
        if not cell:
            return None

        text = clean_text(cell)

        if text.upper() == "OFF":
            return None

        # remove OT safely
        text = re.sub(r"\(.*?\)", "", text).strip()

        # extract shift
        match = re.search(
            r"(\d{1,2})\s*(AM|PM)\s*-\s*(\d{1,2})\s*(AM|PM)",
            text,
            re.IGNORECASE
        )

        if not match:
            return None

        sh, sap, eh, eap = match.groups()
        sh, eh = int(sh), int(eh)

        def to_24(h, ap):
            ap = ap.upper()
            if ap == "AM":
                return 0 if h == 12 else h
            else:
                return 12 if h == 12 else h + 12

        start = to_24(sh, sap)
        end = to_24(eh, eap)

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

    # NORMAL SHIFT
    if start < end:
        return start <= now <= end

    # OVERNIGHT SHIFT (5 PM - 5 AM)
    if start > end:
        return now >= start or now <= end

    return False

# =========================
# UI
# =========================
branches = sorted(df["Branch"].unique()) if not df.empty else []
selected_branch = st.selectbox("🏢 Select Branch", branches)

data = df[df["Branch"] == selected_branch].copy()

today = DAYS[(datetime.today().weekday() + 1) % 7]

# =========================
# OPS COMPUTE
# =========================
active = []
inactive = []

for _, row in data.iterrows():
    row_dict = row.to_dict()

    cell = row_dict.get(today, "")

    if is_active(cell):
        active.append(row_dict)
    else:
        inactive.append(row_dict)

active_df = pd.DataFrame.from_records(active)
inactive_df = pd.DataFrame.from_records(inactive)

# =========================
# CONTROL CENTER HEADER
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
# ACTIVE STAFF
# =========================
st.subheader("🔥 Active Staff (Live Ops)")

if not active_df.empty:
    st.dataframe(
        active_df[["Name", "Role", "Branch"]],
        use_container_width=True
    )
else:
    st.info("No active staff currently working")

# =========================
# FULL OPS VIEW
# =========================
st.subheader("📊 Ops Intelligence View")

combined = pd.concat([
    pd.DataFrame.from_records(active).assign(Status="ACTIVE"),
    pd.DataFrame.from_records(inactive).assign(Status="INACTIVE")
], ignore_index=True)

if not combined.empty:
    st.dataframe(
        combined[["Name", "Role", "Status"]],
        use_container_width=True
    )
