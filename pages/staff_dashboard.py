import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from background import set_background

# -----------------------------
# Background & UI Setup
# -----------------------------
set_background("barthomepage.jpg")
st.set_page_config(layout="wide")
st.title("BART")
st.markdown("## Staff Dashboard")
st.write("## Kindly choose your Branch Name")

# Hide Streamlit default UI
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}
.block-container {padding:0 !important; margin:0 auto !important; max-width: 100% !important;}
body {
    background-size: cover !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Google Sheets Setup (Master Branch Sheet)
# -----------------------------
creds_dict = JSON.loads(st.secrets["GOOGLE_CREDS_JSON"])
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
@st.cache_data
def load_branches():
    try:
        sheet = client.open("MASTERBRANCHSHEET").sheet1
        return sheet.get_all_records()
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("MASTERBRANCHSHEET not found. Make sure the service account has access and the sheet name is correct.")
        st.stop()

branch_data = load_branches()
branches = [f"{b['BranchCode']} - {b['BranchName']}" for b in branch_data]

# -----------------------------
# Branch Selection Dropdown
# -----------------------------
if 'selected_branch' not in st.session_state:
    st.session_state.selected_branch = "-- Select Branch --"

st.session_state.selected_branch = st.selectbox(
    "Select Branch",
    ["-- Select Branch --"] + branches,
    index=branches.index(st.session_state.selected_branch) + 1
    if st.session_state.selected_branch != "-- Select Branch --" else 0
)
selected_branch = st.session_state.selected_branch

# -----------------------------
# Buttons visible only after branch selection
# -----------------------------
if selected_branch != "-- Select Branch --":
    branch_info = next(b for b in branch_data if f"{b['BranchCode']} - {b['BranchName']}" == selected_branch)
    
    st.write(f"### Selected Branch: {selected_branch}")
    
    # All buttons in a single horizontal row
    col1, col2, col3, col4, col5 = st.columns(5, gap="medium")
    
    btn_daily_stock = col1.button("📦 Daily Stock Consumption")
    btn_daily_sales = col2.button("💰 Daily Sales Report")
    btn_new_stock = col3.button("🆕 New Stock Report")
    btn_stock_view = col4.button("🔍 Stock View")
    btn_sales_view = col5.button("📊 Daily Sales View")
    
    # Button actions
    if btn_daily_stock:
        st.session_state.sheet_id = branch_info['SheetID']
        st.session_state.selected_branch = selected_branch
        st.session_state.tab_name = "Stocks"
        st.switch_page("pages/stock_consumption.py")

    if btn_daily_sales:
        st.session_state.sheet_id = branch_info['SheetID']
        st.session_state.selected_branch = selected_branch
        st.session_state.tab_name = "Sales"
        st.switch_page("pages/daily_sales.py")

    if btn_new_stock:
        st.session_state.sheet_id = branch_info['SheetID']
        st.session_state.selected_branch = selected_branch
        st.session_state.tab_name = "NewStocks"
        st.switch_page("pages/new_stock.py")

    if btn_stock_view:
        if branch_info.get('SheetID'):
            try:
                branch_file = client.open_by_key(branch_info['SheetID'])
                stock_sheet = branch_file.worksheet("Stocks")
                stock_data = stock_sheet.get_all_records()
            except Exception as e:
                st.error(f"Failed to load stock data: {e}")
            else:
                with st.expander("Stock Items (expand to view)", expanded=True):
                    st.dataframe(stock_data, use_container_width=True, height=600)
        else:
            st.error("No SheetID found for this branch.")

    if btn_sales_view:
        if branch_info.get('SheetID'):
            try:
                branch_file = client.open_by_key(branch_info['SheetID'])
                sales_sheet = branch_file.worksheet("Sales")
                sales_data = sales_sheet.get_all_records()
            except Exception as e:
                st.error(f"Failed to load sales data: {e}")
            else:
                with st.expander("Daily Sales (expand to view)", expanded=True):
                    st.dataframe(sales_data, use_container_width=True, height=600)
        else:
            st.error("No SheetID found for this branch.")

# Optional Back Button
if st.button("⬅ Back"):
    st.switch_page("app.py")
