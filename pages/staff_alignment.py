import streamlit as st
import pandas as pd
import gspread
import re
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(layout="wide", page_title="Ops Intelligence Live")

# =========================
# SHEET CONFIG
# =========================
SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
TAB_NAME = "StaffSchedule"

DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

# =========================
# GOOGLE CLIENT
# =========================
@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["GOOGLE_CREDS_JSON"],
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

client = get_client()
sheet = client.open_by_key(SHEET_ID)

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=60)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0]).fillna("")

df = load_data()

# =========================
# SUPER ROBUST SHIFT PARSER
# =========================
def parse_shift(cell):
    try:
        if not cell:
            return None

        text = str(cell)

        # normalize everything
        text = text.replace("–", "-").replace("—", "-")
        text = text.replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text)

        if "OFF" in text.upper():
            return None

        # REMOVE OT
        text = re.sub(r"\(.*?\)", "", text)

        # 🔥 VERY FLEXIBLE MATCH (KEY FIX)
        match = re.search(
            r"(\d{1,2})\s*(AM|PM)\s*-\s*(\d{1,2})\s*(AM|PM)",
            text,
            re.IGNORECASE
        )

        if not match:
            return None

        sh, sap, eh, eap = match.groups()

        def to24(h, ap):
            h = int(h)
            ap = ap.upper()
            if ap == "AM":
                return 0 if h == 12 else h
            return 12 if h == 12 else h + 12

        start = to24(sh, sap)
        end = to24(eh, eap)

        return start, end

    except:
        return None

# =========================
# ACTIVE CHECK
# =========================
def is_active(cell):
    shift = parse_shift(cell)
    if not shift:
        return False

    start, end = shift
    now = datetime.now().hour

    # normal shift
    if start < end:
        return start <= now <= end

    # overnight shift
    return now >= start or now <= end

# =========================
# UI
# =========================
st.title("⚡ Ops Intelligence Control Center")

branches = sorted(df["Branch"].unique()) if not df.empty else []
branch = st.selectbox("Select Branch", branches)

data = df[df["Branch"] == branch]

today = DAYS[(datetime.today().weekday() + 1) % 7]

# =========================
# OPS ENGINE
# =========================
active = []
inactive = []

debug_fail = []

for _, row in data.iterrows():
    cell = row.get(today, "")

    if parse_shift(cell) is None and cell and "OFF" not in cell.upper():
        debug_fail.append(cell)

    if is_active(cell):
        active.append(row.to_dict())
    else:
        inactive.append(row.to_dict())

# =========================
# DEBUG (IMPORTANT)
# =========================
with st.expander("🔍 Debug Unparsed Shifts"):
    st.write(debug_fail)

# =========================
# KPI
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total", len(data))

with col2:
    st.metric("Active", len(active))

with col3:
    st.metric("Inactive", len(inactive))

st.divider()

# =========================
# ACTIVE
# =========================
st.subheader("🔥 Active Staff")

if active:
    st.dataframe(pd.DataFrame(active)[["Name","Role"]], use_container_width=True)
else:
    st.error("❌ STILL NO ACTIVE → check debug panel above")

# =========================
# FULL VIEW
# =========================
st.subheader("📊 Full View")

all_df = pd.DataFrame(active + inactive)
if not all_df.empty:
    st.dataframe(all_df[["Name","Role"]])
