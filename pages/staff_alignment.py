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
# CLEAN
# =========================
def clean(text):
    text = str(text)
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\(.*?\)", "", text)  # remove OT
    text = re.sub(r"\s+", " ", text).strip()
    return text

# =========================
# 🔥 FIXED SHIFT PARSER (MAIN FIX)
# =========================
def get_shift(cell):
    if not cell:
        return None

    text = clean(cell)

    # Extract full time tokens correctly
    matches = re.findall(r"\d{1,2}\s*(?:AM|PM)", text, re.I)

    if len(matches) < 2:
        return None

    def convert(t):
        t = t.upper().replace(" ", "")
        h = int(re.findall(r"\d{1,2}", t)[0])
        ap = "AM" if "AM" in t else "PM"

        if ap == "AM":
            if h == 12:
                h = 0
        else:
            if h != 12:
                h += 12

        return h * 60

    start = convert(matches[0])
    end = convert(matches[1])

    return start, end

# =========================
# ACTIVE LOGIC
# =========================
def is_active(cell, now_min):
    shift = get_shift(cell)
    if not shift:
        return False

    start, end = shift

    # normal shift
    if start < end:
        return start <= now_min < end

    # overnight shift
    return now_min >= start or now_min < end

# =========================
# UI
# =========================
branches = sorted(df["Branch"].dropna().unique().tolist())
branch = st.selectbox("🏢 Select Branch", branches)

data = df[df["Branch"] == branch].copy()

shift_cols = [c for c in df.columns if c not in ["Branch", "Name", "Role"]]
selected_col = st.selectbox("📅 Select Shift Column", shift_cols)

# =========================
# CALCULATE BUTTON
# =========================
if st.button("⚡ Calculate Active / Inactive"):

    now = datetime.now()
    now_min = now.hour * 60 + now.minute

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
    st.session_state.last_calc = now.strftime("%Y-%m-%d %H:%M:%S")

    st.success("Updated Successfully!")

# =========================
# OUTPUT
# =========================
active_df = st.session_state.get("active_df", pd.DataFrame())
inactive_df = st.session_state.get("inactive_df", pd.DataFrame())

st.info(f"🕒 Last Calculation: {st.session_state.get('last_calc')}")

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
