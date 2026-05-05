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
st.session_state.setdefault("page", "mode_select")
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
# SHEET CHECK
# -----------------------------
sheet_id = st.session_state.get("sheet_id")
tab_name = st.session_state.get("tab_name")

if not sheet_id or not tab_name:
    st.warning("Please select a branch first.")
    st.stop()

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
# LOAD COLUMN A ONLY
# -----------------------------
def load_column_a(ws):
    data = ws.get_all_values()

    col_a = []
    for row in data:
        if row and len(row) > 0:
            val = row[0].strip()
            if val:
                col_a.append(val)

    return col_a

items_list = load_column_a(sheet)

# -----------------------------
# FIND SECTIONS
# -----------------------------
def find_index(items, name):
    for i, v in enumerate(items):
        if v.strip().upper() == name:
            return i
    return None

daily_start = find_index(items_list, "DAILY ITEM")
weekly_start = find_index(items_list, "WEEKLY ITEM")

if daily_start is None or weekly_start is None:
    st.error("❌ DAILY ITEM or WEEKLY ITEM not found in Column A")
    st.stop()

# -----------------------------
# MODE SELECT PAGE
# -----------------------------
if st.session_state.page == "mode_select":

    st.markdown("## Select Option")

    c1, c2, c3 = st.columns(3)

    if c1.button("📦 Daily Stock"):
        st.session_state.mode = "daily"
        st.session_state.page = "stock_entry"
        st.rerun()

    if c2.button("📊 Weekly Stock"):
        st.session_state.mode = "weekly"
        st.session_state.page = "stock_entry"
        st.rerun()

    if c3.button("👁 View Stock"):
        st.session_state.page = "view_stock"
        st.rerun()

    st.markdown("---")

    if st.button("⬅ Back to Staff Dashboard"):
        st.session_state.page = "mode_select"
        st.session_state.mode = None
        st.switch_page("pages/staff_dashboard.py")
        st.stop()

    st.stop()

# -----------------------------
# VIEW STOCK PAGE (IMPROVED ONLY)
# -----------------------------
if st.session_state.page == "view_stock":

    st.markdown("## 👁 Stock Overview")

    daily_items = items_list[daily_start + 1 : weekly_start]
    weekly_items = items_list[weekly_start + 1 :]

    # -----------------------------
    # DAILY SECTION (CARD UI)
    # -----------------------------
    st.markdown("### 📦 DAILY STOCK")

    st.markdown("""
    <div style="background-color:white;padding:15px;border-radius:10px;
    box-shadow:0px 2px 8px rgba(0,0,0,0.1);">
    """, unsafe_allow_html=True)

    if daily_items:
        for item in daily_items:
            st.markdown(f"✔️ {item}")
    else:
        st.info("No daily items found")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # -----------------------------
    # WEEKLY SECTION (CARD UI)
    # -----------------------------
    st.markdown("### 📊 WEEKLY STOCK")

    st.markdown("""
    <div style="background-color:white;padding:15px;border-radius:10px;
    box-shadow:0px 2px 8px rgba(0,0,0,0.1);">
    """, unsafe_allow_html=True)

    if weekly_items:
        for item in weekly_items:
            st.markdown(f"✔️ {item}")
    else:
        st.info("No weekly items found")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    if st.button("⬅ Back"):
        st.session_state.page = "mode_select"
        st.rerun()

    st.stop()

# -----------------------------
# STOCK ENTRY PAGE
# -----------------------------
mode = st.session_state.mode

if mode == "daily":
    filtered_items = items_list[daily_start + 1 : weekly_start]
else:
    filtered_items = items_list[weekly_start + 1 :]

st.info(f"Mode: {mode.upper()} | Items: {len(filtered_items)}")

if st.button("⬅ Back"):
    st.session_state.page = "mode_select"
    st.rerun()

date = st.date_input("Select Date")
date_str = str(date)

st.markdown("## Enter Stock")

inputs = {}

for i in range(0, len(filtered_items, 4)):
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

if st.button("🔍 Review Stock"):

    missing = [k for k, v in inputs.items() if v is None]

    if missing:
        st.error("Missing inputs")
        st.stop()

    st.session_state.draft_data = inputs
    st.session_state.review_mode = True

if st.session_state.review_mode:

    st.markdown("## Review")

    for k, v in st.session_state.draft_data.items():
        st.write(f"{k} → {v}")

    if st.button("✅ Submit"):

        try:
            sheet_data = sheet.get_all_values()
            headers = sheet_data[0]

            if date_str in headers:
                col_index = headers.index(date_str) + 1
            else:
                col_index = len(headers) + 1
                sheet.update_cell(1, col_index, date_str)

            col_values = sheet.col_values(1)

            updates = []

            for item, qty in st.session_state.draft_data.items():
                for r, val in enumerate(col_values):
                    if val.strip() == item:
                        cell = gspread.utils.rowcol_to_a1(r + 1, col_index)
                        updates.append({
                            "range": cell,
                            "values": [[qty]]
                        })
                        break

            if updates:
                sheet.batch_update(updates)

            st.success("✅ Stock Saved")

            time.sleep(1)

            st.session_state.page = "mode_select"
            st.session_state.mode = None
            st.session_state.review_mode = False
            st.session_state.draft_data = {}

            st.rerun()

        except Exception as e:
            st.error(e)
