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

# ---------------- GLOBAL SAFETY LOCKS ----------------
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

# ---------------- SAFE FETCH FUNCTION ----------------
@st.cache_data(ttl=600)
def get_all_sheets(branches):
    results = []
    sheet_cache = {}

    for branch in branches:
        sheet_id = branch["SheetID"]
        branch_name = branch["BranchName"]

        try:
            if sheet_id not in sheet_cache:
                sheet_cache[sheet_id] = client.open_by_key(sheet_id)

            file = sheet_cache[sheet_id]
            ws = file.worksheet("Stocks")

            raw = ws.get_all_values()

            results.append((branch_name, raw))

            time.sleep(0.25)

        except Exception as e:
            results.append((branch_name, None))
            st.error(f"{branch_name} error: {e}")

    return results

# ---------------- FETCH ----------------
try:
    st.session_state.is_fetching = True
    all_data = get_all_sheets(branches)
finally:
    st.session_state.is_fetching = False

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

# ---------------- FINAL DATAFRAME ----------------
rows = []
for i, (item, values) in enumerate(all_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
    rows.append(row)

df = pd.DataFrame(rows)

# ---------------- DISPLAY ----------------
st.subheader("📊 Stock Data")
st.dataframe(df, use_container_width=True)

# ---------------- LOW STOCK ----------------
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

# =========================================================
# ✅ STOCK VIEW (ADDED - DAILY + WEEKLY SPLIT)
# =========================================================

st.markdown("---")
st.subheader("🔍 Stock View (Daily & Weekly)")

selected_branch = st.selectbox("Select Branch for Stock View", ["-- Select --"] + branch_names)

if selected_branch != "-- Select --":

    branch = next(b for b in branches if b["BranchName"] == selected_branch)
    sheet = client.open_by_key(branch["SheetID"])
    ws = sheet.worksheet("Stocks")

    data = ws.get_all_values()

    headers = data[0]
    date_columns = headers[1:]

    daily = []
    weekly = []

    current_section = None

    for row in data:

        if not row:
            continue

        text = " ".join(row).strip().lower()

        if "daily item" in text:
            current_section = "daily"
            continue

        if "weekly item" in text:
            current_section = "weekly"
            continue

        if current_section is None:
            continue

        if not row[0]:
            continue

        item = row[0].strip()

        values = row[1:]
        values = values + [""] * (len(date_columns) - len(values))

        cleaned = []
        total = 0

        for v in values:
            try:
                num = float(v) if v != "" else 0
            except:
                num = 0
            cleaned.append(num)
            total += num

        row_dict = {"Item": item}

        for i, col in enumerate(date_columns):
            row_dict[col] = cleaned[i]

        row_dict["Total"] = total

        if current_section == "daily":
            daily.append(row_dict)
        elif current_section == "weekly":
            weekly.append(row_dict)

    st.write("### 📦 Daily Items")
    st.dataframe(pd.DataFrame(daily), use_container_width=True, height=350)

    st.write("### 📦 Weekly Items")
    st.dataframe(pd.DataFrame(weekly), use_container_width=True, height=350)
