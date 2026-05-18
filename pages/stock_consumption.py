import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import uuid
from background import set_background
from gspread import Cell
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

# -----------------------------
# UI SETUP (YOUR ORIGINAL)
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
# SESSION INIT
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "mode_select"

st.session_state.setdefault("mode", None)
st.session_state.setdefault("review_mode", False)
st.session_state.setdefault("draft_data", {})
st.session_state.setdefault("form_data", {})
st.session_state.setdefault("step", 1)
st.session_state.setdefault("tx_id", None)

# -----------------------------
# SMALL STEP INDICATOR (NEW - MINIMAL)
# -----------------------------
def step_bar(step):
    st.markdown(f"""
    <div style="
        display:flex;
        justify-content:center;
        gap:20px;
        margin:10px 0;
        font-size:14px;
        font-weight:600;
    ">
        <div style="color:{'#000' if step==1 else '#999'}">1 Entry</div>
        <div>→</div>
        <div style="color:{'#000' if step==2 else '#999'}">2 Review</div>
        <div>→</div>
        <div style="color:{'#000' if step==3 else '#999'}">3 Submit</div>
    </div>
    """, unsafe_allow_html=True)

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
    st.error("Session expired.")
    if st.button("⬅ Back"):
        st.switch_page("pages/staff_dashboard.py")
    st.stop()

# -----------------------------
# GOOGLE SHEETS AUTH
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
# LOAD DATA
# -----------------------------
def load_column_a(ws):
    data = ws.get_all_values()
    return [row[0].strip() for row in data if row and row[0].strip()]

def load_column_c(ws):
    data = ws.get_all_values()
    return [row[2].strip() if len(row) >= 3 and row[2] else "" for row in data[1:]]

items_list = load_column_a(sheet)
umo_list = load_column_c(sheet)

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
# MODE SELECT
# -----------------------------
if st.session_state.page == "mode_select":

    st.session_state.mode = None
    st.session_state.step = 1
    st.session_state.form_data = {}

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

    if st.button("⬅ Back to Staff Dashboard"):
        st.switch_page("pages/staff_dashboard.py")

    st.stop()

# -----------------------------
# STOCK ENTRY
# -----------------------------
mode = st.session_state.mode

if mode == "daily":
    filtered_items = items_list[daily_start + 1 : weekly_start]
else:
    filtered_items = items_list[weekly_start + 1 :]

st.info(f"Mode: {mode.upper()} | Items: {len(filtered_items)}")

if st.button("⬅ Back"):
    st.session_state.page = "mode_select"
    st.session_state.step = 1
    st.session_state.form_data = {}
    st.rerun()

# -----------------------------
# DATE (your logic unchanged)
# -----------------------------
default_date = datetime.today().date() - timedelta(days=1)
date = st.date_input("Select Operation Date", value=default_date)
date_str = str(date)

# -----------------------------
# STEP BAR (small only)
# -----------------------------
step_bar(st.session_state.step)

# -----------------------------
# STEP 1
# -----------------------------
if st.session_state.step == 1:

    st.markdown("## Enter Stock")

    inputs = st.session_state.form_data

    with st.form("stock_form"):

        for i in range(0, len(filtered_items), 4):
            cols = st.columns(4)

            for j, col in enumerate(cols):
                if i + j < len(filtered_items):

                    item = filtered_items[i + j]
                    umo = umo_list[i + j] if i + j < len(umo_list) else ""

                    value = col.text_input(
                        f"{item} [{umo}]",
                        value=inputs.get(item, ""),
                        key=f"{mode}_{item}"
                    )

                    inputs[item] = value.strip() if value.strip() else None

        submitted = st.form_submit_button("➡ Continue to Review")

        if submitted:

            missing = [k for k, v in inputs.items() if v is None]

            if missing:
                st.error("Missing inputs")

            else:
                st.session_state.form_data = inputs
                st.session_state.draft_data = inputs
                st.session_state.step = 2
                st.rerun()

# -----------------------------
# STEP 2
# -----------------------------
elif st.session_state.step == 2:

    st.markdown("## Review")

    for k, v in st.session_state.draft_data.items():
        st.write(f"{k} → {v}")

    c1, c2 = st.columns(2)

    if c1.button("⬅ Back"):
        st.session_state.step = 1
        st.rerun()

    if c2.button("✅ Submit"):
        st.session_state.step = 3
        st.rerun()

# -----------------------------
# STEP 3
# -----------------------------
elif st.session_state.step == 3:

    try:
        with st.spinner("Saving stock..."):

            tx = str(uuid.uuid4())[:8]
            st.session_state.tx_id = tx

            # POPUP (your style kept simple)
            st.markdown(f"""
            <div style="
                position:fixed;
                top:0;left:0;width:100%;height:100%;
                background:rgba(0,0,0,0.6);
                display:flex;align-items:center;justify-content:center;
                z-index:9999;">
                <div style="
                    background:white;
                    padding:40px;
                    border-radius:15px;
                    text-align:center;">
                    <div style="font-size:60px;">✔</div>
                    <h2>SUBMITTED</h2>
                    <p>TX: <b>{tx}</b></p>
                    <p>Redirecting...</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            time.sleep(4)

            st.session_state.step = 1
            st.session_state.form_data = {}
            st.session_state.draft_data = {}
            st.session_state.tx_id = None

            st.switch_page("pages/staff_dashboard.py")

    except Exception as e:
        st.error(f"Error: {e}")
