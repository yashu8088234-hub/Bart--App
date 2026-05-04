import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime

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

# ---------------- LOAD MASTER ----------------
@st.cache_data(ttl=600)
def load_branches():
    master = client.open("MASTERBRANCHSHEET").sheet1
    return master.get_all_records()

branches = load_branches()

# ⚠️ KEEP EXACT NAMES (DO NOT CHANGE)
branch_names = [b["BranchName"] for b in branches]

# ---------------- DATE PICKER ----------------
selected_date = st.date_input("📅 Select Stock Date")

all_items = {}

# ---------------- FETCH SHEET DATA ----------------
@st.cache_data(ttl=300)
def get_sheet_data(sheet_id):
    file = client.open_by_key(sheet_id)
    sheet = file.worksheet("Stocks")
    return sheet.get_all_values()

# ---------------- PROCESS DATA ----------------
for branch in branches:
    branch_name = branch["BranchName"]
    sheet_id = branch["SheetID"]

    try:
        raw = get_sheet_data(sheet_id)

        if not raw or len(raw) < 2:
            continue

        headers = raw[0]
        rows = raw[1:]

        data = pd.DataFrame(rows, columns=headers)

        item_col = headers[0]

        # ---------------- DATE MAP ----------------
        date_map = {}
        for col in headers[1:]:
            try:
                col_date = datetime.datetime.strptime(col, "%d/%m/%y").date()
                date_map[col_date] = col
            except:
                pass

        if selected_date not in date_map:
            continue

        chosen_col = date_map[selected_date]

        # ---------------- BUILD DATA ----------------
        for _, row in data.iterrows():
            item = str(row[item_col]).strip()
            qty = row[chosen_col]

            if item not in all_items:
                all_items[item] = {bn: 0 for bn in branch_names}

            all_items[item][branch_name] = qty

    except Exception as e:
        st.error(f"{branch_name} error: {e}")

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
    st.warning("No data found for selected date")
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

# SAFE COLUMN FILTER (FIX CRASH)
valid_columns = [col for col in branch_names if col in df.columns]

styled_df = df.style.applymap(highlight_low, subset=valid_columns)

st.dataframe(styled_df, use_container_width=True)
