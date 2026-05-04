import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from background import set_background

# -----------------------------
# BACKGROUND + UI
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
    f"{branch} - Stock Management System</h1>",
    unsafe_allow_html=True
)

# -----------------------------
# GOOGLE SHEETS AUTH
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

if "sheet_id" not in st.session_state or "tab_name" not in st.session_state:
    st.error("No branch selected")
    st.stop()

sheet = client.open_by_key(st.session_state.sheet_id).worksheet(st.session_state.tab_name)

# -----------------------------
# LOAD DATA (IGNORE EMPTY ROWS SAFELY)
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

    if c1.button("📦 Daily Stock (0–99)"):
        st.session_state.mode = "daily"
        st.rerun()

    if c2.button("📊 Weekly Stock (100+)"):
        st.session_state.mode = "weekly"
        st.rerun()

    st.stop()

mode = st.session_state.mode

# -----------------------------
# FILTER ITEMS
# -----------------------------
if mode == "daily":
    filtered_items = items_list[:99]
else:
    filtered_items = items_list[99:]

st.info(f"Mode: {mode.upper()} | Items: {len(filtered_items)}")

# -----------------------------
# DATE
# -----------------------------
date = st.date_input("Select Date")
date_str = str(date)

# -----------------------------
# INPUT SECTION (NO DEFAULTS)
# -----------------------------
st.markdown("## Enter Stock Manually (No Defaults Allowed)")

search = st.text_input("Search Item")

if search:
    filtered_items = [
        i for i in filtered_items if search.lower() in i.lower()
    ]

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
# STEP 1: REVIEW
# -----------------------------
if st.button("🔍 Review Stock"):

    missing = [k for k, v in inputs.items() if v is None]

    if missing:
        st.error("Missing values detected!")
        for m in missing:
            st.warning(f"Enter value for: {m}")
        st.stop()

    st.session_state.pending = inputs
    st.session_state.review = True

# -----------------------------
# STEP 2: PENDING LIST
# -----------------------------
if st.session_state.get("review"):

    st.markdown("## 🟡 Pending Review List (NOT SAVED YET)")

    for k, v in st.session_state.pending.items():
        st.write(f"{k} → {v}")

    st.warning("⚠️ Data is NOT saved to Google Sheets yet.")

    # -----------------------------
    # FINAL SUBMIT
    # -----------------------------
    if st.button("✅ Final Submit to Google Sheet"):

        try:
            sheet_data, headers, items_list = load_data(sheet)

            col_index = headers.index(date_str) if date_str in headers else len(headers)

            if date_str not in headers:
                sheet.update_cell(1, col_index + 1, date_str)
                headers.append(date_str)

            updates = []

            for item, qty in st.session_state.pending.items():

                # -----------------------------
                # IGNORE EMPTY / FUTURE ROWS
                # -----------------------------
                if not item or item.strip() == "":
                    continue

                if item not in items_list:
                    continue

                row = items_list.index(item) + 2

                master_value = sheet.cell(row, 1).value

                if not master_value or master_value.strip() == "":
                    continue

                cell = gspread.utils.rowcol_to_a1(row, col_index + 1)

                updates.append({
                    "range": cell,
                    "values": [[qty]]
                })

            if updates:
                sheet.batch_update(updates)
                st.success(f"✅ {len(updates)} items successfully saved")

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
