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
# GOOGLE SHEETS
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
@st.cache_data(ttl=None)
def fetch_sheet():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

df = fetch_sheet()

# =========================
# CLEAN SHIFT
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
# SESSION
# =========================
if "active_df" not in st.session_state:
    st.session_state.active_df = pd.DataFrame()

if "inactive_df" not in st.session_state:
    st.session_state.inactive_df = pd.DataFrame()

# =========================
# FILTERS
# =========================
branches = sorted(df["Branch"].dropna().unique().tolist())
shift_cols = [c for c in df.columns if c not in ["Branch", "Name", "Role"]]

c1, c2, c3 = st.columns([2, 2, 1])

with c1:
    branch = st.selectbox("Branch", branches, label_visibility="collapsed")

data = df[df["Branch"] == branch].copy()

with c2:
    selected_col = st.selectbox("Shift", shift_cols, label_visibility="collapsed")

with c3:
    calculate = st.button("⚡ Calculate", use_container_width=True)

# =========================
# CALCULATION
# =========================
if calculate:
    now = datetime.now()
    now_min = now.hour * 60 + now.minute

    # ---------- UNIVERSAL ----------
    u_active, u_inactive = [], []

    for _, row in df.iterrows():
        cell = row.get(selected_col, "")
        r = row.to_dict()
        r["Shift"] = cell

        if is_active(cell, now_min):
            u_active.append(r)
        else:
            u_inactive.append(r)

    st.session_state.universal_active = pd.DataFrame(u_active)
    st.session_state.universal_inactive = pd.DataFrame(u_inactive)

    # ---------- BRANCH ----------
    b_active, b_inactive = [], []

    for _, row in data.iterrows():
        cell = row.get(selected_col, "")
        r = row.to_dict()
        r["Shift"] = cell

        if is_active(cell, now_min):
            b_active.append(r)
        else:
            b_inactive.append(r)

    st.session_state.active_df = pd.DataFrame(b_active)
    st.session_state.inactive_df = pd.DataFrame(b_inactive)

    st.toast("✅ Updated")

# =========================
# 🌍 UNIVERSAL TOP DASHBOARD
# =========================
u_active = st.session_state.get("universal_active", pd.DataFrame())
u_inactive = st.session_state.get("universal_inactive", pd.DataFrame())

st.subheader("🌍 Universal Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("🏢 Total Branches", df["Branch"].nunique())

with c2:
    st.metric("👥 Total Staff", len(df))

with c3:
    st.metric("🟢 Active (All)", len(u_active))

with c4:
    st.metric("⚪ Inactive (All)", len(u_inactive))

st.divider()

# =========================
# 🪟 BRANCH STATUS MINI WINDOW
# =========================
st.subheader("🪟 Branch Status")

branch_summary = []

for b in branches:
    temp = df[df["Branch"] == b]

    active_count = 0
    inactive_count = 0

    for _, row in temp.iterrows():
        if is_active(row[selected_col], datetime.now().hour * 60 + datetime.now().minute):
            active_count += 1
        else:
            inactive_count += 1

    branch_summary.append({
        "Branch": b,
        "Active": active_count,
        "Inactive": inactive_count
    })

summary_df = pd.DataFrame(branch_summary)

st.dataframe(summary_df, use_container_width=True, hide_index=True)

st.divider()

# =========================
# 🏢 BRANCH OVERVIEW
# =========================
b_active = st.session_state.get("active_df", pd.DataFrame())
b_inactive = st.session_state.get("inactive_df", pd.DataFrame())

st.subheader("🏢 Branch Overview")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("🏢 Branch", branch)

with c2:
    st.metric("👥 Branch Staff", len(data))

with c3:
    st.metric("🟢 Active", len(b_active))

with c4:
    st.metric("⚪ Inactive", len(b_inactive))

st.divider()

# =========================
# ACTIVE TABLE
# =========================
st.subheader("🔥 Active Staff")

if not b_active.empty:
    cols = ["Name", "Role"]
    if selected_col in b_active.columns:
        cols.append(selected_col)

    st.dataframe(b_active[cols], use_container_width=True, hide_index=True)
else:
    st.info("No active staff")

# =========================
# FULL VIEW
# =========================
st.subheader("📊 Full View")

full = pd.concat([b_active, b_inactive], ignore_index=True)

if not full.empty:
    cols = ["Name", "Role"]
    if selected_col in full.columns:
        cols.append(selected_col)

    st.dataframe(full[cols], use_container_width=True, hide_index=True)
else:
    st.info("Click Calculate")
