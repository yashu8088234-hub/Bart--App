import streamlit as st
import pandas as pd

st.set_page_config(page_title="Staff Schedule", layout="wide")

st.title("📅 Weekly Staff Schedule")

# 1. Fetch data from your Master Sheet
@st.cache_data(ttl=60)
def get_schedule():
    # Use gspread to pull the 'Schedules' tab from your Master Sheet
    # df = ... 
    return df

df = get_schedule()

# 2. Filter by Date (Crucial for the manager)
selected_date = st.date_input("Select Date")
filtered_df = df[df['Date'] == str(selected_date)]

# 3. Interactive Editor
# This allows the manager to change a staff member if someone is sick
updated_df = st.data_editor(filtered_df, use_container_width=True, hide_index=True)

if st.button("Save Changes"):
    # Code to push updated_df back to Google Sheets
    st.success("Schedule Updated!")
