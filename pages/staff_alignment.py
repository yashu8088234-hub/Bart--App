import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

# =========================
# PAGE CONFIG (MODERN FEEL)
# =========================
st.set_page_config(
    layout="wide",
    page_title="Ops Control Center"
)

# =========================
# AUTH
# =========================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Session expired. Please login again.")
    if st.button("Back"):
        st.switch_page("app.py")
    st.stop()

# =========================
# CONFIG
# =========================
SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
TAB_NAME = "StaffSchedule"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# =========================
# CLIENT
# =========================
@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["GOOGLE_CREDS_JSON"],
        scopes=SCOPES
    )
    return gspread.authorize(creds)

client = get_client()
sheet = client.open_by_key(SHEET_ID)

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=300)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    raw = ws.get_all_values()

    if not raw or len(raw) < 2:
        return pd.DataFrame()

    headers = [h.strip() for h in raw[0]]

    seen = {}
    clean_headers = []
    for h in headers:
        if h in seen:
            seen[h] += 1
            h = f"{h}_{seen[h]}"
        else:
            seen[h] = 0
        clean_headers.append(h)

    return pd.DataFrame(raw[1:], columns=clean_headers)

df = load_data()

# =========================
# CURRENT CONTEXT
# =========================
today = datetime.today()
today_name = DAYS[(today.weekday() + 1) % 7]

# =========================
# FILTER
# =========================
branches = sorted(df["Branch"].dropna().unique()) if not df.empty else []
selected_branch = st.selectbox("🏢 Branch", ["All"] + branches)

data = df.copy()
if selected_branch != "All":
    data = data[data["Branch"] == selected_branch]

# =========================
# HEADER KPIs (CLEAN + MODERN)
# =========================
st.title("⚡ Operations Control Center")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("👥 Active Staff", len(data))

with col2:
    st.metric("📅 Today", today_name)

with col3:
    st.metric("🏢 Branch", selected_branch if selected_branch != "All" else "All")

st.divider()

# =========================
# MAIN VIEW (SHIFT VIEW - CORE)
# =========================
st.subheader("🧑‍💼 Live Staff Schedule View")

if not data.empty:

    view = data[["Name", "Role", "Branch"]].copy()

    # show full week schedule clearly (not OT)
    for d in DAYS:
        if d in data.columns:
            view[d] = data[d]

    st.dataframe(
        view,
        use_container_width=True,
        height=520
    )

else:
    st.info("No staff available")

# =========================
# TODAY HIGHLIGHT VIEW (IMPORTANT OPS FEATURE)
# =========================
st.subheader(f"🔥 Today’s Active Schedule ({today_name})")

if not data.empty and today_name in data.columns:

    today_view = data[["Name", "Role", today_name]].copy()
    today_view = today_view[today_view[today_name].astype(str).str.strip() != ""]

    st.dataframe(
        today_view,
        use_container_width=True,
        height=300
    )

# =========================
# BRANCH DISTRIBUTION (LIGHT INSIGHT ONLY)
# =========================
st.subheader("📊 Branch Distribution")

if not data.empty:
    st.bar_chart(data["Branch"].value_counts())
