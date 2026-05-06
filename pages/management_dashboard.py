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

# ---------------- SESSION SAFETY ----------------
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

# ---------------- SHEET CACHE ----------------
@st.cache_resource
def get_sheets(branches):
    cache = {}
    for b in branches:
        cache[b["SheetID"]] = client.open_by_key(b["SheetID"])
    return cache

sheet_cache = get_sheets(branches)

# ---------------- FETCH FUNCTION ----------------
def fetch_branch(branch):
    try:
        file = sheet_cache[branch["SheetID"]]
        ws = file.worksheet("Stocks")
        return branch["BranchName"], ws.get_all_values()
    except:
        return branch["BranchName"], None

# ---------------- FETCH DATA ----------------
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

    current_type = None  # 🔥 detects DAILY / WEEKLY section

    for _, row in df.iterrows():

        first_cell = str(row[item_col]).strip()

        # ---------------- SECTION DETECTION ----------------
        if "DAILY ITEM" in first_cell.upper():
            current_type = "Daily"
            continue

        if "WEEKLY ITEM" in first_cell.upper():
            current_type = "Weekly"
            continue

        # skip empty rows
        if first_cell == "" or first_cell.lower() == "nan":
            continue

        item = first_cell
        qty = row.get(chosen_col, "")

        if item not in all_items:
            all_items[item] = {bn: 0 for bn in branch_names}
            all_items[item]["Type"] = current_type

        try:
            all_items[item][branch_name] = float(qty) if qty != "" else 0
        except:
            all_items[item][branch_name] = 0

# ---------------- BUILD DATAFRAME ----------------
rows = []

for i, (item, values) in enumerate(all_items.items(), start=1):
    row = {
        "Sl No": i,
        "Item Name": item,
        "Type": values.get("Type", "Unknown")
    }
    row.update(values)
    rows.append(row)

df = pd.DataFrame(rows)

# ---------------- SEARCH ----------------
search = st.text_input("🔎 Search Item")

if search and not df.empty:
    df = df[df["Item Name"].str.contains(search, case=False, na=False)]

# ---------------- DISPLAY ----------------
st.subheader("📊 Stock Data")

if df.empty:
    st.warning("No stock data found for selected date")
else:

    tab1, tab2, tab3 = st.tabs(["🟢 Daily Items", "🔵 Weekly Items", "⚪ Unclassified"])

    with tab1:
        st.dataframe(df[df["Type"] == "Daily"].drop(columns=["Type"]),
                     use_container_width=True)

    with tab2:
        st.dataframe(df[df["Type"] == "Weekly"].drop(columns=["Type"]),
                     use_container_width=True)

    with tab3:
        st.dataframe(df[df["Type"] == "Unknown"].drop(columns=["Type"]),
                     use_container_width=True)

# ---------------- DOWNLOAD ----------------
if not df.empty:
    st.download_button(
        "📥 Download CSV",
        df.to_csv(index=False),
        "stock_report.csv",
        "text/csv"
    )
