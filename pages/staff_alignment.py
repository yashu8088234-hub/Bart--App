import streamlit as st
import pandas as pd
import gspread
import re
from google.oauth2.service_account import Credentials
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Ops Control Center")
st.title("⚡ Ops Control Center")

SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
TAB_NAME = "StaffSchedule"

# =========================
# GOOGLE CLIENT (ONLY ONCE)
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
# DATA CACHE (15 MIN CACHE)
# =========================
@st.cache_data(ttl=900)  # 15 minutes
def fetch_sheet():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

# =========================
# MANUAL REFRESH CONTROL
# =========================
colA, colB = st.columns([1, 4])

with colA:
    refresh = st.button("🔄 Refresh Data")

if refresh:
    st.cache_data.clear()   # clear only sheet cache
    st.toast("🔄 Data Refreshed from Google Sheets")

df = fetch_sheet()

# =========================
# SHIFT LOGIC
# =========================
def clean(text):
    text = str(text)
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_shift(cell):
    if not cell:
        return None

    text = clean(cell)
    matches = re.findall(r"\d{1,2}\s*(?:AM|PM)", text, re.I)

    if len(matches) < 2:
        return None

    def convert(t):
        t = t.upper().replace(" ", "")
        h = int(re.findall(r"\d{1,2}", t)[0])

        if "AM" in t:
            if h == 12:
                h = 0
        else:
            if h != 12:
                h += 12

        return h * 60

    return convert(matches[0]), convert(matches[1])

def is_active(cell, now_min):
    shift = get_shift(cell)
    if not shift:
        return False

    start, end = shift
    return (start <= now_min < end) if start < end else (now_min >= start or now_min < end)

# =========================
# UI FILTERS (NO API CALLS HERE)
# =========================
branches = sorted(df["Branch"].dropna().unique().tolist())
shift_cols = [c for c in df.columns if c not in ["Branch", "Name", "Role"]]

c1, c2 = st.columns([2, 2])

with c1:
    branch = st.selectbox("🏢 Branch", branches)

with c2:
    selected_col = st.selectbox("📅 Shift Column", shift_cols)

data = df[df["Branch"] == branch].copy()

# =========================
# CALCULATION (LOCAL ONLY)
# =========================
now = datetime.now()
now_min = now.hour * 60 + now.minute

u_active, u_inactive = [], []
b_active, b_inactive = [], []

for _, row in df.iterrows():
    cell = row.get(selected_col, "")
    r = row.to_dict()

    if is_active(cell, now_min):
        u_active.append(r)
    else:
        u_inactive.append(r)

for _, row in data.iterrows():
    cell = row.get(selected_col, "")
    r = row.to_dict()

    if is_active(cell, now_min):
        b_active.append(r)
    else:
        b_inactive.append(r)

# =========================
# STORE RESULTS (NO API CALLS AFTER THIS)
# =========================
st.session_state.universal_active = pd.DataFrame(u_active)
st.session_state.universal_inactive = pd.DataFrame(u_inactive)

st.session_state.active_df = pd.DataFrame(b_active)
st.session_state.inactive_df = pd.DataFrame(b_inactive)

# =========================
# 🌍 UNIVERSAL DASHBOARD
# =========================
st.subheader("🌍 Universal Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("🏢 Total Branches", len(branches))

with c2:
    st.metric("👥 Total Staff", len(df))

with c3:
    st.metric("🟢 Active (All)", len(st.session_state.universal_active))

with c4:
    st.metric("⚪ Inactive (All)", len(st.session_state.universal_inactive))

st.divider()

# =========================
# 🪟 BRANCH SUMMARY
# =========================
st.subheader("🪟 Branch Status")

summary = []

for b in branches:
    temp = df[df["Branch"] == b]

    a = 0
    i = 0

    for _, row in temp.iterrows():
        if is_active(row[selected_col], now_min):
            a += 1
        else:
            i += 1

    summary.append({
        "Branch": b,
        "Active": a,
        "Inactive": i
    })

st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

st.divider()

# =========================
# 🏢 BRANCH OVERVIEW
# =========================
st.subheader("🏢 Branch Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("🏢 Branch", branch)

with c2:
    st.metric("👥 Branch Staff", len(data))

with c3:
    st.metric("🟢 Active", len(st.session_state.active_df))

with c4:
    st.metric("⚪ Inactive", len(st.session_state.inactive_df))

st.divider()

# =========================
# TABLES
# =========================
st.subheader("🔥 Active Staff")

if not st.session_state.active_df.empty:
    st.dataframe(st.session_state.active_df, use_container_width=True, hide_index=True)
else:
    st.info("No active staff")

st.subheader("📊 Full View")

full = pd.concat([st.session_state.active_df, st.session_state.inactive_df], ignore_index=True)

if not full.empty:
    st.dataframe(full, use_container_width=True, hide_index=True)
