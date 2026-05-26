import streamlit as st
import pandas as pd
import gspread
import time
import re
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from st_aggrid import AgGrid

# 1. SETUP PAGE SETTINGS
st.set_page_config(layout="wide", page_title="BART Master Schedule")

# 2. AUTHENTICATION CHECK
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login first.")
    st.stop()

# 3. CONNECT TO GOOGLE SHEETS
if "gspread_client" not in st.session_state:
    creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    st.session_state.gspread_client = gspread.authorize(creds)

master_sheet = st.session_state.gspread_client.open_by_key("1UtHUn7miqYzaP-NnrwMR_5wnSgLnaYPRQX2c4I7_9B0")

# 4. CONFIGURATION
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
ROLE_OPTIONS = ["Team-Member", "Acting_Team_Leader", "Team_Leader", "Acting_Supervisor", "Supervisor", "Branch_Manager"]

# 5. DATA LOADING FUNCTION
def load_data(force_reload=False):
    if force_reload or st.session_state.get("cached_df") is None:
        try:
            ws = master_sheet.worksheet("StaffSchedule")
            data = ws.get_all_records()
            df = pd.DataFrame(data) if data else pd.DataFrame()
            if not df.empty:
                # Rename columns containing day names to standard Day names
                new_cols = {col: day for col in df.columns for day in DAYS if day in col}
                df = df.rename(columns=new_cols)
            st.session_state.cached_df = df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.session_state.cached_df = pd.DataFrame(columns=["Branch", "Name", "Role"] + DAYS + ["Over-Time"])
    return st.session_state.cached_df

# 6. SHIFT CUSTOMIZER MODAL
@st.dialog("⏰ Set Custom Time")
def custom_time_dialog(row_idx, row_name, day_name):
    st.write(f"Configure shift for **{row_name}** on **{day_name}**")
    c1, c2 = st.columns(2)
    with c1: 
        sh = st.selectbox("Start", list(range(1, 13)), index=8)
        sap = st.selectbox("AM/PM", ["AM", "PM"], key="s")
    with c2: 
        eh = st.selectbox("End", list(range(1, 13)), index=5)
        eap = st.selectbox("AM/PM", ["AM", "PM"], index=1, key="e")
    
    if st.button("Apply"):
        st.session_state.shift_buffer[f"{row_idx}_{day_name}"] = f"{sh} {sap} - {eh} {eap}"
        st.rerun()

# 7. MAIN UI
st.title(f"🏢 Schedule: {st.session_state.selected_branch}")
sel_date = st.date_input("📅 Select Date", value=datetime.today())
edit_mode = st.toggle("Edit Mode Only")

df = load_data()
df = df[df["Branch"] == st.session_state.selected_branch].copy()

# 8. EDIT MODE (WITH STABILITY FIXES)
if edit_mode:
    # Fixes: Ensure column names are unique and strings
    df.columns = df.columns.astype(str)
    df = df.loc[:, ~df.columns.duplicated()]
    df_for_editor = df.astype(str)

    edited_df = st.data_editor(df_for_editor, num_rows="dynamic", use_container_width=True)
    
    # Custom Time Trigger
    for i, row in edited_df.iterrows():
        for d in DAYS:
            if row.get(d) == "➕ Custom Time": custom_time_dialog(i, row['Name'], d)

    if st.button("🚀 Submit to Master Sheet"):
        ws = master_sheet.worksheet("StaffSchedule")
        others = st.session_state.cached_df[st.session_state.cached_df["Branch"] != st.session_state.selected_branch]
        final = pd.concat([others, edited_df], ignore_index=True)
        ws.update([final.columns.tolist()] + final.fillna("").values.tolist())
        
        # FULL SCREEN SUCCESS OVERLAY
        placeholder = st.empty()
        with placeholder.container():
            st.markdown("""<div style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:9999; display:flex; justify-content:center; align-items:center; color:white;">
                <h1>✅ Submitted Successfully!</h1></div>""", unsafe_allow_html=True)
            time.sleep(2)
        placeholder.empty()
        st.session_state.cached_df = final
        st.rerun()

# 9. VIEW MODE
else:
    if st.button("🔄 Refresh Data"):
        load_data(force_reload=True)
        st.rerun()
    AgGrid(df, use_container_width=True)

if st.button("⬅ Back"): st.switch_page("app.py")
