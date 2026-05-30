import streamlit as st
import pandas as pd
import gspread
import re
import json

from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from st_aggrid import AgGrid

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Management Control System v2")

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
# GOOGLE SHEETS CONNECTION (JSON VERSION)
# =========================
SHEET_ID = "1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0"
TAB_NAME = "StaffSchedule"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_client():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDS_JSON"])

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=SCOPES
    )

    return gspread.authorize(creds)

client = get_client()
sheet = client.open_by_key(SHEET_ID)

# =========================
# CONSTANTS
# =========================
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=60)
def load_data():
    ws = sheet.worksheet(TAB_NAME)
    data = ws.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        df = pd.DataFrame(columns=["Branch", "Name", "Role"] + DAYS + ["Over-Time"])

    return df

df = load_data()

# =========================
# OT CALCULATION
# =========================
def extract_ot(row):
    total = 0
    for d in DAYS:
        val = str(row.get(d, ""))
        m = re.search(r"\(OT\s+(\d+(?:\.\d+)?)\s*h\)", val)
        if m:
            total += float(m.group(1))
    return total

# =========================
# HEADER
# =========================
st.title("🏢 Management Control System v2")

branches = sorted(df["Branch"].dropna().unique().tolist()) if not df.empty else []

selected_branch = st.selectbox("🏢 Branch Filter", ["All"] + branches)

selected_date = st.date_input("📅 Week Selector", value=datetime.today())
week_start = selected_date - timedelta(days=(selected_date.weekday() + 1) % 7)

st.caption(f"Week Start: {week_start.strftime('%d %b %Y')}")

tab1, tab2, tab3 = st.tabs(["📊 Live View", "📈 Insights", "✏ Edit Mode"])

# =========================
# FILTER DATA
# =========================
data = df.copy()
if selected_branch != "All":
    data = data[data["Branch"] == selected_branch]

# ======================================================
# TAB 1 - LIVE VIEW
# ======================================================
with tab1:

    st.subheader("📊 Live Schedule")

    view_df = data.copy()

    if not view_df.empty:
        view_df["Over-Time"] = view_df.apply(lambda r: f"{extract_ot(r)} hrs", axis=1)

    column_defs = [
        {"field": "Branch", "pinned": "left"},
        {"field": "Name", "pinned": "left"},
        {"field": "Role"},
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

# ======================================================
# TAB 2 - INSIGHTS
# ======================================================
with tab2:

    st.subheader("📈 Branch Insights")

    if data.empty:
        st.warning("No data available")
    else:

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

        st.markdown("### 📊 OT Chart")
        st.bar_chart(ot_sum.set_index("Branch"))

# ======================================================
# TAB 3 - EDIT MODE
# ======================================================
with tab3:

    st.subheader("✏ Schedule Editor")

    if data.empty:
        st.warning("No data found")
        st.stop()

    edit_df = data.copy()
    edit_df["Over-Time"] = edit_df.apply(lambda r: f"{extract_ot(r)} hrs", axis=1)

    edited = st.data_editor(
        edit_df,
        use_container_width=True,
        num_rows="dynamic"
    )

    if st.button("💾 Save Changes"):
        try:
            ws = sheet.worksheet(TAB_NAME)

            ws.clear()
            ws.update(
                [edited.columns.tolist()] +
                edited.fillna("").values.tolist()
            )

            st.success("✅ Saved successfully!")
            st.cache_data.clear()
            st.rerun()

        except Exception as e:
            st.error(f"❌ Save failed: {e}")

# =========================
# REFRESH
# =========================
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
