import streamlit as st
import pandas as pd
import gspread
import re
from google.oauth2.service_account import Credentials
from datetime import datetime, date

# =========================
# APP CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Ops Control Center")
st.title("⚡ Ops Control Center")

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
# DATA LOAD (CACHE 15 MIN)
# =========================
@st.cache_data(ttl=900)
def fetch_sheet():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

df = fetch_sheet()

# =========================
# SHIFT PARSER
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
# UI CONTROLS
# =========================
branches = sorted(df["Branch"].dropna().unique().tolist())
shift_cols = [c for c in df.columns if c not in ["Branch", "Name", "Role"]]

c1, c2 = st.columns([2, 2])

with c1:
    branch = st.selectbox("🏢 Branch", branches)

with c2:
    selected_date = st.date_input("📅 Select Date", value=date.today())

# FIXED SAFE DISPLAY
st.metric("📅 Date", selected_date.strftime("%d-%m-%Y"))

selected_col = shift_cols[0]

data = df[df["Branch"] == branch].copy()

# =========================
# CURRENT TIME
# =========================
now = datetime.now()
now_min = now.hour * 60 + now.minute

# =========================
# UNIVERSAL CALCULATION
# =========================
u_active, u_inactive = [], []

for _, row in df.iterrows():
    cell = row.get(selected_col, "")
    r = row.to_dict()
    r["Date"] = selected_date

    if is_active(cell, now_min):
        u_active.append(r)
    else:
        u_inactive.append(r)

# =========================
# BRANCH CALCULATION
# =========================
b_active, b_inactive = [], []

for _, row in data.iterrows():
    cell = row.get(selected_col, "")
    r = row.to_dict()
    r["Date"] = selected_date

    if is_active(cell, now_min):
        b_active.append(r)
    else:
        b_inactive.append(r)

branch_active_df = pd.DataFrame(b_active)
branch_inactive_df = pd.DataFrame(b_inactive)

# =========================
# 🌍 UNIVERSAL OVERVIEW
# =========================
st.subheader("🌍 Universal Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("🏢 Total Branches", len(branches))

with c2:
    st.metric("👥 Total Staff", len(df))

with c3:
    st.metric("🟢 Active (All)", len(u_active))

with c4:
    st.metric("⚪ Inactive (All)", len(u_inactive))

st.divider()

# =========================
# 🪟 BRANCH STATUS
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
    st.metric("📅 Date", selected_date.strftime("%d-%m-%Y"))

with c3:
    st.metric("🟢 Active", len(branch_active_df))

with c4:
    st.metric("⚪ Inactive", len(branch_inactive_df))

st.divider()

# =========================
# 🔥 ACTIVE STAFF
# =========================
st.subheader("🔥 Active Staff")

if not branch_active_df.empty:
    st.dataframe(branch_active_df, use_container_width=True, hide_index=True)
else:
    st.info("No active staff")

# =========================
# 📊 FULL VIEW
# =========================
st.subheader("📊 Full View")

full = pd.concat([branch_active_df, branch_inactive_df], ignore_index=True)

if not full.empty:
    st.dataframe(full, use_container_width=True, hide_index=True)
else:
    st.info("No data available")
