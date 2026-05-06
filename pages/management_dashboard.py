import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime
import time

st.set_page_config(layout="wide", page_title="Stock Overview")

st.title("📦 BART - Stock Management (All Branches)")

# ---------------- GOOGLE AUTH ----------------
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

# ---------------- MASTER SHEET ----------------
@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    return sheet.get_all_records()

branches = load_branches()

branch_names = [b["BranchName"] for b in branches]

# ---------------- GLOBAL RATE CONTROL ----------------
if "last_fetch_time" not in st.session_state:
    st.session_state.last_fetch_time = 0

# ---------------- DATE PICKER ----------------
selected_date = st.date_input("📅 Select Stock Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

all_items = {}

# ---------------- REFRESH BUTTON (SAFE) ----------------
if st.button("🔄 Refresh Data"):

    now = time.time()

    # 🔴 prevent API spam (VERY IMPORTANT)
    if now - st.session_state.last_fetch_time < 5:
        st.warning("Please wait a few seconds before refreshing again.")
        st.stop()

    st.session_state.last_fetch_time = now

    st.cache_data.clear()
    st.rerun()

# ---------------- SAFE FETCH FUNCTION ----------------
@st.cache_data(ttl=600)
def get_all_sheets(branches):
    results = []
    sheet_cache = {}

    for branch in branches:
        sheet_id = branch["SheetID"]
        branch_name = branch["BranchName"]

        try:
            # cache opened spreadsheet (important optimization)
            if sheet_id not in sheet_cache:
                sheet_cache[sheet_id] = client.open_by_key(sheet_id)

            file = sheet_cache[sheet_id]
            ws = file.worksheet("Stocks")

            raw = ws.get_all_values()

            results.append((branch_name, raw))

            # small throttle to avoid burst
            time.sleep(0.3)

        except Exception as e:
            results.append((branch_name, None))
            st.error(f"{branch_name} error: {e}")

    return results

# ---------------- FETCH DATA ----------------
all_data = get_all_sheets(branches)

# ---------------- PROCESS DATA ----------------
for branch_name, raw in all_data:

    if not raw or len(raw) < 2:
        continue

    headers = raw[0]
    rows = raw[1:]

    df = pd.DataFrame(rows, columns=headers)

    item_col = headers[0]

    if selected_date_str not in headers:
        continue

    chosen_col = selected_date_str

    for _, row in df.iterrows():
        item = str(row[item_col]).strip()
        qty = row.get(chosen_col, "")

        if item not in all_items:
            all_items[item] = {bn: 0 for bn in branch_names}

        try:
            all_items[item][branch_name] = float(qty) if qty != "" else 0
        except:
            all_items[item][branch_name] = 0

# ---------------- FINAL TABLE ----------------
rows = []
for i, (item, values) in enumerate(all_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
    rows.append(row)

df = pd.DataFrame(rows)

# ---------------- DISPLAY ----------------
st.subheader("📊 Stock Data")
st.dataframe(df, use_container_width=True)

# ---------------- LOW STOCK HIGHLIGHT ----------------
st.markdown("## ⚠️ Low Stock Highlight")

if df.empty:
    st.warning("No stock data found for selected date")
    st.stop()

def highlight_low(val):
    try:
        val = float(val)
        if val == 0:
            return "background-color: red; color: white;"
        elif val < 5:
            return "background-color: orange;"
    except:
        return ""
    return ""

valid_columns = [col for col in branch_names if col in df.columns]

styled_df = df.style.applymap(highlight_low, subset=valid_columns)

st.dataframe(styled_df, use_container_width=True)
