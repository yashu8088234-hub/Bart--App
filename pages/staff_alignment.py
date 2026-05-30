import streamlit as st
import pandas as pd
import gspread
import re
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(layout="wide", page_title="Ops Debug System")

st.title("⚡ OPS DEBUG CONTROL CENTER")

# =========================
# SHEET
# =========================
SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
TAB_NAME = "StaffSchedule"

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

@st.cache_data(ttl=30)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

df = load_data()

# =========================
# CLEAN
# =========================
def clean(text):
    text = str(text)
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_times(text):
    return re.findall(r"(\d{1,2})\s*(AM|PM)", text, re.IGNORECASE)

def to_minutes(h, ap):
    h = int(h)
    ap = ap.upper()
    if ap == "AM":
        h = 0 if h == 12 else h
    else:
        h = 12 if h == 12 else h + 12
    return h * 60

# =========================
# PARSER (STRICT + TRACEABLE)
# =========================
def parse_shift_debug(cell):
    raw = str(cell)

    text = clean(raw)
    text = re.sub(r"\(.*?\)", "", text)

    times = extract_times(text)

    if len(times) < 2:
        return None, f"FAILED PARSE → {raw}"

    start = to_minutes(*times[0])
    end = to_minutes(*times[1])

    return (start, end), f"OK → {times}"

# =========================
# ACTIVE ENGINE (CORRECT)
# =========================
def is_active(cell):
    shift, debug = parse_shift_debug(cell)

    if not shift:
        return False, debug

    start, end = shift

    now = datetime.now()
    now_m = now.hour * 60 + now.minute

    if start < end:
        return (start <= now_m < end), debug

    return (now_m >= start or now_m < end), debug

# =========================
# UI
# =========================
branches = sorted(df["Branch"].unique()) if not df.empty else []
branch = st.selectbox("Select Branch", branches)

data = df[df["Branch"] == branch].copy()

shift_columns = [c for c in df.columns if c not in ["Branch","Name","Role"]]
selected_col = st.selectbox("Select Shift Column", shift_columns)

# =========================
# ENGINE
# =========================
active = []
inactive = []
debug_log = []

for _, row in data.iterrows():
    cell = row.get(selected_col, "")

    status, debug = is_active(cell)

    row_dict = row.to_dict()
    row_dict["Shift"] = cell
    row_dict["DEBUG"] = debug

    debug_log.append(debug)

    if status:
        active.append(row_dict)
    else:
        inactive.append(row_dict)

active_df = pd.DataFrame(active)
inactive_df = pd.DataFrame(inactive)

# =========================
# KPI
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total", len(data))

with col2:
    st.metric("Active", len(active_df))

with col3:
    st.metric("Inactive", len(inactive_df))

st.divider()

# =========================
# ACTIVE VIEW
# =========================
st.subheader("🔥 Active Staff")

if not active_df.empty:
    st.dataframe(active_df[["Name","Role","Shift","DEBUG"]], use_container_width=True)
else:
    st.warning("No active staff")

# =========================
# FULL VIEW
# =========================
st.subheader("📊 Full Ops View")

full = pd.concat([active_df, inactive_df], ignore_index=True)

if not full.empty:
    st.dataframe(full[["Name","Role","Shift","DEBUG"]], use_container_width=True)

# =========================
# RAW DEBUG PANEL
# =========================
with st.expander("🧠 RAW DEBUG LOG"):
    st.write(debug_log)
