import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from background import set_background

# -----------------------------
# UI SETUP
# -----------------------------
set_background("barthomepage.jpg")
st.set_page_config(page_title="Stock System", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stSidebar"] {display:none;}
.block-container {padding:0 !important; max-width:100% !important;}
.stApp {background: linear-gradient(135deg,#eef2f7,#d6e4ff);}
div.stButton > button{
    height:55px;
    font-size:18px;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION INIT (DO NOT BREAK FLOW)
# -----------------------------
st.session_state.setdefault("mode", None)
st.session_state.setdefault("review_mode", False)
st.session_state.setdefault("draft_data", {})

# -----------------------------
# IF NO MODE → STOP
# -----------------------------
if st.session_state.mode is None:
    st.warning("Please select stock type from dashboard")
    st.stop()

mode = st.session_state.mode

# -----------------------------
# TITLE
# -----------------------------
branch = st.session_state.get("selected_branch", "Branch")

st.markdown(
    f"<h1 style='text-align:center;color:red;'>{branch} - Stock System</h1>",
    unsafe_allow_html=True
)

# -----------------------------
# GOOGLE SHEETS
# -----------------------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

sheet_id = st.session_state.get("sheet_id")
tab_name = st.session_state.get("tab_name")

if not sheet_id or not tab_name:
    st.error("No branch selected")
    st.stop()

sheet = client.open_by_key(sheet_id).worksheet(tab_name)

# -----------------------------
# LOAD DATA
# -----------------------------
def load_data(ws):
    data = ws.get_all_values()
    headers = data[0] if data else []

    items = [
        r[0].strip()
        for r in data[1:]
        if r and r[0] and r[0].strip()
    ]

    return data, headers, items

sheet_data, headers, items_list = load_data(sheet)

# -----------------------------
# FILTER ITEMS
# -----------------------------
filtered_items = items_list[:99] if mode == "daily" else items_list[99:]

st.info(f"Mode: {mode.upper()} | Items: {len(filtered_items)}")

# -----------------------------
# 🔥 BACK BUTTON (ONLY STAFF DASHBOARD)
# -----------------------------
if st.button("⬅ Back"):

    # reset ONLY stock state
    st.session_state.mode = None
    st.session_state.review_mode = False
    st.session_state.draft_data = {}

    # go to staff dashboard
    st.switch_page("pages/staff_dashboard.py")

# -----------------------------
# DATE
# -----------------------------
date = st.date_input("Select Date")
date_str = str(date)

# -----------------------------
# INPUTS
# -----------------------------
st.markdown("## Enter Stock (Manual Only)")

inputs = {}

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

            inputs[item] = value.strip() if value.strip() != "" else None

# -----------------------------
# REVIEW BUTTON
# -----------------------------
if st.button("🔍 Review Stock"):

    missing = [k for k, v in inputs.items() if v is None]

    if missing:
        st.error("Missing inputs")
        st.stop()

    st.session_state.draft_data = inputs
    st.session_state.review_mode = True

# -----------------------------
# REVIEW SCREEN
# -----------------------------
if st.session_state.review_mode:

    st.markdown("## Pending Review")

    for k, v in st.session_state.draft_data.items():
        st.write(f"{k} → {v}")

    if st.button("✅ Final Submit"):

        try:
            sheet_data, headers, items_list = load_data(sheet)

            if date_str in headers:
                col_index = headers.index(date_str) + 1
            else:
                col_index = len(headers) + 1
                sheet.update_cell(1, col_index, date_str)

            col_values = sheet.col_values(1)

            updates = []

            for item, qty in st.session_state.draft_data.items():

                if item not in items_list:
                    continue

                row = items_list.index(item) + 2

                if row - 1 < len(col_values) and col_values[row - 1]:
                    cell = gspread.utils.rowcol_to_a1(row, col_index)

                    updates.append({
                        "range": cell,
                        "values": [[qty]]
                    })

            if updates:
                sheet.batch_update(updates)

            st.success("Stock Saved")
            time.sleep(1)

            # RESET ONLY STOCK FLOW
            st.session_state.mode = None
            st.session_state.review_mode = False
            st.session_state.draft_data = {}

            st.switch_page("pages/staff_dashboard.py")

        except Exception as e:
            st.error(e)
