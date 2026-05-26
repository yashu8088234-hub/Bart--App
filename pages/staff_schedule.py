import streamlit as st
import pandas as pd
import gspread
import time
import re
import streamlit.components.v1 as components
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from st_aggrid import AgGrid

st.set_page_config(layout="wide", page_title="BART Master Schedule")

# =========================
# AUTH & INIT
# =========================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠ Session expired. Please login again.")
    if st.button("⬅ Back to Staff Login"): st.switch_page("app.py")
    st.stop()

if "gspread_client" not in st.session_state:
    creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://googleapis.com/auth/drive"])
    st.session_state.gspread_client = gspread.authorize(creds)

master_sheet = st.session_state.gspread_client.open_by_key("1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0")

# =========================
# CONFIG & LOGIC
# =========================
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
SHIFT_OPTIONS = ["➕ Custom Time", "📴 Day Off"]
ROLE_OPTIONS = ["Team-Member", "Acting_Team_Leader", "Team_Leader", "Acting_Supervisor", "Supervisor", "Branch_Manager"]

def parse_hour(val):
    hour, ap = val.split()
    hour = int(hour)
    if ap == "PM" and hour != 12: hour += 12
    if ap == "AM" and hour == 12: hour = 0
    return hour

def calculate_hours(start, end):
    s, e = parse_hour(start), parse_hour(end)
    if e <= s: e += 24
    return e - s

def format_shift(start, end):
    hrs = calculate_hours(start, end)
    if hrs < 9: return None, hrs
    ot = max(0, hrs - 9)
    return (f"{start} - {end} (OT {ot}h)", hrs) if ot > 0 else (f"{start} - {end}", hrs)

def calculate_row_ot(row):
    total_ot = 0
    for day in DAYS:
        val = str(row.get(day, ""))
        match = re.search(r"\(OT\s+(\d+(?:\.\d+)?)\s*h\)", val)
        if match: total_ot += float(match.group(1))
    return f"{total_ot} hrs" if total_ot > 0 else "0 hrs"

# =========================
# DIALOGS
# =========================
@st.dialog("✅ Submission Successful")
def success_dialog(df_to_capture):
    st.success("Your schedule has been successfully submitted.")
    html_table = df_to_capture.to_html(classes="table", index=False)
    capture_html = f"""
    <div id="capture-area" style="padding: 20px; background: white; border: 2px solid #004a99; border-radius: 10px;">
        <h2 style="color: #004a99; font-family: sans-serif;">Weekly Staff Schedule</h2>
        {html_table}
        <style>
            .table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; }}
            .table td, .table th {{ padding: 8px; border: 1px solid #ddd; text-align: left; }}
            .table th {{ background-color: #f8f9fa; }}
        </style>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
        html2canvas(document.querySelector("#capture-area")).then(canvas => {{
            const imgData = canvas.toDataURL("image/png");
            document.getElementById("img-preview").src = imgData;
            document.getElementById("download-btn").href = imgData;
            document.getElementById("download-btn").style.display = "block";
        }});
    </script>
    <img id="img-preview" style="width: 100%; margin-top: 20px; border: 1px solid #ccc;"/>
    <a id="download-btn" download="Schedule.png" style="display:none; margin-top:10px; padding:10px; background:#28a745; color:white; text-align:center; border-radius:5px; text-decoration:none;">💾 Save Image</a>
    """
    components.html(capture_html, height=700)
    if st.button("Close"): st.rerun()

@st.dialog("⏰ Set Custom Time")
def custom_time_dialog(row_idx, row_name, day_name):
    # ... (Keep your existing custom_time_dialog logic)
    pass

@st.dialog("🚫 Submission Blocked")
def duplicate_submission_dialog():
    st.error("This week's schedule has already been submitted.")
    if st.button("Close"): st.rerun()

# =========================
# MAIN APP FLOW
# =========================
# ... (Keep your initialization and data loading logic)

if edit_mode:
    # ... (Keep your data_editor logic)
    if st.button("✅ Submit"):
        if not existing_week_data.empty:
            duplicate_submission_dialog()
        else:
            # Add your Google Sheets update logic here
            # Then call the dialog:
            success_dialog(edited_df)
else:
    # ... (Keep your standard AgGrid display logic)
