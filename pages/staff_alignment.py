import streamlit as st
import pandas as pd
import gspread
import re
from google.oauth2.service_account import Credentials
from datetime import datetime

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
# LOAD DATA
# =========================
@st.cache_data(ttl=None)
def fetch_sheet():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

df = fetch_sheet()

# =========================
# CLEAN + SHIFT PARSER
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

    if start < end:
        return start <= now_min < end

    return now_min >= start or now_min < end

# =========================
# SESSION STATE
# =========================
if "active_df" not in st.session_state:
    st.session_state.active_df = pd.DataFrame()

if "inactive_df" not in st.session_state:
    st.session_state.inactive_df = pd.DataFrame()

if "universal_active_df" not in st.session_state:
    st.session_state.universal_active_df = pd.DataFrame()

if "universal_inactive_df" not in st.session_state:
    st.session_state.universal_inactive_df = pd.DataFrame()

# =========================
# FILTER UI (ROW)
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
# CALCULATION (FIXED)
# =========================
if calculate:
    now = datetime.now()
    now_min = now.hour * 60 + now.minute

    # =========================
    # UNIVERSAL (ALL DATA)
    # =========================
    u_active, u_inactive = [], []

    for _, row in df.iterrows():
        cell = row.get(selected_col, "")

        row_dict = row.to_dict()
        row_dict["Shift"] = cell

        if is_active(cell, now_min):
            u_active.append(row_dict)
        else:
            u_inactive.append(row_dict)

    st.session_state.universal_active_df = pd.DataFrame(u_active)
    st.session_state.universal_inactive_df = pd.DataFrame(u_inactive)

    # =========================
    # BRANCH (SELECTED ONLY)
    # =========================
    b_active, b_inactive = [], []

    for _, row in data.iterrows():
        cell = row.get(selected_col, "")

        row_dict = row.to_dict()
        row_dict["Shift"] = cell

        if is_active(cell, now_min):
            b_active.append(row_dict)
        else:
            b_inactive.append(row_dict)

    st.session_state.active_df = pd.DataFrame(b_active)
    st.session_state.inactive_df = pd.DataFrame(b_inactive)

    st.toast("✅ Updated Successfully")
    st.toast(f"🕒 {now.strftime('%H:%M:%S')}")

# =========================
# UNIVERSAL OVERVIEW
# =========================
u_active_df = st.session_state.universal_active_df
u_inactive_df = st.session_state.universal_inactive_df

st.subheader("🌍 Universal Overview")

u1, u2, u3, u4 = st.columns(4)

with u1:
    st.metric("🏢 Total Branches", df["Branch"].nunique())

with u2:
    st.metric("👥 Total Staff", len(df))

with u3:
    st.metric("🟢 Active (All)", len(u_active_df))

with u4:
    st.metric("⚪ Inactive (All)", len(u_inactive_df))

st.divider()

# =========================
# BRANCH OVERVIEW
# =========================
b_active_df = st.session_state.active_df
b_inactive_df = st.session_state.inactive_df

st.subheader("🏢 Branch Overview")

b1, b2, b3, b4 = st.columns(4)

with b1:
    st.metric("🏢 Branch", branch)

with b2:
    st.metric("👥 Branch Staff", len(data))

with b3:
    st.metric("🟢 Active", len(b_active_df))

with b4:
    st.metric("⚪ Inactive", len(b_inactive_df))

st.divider()

# =========================
# ACTIVE STAFF
# =========================
st.subheader("🔥 Active Staff")

if not b_active_df.empty:
    cols = ["Name", "Role"]
    if selected_col in b_active_df.columns:
        cols.append(selected_col)

    st.dataframe(b_active_df[cols], use_container_width=True, hide_index=True)
else:
    st.info("No active staff")

# =========================
# FULL VIEW
# =========================
st.subheader("📊 Full View")

full_df = pd.concat([b_active_df, b_inactive_df], ignore_index=True)

if not full_df.empty:
    cols = ["Name", "Role"]
    if selected_col in full_df.columns:
        cols.append(selected_col)

    st.dataframe(full_df[cols], use_container_width=True, hide_index=True)
else:
    st.info("Click Calculate to load data")
