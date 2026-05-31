import streamlit as st
import pandas as pd
import gspread
import re
from google.oauth2.service_account import Credentials
from datetime import datetime

# =========================
# APP CONFIG
# =========================
st.set_page_config(
    layout="wide",
    page_title="Ops Control Center"
)

st.title("Staff Schedule Center")

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

    if not raw:
        return pd.DataFrame()

    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

df = fetch_sheet()

if df.empty:
    st.error("No data found in sheet.")
    st.stop()

# =========================
# CLEAN SHIFT TEXT
# =========================
def clean(text):
    text = str(text)
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# =========================
# SHIFT PARSER
# =========================
def get_shift(cell):
    if not cell:
        return None

    text = clean(cell)

    matches = re.findall(
        r"\d{1,2}\s*(?:AM|PM)",
        text,
        re.I
    )

    if len(matches) < 2:
        return None

    def convert(t):
        t = t.upper().replace(" ", "")

        hour = int(re.findall(r"\d{1,2}", t)[0])

        if "AM" in t:
            if hour == 12:
                hour = 0
        else:
            if hour != 12:
                hour += 12

        return hour * 60

    start = convert(matches[0])
    end = convert(matches[1])

    return start, end

# =========================
# ACTIVE CHECK
# =========================
def is_active(cell, now_min):
    shift = get_shift(cell)

    if not shift:
        return False

    start, end = shift

    # Normal shift
    if start < end:
        return start <= now_min < end

    # Overnight shift
    return now_min >= start or now_min < end

# =========================
# SESSION DEFAULTS
# =========================
if "active_df" not in st.session_state:
    st.session_state.active_df = pd.DataFrame()

if "inactive_df" not in st.session_state:
    st.session_state.inactive_df = pd.DataFrame()

# =========================
# UNIVERSAL COUNTS
# =========================
total_staff = len(df)
total_branches = df["Branch"].nunique()

# =========================
# OVERVIEW
# =========================
total_branches = df["Branch"].nunique()

branch_total_staff = len(data)
branch_active_count = len(st.session_state.active_df)
branch_inactive_count = len(st.session_state.inactive_df)

st.subheader("📈 Overview")

m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("🏢 Branch", branch)

with m2:
    st.metric("🌍 Total Branches", total_branches)

with m3:
    st.metric("👥 Branch Staff", branch_total_staff)

with m4:
    st.metric("🟢 Active", branch_active_count)

with m5:
    st.metric("⚪ Inactive", branch_inactive_count)

st.divider()
# =========================
# FILTER BAR
# =========================
branches = sorted(
    [b for b in df["Branch"].dropna().unique().tolist() if str(b).strip()]
)

c1, c2, c3 = st.columns([2, 2, 1])

with c1:
    branch = st.selectbox(
        "Branch",
        branches,
        label_visibility="collapsed",
        key="branch_selector"
    )

data = df[df["Branch"] == branch].copy()

shift_cols = [
    c for c in df.columns
    if c not in ["Branch", "Name", "Role"]
]

with c2:
    selected_col = st.selectbox(
        "Shift Column",
        shift_cols,
        label_visibility="collapsed",
        key="shift_selector"
    )

with c3:
    calculate = st.button(
        "⚡ Calculate",
        use_container_width=True
    )

# =========================
# CALCULATE
# =========================
if calculate:

    now = datetime.now()
    now_min = (now.hour * 60) + now.minute

    active = []
    inactive = []

    for _, row in data.iterrows():

        cell = row.get(selected_col, "")

        row_dict = row.to_dict()
        row_dict["Shift"] = cell

        if is_active(cell, now_min):
            active.append(row_dict)
        else:
            inactive.append(row_dict)

    st.session_state.active_df = pd.DataFrame(active)
    st.session_state.inactive_df = pd.DataFrame(inactive)

    st.toast("✅ Updated Successfully")
    st.toast(f"🕒 {now.strftime('%H:%M:%S')}")

# =========================
# CURRENT RESULTS
# =========================
active_df = st.session_state.active_df
inactive_df = st.session_state.inactive_df

# =========================
# BRANCH SUMMARY
# =========================
branch_total = len(data)

bc1, bc2, bc3 = st.columns(3)

with bc1:
    st.metric("👥 Branch Staff", branch_total)

with bc2:
    st.metric("🟢 Active", len(active_df))

with bc3:
    st.metric("⚪ Inactive", len(inactive_df))

st.divider()

# =========================
# ACTIVE STAFF
# =========================
st.subheader("🔥 Active Staff")

if not active_df.empty:

    cols = ["Name", "Role"]

    if selected_col in active_df.columns:
        cols.append(selected_col)

    st.dataframe(
        active_df[cols],
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("No active staff found.")

# =========================
# FULL VIEW
# =========================
st.subheader("📊 Full View")

full_df = pd.concat(
    [active_df, inactive_df],
    ignore_index=True
)

if not full_df.empty:

    cols = ["Name", "Role"]

    if selected_col in full_df.columns:
        cols.append(selected_col)

    st.dataframe(
        full_df[cols],
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("Click Calculate to load staff status.")
