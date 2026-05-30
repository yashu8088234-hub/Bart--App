import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG
# =========================
SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
SHEET_NAME = "StaffSchedule"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# =========================
# GOOGLE AUTH (STREAMLIT SECRETS FIX)
# =========================
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

data = sheet.get_all_values()
df = pd.DataFrame(data)

# =========================
# CLEAN DATA
# =========================
df.columns = df.iloc[0]
df = df[1:]

branch_col = "Branch"
name_col = "Name"

# all schedule columns (days + OT)
schedule_cols = df.columns[3:]

# =========================
# AUTO DETECT TODAY COLUMN
# =========================
today_col = schedule_cols[-2]  # last day before OT column

# =========================
# LIVE LOGIC
# =========================
def is_live(row):
    val = str(row[today_col]).strip()
    return val != "" and val.upper() != "OFF"

df["Live"] = df.apply(is_live, axis=1)

# =========================
# STATS
# =========================
total_staff = len(df)
live_staff = df["Live"].sum()

# =========================
# UI
# =========================
st.set_page_config(page_title="Staff Live Dashboard", layout="wide")

st.title("🏢 Staff Live Management Dashboard")

col1, col2 = st.columns(2)

col1.metric("👥 Total Staff", total_staff)
col2.metric("🟢 Live Now", int(live_staff))

st.divider()

# =========================
# BRANCH WISE LIVE VIEW
# =========================
st.subheader("📍 Branch Wise Live Staff")

branches = df[branch_col].unique()

for b in branches:

    branch_df = df[df[branch_col] == b]
    live_df = branch_df[branch_df["Live"]]

    st.markdown(f"### 🏬 {b}")

    st.write(f"🟢 Live: {len(live_df)} / {len(branch_df)}")

    if len(live_df) > 0:
        st.write("👷 Working Now:")
        st.write(", ".join(live_df[name_col].tolist()))
    else:
        st.write("🔴 No staff working now")

    st.divider()

# =========================
# FULL TABLE
# =========================
st.subheader("📊 Live Status Table")

st.dataframe(df[[branch_col, name_col, "Live"]])
