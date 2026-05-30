import streamlit as st
import pandas as pd
import gspread
import re
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from st_aggrid import AgGrid

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    layout="wide",
    page_title="Staff Alignment - Management System"
)

# =========================
# AUTH CHECK
# =========================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠ Session expired. Please login again.")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("⬅ Back to Login", use_container_width=True):
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

# =========================
# GOOGLE CLIENT (SAFE)
# =========================
@st.cache_resource
def get_client():
    creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=SCOPES
    )

    return gspread.authorize(creds)

client = get_client()
sheet = client.open_by_key(SHEET_ID)

# =========================
# SAFE LOADER (FIX DUPLICATE HEADER CRASH)
# =========================
@st.cache_data(ttl=300)
def load_data():
    try:
        ws = sheet.worksheet(TAB_NAME)

        raw = ws.get_all_values()

        if not raw or len(raw) < 2:
            return pd.DataFrame(columns=["Branch", "Name", "Role"])

        headers = [str(h).strip() for h in raw[0]]

        # 🔥 FIX DUPLICATE HEADERS
        seen = {}
        clean_headers = []

        for h in headers:
            if h in seen:
                seen[h] += 1
                h = f"{h}_{seen[h]}"
            else:
                seen[h] = 0

            clean_headers.append(h)

        rows = raw[1:]
        df = pd.DataFrame(rows, columns=clean_headers)

        return df

    except Exception as e:
        st.error(f"Sheet Load Error: {e}")
        return pd.DataFrame(columns=["Branch", "Name", "Role"])

df = load_data()

# =========================
# CONSTANTS
# =========================
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# =========================
# OT CALCULATION
# =========================
def extract_ot(row):
    total = 0

    for d in DAYS:
        val = str(row.get(d, ""))

        match = re.search(r"\(OT\s+(\d+(?:\.\d+)?)\s*h\)", val)
        if match:
            total += float(match.group(1))

    return total

# =========================
# HEADER UI
# =========================
st.title("🏢 Staff Alignment System (Management View)")

branches = sorted(df["Branch"].dropna().unique().tolist()) if not df.empty else []

selected_branch = st.selectbox("🏢 Select Branch", ["All"] + branches)

selected_date = st.date_input("📅 Week Selector", value=datetime.today())

week_start = selected_date - timedelta(days=(selected_date.weekday() + 1) % 7)
st.caption(f"Week Start: {week_start.strftime('%d %b %Y')}")

# =========================
# FILTER DATA
# =========================
data = df.copy()

if selected_branch != "All":
    data = data[data["Branch"] == selected_branch]

# =========================
# VIEW TABLE
# =========================
st.subheader("📊 Staff Schedule")

if not data.empty:
    view_df = data.copy()

    view_df["Over-Time"] = view_df.apply(lambda r: f"{extract_ot(r)} hrs", axis=1)

    column_defs = [
        {"field": "Branch", "pinned": "left"},
        {"field": "Name", "pinned": "left"},
        {"field": "Role"}
    ]

    for d in DAYS:
        column_defs.append({"field": d})

    column_defs.append({"field": "Over-Time"})

    AgGrid(
        view_df,
        gridOptions={"columnDefs": column_defs},
        height=600,
        fit_columns_on_grid_load=True
    )

else:
    st.info("No data found for selected branch")

# =========================
# INSIGHTS
# =========================
st.subheader("📈 Insights")

if not data.empty:
    staff_count = data.groupby("Branch")["Name"].count().reset_index(name="Staff Count")

    data["OT"] = data.apply(extract_ot, axis=1)
    ot_sum = data.groupby("Branch")["OT"].sum().reset_index()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 👥 Staff Count")
        st.dataframe(staff_count, use_container_width=True)

    with col2:
        st.markdown("### ⏱ OT Hours")
        st.dataframe(ot_sum, use_container_width=True)

    st.bar_chart(ot_sum.set_index("Branch"))

# =========================
# REFRESH
# =========================
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
