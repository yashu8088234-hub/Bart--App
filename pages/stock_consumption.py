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
# MODE SELECTION
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
# INIT SESSION STORAGE
# -----------------------------
if "draft_data" not in st.session_state:
    st.session_state.draft_data = {}

if "review_mode" not in st.session_state:
    st.session_state.review_mode = False

# -----------------------------
# INPUT (STRICT MANUAL ONLY)
# -----------------------------
st.markdown("## Enter Stock (Manual Only - No Defaults)")

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

    st.warning("⚠️ Data is stored locally only")

    # -----------------------------
    # FINAL SUBMIT
    # -----------------------------
    if st.button("✅ Final Submit"):

        try:
            sheet_data, headers, items_list = load_data(sheet)

            # COLUMN SETUP
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

            # SINGLE API CALL ONLY
            if updates:
                sheet.batch_update(updates)

            # -----------------------------
            # SUCCESS SCREEN
            # -----------------------------
            st.markdown("""
                <div style='text-align:center;padding:40px;'>
                    <div style='font-size:90px;color:green;'>✔</div>
                    <h2 style='color:green;'>Stock Submitted Successfully</h2>
                    <p>Redirecting to main page...</p>
                </div>
            """, unsafe_allow_html=True)

            # RESET
            st.session_state.draft_data = {}
            st.session_state.review_mode = False

            time.sleep(4)

            st.session_state.mode = None
            st.rerun()

        except Exception as e:
            st.error(f"API Error: {e}")

# -----------------------------
# BACK BUTTON
# -----------------------------
if st.button("⬅ Back"):
    st.session_state.mode = None
    st.rerun()
