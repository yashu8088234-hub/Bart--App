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
# LOAD SHEET (ONLY BUTTON)
# =========================
def fetch_sheet():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

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
# TIME PARSER (ROBUST)
# =========================
def parse_time_str(t):
    return datetime.strptime(t.strip().upper(), "%I %p").time()

# =========================
# SHIFT PARSER
# =========================
def parse_shift(cell):
    if not cell:
        return None

    text = clean(cell)

    if "OFF" in text.upper():
        return None

    text = re.sub(r"\(.*?\)", "", text)

    matches = re.findall(r"\d{1,2}\s*(?:AM|PM)", text, re.IGNORECASE)

    if len(matches) < 2:
        return None

    try:
        start = parse_time_str(matches[0])
        end = parse_time_str(matches[1])
    except:
        return None

    return start, end

# =========================
# ACTIVE CHECK
# =========================
def is_active(cell, now_t):
    shift = parse_shift(cell)
    if not shift:
        return False

    start, end = shift

    # NORMAL SHIFT
    if start < end:
        return start <= now_t < end

    # OVERNIGHT SHIFT
    return now_t >= start or now_t < end

# =========================
# SESSION STATE
# =========================
if "df" not in st.session_state:
    st.session_state.df = None

if "active_df" not in st.session_state:
    st.session_state.active_df = pd.DataFrame()

if "inactive_df" not in st.session_state:
    st.session_state.inactive_df = pd.DataFrame()

if "last_calc" not in st.session_state:
    st.session_state.last_calc = None

# =========================
# BUTTON 1: LOAD SHEET
# =========================
col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Load Google Sheet"):
        st.session_state.df = fetch_sheet()
        st.success("Sheet Loaded Successfully!")

# STOP IF NO DATA
if st.session_state.df is None:
    st.warning("Click 'Load Google Sheet' first")
    st.stop()

df = st.session_state.df

# =========================
# UI FILTERS
# =========================
branches = sorted(df["Branch"].dropna().unique().tolist())
branch = st.selectbox("🏢 Select Branch", branches)

data = df[df["Branch"] == branch].copy()

shift_cols = [c for c in df.columns if c not in ["Branch", "Name", "Role"]]
selected_col = st.selectbox("📅 Select Shift Column", shift_cols)

# =========================
# BUTTON 2: CALCULATE
# =========================
with col2:
    if st.button("⚡ Calculate Active / Inactive"):
        now_t = datetime.now().time()  # FIXED TIME SNAPSHOT

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

        st.success("Calculation Updated!")

# =========================
# OUTPUT
# =========================
active_df = st.session_state.active_df
inactive_df = st.session_state.inactive_df

st.info(f"🕒 Last Calculation: {st.session_state.last_calc}")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("👥 Total Staff", len(data))

with col2:
    st.metric("🟢 Active", len(active_df))

with col3:
    st.metric("⚪ Inactive", len(inactive_df))

st.divider()

st.subheader("🔥 Active Staff")

if not active_df.empty:
    st.dataframe(active_df[["Name", "Role", selected_col]], use_container_width=True)
else:
    st.warning("No active staff")

st.subheader("📊 Full View")

full_df = pd.concat([active_df, inactive_df], ignore_index=True)

if not full_df.empty:
    st.dataframe(full_df[["Name", "Role", selected_col]], use_container_width=True)
