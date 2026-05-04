import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from background import set_background

# -----------------------------
# Background & UI Setup
# -----------------------------
set_background("barthomepage.jpg")
st.set_page_config(page_title="Stock Count System", layout="wide")

hide_streamlit = """
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stSidebar"] {display:none;}
.block-container {padding:0 !important; margin:0 auto !important; max-width:100% !important;}
.stApp {background: linear-gradient(135deg,#eef2f7,#d6e4ff);}
div.stButton > button{height:60px;font-size:20px;border-radius:10px;transition:0.3s;}
div.stButton > button:hover{background-color:#ff4b4b;color:white;}
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button { -webkit-appearance:none; margin:0; }
input[type=number] { -moz-appearance:textfield; }
</style>
"""
st.markdown(hide_streamlit, unsafe_allow_html=True)

# -----------------------------
# Title
# -----------------------------
branch_name_display = st.session_state.get("selected_branch", "Unknown Branch")
st.markdown(
    f"<h1 style='text-align:center;color:red;font-size:55px;'>"
    f"{branch_name_display} - Stock Count System</h1>",
    unsafe_allow_html=True
)

# -----------------------------
# Google Sheets Auth
# -----------------------------
try:
    creds_dict = dict(st.secrets["GOOGLE_CREDS_JSON"])
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"Google Auth Error: {e}")
    st.stop()

# -----------------------------
# Sheet Validation
# -----------------------------
if "sheet_id" not in st.session_state or "tab_name" not in st.session_state:
    st.error("No branch selected. Go back to dashboard.")
    st.stop()

branch_sheet = client.open_by_key(st.session_state.sheet_id)
sheet = branch_sheet.worksheet(st.session_state.tab_name)

# -----------------------------
# Load Sheet Data (cached)
# -----------------------------
@st.cache_data(ttl=300)
def load_sheet(_sheet):
    data = _sheet.get_all_values()
    headers = data[0]
    items = [row[0].strip() for row in data[1:] if row]
    return data, headers, items

sheet_data, headers, existing_items_list = load_sheet(sheet)

# -----------------------------
# Session State
# -----------------------------
st.session_state.setdefault("smart_inputs", {})
st.session_state.setdefault("smart_review", False)
st.session_state.setdefault("view_mode", "daily")

# -----------------------------
# MODE SELECTION
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("📦 Daily Stock Count"):
        st.session_state.view_mode = "daily"
        st.session_state.smart_review = False

with col2:
    if st.button("📊 Weekly Stock Count"):
        st.session_state.view_mode = "weekly"
        st.session_state.smart_review = False

mode = st.session_state.view_mode

# -----------------------------
# FILTER ITEMS (KEY CHANGE)
# -----------------------------
if mode == "daily":
    filtered_items = existing_items_list[:99]
    st.info("📦 Daily Mode: Showing first 99 items")
else:
    filtered_items = existing_items_list[99:]
    st.info("📊 Weekly Mode: Showing items after 99")

# -----------------------------
# DATE
# -----------------------------
date = st.date_input("Select Date")
date_str = str(date)

st.write(f"Recording stock for: {date_str}")

# -----------------------------
# SMART INVENTORY UI
# -----------------------------
st.markdown("## 🧠 Smart Inventory Entry")

search = st.text_input("Search Item")

if search:
    filtered_items = [i for i in filtered_items if search.lower() in i.lower()]

smart_inputs = {}

cols_per_row = 4

for i in range(0, len(filtered_items), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, col in enumerate(cols):
        if i + j < len(filtered_items):
            item = filtered_items[i + j]
            qty = col.number_input(
                item,
                min_value=0,
                step=1,
                key=f"{mode}_{item}"
            )
            if qty > 0:
                smart_inputs[item] = qty

# -----------------------------
# REVIEW
# -----------------------------
if st.button("Review Stock"):
    st.session_state.smart_inputs = smart_inputs
    st.session_state.smart_review = True

if st.session_state.smart_review:
    st.markdown("## 🔍 Review")
    for k, v in st.session_state.smart_inputs.items():
        st.write(f"{k} → {v}")

    if st.button("Submit Stock"):
        try:
            sheet_data, headers, existing_items_list = load_sheet(sheet)

            col_index = headers.index(date_str) if date_str in headers else len(headers)

            if date_str not in headers:
                sheet.update_cell(1, col_index + 1, date_str)
                headers.append(date_str)

            updates = []

            for item, qty in st.session_state.smart_inputs.items():
                if item not in existing_items_list:
                    continue

                row = existing_items_list.index(item) + 2
                cell = gspread.utils.rowcol_to_a1(row, col_index + 1)
                updates.append({"range": cell, "values": [[qty]]})

            if updates:
                sheet.batch_update(updates)
                st.success(f"{len(updates)} items updated")

            st.session_state.smart_inputs = {}
            st.session_state.smart_review = False

            time.sleep(2)
            st.rerun()

        except Exception as e:
            st.error(f"Submit error: {e}")

# -----------------------------
# BACK BUTTON
# -----------------------------
if st.button("⬅ Back"):
    st.switch_page("pages/staff_dashboard.py")
