import streamlit as st
import pandas as pd
import gspread
import re
from google.oauth2.service_account import Credentials
from datetime import datetime

# =========================
# APP
# =========================
st.set_page_config(layout="wide", page_title="Ops System")
st.title("⚡ Ops Control Center")

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

# =========================
# LOAD
# =========================
@st.cache_data(ttl=60)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

df = load_data()

# =========================
# PARSE SHIFT
# =========================
def clean(t):
    t = str(t).replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", t).strip()

def extract(t):
    return re.findall(r"(\d{1,2})\s*(AM|PM)", t, re.I)

def to_minutes(h, ap):
    h = int(h)
    ap = ap.upper()

    if ap == "AM":
        h = 0 if h == 12 else h
    else:
        h = 12 if h == 12 else h + 12

    return h * 60

def get_shift(cell):
    if not cell or "OFF" in cell.upper():
        return None

    cell = clean(cell)
    cell = re.sub(r"\(.*?\)", "", cell)

    times = extract(cell)
    if len(times) < 2:
        return None

    start = to_minutes(*times[0])
    end = to_minutes(*times[1])

    return start, end

# =========================
# 🔥 SIMPLE CORRECT LOGIC
# =========================
def is_active(cell):
    shift = get_shift(cell)
    if not shift:
        return False

    start, end = shift

    now = datetime.now()
    now_m = now.hour * 60 + now.minute

    # NORMAL SHIFT
    if start < end:
        return start <= now_m < end

    # OVERNIGHT SHIFT
    return now_m >= start or now_m < end

# =========================
# UI
# =========================
branches = sorted(df["Branch"].unique()) if not df.empty else []
branch = st.selectbox("Branch", branches)

data = df[df["Branch"] == branch]

shift_cols = [c for c in df.columns if c not in ["Branch","Name","Role"]]
col = st.selectbox("Shift Column", shift_cols)

# =========================
# SPLIT
# =========================
active, inactive = [], []

for _, row in data.iterrows():
    cell = row[col]

    if is_active(cell):
        active.append(row)
    else:
        inactive.append(row)

active_df = pd.DataFrame(active)
inactive_df = pd.DataFrame(inactive)

# =========================
# KPI
# =========================
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Total", len(data))
with c2:
    st.metric("Active", len(active_df))
with c3:
    st.metric("Inactive", len(inactive_df))

st.divider()

# =========================
# ACTIVE VIEW
# =========================
st.subheader("🔥 Active Staff")

if not active_df.empty:
    st.dataframe(active_df[["Name","Role",col]])
else:
    st.warning("No active staff")

# =========================
# FULL VIEW
# =========================
st.subheader("📊 Full View")

st.dataframe(pd.concat([active_df, inactive_df], ignore_index=True)[["Name","Role",col]])
