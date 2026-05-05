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
# SESSION INIT
# -----------------------------
st.session_state.setdefault("mode", None)
st.session_state.setdefault("review_mode", False)
st.session_state.setdefault("draft_data", {})

# -----------------------------
# TITLE
# -----------------------------
branch = st.session_state.get("selected_branch", "Branch")

st.markdown(
    f"<h1 style='text-align:center;color:red;'>{branch} - Stock System</h1>",
    unsafe_allow_html=True
)

# -----------------------------
# CHECK BRANCH
# -----------------------------
sheet_id = st.session_state.get("sheet_id")
tab_name = st.session_state.get("tab_name")

if not sheet_id or not tab_name:
    st.warning("Please select a branch first.")
    if st.button("⬅ Go to Dashboard"):
        st.switch_page("pages/staff_dashboard.py")
    st.stop()

# -----------------------------
# MODE SELECT
# -----------------------------
if st.session_state.mode is None:

    st.markdown("## Select Stock Type")

    c1, c2 = st.columns(2)

    if c1.button("📦 Daily Stock"):
        st.session_state.mode = "daily"
        st.rerun()

    if c2.button("📊 Weekly Stock"):
        st.session_state.mode = "weekly"
        st.rerun()

    st.markdown("---")

    if st.button("⬅ Back to Staff Dashboard"):
        for key in ["mode", "review_mode", "draft_data"]:
            if key in st.session_state:
                del st.session_state[key]

        st.switch_page("pages/staff_dashboard.py")
        st.stop()

    st.stop()

mode = st.session_state.mode

# -----------------------------
# GOOGLE SHEETS
# -----------------------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

sheet = client.open_by_key(sheet_id).worksheet(tab_name)

# -----------------------------
# LOAD DATA
# -----------------------------
def load_data(ws):
    data = ws.get_all_values()
    headers = data[0] if data else []

    items = []

    for row in data[1:]:
        if row and len(row) > 0:
            item = row[0]
            if item and item.strip():
                items.append(item.strip())

    return data, headers, items

sheet_data, headers, items_list = load_data(sheet)

# -----------------------------
# 🔥 SECTION DETECTION (FULL SENTENCE MATCH)
# -----------------------------
def normalize(text):
    return text.replace("\xa0", " ").strip()

def find_section(items, section_name):
    target = normalize(section_name)

    for i, item in enumerate(items):
        if item and normalize(item) == target:
            return i
    return None


daily_start = find_section(items_list, "DAILY ITEM")
weekly_start = find_section(items_list, "WEEKLY ITEM")

if daily_start is None or weekly_start is None:
    st.error("""
❌ Cannot find section headers in sheet.

Make sure these exist EXACTLY in Column A:
- DAILY ITEM
- WEEKLY ITEM
""")
    st.stop()

# -----------------------------
# FILTER ITEMS
# -----------------------------
if mode == "daily":
    filtered_items = items_list[daily_start + 1 : weekly_start]
else:
    filtered_items = items_list[weekly_start + 1 :]

st.info(f"Mode: {mode.upper()} | Items: {len(filtered_items)}")

# -----------------------------
# BACK BUTTON
# -----------------------------
if st.button("⬅ Back"):
    st.session_state.mode = None
    st.session_state.review_mode = False
    st.session_state.draft_data = {}
    st.rerun()

# -----------------------------
# DATE
# -----------------------------
date = st.date_input("Select Date")
date_str = str(date)

# -----------------------------
# INPUTS
# -----------------------------
st.markdown("## Enter Stock")

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
# REVIEW
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

            # Date column
            if date_str in headers:
                col_index = headers.index(date_str) + 1
            else:
                col_index = len(headers) + 1
                sheet.update_cell(1, col_index, date_str)

            updates = []

            for item, qty in st.session_state.draft_data.items():

                if item not in items_list:
                    continue

                row = items_list.index(item) + 2

                cell = gspread.utils.rowcol_to_a1(row, col_index)

                updates.append({
                    "range": cell,
                    "values": [[qty]]
                })

            if updates:
                sheet.batch_update(updates)

            st.success("✅ Stock Saved")
            time.sleep(1)

            st.session_state.mode = None
            st.session_state.review_mode = False
            st.session_state.draft_data = {}

            st.rerun()

        except Exception as e:
            st.error(e)
