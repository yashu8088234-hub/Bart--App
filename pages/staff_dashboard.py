import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from pathlib import Path
import time
import uuid

# -----------------------------
# UI SETUP (UNCHANGED)
# -----------------------------
st.set_page_config(page_title="Stock System", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stSidebar"] {display:none;}
.block-container {padding:0 !important; max-width:100% !important;}

.stApp {
    background: linear-gradient(135deg,#eef2f7,#d6e4ff);
}

div.stButton > button{
    height:55px;
    font-size:18px;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION INIT (UNCHANGED)
# -----------------------------
if "selected_branch" not in st.session_state:
    st.session_state.selected_branch = "-- Select Branch --"

if "branch_info" not in st.session_state:
    st.session_state.branch_info = None

if "sheet_id" not in st.session_state:
    st.session_state.sheet_id = None

if "tab_name" not in st.session_state:
    st.session_state.tab_name = None

if "auth_token" not in st.session_state:
    st.session_state.auth_token = None

# -----------------------------
# TITLE (UNCHANGED)
# -----------------------------
branch = st.session_state.get("selected_branch", "Branch")

st.markdown(
    f"<h1 style='text-align:center;color:red;'>{branch} - Stock System</h1>",
    unsafe_allow_html=True
)

# -----------------------------
# SHEET CHECK (UNCHANGED)
# -----------------------------
sheet_id = st.session_state.get("sheet_id")
tab_name = st.session_state.get("tab_name")

if not sheet_id or not tab_name:
    st.error("Session expired.")

    if st.button("⬅ Back to Staff Dashboard"):
        st.switch_page("pages/staff_dashboard.py")

    st.stop()

# -----------------------------
# GOOGLE AUTH (UNCHANGED)
# -----------------------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

client = get_client()

@st.cache_resource
def get_sheet(sheet_id, tab_name):
    return client.open_by_key(sheet_id).worksheet(tab_name)

sheet = get_sheet(sheet_id, tab_name)

# -----------------------------
# COLUMN LOAD (UNCHANGED)
# -----------------------------
def load_column_a(ws):
    data = ws.get_all_values()
    return [row[0].strip() for row in data if row and row[0].strip()]

items_list = load_column_a(sheet)

# -----------------------------
# FIND SECTIONS (UNCHANGED)
# -----------------------------
def find_index(items, name):
    for i, v in enumerate(items):
        if v.strip().upper() == name:
            return i
    return None

daily_start = find_index(items_list, "DAILY ITEM")
weekly_start = find_index(items_list, "WEEKLY ITEM")

if daily_start is None or weekly_start is None:
    st.error("❌ DAILY ITEM or WEEKLY ITEM not found")
    st.stop()

# -----------------------------
# MODE SELECT (UNCHANGED)
# -----------------------------
if st.session_state.page == "mode_select":

    st.markdown("## Select Option")

    c1, c2 = st.columns(2)

    if c1.button("📦 Daily Stock"):
        st.session_state.mode = "daily"
        st.session_state.page = "stock_entry"
        st.rerun()

    if c2.button("📊 Weekly Stock"):
        st.session_state.mode = "weekly"
        st.session_state.page = "stock_entry"
        st.rerun()

    st.stop()

# -----------------------------
# STOCK ENTRY (UNCHANGED)
# -----------------------------
mode = st.session_state.mode

if mode == "daily":
    filtered_items = items_list[daily_start + 1 : weekly_start]
else:
    filtered_items = items_list[weekly_start + 1 :]

st.info(f"Mode: {mode.upper()} | Items: {len(filtered_items)}")

if st.button("⬅ Back"):
    st.switch_page("pages/staff_dashboard.py")

date = st.date_input("Select Date")
date_str = str(date)

inputs = {}

with st.form("stock_form", clear_on_submit=False):

    for i in range(0, len(filtered_items), 4):
        cols = st.columns(4)

        for j, col in enumerate(cols):
            if i + j < len(filtered_items):

                item = filtered_items[i + j]

                value = col.text_input(
                    item,
                    placeholder="Enter quantity",
                    key=f"{mode}_{item}"
                )

                inputs[item] = value.strip() if value.strip() else None

    submitted = st.form_submit_button("🔍 Review Stock")

    if submitted:
        missing = [k for k, v in inputs.items() if v is None]

        if missing:
            st.error("Missing inputs")
        else:
            st.session_state.draft_data = inputs
            st.session_state.review_mode = True

if st.session_state.review_mode:

    st.markdown("## Review")

    for k, v in st.session_state.draft_data.items():
        st.write(f"{k} → {v}")

    if st.button("✅ Submit"):

        try:
            with st.spinner("Saving stock..."):

                sheet_data = sheet.get_all_values()
                headers = sheet_data[0]

                if date_str in headers:
                    col_index = headers.index(date_str) + 1
                else:
                    col_index = len(headers) + 1
                    sheet.update_cell(1, col_index, date_str)

                col_values = sheet.col_values(1)
                item_to_row = {val.strip(): i + 1 for i, val in enumerate(col_values)}

                from gspread import Cell
                cells = []

                for item, qty in st.session_state.draft_data.items():
                    row = item_to_row.get(item)

                    if row:
                        cells.append(Cell(row=row, col=col_index, value=qty))

                if cells:
                    sheet.update_cells(cells, value_input_option="USER_ENTERED")

                st.session_state.review_mode = False
                st.session_state.draft_data = {}

                st.success("Submitted ✔")

                time.sleep(2)

                # -----------------------------
                # 🔴 ONLY FIX (IMPORTANT)
                # FORCE CLEAN SESSION BEFORE RETURN
                # -----------------------------
                st.session_state.sheet_id = sheet_id
                st.session_state.tab_name = tab_name

                st.switch_page("pages/staff_dashboard.py")

        except Exception as e:
            st.error(f"Error: {e}")
