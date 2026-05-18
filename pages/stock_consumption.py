import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import uuid
from datetime import datetime, timedelta
from gspread import Cell
import smtplib
from email.mime.text import MIMEText
from background import set_background

# ---------------- UI ----------------
set_background("barthomepage.jpg")
st.set_page_config(page_title="Stock Wizard", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stSidebar"] {display:none;}

.step-bar {
    display:flex;
    justify-content:space-between;
    margin:20px 0;
    padding:10px;
    background:#fff;
    border-radius:12px;
    box-shadow:0 2px 10px rgba(0,0,0,0.08);
}

.step {
    flex:1;
    text-align:center;
    font-weight:600;
    padding:10px;
    border-radius:10px;
}

.active {background:#2563eb;color:white;}
.done {background:#22c55e;color:white;}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION ----------------
st.session_state.setdefault("step", 1)
st.session_state.setdefault("form_data", {})
st.session_state.setdefault("draft_data", {})
st.session_state.setdefault("mode", None)
st.session_state.setdefault("tx_id", None)

# ---------------- STEP HEADER ----------------
def step_header():
    step = st.session_state.step
    st.markdown(f"""
    <div class="step-bar">
        <div class="step {'active' if step==1 else 'done' if step>1 else ''}">1. Entry</div>
        <div class="step {'active' if step==2 else 'done' if step>2 else ''}">2. Review</div>
        <div class="step {'active' if step==3 else ''}">3. Submit</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------- GOOGLE SHEETS ----------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]

@st.cache_resource
def client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

gc = client()

@st.cache_resource
def sheet():
    return gc.open_by_key(st.session_state.sheet_id).worksheet(st.session_state.tab_name)

ws = sheet()

# ---------------- DATA ----------------
def load_items(ws):
    data = ws.get_all_values()
    return [r[0].strip() for r in data if r and r[0]]

items = load_items(ws)

daily_start = next(i for i,v in enumerate(items) if v=="DAILY ITEM")
weekly_start = next(i for i,v in enumerate(items) if v=="WEEKLY ITEM")

mode = st.session_state.mode or "daily"
filtered = items[daily_start+1:weekly_start] if mode=="daily" else items[weekly_start+1:]

umo = [""] * len(filtered)

# ---------------- HEADER ----------------
step_header()

st.title("Stock Checkout Wizard")

# ---------------- STEP 1 ----------------
if st.session_state.step == 1:

    st.subheader("Step 1: Enter Stock")

    inputs = st.session_state.form_data

    with st.form("step1"):

        for i in range(len(filtered)):
            inputs[filtered[i]] = st.text_input(
                filtered[i],
                value=inputs.get(filtered[i], "")
            )

        if st.form_submit_button("Next → Review"):
            st.session_state.form_data = inputs
            st.session_state.draft_data = inputs
            st.session_state.step = 2
            st.stop()

# ---------------- STEP 2 ----------------
elif st.session_state.step == 2:

    st.subheader("Step 2: Review")

    for k,v in st.session_state.draft_data.items():
        st.write(f"{k} → {v}")

    c1,c2 = st.columns(2)

    if c1.button("← Back"):
        st.session_state.step = 1
        st.stop()

    if c2.button("Confirm → Submit"):
        st.session_state.step = 3
        st.stop()

# ---------------- STEP 3 ----------------
elif st.session_state.step == 3:

    try:
        with st.spinner("Submitting stock..."):

            tx = str(uuid.uuid4())[:8]
            st.session_state.tx_id = tx

            # ---------------- SAVE DELAY SIM ----------------
            time.sleep(1)

            # ---------------- POPUP ----------------
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
                    border-radius:20px;
                    text-align:center;">
                    <div style="font-size:60px;">✔</div>
                    <h2>Stock Submitted</h2>
                    <p>Transaction ID: <b>{tx}</b></p>
                    <p>Redirecting to dashboard...</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ---------------- WAIT 4 SECONDS ----------------
            time.sleep(4)

            # ---------------- RESET ----------------
            st.session_state.step = 1
            st.session_state.form_data = {}
            st.session_state.draft_data = {}
            st.session_state.tx_id = None

            # ---------------- REDIRECT ----------------
            st.switch_page("pages/staff_dashboard.py")

    except Exception as e:
        st.error(f"Error: {e}")
