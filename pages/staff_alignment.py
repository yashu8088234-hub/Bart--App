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
st.title("⚡ Ops Control Center")

# =========================
# SHEET CONFIG
# =========================
SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
TAB_NAME = "StaffSchedule"

# =========================
# GOOGLE CLIENT (NO REFRESH CACHE)
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
# LOAD DATA (ONLY WHEN BUTTON PRESSED)
# =========================
def fetch_sheet():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

# =========================
# CLEAN + PARSE SHIFT
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

    start = to_minutes(*times[0])
    end = to_minutes(*times[1])

    return start, end

# =========================
# ACTIVE CHECK (USES FIXED TIME)
# =========================
def is_active(cell, now_m):
    shift = parse_shift(cell)
    if not shift:
        return False

    start, end = shift

    # NORMAL SHIFT
    if start < end:
        return start <= now_m < end

    # OVERNIGHT SHIFT
    return now_m >= start or now_m < end

# =========================
# SESSION STATE INIT
# =========================
if "df" not in st.session_state:
    st.session_state.df = None

if "last_calc_time" not in st.session_state:
    st.session_state.last_calc_time = None

if "active_df" not in st.session_state:
    st.session_state.active_df = pd.DataFrame()

if "inactive_df" not in st.session_state:
    st.session_state.inactive_df = pd.DataFrame()

# =========================
# BUTTON 1: LOAD SHEET
# =========================
col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Load / Refresh Google Sheet"):
        st.session_state.df = fetch_sheet()
        st.success("Sheet loaded successfully!")

# =========================
# STOP IF NO DATA
# =========================
if st.session_state.df is None:
    st.warning("Click 'Load / Refresh Google Sheet' first.")
    st.stop()

df = st.session_state.df

# =========================
# UI SELECTORS
# =========================
branches = sorted(df["Branch"].dropna().unique().tolist())
branch = st.selectbox("🏢 Select Branch", branches)

data = df[df["Branch"] == branch].copy()

shift_cols = [c for c in df.columns if c not in ["Branch", "Name", "Role"]]
selected_col = st.selectbox("📅 Select Shift Column", shift_cols)

# =========================
# BUTTON 2: CALCULATE STATUS
# =========================
with col2:
    if st.button("⚡ Calculate Active / Inactive Now"):
        now = datetime.now()
        now_m = now.hour * 60 + now.minute  # FIXED SNAPSHOT TIME

        active = []
        inactive = []

        for _, row in data.iterrows():
            cell = row.get(selected_col, "")
            row_dict = row.to_dict()
            row_dict["Shift"] = cell

            if is_active(cell, now_m):
                active.append(row_dict)
            else:
                inactive.append(row_dict)

        st.session_state.active_df = pd.DataFrame(active)
        st.session_state.inactive_df = pd.DataFrame(inactive)

        st.session_state.last_calc_time = now.strftime("%Y-%m-%d %H:%M:%S")

        st.success("Calculation updated!")

# =========================
# DISPLAY
# =========================
active_df = st.session_state.active_df
inactive_df = st.session_state.inactive_df

st.info(f"🕒 Last Calculation: {st.session_state.last_calc_time}")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("👥 Total Staff", len(data))

with col2:
    st.metric("🟢 Active Now", len(active_df))

with col3:
    st.metric("⚪ Inactive", len(inactive_df))

st.divider()

st.subheader("🔥 Active Staff")
if not active_df.empty:
    st.dataframe(active_df[["Name", "Role", selected_col]], use_container_width=True)
else:
    st.warning("No active staff right now")

st.subheader("📊 Full Ops View")
full_df = pd.concat([active_df, inactive_df], ignore_index=True)

if not full_df.empty:
    st.dataframe(full_df[["Name", "Role", selected_col]], use_container_width=True)
