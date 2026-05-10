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

    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# ---------------- SAFE SHEET CACHE ----------------
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

# ---------------- FETCH BRANCH DATA ----------------
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


# ---------------- CACHE ALL DATA ----------------
@st.cache_data(ttl=300)
def load_all_data(branches):
    with ThreadPoolExecutor(max_workers=3) as executor:
        return list(executor.map(fetch_branch, branches))


all_data = load_all_data(branches)

# ---------------- SESSION STORAGE ----------------
st.session_state.all_data = all_data
st.session_state.branches = branches

# ---------------- DATE PICKER ----------------
selected_date = st.date_input("📅 Select Stock Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ---------------- PROCESS STOCK ----------------
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

# ---------------- SAVE FOR AI ----------------
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


# =========================================================
# 🤖 AI ASSISTANT (SAFE ADD-ON - NOTHING MODIFIED ABOVE)
# =========================================================

from difflib import get_close_matches
from ai_core import run_ai


if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

if "chat" not in st.session_state:
    st.session_state.chat = []

if "ai_input" not in st.session_state:
    st.session_state.ai_input = ""


def find_best_item(user_input, items_dict):

    if not items_dict:
        return None

    keys = list(items_dict.keys())
    user_input = user_input.lower().strip()

    for k in keys:
        if user_input == k.lower():
            return k

    for k in keys:
        if user_input in k.lower():
            return k

    match = get_close_matches(user_input, keys, n=1, cutoff=0.5)
    if match:
        return match[0]

    return None


def render_ai_button():
    if st.button("🤖 AI Assistant"):
        st.session_state.ai_open = not st.session_state.ai_open


render_ai_button()


if st.session_state.ai_open:

    st.markdown("## 🤖 Stock AI Assistant")

    combined = {}
    combined.update(st.session_state.get("DAILY_ITEMS", {}))
    combined.update(st.session_state.get("WEEKLY_ITEMS", {}))

    if not combined:
        st.warning("⚠ No stock data available for AI.")
    else:

        for sender, msg in st.session_state.chat[-30:]:
            icon = "🧑" if sender == "You" else "🤖"
            st.markdown(f"**{icon} {sender}:** {msg}")

        st.markdown("---")

        user_input = st.text_input("Ask about stock...", key="ai_input")

        col1, col2 = st.columns(2)

        send = col1.button("Send")
        clear = col2.button("Clear Chat")

        if clear:
            st.session_state.chat = []
            st.rerun()

        if send and user_input.strip():

            matched = find_best_item(user_input, combined)

            if not matched:
                response = "❌ Item not found in stock database."
            else:
                context = {
                    "item": matched,
                    "daily": st.session_state.get("DAILY_ITEMS", {}),
                    "weekly": st.session_state.get("WEEKLY_ITEMS", {})
                }

                with st.spinner("Analyzing stock... 🤖"):
                    response = run_ai(user_input, context)

            st.session_state.chat.append(("You", user_input))
            st.session_state.chat.append(("AI", response))

            st.session_state.ai_input = ""

            st.rerun()
