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
# TOAST FUNCTION (BOTTOM POPUP)
# -----------------------------
def success_toast(message):
    st.markdown(
        f"""
        <div style="
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background-color: #1e7e34;
            color: white;
            padding: 15px 25px;
            border-radius: 12px;
            font-size: 18px;
            z-index: 9999;
            box-shadow: 0px 5px 15px rgba(0,0,0,0.3);
        ">
            ✔ {message}
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# TITLE
# -----------------------------
branch = st.session_state.get("selected_branch", "Branch")
st.markdown(
    f"<h1 style='text-align:center;color:red;'>"
    f"{branch} - Stock System</h1>",
    unsafe_allow_html=True
)

# -----------------------------
# GOOGLE SHEETS
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
    st.error(e)
    st.stop()

if "sheet_id" not in st.session_state or "tab_name" not in st.session_state:
    st.error("No branch selected")
    st.stop()

sheet = client.open_by_key(st.session_state.sheet_id).worksheet(st.session_state.tab_name)

# -----------------------------
# LOAD DATA (IGNORE EMPTY ROWS)
# -----------------------------
@st.cache_data(ttl=300)
def load_data(_sheet):
    data = _sheet.get_all_values()
    headers = data[0]

    items = [
        r[0].strip()
        for r in data[1:]
        if r and r[0] and r[0].strip() != ""
    ]

    return data, headers, items

sheet_data, headers, items_list = load_data(sheet)

# -----------------------------
# MODE SELECTION SCREEN
# -----------------------------
if "mode" not in st.session_state:
    st.session_state.mode = None

if st.session_state.mode is None:

    st.markdown("## Select Stock Type")

    c1, c2 = st.columns(2)

    if c1.button("📦 Daily Stock"):
        st.session_state.mode = "daily"
        st.rerun()

    if c2.button("📊 Weekly Stock"):
        st.session_state.mode = "weekly"
        st.rerun()

    if st.button("⬅ Back to Dashboard"):
        st.switch_page("pages/staff_dashboard.py")
        st.stop()

    st.stop()

mode = st.session_state.mode

# -----------------------------
# FILTER ITEMS
# -----------------------------
filtered_items = items_list[:99] if mode == "daily" else items_list[99:]

st.info(f"Mode: {mode.upper()} | Items: {len(filtered_items)}")

# -----------------------------
# BACK BUTTON (INSIDE PAGE)
# -----------------------------
if st.button("⬅ Back"):
    st.session_state.mode = None
    st.session_state.review_mode = False
    st.session_state.draft_data = {}
    st.switch_page("pages/staff_dashboard.py")
    st.stop()

# -----------------------------
# DATE
# -----------------------------
date = st.date_input("Select Date")
date_str = str(date)

# -----------------------------
# SESSION STORAGE
# -----------------------------
if "draft_data" not in st.session_state:
    st.session_state.draft_data = {}

if "review_mode" not in st.session_state:
    st.session_state.review_mode = False

# -----------------------------
# INPUT (STRICT MANUAL)
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
                placeholder="Enter quantity (required)",
                key=f"{mode}_{item}"
            )

            inputs[item] = value.strip() if value.strip() != "" else None

# -----------------------------
# REVIEW STEP
# -----------------------------
if st.button("🔍 Review Stock"):

    missing = [k for k, v in inputs.items() if v is None]

    if missing:
        st.error("🚨 Missing Inputs Found")

        for m in missing[:20]:
            st.warning(f"Fill: {m}")

        st.stop()

    st.session_state.draft_data = inputs
    st.session_state.review_mode = True

# -----------------------------
# REVIEW SCREEN
# -----------------------------
if st.session_state.review_mode:

    st.markdown("## 🟡 Pending Review (Not Saved Yet)")

    for k, v in st.session_state.draft_data.items():
        st.write(f"{k} → {v}")

    st.warning("⚠️ Data stored locally only")

    # -----------------------------
    # FINAL SUBMIT
    # -----------------------------
    if st.button("✅ Final Submit"):

        try:
            sheet_data, headers, items_list = load_data(sheet)

            if date_str in headers:
                col_index = headers.index(date_str) + 1
            else:
                col_index = len(headers) + 1
                sheet.update_cell(1, col_index, date_str)
                headers.append(date_str)

            updates = []

            for item, qty in st.session_state.draft_data.items():

                if not item or item.strip() == "":
                    continue

                if item not in items_list:
                    continue

                row = items_list.index(item) + 2

                master_value = sheet.cell(row, 1).value
                if not master_value:
                    continue

                cell = gspread.utils.rowcol_to_a1(row, col_index)

                updates.append({
                    "range": cell,
                    "values": [[qty]]
                })

            if updates:
                sheet.batch_update(updates)

            success_toast("Stock Submitted Successfully")

            time.sleep(4)

            st.session_state.draft_data = {}
            st.session_state.review_mode = False
            st.session_state.mode = None

            st.rerun()

        except Exception as e:
            st.error(f"API Error: {e}")
