

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import uuid
from background import set_background
from gspread import Cell
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# -----------------------------
# PAGE SETUP
# -----------------------------
st.set_page_config(
    page_title="Stock System",
    layout="wide",
    initial_sidebar_state="collapsed"
)

set_background("barthomepage.jpg")

# -----------------------------
# ADVANCED UI/UX
# -----------------------------
st.markdown("""
<style>

#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stSidebar"] {display:none;}

.block-container{
    padding-top:1rem !important;
    padding-left:2rem !important;
    padding-right:2rem !important;
    max-width:100% !important;
}

.stApp{
    background:
        linear-gradient(135deg, rgba(238,242,247,0.92), rgba(214,228,255,0.92));
    backdrop-filter: blur(8px);
}

/* MAIN GLASS CARD */
.glass-card{
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(16px);
    border:1px solid rgba(255,255,255,0.4);
    border-radius:22px;
    padding:24px;
    margin-bottom:18px;
    box-shadow:0 10px 30px rgba(0,0,0,0.08);
}

/* HEADER */
.main-title{
    text-align:center;
    font-size:42px;
    font-weight:900;
    color:#ff2400;
    margin-bottom:8px;
    letter-spacing:0.5px;
}

.sub-title{
    text-align:center;
    color:#555;
    margin-bottom:20px;
    font-size:15px;
}

/* STEP BAR */
.step-wrap{
    display:flex;
    align-items:center;
    justify-content:center;
    gap:12px;
    margin:12px 0 22px 0;
    font-weight:700;
}

.step-box{
    padding:10px 18px;
    border-radius:12px;
    background:white;
    border:1px solid #dbe4ff;
    box-shadow:0 3px 10px rgba(0,0,0,0.04);
}

.active-step{
    background:linear-gradient(135deg,#1f4fff,#6a8dff);
    color:white;
    border:none;
}

/* BUTTONS */
div.stButton > button{
    width:100%;
    height:58px;
    border-radius:16px;
    border:none;
    font-size:17px;
    font-weight:700;
    background:white;
    color:#222;
    transition:0.25s;
    box-shadow:0 5px 16px rgba(0,0,0,0.08);
}

div.stButton > button:hover{
    transform:translateY(-2px);
    background:#f5f8ff;
    color:#1f4fff;
}

/* INPUTS */
div[data-baseweb="input"]{
    border-radius:14px !important;
    border:1px solid #d8e1ff !important;
    background:white !important;
    box-shadow:0 2px 10px rgba(0,0,0,0.03);
}

input{
    border-radius:14px !important;
    padding:12px !important;
    font-size:15px !important;
}

/* INFO STRIP */
.info-strip{
    background:white;
    border-radius:18px;
    padding:18px 24px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:18px;
    box-shadow:0 5px 20px rgba(0,0,0,0.05);
}

.info-title{
    color:#666;
    font-size:14px;
    margin-bottom:4px;
}

.info-value{
    font-size:20px;
    font-weight:800;
}

/* REVIEW CARD */
.review-row{
    background:white;
    border-radius:14px;
    padding:14px 18px;
    margin-bottom:10px;
    display:flex;
    justify-content:space-between;
    border:1px solid #edf1ff;
    box-shadow:0 2px 10px rgba(0,0,0,0.03);
}

/* SUCCESS MODAL */
.success-overlay{
    position:fixed;
    top:0;
    left:0;
    width:100%;
    height:100vh;
    background:rgba(0,0,0,0.65);
    display:flex;
    justify-content:center;
    align-items:center;
    z-index:9999;
}

.success-box{
    width:520px;
    background:white;
    border-radius:28px;
    padding:50px;
    text-align:center;
    box-shadow:0 20px 60px rgba(0,0,0,0.25);
    animation:pop 0.35s ease;
}

@keyframes pop{
    from{transform:scale(0.85);opacity:0;}
    to{transform:scale(1);opacity:1;}
}

.success-check{
    font-size:92px;
    color:#00c853;
}

.success-title{
    font-size:40px;
    font-weight:900;
    margin-top:10px;
}

.success-sub{
    color:#666;
    margin-top:8px;
    font-size:16px;
}

.tx-box{
    margin-top:18px;
    background:#f5f7ff;
    padding:14px;
    border-radius:14px;
    font-weight:700;
    color:#1f4fff;
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
# SCROLL FUNCTION
# -----------------------------
def scroll_to_review():
    st.markdown(
        """
        <script>
            const el = document.getElementById("review_section");
            if (el) {
                el.scrollIntoView({behavior: "smooth"});
            }
        </script>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# TITLE
# -----------------------------
branch = st.session_state.get("selected_branch", "Branch")

st.markdown(
    f"""
    <div class='glass-card'>
        <div class='main-title'>{branch} - Stock System</div>
        <div class='sub-title'>Smart Inventory Submission Dashboard</div>
    </div>
    """,
    unsafe_allow_html=True
)

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
# LOAD COLUMN A
# -----------------------------
def load_column_a(ws):
    data = ws.get_all_values()
    return [row[0].strip() for row in data if row and row[0].strip()]

items_list = load_column_a(sheet)

# -----------------------------
# LOAD COLUMN C (UMO)
# -----------------------------
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
# STEP BAR
# -----------------------------
def step_bar(step):

    one = "active-step" if step == 1 else ""
    two = "active-step" if step == 2 else ""
    three = "active-step" if step == 3 else ""

    st.markdown(f"""
    <div class='step-wrap'>
        <div class='step-box {one}'>1 Entry</div>
        ➜
        <div class='step-box {two}'>2 Review</div>
        ➜
        <div class='step-box {three}'>3 Submit</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# MODE SELECT
# -----------------------------
if st.session_state.page == "mode_select":

    st.session_state.show_success = False

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("## Select Stock Operation")

    c1, c2 = st.columns(2)

    if c1.button("📦 Daily Stock"):
        st.session_state.mode = "daily"
        st.session_state.page = "stock_entry"
        st.rerun()

    if c2.button("📊 Weekly Stock"):
        st.session_state.mode = "weekly"
        st.session_state.page = "stock_entry"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("⬅ Back to Staff Dashboard"):
        st.switch_page("pages/staff_dashboard.py")

    st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# -----------------------------
# STOCK ENTRY
# -----------------------------
mode = st.session_state.mode

if mode == "daily":
    filtered_items = items_list[daily_start + 1 : weekly_start]
else:
    filtered_items = items_list[weekly_start + 1 :]

# -----------------------------
# STEP STATUS
# -----------------------------
step = 1
if st.session_state.review_mode:
    step = 2
if st.session_state.proceed_submit:
    step = 3

step_bar(step)

# -----------------------------
# INFO STRIP
# -----------------------------
st.markdown(f"""
<div class='info-strip'>
    <div>
        <div class='info-title'>Current Mode</div>
        <div class='info-value' style='color:#ff2400;'>
            {mode.upper()}
        </div>
    </div>

    <div>
        <div class='info-title'>Total Items</div>
        <div class='info-value' style='color:#1f4fff;'>
            {len(filtered_items)}
        </div>
    </div>

    <div>
        <div class='info-title'>Submission Date</div>
        <div class='info-value' style='color:#444;'>
            {datetime.now().strftime('%d %b %Y')}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# BACK BUTTON
# -----------------------------
if st.button("⬅ Back"):
    st.session_state.page = "mode_select"
    st.session_state.mode = None
    st.rerun()

# -----------------------------
# DATE
# -----------------------------
default_date = datetime.today().date() - timedelta(days=1)

date = st.date_input(
    "Select Operation Date",
    value=default_date
)


date_str = str(date)

# -----------------------------
# INPUT FORM
# -----------------------------
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("## Enter Stock Quantities")

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

    st.markdown("<br>", unsafe_allow_html=True)

    submitted = st.form_submit_button("➡ Continue to Review")

    if submitted:

        missing = [k for k, v in inputs.items() if v is None]

        if missing:
            st.error("Please complete all stock quantities before proceeding.")
        else:
            st.session_state.draft_data = inputs
            st.session_state.review_mode = True
            st.session_state.scroll_to_review = True
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# REVIEW SECTION
# -----------------------------
if st.session_state.review_mode:

    st.markdown('<div id="review_section"></div>', unsafe_allow_html=True)

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("## Review Submission")

    for k, v in st.session_state.draft_data.items():
        st.markdown(
            f"""
            <div class='review-row'>
                <div><b>{k}</b></div>
                <div>{v}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    c1, c2 = st.columns(2)

    if c1.button("⬅ Edit Entries"):
        st.session_state.review_mode = False
        st.rerun()

    if c2.button("✅ Submit Stock"):
        st.session_state.proceed_submit = True

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# AUTO SCROLL
# -----------------------------
if st.session_state.scroll_to_review:
    scroll_to_review()
    st.session_state.scroll_to_review = False

# -----------------------------
# FINAL SUBMIT
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

            # ---------------- EMAIL ----------------
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
            msg["To"] = "Ramees@bartksa.com"

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, "Ramees@bartksa.com", msg.as_string())
            server.quit()

            st.session_state.proceed_submit = False
            st.session_state.review_mode = False
            st.session_state.show_success = True
            st.session_state.submitted = True

        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")

# -----------------------------
# SUCCESS SCREEN
# -----------------------------
if st.session_state.show_success:

    st.markdown(f"""
    <div class='success-overlay'>
        <div class='success-box'>
            <div class='success-check'>✔</div>
            <div class='success-title'>SUBMITTED</div>
            <div class='success-sub'>
                Stock saved successfully
            </div>

            <div class='tx-box'>
                Transaction ID: {st.session_state.tx_id}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.toast(
        f"Submitted Successfully ✔ | TX: {st.session_state.tx_id}",
        icon="✅"
    )

    time.sleep(3)

    st.session_state.page = "mode_select"
    st.session_state.mode = None
    st.session_state.review_mode = False
    st.session_state.draft_data = {}
    st.session_state.show_success = False
    st.session_state.submitted = False
    st.session_state.tx_id = None

    st.switch_page("pages/staff_dashboard.py")

UI/UX Upgrades Added
Visual Improvements
* Glassmorphism cards
* Premium shadows and rounded corners
* Modern spacing system
* Better typography hierarchy
* Professional dashboard feel
* Animated success modal
* Better input styling
* Enhanced buttons with hover effects
UX Improvements
* Cleaner review layout
* Better step indicator
* Smart information strip
* Improved spacing and readability
* More professional submission flow
* Better visual grouping
* Improved responsive layout
Logic Safety
* Google Sheets logic untouched
* Email sending untouched
* Data flow untouched
* Session logic untouched
* Submission structure untouched
* Existing navigation untouched
