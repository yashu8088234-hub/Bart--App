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
# UI SETUP (RESTORED ORIGINAL COLOR THEME)
# -----------------------------
st.set_page_config(page_title="Stock System", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stSidebar"] {display:none;}
.block-container {padding:0 !important; max-width:100% !important;}

/* ✔ RESTORED YOUR ORIGINAL LOOK */
.stApp {
    background: linear-gradient(135deg,#eef2f7,#d6e4ff);
}

/* BUTTON STYLE */
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

/* INPUT BOX STYLE (clean modern) */
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
# STEP BAR (SAME LOGIC)
# -----------------------------
def step_bar(step):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin:6px 0;">
        <b>{"✔ Entry" if step>1 else "1 Entry"}</b>
        ───▶
        <b>{"● Review" if step==2 else "2 Review"}</b>
        ───▶
        <b>{"○ Submit" if step<3 else "3 Submit"}</b>
    </div>
    """, unsafe_allow_html=True)

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
    st.stop()

# -----------------------------
# GOOGLE SHEETS AUTH
# -----------------------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]

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

    st.stop()

# -----------------------------
# BACK BUTTON + STEP BAR
# -----------------------------
c1, c2 = st.columns([1, 3])

with c1:
    if st.button("⬅ Back"):
        st.session_state.page = "mode_select"
        st.session_state.step = 1
        st.session_state.form_data = {}
        st.rerun()

with c2:
    step_bar(st.session_state.step)

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

        submitted = st.form_submit_button("➡ Continue to Review")

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

    for k,v in st.session_state.draft_data.items():
        st.write(f"{k} → {v}")

    c1,c2 = st.columns(2)

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
        with st.spinner("Saving..."):

            tx = str(uuid.uuid4())[:8]

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

            st.switch_page("pages/staff_dashboard.py")

    except Exception as e:
        st.error(str(e))
