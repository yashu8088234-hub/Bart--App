import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import uuid
from gspread import Cell
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

# -----------------------------
# UI SETUP
# -----------------------------
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
    background: white;
    border: 1px solid #d0d7ff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

div.stButton > button:hover{
    background:#f5f7ff;
    border:1px solid #aab6ff;
}

input{
    border-radius:8px !important;
    border:1px solid #d0d7ff !important;
    padding:8px !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION INIT
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "mode_select"

st.session_state.setdefault("mode", None)
st.session_state.setdefault("step", 1)
st.session_state.setdefault("form_data", {})
st.session_state.setdefault("draft_data", {})
st.session_state.setdefault("tx_id", None)

# -----------------------------
# TITLE
# -----------------------------
branch = st.session_state.get("selected_branch", "Branch")

st.markdown(
    f"<h2 style='text-align:center;color:#FF2400;margin-bottom:10px;'>{branch} - Stock System</h2>",
    unsafe_allow_html=True
)

# -----------------------------
# SHEET CHECK
# -----------------------------
sheet_id = st.session_state.get("sheet_id")
tab_name = st.session_state.get("tab_name")

if not sheet_id or not tab_name:
    st.error("Session expired")
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
def client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

gc = client()

@st.cache_resource
def sheet():
    return gc.open_by_key(sheet_id).worksheet(tab_name)

ws = sheet()

# -----------------------------
# DATA
# -----------------------------
def load_items(ws):
    data = ws.get_all_values()
    return [r[0].strip() for r in data if r and r[0].strip()]

def load_umo(ws):
    data = ws.get_all_values()
    return [row[2].strip() if len(row) >= 3 else "" for row in data[1:]]

items = load_items(ws)
umo_list = load_umo(ws)

daily_start = next(i for i,v in enumerate(items) if v=="DAILY ITEM")
weekly_start = next(i for i,v in enumerate(items) if v=="WEEKLY ITEM")

mode = st.session_state.mode or "daily"
filtered = items[daily_start+1:weekly_start] if mode=="daily" else items[weekly_start+1:]

# -----------------------------
# MODE SELECT
# -----------------------------
if st.session_state.page == "mode_select":

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

    if st.button("⬅ Back to Dashboard"):
        st.switch_page("pages/staff_dashboard.py")

    st.stop()

# -----------------------------
# BACK + INFO
# -----------------------------
c1, c2 = st.columns([1, 3])

with c1:
    if st.button("⬅ Back to Mode Select"):
        st.session_state.page = "mode_select"
        st.session_state.step = 1
        st.session_state.form_data = {}
        st.rerun()

with c2:
    st.markdown(f"### Step {st.session_state.step}")

# -----------------------------
# DATE
# -----------------------------
default_date = datetime.today().date() - timedelta(days=1)
date = st.date_input("Select Operation Date", value=default_date)
date_str = str(date)

# -----------------------------
# STEP 1
# -----------------------------
if st.session_state.step == 1:

    st.markdown("## Enter Stock")

    inputs = st.session_state.form_data

    with st.form("stock_form"):

        for i in range(0, len(filtered), 4):
            cols = st.columns(4)

            for j, col in enumerate(cols):
                if i + j < len(filtered):

                    item = filtered[i + j]
                    umo = umo_list[i + j] if i + j < len(umo_list) else ""

                    inputs[item] = col.text_input(
                        f"{item} [{umo}]",
                        value=inputs.get(item, ""),
                        placeholder="Enter quantity"
                    )

        submitted = st.form_submit_button("➡ Continue")

        if submitted:
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
# STEP 3 (FIXED GOOGLE SHEETS LOGIC)
# -----------------------------
elif st.session_state.step == 3:

    try:
        with st.spinner("Saving..."):

            sheet_data = ws.get_all_values()
            headers = sheet_data[0]

            tx = str(uuid.uuid4())[:8]
            st.session_state.tx_id = tx

            submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # -----------------------------
            # FIND / CREATE DATE COLUMN
            # -----------------------------
            if date_str in headers:
                col_index = headers.index(date_str) + 1
            else:
                col_index = len(headers) + 1
                ws.update_cell(1, col_index, date_str)

            # -----------------------------
            # MAP ITEM → ROW
            # -----------------------------
            col_values = ws.col_values(1)
            item_to_row = {val.strip(): i + 1 for i, val in enumerate(col_values)}

            # -----------------------------
            # BUILD CELLS
            # -----------------------------
            cells = []

            for item, qty in st.session_state.draft_data.items():

                if qty is None or qty == "":
                    continue

                row = item_to_row.get(item)

                if row:
                    cells.append(Cell(row=row, col=col_index, value=qty))

            # -----------------------------
            # WRITE TO SHEET
            # -----------------------------
            if cells:
                ws.update_cells(cells, value_input_option="USER_ENTERED")

            # -----------------------------
            # EMAIL (UNCHANGED)
            # -----------------------------
            report = f"""
Stock Submission Report

Submitted By: System Auto Entry
Time: {submission_time}
Transaction ID: {tx}
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

            time.sleep(2)

            st.session_state.step = 1
            st.session_state.form_data = {}
            st.session_state.draft_data = {}

            st.switch_page("pages/staff_dashboard.py")

    except Exception as e:
        st.error(f"ERROR: {e}")import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import uuid
from gspread import Cell
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

# -----------------------------
# UI SETUP
# -----------------------------
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
    background: white;
    border: 1px solid #d0d7ff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

div.stButton > button:hover{
    background:#f5f7ff;
    border:1px solid #aab6ff;
}

input{
    border-radius:8px !important;
    border:1px solid #d0d7ff !important;
    padding:8px !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION INIT
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "mode_select"

st.session_state.setdefault("mode", None)
st.session_state.setdefault("step", 1)
st.session_state.setdefault("form_data", {})
st.session_state.setdefault("draft_data", {})
st.session_state.setdefault("tx_id", None)

# -----------------------------
# TITLE
# -----------------------------
branch = st.session_state.get("selected_branch", "Branch")

st.markdown(
    f"<h2 style='text-align:center;color:#FF2400;margin-bottom:10px;'>{branch} - Stock System</h2>",
    unsafe_allow_html=True
)

# -----------------------------
# SHEET CHECK
# -----------------------------
sheet_id = st.session_state.get("sheet_id")
tab_name = st.session_state.get("tab_name")

if not sheet_id or not tab_name:
    st.error("Session expired")
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
def client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

gc = client()

@st.cache_resource
def sheet():
    return gc.open_by_key(sheet_id).worksheet(tab_name)

ws = sheet()

# -----------------------------
# DATA
# -----------------------------
def load_items(ws):
    data = ws.get_all_values()
    return [r[0].strip() for r in data if r and r[0].strip()]

def load_umo(ws):
    data = ws.get_all_values()
    return [row[2].strip() if len(row) >= 3 else "" for row in data[1:]]

items = load_items(ws)
umo_list = load_umo(ws)

daily_start = next(i for i,v in enumerate(items) if v=="DAILY ITEM")
weekly_start = next(i for i,v in enumerate(items) if v=="WEEKLY ITEM")

mode = st.session_state.mode or "daily"
filtered = items[daily_start+1:weekly_start] if mode=="daily" else items[weekly_start+1:]

# -----------------------------
# MODE SELECT
# -----------------------------
if st.session_state.page == "mode_select":

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

    if st.button("⬅ Back to Dashboard"):
        st.switch_page("pages/staff_dashboard.py")

    st.stop()

# -----------------------------
# BACK + INFO
# -----------------------------
c1, c2 = st.columns([1, 3])

with c1:
    if st.button("⬅ Back to Mode Select"):
        st.session_state.page = "mode_select"
        st.session_state.step = 1
        st.session_state.form_data = {}
        st.rerun()

with c2:
    st.markdown(f"### Step {st.session_state.step}")

# -----------------------------
# DATE
# -----------------------------
default_date = datetime.today().date() - timedelta(days=1)
date = st.date_input("Select Operation Date", value=default_date)
date_str = str(date)

# -----------------------------
# STEP 1
# -----------------------------
if st.session_state.step == 1:

    st.markdown("## Enter Stock")

    inputs = st.session_state.form_data

    with st.form("stock_form"):

        for i in range(0, len(filtered), 4):
            cols = st.columns(4)

            for j, col in enumerate(cols):
                if i + j < len(filtered):

                    item = filtered[i + j]
                    umo = umo_list[i + j] if i + j < len(umo_list) else ""

                    inputs[item] = col.text_input(
                        f"{item} [{umo}]",
                        value=inputs.get(item, ""),
                        placeholder="Enter quantity"
                    )

        submitted = st.form_submit_button("➡ Continue")

        if submitted:
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
# STEP 3 (FIXED GOOGLE SHEETS LOGIC)
# -----------------------------
elif st.session_state.step == 3:

    try:
        with st.spinner("Saving..."):

            sheet_data = ws.get_all_values()
            headers = sheet_data[0]

            tx = str(uuid.uuid4())[:8]
            st.session_state.tx_id = tx

            submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # -----------------------------
            # FIND / CREATE DATE COLUMN
            # -----------------------------
            if date_str in headers:
                col_index = headers.index(date_str) + 1
            else:
                col_index = len(headers) + 1
                ws.update_cell(1, col_index, date_str)

            # -----------------------------
            # MAP ITEM → ROW
            # -----------------------------
            col_values = ws.col_values(1)
            item_to_row = {val.strip(): i + 1 for i, val in enumerate(col_values)}

            # -----------------------------
            # BUILD CELLS
            # -----------------------------
            cells = []

            for item, qty in st.session_state.draft_data.items():

                if qty is None or qty == "":
                    continue

                row = item_to_row.get(item)

                if row:
                    cells.append(Cell(row=row, col=col_index, value=qty))

            # -----------------------------
            # WRITE TO SHEET
            # -----------------------------
            if cells:
                ws.update_cells(cells, value_input_option="USER_ENTERED")

            # -----------------------------
            # EMAIL (UNCHANGED)
            # -----------------------------
            report = f"""
Stock Submission Report

Submitted By: System Auto Entry
Time: {submission_time}
Transaction ID: {tx}
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

            time.sleep(2)

            st.session_state.step = 1
            st.session_state.form_data = {}
            st.session_state.draft_data = {}

            st.switch_page("pages/staff_dashboard.py")

    except Exception as e:
        st.error(f"ERROR: {e}")
