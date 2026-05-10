import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from difflib import get_close_matches
from ai_core import run_ai

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

# ---------------- AI STATE ----------------
if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

if "chat" not in st.session_state:
    st.session_state.chat = []

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
    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# ---------------- SHEET CACHE ----------------
@st.cache_resource
def get_sheets(branches):
    cache = {}
    for b in branches:
        sheet_id = b.get("SheetID")
        if not sheet_id:
            continue
        try:
            cache[sheet_id] = client.open_by_key(sheet_id)
        except:
            pass
    return cache

sheet_cache = get_sheets(branches)

# ---------------- FETCH DATA ----------------
def fetch_branch(branch):
    try:
        sheet_id = branch.get("SheetID")
        if not sheet_id or sheet_id not in sheet_cache:
            return branch["BranchName"], None

        file = sheet_cache[sheet_id]
        ws = file.worksheet("Stocks")
        return branch["BranchName"], ws.get_all_values()

    except:
        return branch["BranchName"], None

@st.cache_data(ttl=300)
def load_all_data(branches):
    with ThreadPoolExecutor(max_workers=3) as executor:
        return list(executor.map(fetch_branch, branches))

all_data = load_all_data(branches)

st.session_state.all_data = all_data
st.session_state.branches = branches

# ---------------- DATE ----------------
selected_date = st.date_input("📅 Select Stock Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# ---------------- REFRESH ----------------
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ---------------- STOCK PROCESSING ----------------
@st.cache_data(ttl=300)
def process_stock(all_data, selected_date_str, branch_names):

    daily = {}
    weekly = {}

    for branch_name, raw in all_data:

        if not raw or len(raw) < 2:
            continue

        headers = raw[0]

        if selected_date_str not in headers:
            continue

        date_index = headers.index(selected_date_str)
        current_section = None

        for row in raw:

            row_text = " ".join(row).lower()

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

            qty = 0
            if len(row) > date_index:
                try:
                    qty = float(row[date_index] or 0)
                except:
                    qty = 0

            if current_section == "daily":
                if item not in daily:
                    daily[item] = {bn: 0 for bn in branch_names}
                daily[item][branch_name] = qty

            elif current_section == "weekly":
                if item not in weekly:
                    weekly[item] = {bn: 0 for bn in branch_names}
                weekly[item][branch_name] = qty

    return daily, weekly

daily_items, weekly_items = process_stock(all_data, selected_date_str, branch_names)

st.session_state.DAILY_ITEMS = daily_items
st.session_state.WEEKLY_ITEMS = weekly_items

# =========================================================
# 🤖 AI TOGGLE BUTTON
# =========================================================
if st.button("🤖 AI Assistant"):
    st.session_state.ai_open = not st.session_state.ai_open

# =========================================================
# 🔥 SMART ITEM MATCHING FUNCTION (FIX)
# =========================================================
def find_best_item(user_input, items):
    if not items:
        return None

    user_input = user_input.lower().strip()
    items_lower = {i.lower(): i for i in items}

    # 1. exact match
    if user_input in items_lower:
        return items_lower[user_input]

    # 2. partial match
    for key, original in items_lower.items():
        if user_input in key:
            return original

    # 3. fuzzy match
    match = get_close_matches(user_input, items_lower.keys(), n=1, cutoff=0.4)
    if match:
        return items_lower[match[0]]

    return None

# =========================================================
# 🤖 AI PANEL
# =========================================================
if st.session_state.ai_open:

    st.markdown("## 🤖 AI Stock Assistant")

    all_items = list(daily_items.keys()) + list(weekly_items.keys())

    for sender, msg in st.session_state.chat[-20:]:
        icon = "🧑" if sender == "You" else "🤖"
        st.markdown(f"**{icon} {sender}:** {msg}")

    user_input = st.text_input("Ask about stock...", key="ai_input")

    if st.button("Send") and user_input:

        matched_item = find_best_item(user_input, all_items)

        if not matched_item:
            response = "❌ Could not identify item.\n\nTry:\n" + "\n".join(all_items[:5])

        else:
            context = {
                "item": matched_item,
                "daily": daily_items.get(matched_item, {}),
                "weekly": weekly_items.get(matched_item, {}),
                "branches": branch_names
            }

            response = run_ai(user_input, context)

        st.session_state.chat.append(("You", user_input))
        st.session_state.chat.append(("AI", response))

        st.rerun()

# =========================================================
# 📦 DAILY TABLE
# =========================================================
daily_rows = []
for i, (item, values) in enumerate(daily_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
    daily_rows.append(row)

daily_df = pd.DataFrame(daily_rows)

# =========================================================
# 📦 WEEKLY TABLE
# =========================================================
weekly_rows = []
for i, (item, values) in enumerate(weekly_items.items(), start=1):
    row = {"Sl No": i, "Item Name": item}
    row.update(values)
    weekly_rows.append(row)

weekly_df = pd.DataFrame(weekly_rows)

# =========================================================
# DISPLAY
# =========================================================
st.subheader("📦 Daily Items Stock")
st.dataframe(daily_df, use_container_width=True) if not daily_df.empty else st.warning("No data")

st.subheader("📦 Weekly Items Stock")
st.dataframe(weekly_df, use_container_width=True) if not weekly_df.empty else st.warning("No data")
