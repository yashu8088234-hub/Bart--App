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
# UI SETUP (LIGHT GLASS)
# -----------------------------
set_background("barthomepage.jpg")
st.set_page_config(page_title="Stock System", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stSidebar"] {display:none;}

.block-container {
    padding: 10px !important;
    max-width: 100% !important;
}

/* Background */
.stApp {
    background: radial-gradient(circle at top left, #e0eafc, #cfdef3, #d6e4ff);
}

/* Compact glass pill (NOT heavy cards) */
.glass-pill {
    background: rgba(255,255,255,0.25);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 12px;
    padding: 8px 12px;
    backdrop-filter: blur(8px);
    font-size: 13px;
    display: flex;
    justify-content: space-between;
    margin: 6px 0;
}

/* Buttons (medium size) */
.stButton > button {
    height: 44px;
    font-size: 15px;
    border-radius: 10px;
    background: rgba(255,255,255,0.35);
    border: 1px solid rgba(255,255,255,0.25);
    backdrop-filter: blur(8px);
}

.stButton > button:hover {
    background: rgba(255,255,255,0.55);
    transform: translateY(-1px);
}

/* Inputs cleaner */
input, textarea {
    background: rgba(255,255,255,0.55) !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION INIT
# -----------------------------
if "step" not in st.session_state:
    st.session_state.step = 1

st.session_state.setdefault("mode", None)
st.session_state.setdefault("draft_data", {})
st.session_state.setdefault("tx_id", None)
st.session_state.setdefault("proceed_submit", False)
st.session_state.setdefault("show_success", False)

# -----------------------------
# TITLE
# -----------------------------
branch = st.session_state.get("selected_branch", "Branch")

st.markdown(
    f"<h2 style='text-align:center;color:#1f2937;'>{branch} - Stock System</h2>",
    unsafe_allow_html=True
)

# -----------------------------
# SHEET CHECK
# -----------------------------
sheet_id = st.session_state.get("sheet_id")
tab_name = st.session_state.get("tab_name")

if not sheet_id or not tab_name:
    st.error("Session expired.")
    st.stop()

# -----------------------------
# GOOGLE SHEETS
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
    st.error("Missing DAILY/WEEKLY markers")
    st.stop()

# -----------------------------
# MODE + ITEMS
# -----------------------------
mode = st.session_state.mode

if mode == "daily":
    filtered_items = items_list[daily_start + 1 : weekly_start]
else:
    filtered_items = items_list[weekly_start + 1 :]

mode_label = "DAILY" if mode == "daily" else "WEEKLY"

# -----------------------------
# STEP HEADER
# -----------------------------
st.markdown(f"### Step {st.session_state.step}/3")

st.markdown(f"""
<div class="glass-pill">
    <div>📊 {mode_label if mode else "NO MODE SELECTED"}</div>
    <div>{len(filtered_items)} Items</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# STEP 1
# -----------------------------
if st.session_state.step == 1:

    st.markdown("#### Select Mode")

    c1, c2 = st.columns(2)

    if c1.button("📦 Daily Stock"):
        st.session_state.mode = "daily"
        st.session_state.step = 2
        st.rerun()

    if c2.button("📊 Weekly Stock"):
        st.session_state.mode = "weekly"
        st.session_state.step = 2
        st.rerun()

    st.stop()

# -----------------------------
# DATE
# -----------------------------
date = st.date_input("Date")
date_str = str(date)

# -----------------------------
# STEP 2
# -----------------------------
if st.session_state.step == 2:

    st.markdown("#### Enter Stock")

    inputs = {}

    with st.form("stock_form"):

        for i in range(0, len(filtered_items), 4):
            cols = st.columns(4)

            for j, col in enumerate(cols):
                if i + j < len(filtered_items):

                    item = filtered_items[i + j]
                    umo = umo_list[i + j] if i + j < len(umo_list) else ""

                    value = col.text_input(
                        f"{item} [{umo}]",
                        key=f"{mode}_{item}"
                    )

                    inputs[item] = value.strip() if value.strip() else None

        submitted = st.form_submit_button("Review")

    if submitted:
        if any(v is None for v in inputs.values()):
            st.error("Missing values")
        else:
            st.session_state.draft_data = inputs
            st.session_state.step = 3
            st.rerun()

    if st.button("⬅ Back"):
        st.session_state.step = 1
        st.rerun()

# -----------------------------
# STEP 3
# -----------------------------
if st.session_state.step == 3:

    st.markdown("#### Review")

    for k, v in st.session_state.draft_data.items():
        st.write(f"• {k}: {v}")

    c1, c2 = st.columns(2)

    if c1.button("Edit"):
        st.session_state.step = 2
        st.rerun()

    if c2.button("Submit"):
        st.session_state.proceed_submit = True

# -----------------------------
# FINAL SUBMIT
# -----------------------------
if st.session_state.proceed_submit:

    try:
        with st.spinner("Saving..."):

            sheet_data = sheet.get_all_values()
            headers = sheet_data[0]

            if not st.session_state.tx_id:
                st.session_state.tx_id = str(uuid.uuid4())[:8]

            if date_str in headers:
                col_index = headers.index(date_str) + 1
            else:
                col_index = len(headers) + 1
                sheet.update_cell(1, col_index, date_str)

            col_values = sheet.col_values(1)
            item_to_row = {v.strip(): i + 1 for i, v in enumerate(col_values)}

            cells = []

            for item, qty in st.session_state.draft_data.items():
                row = item_to_row.get(item)
                if row:
                    cells.append(Cell(row=row, col=col_index, value=qty))

            if cells:
                sheet.update_cells(cells, value_input_option="USER_ENTERED")

            # EMAIL
            msg = MIMEText(f"""
Stock Submitted
TX: {st.session_state.tx_id}
Branch: {st.session_state.get('selected_branch')}
Mode: {mode_label}
""")

            msg["Subject"] = "Stock Update"
            msg["From"] = st.secrets["EMAIL_USER"]
            msg["To"] = st.secrets["EMAIL_TO"]

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(st.secrets["EMAIL_USER"], st.secrets["EMAIL_PASSWORD"])
            server.sendmail(msg["From"], msg["To"], msg.as_string())
            server.quit()

            st.session_state.show_success = True
            st.session_state.proceed_submit = False
            st.session_state.step = 1
            st.session_state.draft_data = {}

        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")

# -----------------------------
# SUCCESS SCREEN
# -----------------------------
if st.session_state.show_success:

    st.success("Stock submitted successfully ✔")
    st.toast("Submitted ✔", icon="✔")

    time.sleep(1)

    st.session_state.show_success = False
    st.rerun()
