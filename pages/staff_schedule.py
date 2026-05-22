import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. SETUP GOOGLE SHEETS
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

st.set_page_config(page_title="Staff Schedule", layout="wide")
st.title("📅 Staff Schedule View")

# 2. FUNCTION TO LOAD DATA
@st.cache_data(ttl=60)
def get_schedule():
    # Make sure 'Schedules' tab exists in your MASTERBRANCHSHEET
    sheet = client.open("MASTERBRANCHSHEET").worksheet("Schedules")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# 3. DISPLAY DATA
try:
    df = get_schedule()
    
    # Simple search/filter
    branch_search = st.selectbox("Select Branch to View", ["All"] + list(df['BranchName'].unique()))
    
    if branch_search != "All":
        filtered_df = df[df['BranchName'] == branch_search]
    else:
        filtered_df = df
        
    st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"Error loading schedule: {e}")
    st.info("Ensure your 'MASTERBRANCHSHEET' has a tab named 'Schedules' with the correct headers.")
