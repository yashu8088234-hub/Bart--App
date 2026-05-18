import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import uuid
from background import set_background
from gspread import Cell

import smtplib
from email.mime.text import MIMEText

# -----------------------------
# UI SETUP (UNCHANGED LOGIC)
# -----------------------------
set_background("barthomepage.jpg")
st.set_page_config(page_title="Stock System", layout="wide")

# -----------------------------
# MODERN UI THEME (GLASSMORPHISM)
# -----------------------------
st.markdown("""
<style>

/* ===== GLOBAL THEME ===== */
.stApp {
    background: linear-gradient(135deg, #e8efff, #f7f9ff);
    font-family: 'Segoe UI', sans-serif;
}

/* Hide Streamlit UI */
#MainMenu, footer, header {visibility:hidden;}
[data-testid="stSidebar"] {display:none;}
.block-container {padding: 2rem 3rem !important; max-width: 100% !important;}

/* ===== GLASS CARD ===== */
.glass {
    background: rgba(255, 255, 255, 0.55);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 18px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.08);
    border: 1px solid rgba(255,255,255,0.4);
    margin-bottom: 20px;
}

/* ===== TITLE ===== */
h1 {
    font-size: 38px !important;
    font-weight: 800 !important;
    letter-spacing: 0.5px;
}

/* ===== BUTTONS ===== */
div.stButton > button {
    height: 52px;
    font-size: 16px;
    border-radius: 12px;
    border: none;
    background: linear-gradient(135deg, #4a6cf7, #6a8dff);
    color: white;
    font-weight: 600;
    transition: all 0.25s ease-in-out;
    box-shadow: 0 6px 18px rgba(74,108,247,0.25);
}

div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(74,108,247,0.35);
}

/* ===== INPUT FIELDS ===== */
div[data-baseweb="input"] {
    border-radius: 10px !important;
}

input {
    border-radius: 10px !important;
    padding: 10px !important;
}

/* ===== INFO BOX ===== */
[data-testid="stAlert"] {
    border-radius: 12px;
}

/* ===== HEADERS ===== */
h2 {
    font-weight: 700;
    margin-top: 10px;
}

/* ===== SUCCESS MODAL ===== */
.success-box {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(15px);
    border-radius: 20px;
    padding: 40px;
    text-align: center;
    box-shadow: 0 20px 50px rgba(0,0,0,0.2);
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION INIT (UNCHANGED)
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "mode_select"

st.session_state.setdefault("mode", None)
st.session_state.setdefault("review_mode", False)
st.session_state.setdefault("draft_data", {})
st.session_state.setdefault("show_success", False)
st.session_state.setdefault("submitted", False)
st.session_state.setdefault("tx_id", None)
st.session_state.setdefault("scroll_to_review", False)
st.session_state.setdefault("proceed_submit", False)

# -----------------------------
# SCROLL FUNCTION (UNCHANGED)
# -----------------------------
def scroll_to_review():
    st.markdown("""
        <script>
            const el = document.getElementById("review_section");
            if (el) el.scrollIntoView({behavior: "smooth"});
        </script>
    """, unsafe_allow_html=True)

# -----------------------------
# TITLE (ENHANCED VISUAL ONLY)
# -----------------------------
branch = st.session_state.get("selected_branch", "Branch")

st.markdown(f"""
<div class="glass">
    <h1 style="text-align:center; color:#1f2d5a;">
        {branch} - Stock System
    </h1>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# SHEET CHECK (UNCHANGED LOGIC)
# -----------------------------
sheet_id = st.session_state.get("sheet_id")
tab_name = st.session_state.get("tab_name")

if not sheet_id or not tab_name:
    st.error("Session expired.")
    if st.button("⬅ Back to Staff Dashboard"):
        st.switch_page("pages/staff_dashboard.py")
    st.stop()

# -----------------------------
# GOOGLE SHEETS AUTH (UNCHANGED)
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
# DATA LOAD (UNCHANGED)
# -----------------------------
def load_column_a(ws):
    data = ws.get_all_values()
    return [row[0].strip() for row in data if row and row[0].strip()]

items_list = load_column_a(sheet)

def load_column_c(ws):
    data = ws.get_all_values()
    return [row[2].strip() if len(row) >= 3 and row[2] else "" for row in data[1:]]

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
# MODE SELECT (UI UPGRADE ONLY)
# -----------------------------
if st.session_state.page == "mode_select":

    st.session_state.show_success = False

    st.markdown("""
    <div class="glass">
        <h2>Select Mode</h2>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    if c1.button("📦 Daily Stock"):
        st.session_state.mode = "daily"
        st.session_state.page = "stock_entry"
        st.rerun()

    if c2.button("📊 Weekly Stock"):
        st.session_state.mode = "weekly"
        st.session_state.page = "stock_entry"
        st.rerun()

    if st.button("⬅ Back to Staff"):
        st.switch_page("pages/staff_dashboard.py")

    st.stop()

# -----------------------------
# STOCK ENTRY (UI WRAPPED)
# -----------------------------
mode = st.session_state.mode

if mode == "daily":
    filtered_items = items_list[daily_start + 1 : weekly_start]
else:
    filtered_items = items_list[weekly_start + 1 :]

st.markdown(f"""
<div class="glass">
    <h3>Mode: {mode.upper()} | Items: {len(filtered_items)}</h3>
</div>
""", unsafe_allow_html=True)

if st.button("⬅ Back"):
    st.session_state.page = "mode_select"
    st.session_state.mode = None
    st.rerun()

date = st.date_input("Select Date")
date_str = str(date)

# -----------------------------
# FORM (GLASS UI ONLY)
# -----------------------------
st.markdown('<div class="glass"><h2>Enter Stock</h2></div>', unsafe_allow_html=True)

inputs = {}

with st.form("stock_form", clear_on_submit=False):

    for i in range(0, len(filtered_items), 4):
        cols = st.columns(4)

        for j, col in enumerate(cols):
            if i + j < len(filtered_items):

                item = filtered_items[i + j]
                umo = umo_list[i + j] if i + j < len(umo_list) else ""

                label = f"{item} [{umo}]"

                value = col.text_input(
                    label,
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
            st.session_state.scroll_to_review = True
            st.rerun()

# -----------------------------
# REVIEW (UI ONLY)
# -----------------------------
if st.session_state.review_mode:

    st.markdown('<div id="review_section"></div>', unsafe_allow_html=True)

    st.markdown('<div class="glass"><h2>Review</h2></div>', unsafe_allow_html=True)

    for k, v in st.session_state.draft_data.items():
        st.markdown(f"""
        <div class="glass">
            <b>{k}</b> → {v}
        </div>
        """, unsafe_allow_html=True)

    if st.button("✅ Submit"):
        st.session_state.proceed_submit = True

# -----------------------------
# AUTO SCROLL (UNCHANGED)
# -----------------------------
if st.session_state.scroll_to_review:
    scroll_to_review()
    st.session_state.scroll_to_review = False

# -----------------------------
# FINAL SUBMIT (UNCHANGED LOGIC)
# -----------------------------
if st.session_state.proceed_submit:

    try:
        with st.spinner("Saving stock..."):

            sheet_data = sheet.get_all_values()
            headers = sheet_data[0]

            submission_time = time.strftime("%Y-%m-%d %H:%M:%S")

            if not st.session_state.tx_id:
                st.session_state.tx_id = str(uuid.uuid4())[:8]

            if date_str in headers:
                col_index = headers.index(date_str) + 1
            else:
                col_index = len(headers) + 1
                sheet.update_cell(1, col_index, date_str)

            col_values = sheet.col_values(1)
            item_to_row = {val.strip(): i + 1 for i, val in enumerate(col_values)}

            cells = []

            for item, qty in st.session_state.draft_data.items():
                row = item_to_row.get(item)
                if row:
                    cells.append(Cell(row=row, col=col_index, value=qty))

            if cells:
                sheet.update_cells(cells, value_input_option="USER_ENTERED")

            # EMAIL (UNCHANGED)
            report = f"""
Stock Submission Report

Time: {submission_time}
Transaction ID: {st.session_state.tx_id}
Branch: {st.session_state.get('selected_branch')}
Mode: {st.session_state.mode}
"""

            sender_email = "yashu8088234@gmail.com"
            sender_password = st.secrets["EMAIL_PASSWORD"]

            msg = MIMEText(report)
            msg["Subject"] = "New Stock Submission"
            msg["From"] = sender_email
            msg["To"] = "yash2002anitha@gmail.com"

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, "yash2002anitha@gmail.com", msg.as_string())
            server.quit()

            st.session_state.proceed_submit = False
            st.session_state.review_mode = False
            st.session_state.show_success = True

        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")

# -----------------------------
# SUCCESS SCREEN (GLASS UI)
# -----------------------------
if st.session_state.show_success:

    st.markdown("""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100vh;
        background: rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    ">
        <div class="success-box">
            <div style="font-size:80px; color:#2ecc71;">✔</div>
            <h1>SUBMITTED</h1>
            <p>Stock saved successfully</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.toast(f"Submitted ✔ | TX: {st.session_state.tx_id}", icon="✔")

    time.sleep(3)

    st.session_state.page = "mode_select"
    st.session_state.mode = None
    st.session_state.review_mode = False
    st.session_state.draft_data = {}
    st.session_state.show_success = False
    st.session_state.tx_id = None

    st.switch_page("pages/staff_dashboard.py")
