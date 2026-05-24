import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# Page config
st.set_page_config(layout="wide", page_title="Staff Management")

# ----------------- CONFIG & DATA LOAD -----------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

if "branch_info" not in st.session_state:
    st.warning("Session expired. Please re-login.")
    if st.button("Return Home"): st.switch_page("app.py")
    st.stop()

branch_info = st.session_state.branch_info
sheet = client.open_by_key(branch_info["SheetID"])

# Fetch Data
@st.cache_data(ttl=60)
def fetch_schedule():
    ws = sheet.worksheet("StaffSchedule") # Ensure this tab exists
    return pd.DataFrame(ws.get_all_records())

df = fetch_schedule()

# ----------------- UI: SEARCH & HEADER -----------------
st.title(f"📅 Staff Schedule: {branch_info['BranchName']}")
search_query = st.text_input("🔍 Search staff by name or shift...", "")

# Apply filter
filtered_df = df
if search_query:
    filtered_df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

# ----------------- INTERACTIVE EDITOR -----------------
st.subheader("Edit Schedule & Credentials")
st.info("💡 Edit cells below. Changes will be saved to the database on click.")

edited_df = st.data_editor(
    filtered_df,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "MOBILE NUMBER": st.column_config.NumberColumn("Mobile", format="%d"),
        "SHIFT": st.column_config.SelectboxColumn("Shift Type", options=["MORNING", "EVENING"]),
    }
)

# ----------------- SAVE LOGIC -----------------
if st.button("💾 Save Changes to Master Sheet", type="primary"):
    try:
        ws = sheet.worksheet("StaffSchedule")
        ws.clear()
        ws.update([edited_df.columns.values.tolist()] + edited_df.values.tolist())
        st.success("✅ Schedule updated!")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error saving: {e}")

# ----------------- QUICK REFERENCES -----------------
with st.expander("🔗 Reference Links & Credentials"):
    st.write("Keep your branch-specific URLs and login notes here.")
    # You can link this to a separate "References" sheet if preferred
    cred_notes = st.text_area("Internal Notes / Credential Links", height=150)
    if st.button("Update Notes"):
        st.success("Notes saved locally (Connect to DB to persist).")

if st.button("⬅ Back to Dashboard"):
    st.switch_page("app.py")
