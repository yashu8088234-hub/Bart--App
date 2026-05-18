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
# LOAD COLUMN A (UNCHANGED LOGIC)
# -----------------------------
def load_column_a(ws):
    data = ws.get_all_values()
    return [row[0].strip() for row in data if row and row[0].strip()]

items_list = load_column_a(sheet)

# -----------------------------
# ONLY ADDITION: LOAD COLUMN C (UMO)
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
# MODE SELECT
# -----------------------------
if st.session_state.page == "mode_select":

    st.session_state.show_success = False

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
st.markdown("## Enter Stock")

inputs = {}

with st.form("stock_form", clear_on_submit=False):

    for i in range(0, len(filtered_items), 4):
        cols = st.columns(4)

        for j, col in enumerate(cols):
            if i + j < len(filtered_items):

                item = filtered_items[i + j]

                # ONLY UI ADDITION (NO LOGIC CHANGE)
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
# REVIEW SECTION
# -----------------------------
if st.session_state.review_mode:

    st.markdown('<div id="review_section"></div>', unsafe_allow_html=True)

    st.markdown("## Review")

    for k, v in st.session_state.draft_data.items():
        st.write(f"{k} → {v}")

    if st.button("✅ Submit"):
        st.session_state.proceed_submit = True

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
# SUCCESS SCREEN
# -----------------------------
if st.session_state.show_success:

    st.markdown("""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100vh;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    ">
        <div style="
            background: white;
            padding: 50px;
            border-radius: 20px;
            text-align: center;
            width: 500px;
            box-shadow: 0px 10px 30px rgba(0,0,0,0.3);
        ">
            <div style="font-size: 90px; color: #00c853;">✔</div>
            <div style="font-size: 36px; font-weight: 900;">SUBMITTED</div>
            <div style="margin-top:10px; color: gray;">
                Stock saved successfully
            </div>
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
    st.session_state.submitted = False
    st.session_state.tx_id = None

    st.switch_page("pages/staff_dashboard.py")



make this 

# Stock System UI/UX Upgrade Report

## Overview

This report summarizes the UI/UX improvements made to the Streamlit-based Stock System application. The backend logic, including Google Sheets integration, email notification system, and submission workflow, remains unchanged. Only the user interface and user experience have been enhanced.

---

## 1. UI/UX Design Improvements

### 1.1 Visual Design Upgrade

* Implemented **glassmorphism design system**
* Added translucent cards with blur effects
* Improved background layering for a modern dashboard feel
* Enhanced shadows and rounded corners for depth

### 1.2 Typography & Layout

* Clear visual hierarchy (Title → Info → Form → Review → Success)
* Improved spacing and padding for readability
* Center-aligned header with professional styling
* Better section grouping using card-based layout

### 1.3 Color & Theming

* Soft gradient background maintained
* Red accent used for branding (Stock System title)
* Blue highlights for key metrics
* Neutral white cards for content separation

---

## 2. UX (User Experience) Improvements

### 2.1 Workflow Clarity

* Step-based flow:

  1. Entry
  2. Review
  3. Submit
* Clear visual indication of current stage

### 2.2 Form Experience

* Grid-based input layout (4 columns)
* Compact and structured item entry
* UMO (Unit of Measure) displayed beside item names
* Input validation before review

### 2.3 Review Experience

* Clean review cards for each item
* Easy edit vs submit decision flow
* Reduced cognitive load during verification

### 2.4 Feedback System

* Loading spinner during submission
* Success modal overlay after submission
* Toast notification with transaction ID
* Smooth transition between steps

---

## 3. Functional Integrity (No Logic Changes)

The following systems remain unchanged:

* Google Sheets data read/write logic
* Email notification system (SMTP)
* Transaction ID generation
* Session state management
* Stock categorization (Daily / Weekly)
* Sheet column indexing logic

---

## 4. Outcome

The system now provides:

* More modern and professional dashboard appearance
* Improved usability and readability
* Better guided workflow for staff users
* Enhanced feedback and confirmation system
* Cleaner and more structured stock entry process

---

## Conclusion

The upgrade successfully improves UI/UX without modifying core backend functionality, ensuring stability while significantly enhancing user interaction and visual quality.import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import uuid
from background import set_background
from gspread import Cell

import smtplib
from email.mime.text import MIMEText

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
# LOAD COLUMN A (UNCHANGED LOGIC)
# -----------------------------
def load_column_a(ws):
    data = ws.get_all_values()
    return [row[0].strip() for row in data if row and row[0].strip()]

items_list = load_column_a(sheet)

# -----------------------------
# ONLY ADDITION: LOAD COLUMN C (UMO)
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
# MODE SELECT
# -----------------------------
if st.session_state.page == "mode_select":

    st.session_state.show_success = False

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
st.markdown("## Enter Stock")

inputs = {}

with st.form("stock_form", clear_on_submit=False):

    for i in range(0, len(filtered_items), 4):
        cols = st.columns(4)

        for j, col in enumerate(cols):
            if i + j < len(filtered_items):

                item = filtered_items[i + j]

                # ONLY UI ADDITION (NO LOGIC CHANGE)
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
# REVIEW SECTION
# -----------------------------
if st.session_state.review_mode:

    st.markdown('<div id="review_section"></div>', unsafe_allow_html=True)

    st.markdown("## Review")

    for k, v in st.session_state.draft_data.items():
        st.write(f"{k} → {v}")

    if st.button("✅ Submit"):
        st.session_state.proceed_submit = True

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
# SUCCESS SCREEN
# -----------------------------
if st.session_state.show_success:

    st.markdown("""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100vh;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    ">
        <div style="
            background: white;
            padding: 50px;
            border-radius: 20px;
            text-align: center;
            width: 500px;
            box-shadow: 0px 10px 30px rgba(0,0,0,0.3);
        ">
            <div style="font-size: 90px; color: #00c853;">✔</div>
            <div style="font-size: 36px; font-weight: 900;">SUBMITTED</div>
            <div style="margin-top:10px; color: gray;">
                Stock saved successfully
            </div>
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
    st.session_state.submitted = False
    st.session_state.tx_id = None

    st.switch_page("pages/staff_dashboard.py")


