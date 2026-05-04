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

hide_streamlit = """
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stSidebar"] {display:none;}
.block-container {padding:0 !important; max-width:100% !important;}
.stApp {background: linear-gradient(135deg,#eef2f7,#d6e4ff);}
div.stButton > button{height:55px;font-size:18px;border-radius:10px;}
</style>
"""
st.markdown(hide_streamlit, unsafe_allow_html=True)

# -----------------------------
# TITLE
# -----------------------------
branch = st.session_state.get("selected_branch", "Branch")
st.markdown(f"<h1 style='text-align:center;color:red'>{branch} - Stock System</h1>", unsafe_allow_html=True)

# -----------------------------
# GOOGLE SHEET
# -----------------------------
try:
    creds_dict = dict(st.secrets["GOOGLE_CREDS_JSON"])
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(e)
    st.stop()

if "sheet_id" not in st.session_state or "tab_name" not in st.session_state:
    st.error("No branch selected")
    st.stop()

sheet = client.open_by_key(st.session_state.sheet_id).worksheet(st.session_state.tab_name)

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data(ttl=300)
def load_data(_sheet):
    data = _sheet.get_all_values()
    headers = data[0]
    items = [r[0].strip() for r in data[1:]]
    return data, headers, items

sheet_data, headers, items_list = load_data(sheet)

# -----------------------------
# MODE SELECTION (STEP 1)
# -----------------------------
if "mode" not in st.session_state:
    st.session_state.mode = None

if st.session_state.mode is None:
    st.markdown("## Select Mode")

    c1, c2 = st.columns(2)

    if c1.button("📦 Daily Stock"):
        st.session_state.mode = "daily"
        st.rerun()

    if c2.button("📊 Weekly Stock"):
        st.session_state.mode = "weekly"
        st.rerun()

    st.stop()

mode = st.session_state.mode

# -----------------------------
# FILTER ITEMS
# -----------------------------
filtered_items = items_list[:99] if mode == "daily" else items_list[99:]

st.info(f"Mode: {mode.upper()} | Items: {len(filtered_items)}")

# -----------------------------
# DATE
# -----------------------------
date = st.date_input("Select Date")
date_str = str(date)

# -----------------------------
# INPUT SECTION
# -----------------------------
st.markdown("## Enter Stock (Manual Only)")

search = st.text_input("Search item")

if search:
    filtered_items = [i for i in filtered_items if search.lower() in i.lower()]

inputs = {}

for i in range(0, len(filtered_items), 4):
    cols = st.columns(4)
    for j, col in enumerate(cols):
        if i + j < len(filtered_items):
            item = filtered_items[i + j]

            qty = col.number_input(
                item,
                min_value=0,
                step=1,
                key=f"{mode}_{item}"
            )

            inputs[item] = qty

# -----------------------------
# STEP 1: REVIEW (PENDING LIST)
# -----------------------------
if st.button("Review Stock"):

    missing = [k for k, v in inputs.items() if v is None]

    if missing:
        st.error("Missing values detected!")
        for m in missing:
            st.warning(f"Enter value for: {m}")
        st.stop()

    st.session_state.pending = inputs
    st.session_state.review = True

# -----------------------------
# STEP 2: SHOW PENDING LIST
# -----------------------------
if st.session_state.get("review"):

    st.markdown("## 🟡 Pending Approval List")

    for k, v in st.session_state.pending.items():
        st.write(f"{k} → {v}")

    st.warning("⚠️ Nothing saved yet. This is only preview.")

    if st.button("✅ Submit Final to Sheet"):

        try:
            sheet_data, headers, items_list = load_data(sheet)

            col_index = headers.index(date_str) if date_str in headers else len(headers)

            if date_str not in headers:
                sheet.update_cell(1, col_index + 1, date_str)
                headers.append(date_str)

            updates = []

            for item, qty in st.session_state.pending.items():

                if item not in items_list:
                    continue

                row = items_list.index(item) + 2
                cell = gspread.utils.rowcol_to_a1(row, col_index + 1)

                updates.append({
                    "range": cell,
                    "values": [[qty]]
                })

            if updates:
                sheet.batch_update(updates)
                st.success(f"✅ {len(updates)} items saved successfully")

            # RESET
            st.session_state.pending = {}
            st.session_state.review = False

            time.sleep(2)
            st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")

# -----------------------------
# BACK BUTTON
# -----------------------------
if st.button("⬅ Back"):
    st.session_state.mode = None
    st.rerun()
