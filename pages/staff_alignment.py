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

st.title("⚡ Ops Intelligence Control Center (Timeline AI)")

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

# =========================
# ⏱ TIMELINE ENGINE (NEW)
# =========================
def shift_timeline(cell):
    shift = parse_shift(cell)
    if not shift:
        return None

    start, end = shift
    now = datetime.now()

    now_m = now.hour * 60 + now.minute
    start_m = start * 60
    end_m = end * 60

    # NORMAL SHIFT
    if start_m < end_m:
        if now_m < start_m:
            return "UPCOMING", start_m - now_m
        elif now_m > end_m:
            return "ENDED", now_m - end_m
        else:
            return "ACTIVE", end_m - now_m

    # OVERNIGHT SHIFT
    if now_m >= start_m or now_m < end_m:
        # ACTIVE
        if now_m >= start_m:
            return "ACTIVE", (24*60 - now_m) + end_m
        else:
            return "ACTIVE", end_m - now_m
    else:
        return "ENDED", now_m - end_m

# =========================
# STATUS CHECK
# =========================
def is_active(cell):
    result = shift_timeline(cell)
    return result and result[0] == "ACTIVE"

# =========================
# UI
# =========================
branches = sorted(df["Branch"].unique()) if not df.empty else []
branch = st.selectbox("🏢 Select Branch", branches)

data = df[df["Branch"] == branch].copy()

shift_columns = [c for c in df.columns if c not in ["Branch","Name","Role"]]
selected_col = st.selectbox("📅 Select Shift Column", shift_columns)

# =========================
# OPS ENGINE
# =========================
active = []
inactive = []

for _, row in data.iterrows():
    cell = row.get(selected_col, "")

    timeline = shift_timeline(cell)

    row_dict = row.to_dict()
    row_dict["Shift"] = cell

    if timeline:
        status, minutes_left = timeline
        row_dict["Timeline"] = status
        row_dict["Minutes Left"] = minutes_left
    else:
        row_dict["Timeline"] = "NO SHIFT"
        row_dict["Minutes Left"] = None

    if is_active(cell):
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
    st.metric("👥 Total", len(data))

with col2:
    st.metric("🟢 Active", len(active_df))

with col3:
    st.metric("⚪ Inactive", len(inactive_df))

st.divider()

# =========================
# ACTIVE VIEW
# =========================
st.subheader("🔥 Active Staff (Live Timeline)")

if not active_df.empty:
    st.dataframe(
        active_df[["Name","Role","Shift","Timeline","Minutes Left"]],
        use_container_width=True
    )
else:
    st.warning("No active staff")

# =========================
# FULL OPS VIEW
# =========================
st.subheader("📊 Full Ops Intelligence View")

final_df = pd.concat([active_df, inactive_df], ignore_index=True)

if not final_df.empty:
    st.dataframe(
        final_df[["Name","Role","Shift","Timeline","Minutes Left"]],
        use_container_width=True
    )
