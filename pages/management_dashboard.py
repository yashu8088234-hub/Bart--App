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
    data = sheet.get_all_records()

    cleaned = [
        b for b in data
        if b.get("SheetID") and b.get("BranchName")
    ]

    return cleaned

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

daily_items = {}
weekly_items = {}

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

# ---------------- SAFE SHEET LOADER ----------------
@st.cache_resource
def get_sheets(branches):

    cache = {}

    for b in branches:

        sheet_id = b.get("SheetID")

        if not sheet_id:
            continue

        try:
            cache[sheet_id] = client.open_by_key(sheet_id)

        except Exception:
            st.warning(f"⚠️ Failed loading {b.get('BranchName')}")

    return cache

sheet_cache = get_sheets(branches)

# ---------------- FETCH FUNCTION ----------------
def fetch_branch(branch):

    try:
        sheet_id = branch.get("SheetID")

        if not sheet_id or sheet_id not in sheet_cache:
            return branch["BranchName"], None

        file = sheet_cache[sheet_id]
        ws = file.worksheet("Stocks")

        return branch["BranchName"], ws.get_all_values()

    except Exception:
        return branch["BranchName"], None

# ---------------- FETCH DATA ----------------
try:
    st.session_state.is_fetching = True

    with ThreadPoolExecutor(max_workers=5) as executor:
        all_data = list(executor.map(fetch_branch, branches))

finally:
    st.session_state.is_fetching = False

# =========================================================
# 🔥 IMPORTANT FIX (CONNECT TO AI SYSTEM)
# =========================================================
st.session_state.all_data = all_data
st.session_state.branches = branches

# ---------------- PROCESS DATA ----------------
for branch_name, raw in all_data:

    if not raw or len(raw) < 2:
        continue

    headers = raw[0]

    if selected_date_str not in headers:
        continue

    date_index = headers.index(selected_date_str)

    current_section = None

    for row in raw:

        row_text = " ".join(row).strip().lower()

        if "daily item" in row_text:
            current_section = "daily"
            continue

        if "weekly item" in row_text:
            current_section = "weekly"
            continue

        if current_section is None:
            continue

        if not row or not row[0]:
            continue

        item = str(row[0]).strip()

        qty = ""

        if len(row) > date_index:
            qty = row[date_index]

        try:
            qty = float(qty) if qty != "" else 0
        except:
            qty = 0

        if current_section == "daily":

            if item not in daily_items:
                daily_items[item] = {bn: 0 for bn in branch_names}

            daily_items[item][branch_name] = qty

        elif current_section == "weekly":

            if item not in weekly_items:
                weekly_items[item] = {bn: 0 for bn in branch_names}

            weekly_items[item][branch_name] = qty

# ---------------- SAVE ITEMS FOR AI ----------------
st.session_state.DAILY_ITEMS = daily_items
st.session_state.WEEKLY_ITEMS = weekly_items

# ---------------- DAILY DF ----------------
daily_rows = []

for i, (item, values) in enumerate(daily_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
    daily_rows.append(row)

daily_df = pd.DataFrame(daily_rows)

# ---------------- WEEKLY DF ----------------
weekly_rows = []

for i, (item, values) in enumerate(weekly_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
    weekly_rows.append(row)

weekly_df = pd.DataFrame(weekly_rows)

# ---------------- DISPLAY ----------------
st.subheader("📦 Daily Items Stock")

if daily_df.empty:
    st.warning("No daily stock data found")
else:
    st.dataframe(daily_df, use_container_width=True)

st.subheader("📦 Weekly Items Stock")

if weekly_df.empty:
    st.warning("No weekly stock data found")
else:
    st.dataframe(weekly_df, use_container_width=True)

# ---------------- SEARCH ----------------
search = st.text_input("🔎 Search Item")

if search:

    if not daily_df.empty:
        st.subheader("📦 Daily Search Results")
        st.dataframe(
            daily_df[daily_df["Item Name"].str.contains(search, case=False, na=False)],
            use_container_width=True
        )

    if not weekly_df.empty:
        st.subheader("📦 Weekly Search Results")
        st.dataframe(
            weekly_df[weekly_df["Item Name"].str.contains(search, case=False, na=False)],
            use_container_width=True
        )

# ---------------- DOWNLOADS ----------------
if not daily_df.empty:
    st.download_button(
        "📥 Download Daily CSV",
        daily_df.to_csv(index=False),
        "daily_stock_report.csv",
        "text/csv"
    )

if not weekly_df.empty:
    st.download_button(
        "📥 Download Weekly CSV",
        weekly_df.to_csv(index=False),
        "weekly_stock_report.csv",
        "text/csv"
    )

# ---------------- FULL EXPORT ----------------
if not daily_df.empty or not weekly_df.empty:

    full_df = pd.concat(
        [
            daily_df.assign(Type="Daily"),
            weekly_df.assign(Type="Weekly")
        ],
        ignore_index=True
    )

    st.download_button(
        "📥 Download FULL Stock Report",
        full_df.to_csv(index=False),
        "full_stock_report.csv",
        "text/csv"
    )
