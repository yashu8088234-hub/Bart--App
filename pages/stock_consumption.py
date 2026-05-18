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
# UI SETUP (BACKGROUND + CSS)
# -----------------------------
set_background("barthomepage.jpg")
st.set_page_config(page_title="Stock System", layout="wide")

st.markdown("""
<style>

/* 🌈 Background */
.stApp {
    background: radial-gradient(circle at top left, #e0f2fe, #eef2ff, #f8fafc);
}

/* 🧊 Glass effect */
.glass {
    background: rgba(255, 255, 255, 0.25);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.35);
    box-shadow: 0 10px 40px rgba(0,0,0,0.08);
    padding: 20px;
}

/* 🧠 Title */
h1 {
    font-weight: 800 !important;
    letter-spacing: 1px;
    text-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

/* 🧷 Buttons */
div.stButton > button {
    height: 52px;
    font-size: 17px;
    border-radius: 14px;
    background: rgba(255,255,255,0.35);
    border: 1px solid rgba(255,255,255,0.4);
    backdrop-filter: blur(10px);
    transition: all 0.25s ease-in-out;
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
}

div.stButton > button:hover {
    transform: translateY(-2px) scale(1.02);
    background: rgba(255,255,255,0.55);
}

/* ✍️ Inputs */
input {
    border-radius: 12px !important;
    background: rgba(255,255,255,0.4) !important;
    border: 1px solid rgba(255,255,255,0.4) !important;
}

/* 📦 Layout spacing */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
}

/* 🧾 Headings */
h2 {
    font-weight: 700;
    color: #1e293b;
}

/* 🪶 Alerts */
.stAlert {
    border-radius: 12px;
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
st.session_state.setdefault("show_success", False)
st.session_state.setdefault("submitted", False)
st.session_state.setdefault("tx_id", None)

st.session_state.setdefault("scroll_to_review", False)
st.session_state.setdefault("proceed_submit", False)

# -----------------------------
# TITLE (GLASS HEADER)
# -----------------------------
branch = st.session_state.get("selected_branch", "Branch")

st.markdown(f"""
<div class="glass" style="text-align:center;margin-bottom:20px;">
    <h1 style="color:red;margin:0;">
        {branch} - Stock System
    </h1>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# SHEET CHECK
# -----------------------------
sheet_id = st.session_state.get("sheet_id")
tab_name = st.session_state.get("tab_name")

if not sheet_id or not tab_name:
    st.error("Session expired.")

    if st.button("⬅ Back to Staff Dashboard"):
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

items_list = load_column_a(sheet)

def load_column_c(ws):
    data = ws.get_all_values()
    return [row[2].strip() if len(row) >= 3 and row[2] else "" for row in data[1:]]

umo_list = load_column_c(sheet)

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
    st.error("❌ DAILY ITEM or WEEKLY ITEM not found")
    st.stop()

# -----------------------------
# MODE SELECT (GLASS UI)
# -----------------------------
if st.session_state.page == "mode_select":

    st.session_state.show_success = False

    st.markdown('<div class="glass">', unsafe_allow_html=True)
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

    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("⬅ Back to Staff"):
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
    st.session_state.mode = None
    st.rerun()

# -----------------------------
# DATE
# -----------------------------
date = st.date_input("Select Date")
date_str = str(date)

# -----------------------------
# INPUT FORM
# -----------------------------
st.markdown("""
<div class="glass">
    <h2>Enter Stock</h2>
</div>
""", unsafe_allow_html=True)

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
                    placeholder=f"Enter qty for {item}",
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
# REVIEW SECTION (GLASS UI)
# -----------------------------
if st.session_state.review_mode:

    st.markdown('<div class="glass">', unsafe_allow_html=True)

    st.markdown("## Review")

    for k, v in st.session_state.draft_data.items():
        st.markdown(f"""
        <div style="
            padding:8px 12px;
            margin:6px 0;
            border-radius:10px;
            background:rgba(255,255,255,0.4);
            display:flex;
            justify-content:space-between;
        ">
            <strong>{k}</strong>
            <span>{v}</span>
        </div>
        """, unsafe_allow_html=True)

    if st.button("✅ Submit"):
        st.session_state.proceed_submit = True

    st.markdown('</div>', unsafe_allow_html=True)

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

            # EMAIL (unchanged)
            report = f"""
Stock Submission Report

Submitted By: System Auto Entry
Time: {submission_time}
Transaction ID: {st.session_state.tx_id}
Branch: {st.session_state.get('selected_branch')}
Mode: {st.session_state.mode}

STATUS: STOCK SUBMITTED SUCCESSFULLY
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
            st.session_state.submitted = True

        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")

# -----------------------------
# SUCCESS SCREEN (GLASS OVERLAY)
# -----------------------------
if st.session_state.show_success:

    st.markdown("""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100vh;
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    ">
        <div style="
            background: rgba(255,255,255,0.85);
            padding: 60px;
            border-radius: 24px;
            text-align: center;
            width: 420px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.25);
            backdrop-filter: blur(12px);
        ">
            <div style="font-size: 90px;">✅</div>
            <div style="font-size: 34px; font-weight: 800;">SUBMITTED</div>
            <div style="margin-top:10px; color: #64748b;">
                Stock saved successfully
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.toast(f"✔ Submitted | TX: {st.session_state.tx_id}", icon="✨")

    time.sleep(3)

    st.session_state.page = "mode_select"
    st.session_state.mode = None
    st.session_state.review_mode = False
    st.session_state.draft_data = {}
    st.session_state.show_success = False
    st.session_state.submitted = False
    st.session_state.tx_id = None

    st.switch_page("pages/staff_dashboard.py")
