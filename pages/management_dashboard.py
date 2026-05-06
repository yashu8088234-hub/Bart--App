import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor

# ---------------- PAGE CONFIG ----------------
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

# ---------------- SESSION SAFETY FLAGS ----------------
if "last_fetch_time" not in st.session_state:
    st.session_state.last_fetch_time = 0

if "is_fetching" not in st.session_state:
    st.session_state.is_fetching = False

# ---------------- DATE PICKER ----------------
selected_date = st.date_input("📅 Select Stock Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

all_items = {}

# ---------------- REFRESH BUTTON ----------------
if st.button("🔄 Refresh Data"):
    now = time.time()

    if now - st.session_state.last_fetch_time < 5:
        st.warning("⏳ Please wait a few seconds before refreshing again.")
        st.stop()

    if st.session_state.is_fetching:
        st.warning("⏳ Data is already loading. Please wait...")
        st.stop()

    st.session_state.last_fetch_time = now
    st.cache_data.clear()
    st.rerun()

# ---------------- PRELOAD SHEETS ----------------
@st.cache_resource
def get_sheets(branches):
    cache = {}
    for b in branches:
        cache[b["SheetID"]] = client.open_by_key(b["SheetID"])
    return cache

sheet_cache = get_sheets(branches)

# ---------------- FETCH FUNCTION (PARALLEL) ----------------
def fetch_branch(branch):
    try:
        file = sheet_cache[branch["SheetID"]]
        ws = file.worksheet("Stocks")
        return branch["BranchName"], ws.get_all_values()
    except Exception as e:
        return branch["BranchName"], None

# ---------------- SAFE FETCH WRAPPER ----------------
try:
    st.session_state.is_fetching = True

    with ThreadPoolExecutor(max_workers=5) as executor:
        all_data = list(executor.map(fetch_branch, branches))

finally:
    st.session_state.is_fetching = False

# ---------------- PROCESS DATA ----------------
for branch_name, raw in all_data:

    if not raw or len(raw) < 2:
        continue

    headers = raw[0]
    rows = raw[1:]

    if selected_date_str not in headers:
        continue

    item_col = headers[0]
    chosen_col = selected_date_str

    df = pd.DataFrame(rows, columns=headers)

    for _, row in df.iterrows():
        item = str(row[item_col]).strip()
        qty = row.get(chosen_col, "")

        if item not in all_items:
            all_items[item] = {bn: 0 for bn in branch_names}

        try:
            all_items[item][branch_name] = float(qty) if qty != "" else 0
        except:
            all_items[item][branch_name] = 0

# ---------------- FINAL DATAFRAME ----------------
rows = []
for i, (item, values) in enumerate(all_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
    rows.append(row)

df = pd.DataFrame(rows)

# ---------------- DISPLAY ----------------
st.subheader("📊 Stock Data")

if df.empty:
    st.warning("No stock data found for selected date")
else:
    st.dataframe(df, use_container_width=True)

# ---------------- OPTIONAL: SEARCH ----------------
search = st.text_input("🔎 Search Item")
if search and not df.empty:
    df = df[df["Item Name"].str.contains(search, case=False, na=False)]
    st.dataframe(df, use_container_width=True)

# ---------------- DOWNLOAD ----------------
if not df.empty:
    st.download_button(
        "📥 Download CSV",
        df.to_csv(index=False),
        "stock_report.csv",
        "text/csv"
    )
