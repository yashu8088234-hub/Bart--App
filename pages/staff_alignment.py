import streamlit as st
import pandas as pd
import gspread
import re
from google.oauth2.service_account import Credentials
from datetime import datetime, time

# =========================
# APP CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Ops Intelligence System")
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
# LOAD SHEET (cached permanently)
# =========================
@st.cache_data(ttl=None)
def fetch_sheet():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

df = fetch_sheet()

# =========================
# CLEAN TEXT
# =========================
def clean(text):
    text = str(text)
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# =========================
# FLEXIBLE TIME PARSER
# (handles messy formats safely)
# =========================
def parse_time(t):
    try:
        return datetime.strptime(t.strip().upper(), "%I %p").time()
    except:
        return None

def extract_shift_times(text):
    text = clean(text)
    text = re.sub(r"\(.*?\)", "", text)

    matches = re.findall(r"\d{1,2}\s*(?:AM|PM)", text, re.IGNORECASE)

    if len(matches) < 2:
        return None

    start = parse_time(matches[0])
    end = parse_time(matches[1])

    if not start or not end:
        return None

    return start, end

# =========================
# ACTIVE CHECK
# =========================
def is_active(cell, now_t):
    shift = extract_shift_times(cell)
    if not shift:
        return False

    start, end = shift

    # normal shift
    if start < end:
        return start <= now_t < end

    # overnight shift
    return now_t >= start or now_t < end

# =========================
# SESSION STATE
# =========================
if "active_df" not in st.session_state:
    st.session_state.active_df = pd.DataFrame()

if "inactive_df" not in st.session_state:
    st.session_state.inactive_df = pd.DataFrame()

if "last_calc" not in st.session_state:
    st.session_state.last_calc = None

# =========================
# BRANCH SELECT (AUTO REFRESH TRIGGER)
# =========================
branches = sorted(df["Branch"].dropna().unique().tolist())

branch = st.selectbox(
    "🏢 Select Branch",
    branches,
    key="branch_select"
)

# 🔥 AUTO RESET WHEN BRANCH CHANGES
if "last_branch" not in st.session_state:
    st.session_state.last_branch = branch

if st.session_state.last_branch != branch:
    st.session_state.active_df = pd.DataFrame()
    st.session_state.inactive_df = pd.DataFrame()
    st.session_state.last_calc = None
    st.session_state.last_branch = branch
    st.rerun()

data = df[df["Branch"] == branch].copy()

shift_cols = [c for c in df.columns if c not in ["Branch", "Name", "Role"]]
selected_col = st.selectbox("📅 Select Shift Column", shift_cols)

# =========================
# BUTTON: CALCULATE
# =========================
col1, col2 = st.columns(2)

with col1:
    if st.button("⚡ Calculate Now"):
        now_t = datetime.now().time()

        active = []
        inactive = []

        for _, row in data.iterrows():
            cell = row.get(selected_col, "")

            row_dict = row.to_dict()
            row_dict["Shift"] = cell

            if is_active(cell, now_t):
                active.append(row_dict)
            else:
                inactive.append(row_dict)

        st.session_state.active_df = pd.DataFrame(active)
        st.session_state.inactive_df = pd.DataFrame(inactive)
        st.session_state.last_calc = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        st.success("Updated!")

with col2:
    st.info(f"🕒 Last: {st.session_state.last_calc}")

# =========================
# OUTPUT
# =========================
active_df = st.session_state.active_df
inactive_df = st.session_state.inactive_df

st.divider()

st.metric("🟢 Active", len(active_df))
st.metric("⚪ Inactive", len(inactive_df))

st.subheader("🔥 Active Staff")
if not active_df.empty:
    st.dataframe(active_df[["Name", "Role", selected_col]], use_container_width=True)
else:
    st.warning("No active staff")

st.subheader("📊 Full View")

full_df = pd.concat([active_df, inactive_df], ignore_index=True)

if not full_df.empty:
    st.dataframe(full_df[["Name", "Role", selected_col]], use_container_width=True)
