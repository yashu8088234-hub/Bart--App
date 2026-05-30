import streamlit as st
import pandas as pd
import gspread
import re
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Branch Ops System")

SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
TAB_NAME = "StaffSchedule"

DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

# =========================
# AUTH
# =========================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Session expired")
    st.stop()

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

@st.cache_data(ttl=300)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()

    headers = raw[0]
    df = pd.DataFrame(raw[1:], columns=headers)
    return df

df = load_data()

# =========================
# SHIFT PARSER (CORE LOGIC)
# =========================
def parse_shift(cell):
    """
    Example expected formats:
    09:00-18:00
    10:00 - 19:00 (OT 2h)
    """
    if not cell:
        return None

    match = re.search(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", str(cell))
    if match:
        return f"{match.group(1)} → {match.group(2)}"
    return str(cell)

# =========================
# UI - LEVEL 1 (BRANCH)
# =========================
st.title("🏢 Branch Operations Control")

branches = sorted(df["Branch"].dropna().unique())
selected_branch = st.selectbox("Select Branch", branches)

branch_df = df[df["Branch"] == selected_branch].copy()

st.metric("👥 Total Staff", len(branch_df))

st.divider()

# =========================
# LEVEL 2 (STAFF LIST)
# =========================
st.subheader("👨‍💼 Staff in Branch (Click to View Schedule)")

staff_list = branch_df["Name"].dropna().unique().tolist()
selected_staff = st.selectbox("Select Staff Member", staff_list)

staff_df = branch_df[branch_df["Name"] == selected_staff].iloc[0]

st.divider()

# =========================
# LEVEL 3 (FULL SHIFT VIEW)
# =========================
st.subheader(f"📅 Shift Details - {selected_staff}")

shift_data = []

for d in DAYS:
    if d in branch_df.columns:
        shift_data.append({
            "Day": d,
            "Shift": parse_shift(staff_df.get(d, ""))
        })

shift_df = pd.DataFrame(shift_data)

st.dataframe(
    shift_df,
    use_container_width=True,
    height=300
)

st.divider()

# =========================
# FULL RAW VIEW (OPTIONAL EXPANDER)
# =========================
with st.expander("🔍 Full Raw Staff Record"):
    st.write(staff_df)
