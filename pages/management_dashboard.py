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
def get_sheets(sheet_ids):
    cache = {}
    for sid in sheet_ids:
        try:
            cache[sid] = client.open_by_key(sid)
        except:
            pass
    return cache

sheet_ids = [b["SheetID"] for b in branches if b.get("SheetID")]
sheet_cache = get_sheets(sheet_ids)

# ---------------- FETCH ----------------
def fetch_branch(branch):
    try:
        sid = branch.get("SheetID")
        if not sid or sid not in sheet_cache:
            return branch["BranchName"], None

        ws = sheet_cache[sid].worksheet("Stocks")
        return branch["BranchName"], ws.get_all_values()

    except:
        return branch["BranchName"], None

# ---------------- LOAD DATA (CACHED) ----------------
@st.cache_data(ttl=600)
def load_all_data(branches):
    with ThreadPoolExecutor(max_workers=2):
        return [fetch_branch(b) for b in branches]

# ✅ prevents repeated API calls on rerun
if "cached_all_data" not in st.session_state:
    st.session_state.cached_all_data = load_all_data(branches)

all_data = st.session_state.cached_all_data

# ---------------- SESSION STATE ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

if "stock_cache" not in st.session_state:
    st.session_state.stock_cache = {}

# ---------------- DATE ----------------
selected_date = st.date_input("📅 Select Stock Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# ---------------- REFRESH ----------------
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.session_state.stock_cache = {}
    st.session_state.cached_all_data = load_all_data(branches)
    st.rerun()

# ---------------- PROCESS STOCK ----------------
@st.cache_data(ttl=600)
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
            try:
                if date_index < len(row):
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

# ---------------- CACHE PER DATE (IMPORTANT SPEED FIX) ----------------
cache_key = selected_date_str

if cache_key not in st.session_state.stock_cache:
    st.session_state.stock_cache[cache_key] = process_stock(
        all_data,
        selected_date_str,
        branch_names
    )

daily_items, weekly_items = st.session_state.stock_cache[cache_key]

# ---------------- DATAFRAMES ----------------
daily_df = pd.DataFrame([
    {"Sl No": i+1, "Item Name": item, **values}
    for i, (item, values) in enumerate(daily_items.items())
])

weekly_df = pd.DataFrame([
    {"Sl No": i+1, "Item Name": item, **values}
    for i, (item, values) in enumerate(weekly_items.items())
])

# ---------------- AI MATCH ----------------
def find_best_item(user_input, items_dict):

    if not items_dict:
        return None

    keys = list(items_dict.keys())
    user_input = user_input.lower().strip()

    for k in keys:
        if user_input in k.lower():
            return k

    match = get_close_matches(user_input, keys, n=1, cutoff=0.5)
    return match[0] if match else None

# ---------------- AI TOGGLE ----------------
if st.button("🤖 AI Assistant"):
    st.session_state.ai_open = not st.session_state.ai_open

if st.session_state.ai_open:

    st.markdown("## 🤖 Stock AI Assistant")

    # ✅ build combined ONCE only
    if "combined" not in st.session_state:
        st.session_state.combined = {}
        st.session_state.combined.update(daily_items)
        st.session_state.combined.update(weekly_items)

    combined = st.session_state.combined

    # ---------------- CHAT DISPLAY ----------------
    for role, msg in st.session_state.chat:
        st.markdown(f"{'🧑' if role=='You' else '🤖'} **{role}:** {msg}")

    if combined:

        user_input = st.text_input("Ask about stock...")

        col1, col2 = st.columns(2)

        submitted = col1.button("Send")
        clear = col2.button("Clear Chat")

        # ---------------- CLEAR CHAT (FAST - NO RERUN PIPELINE) ----------------
        if clear:
            st.session_state.chat = []

        # ---------------- SEND ----------------
        if submitted and user_input.strip():

            matched = find_best_item(user_input, combined)

            context = {
                "branch_list": branch_names,
                "master_items": list(combined.keys())[:200]
            }

            if not matched:
                response = "❌ Item not found in stock database."
            else:
                with st.spinner("Analyzing..."):
                    response = run_ai(user_input, context)

            st.session_state.chat.append(("You", user_input))
            st.session_state.chat.append(("AI", response))

# ---------------- TABLES ----------------
st.subheader("📦 Daily Items Stock")
st.dataframe(daily_df if not daily_df.empty else "No data", use_container_width=True)

st.subheader("📦 Weekly Items Stock")
st.dataframe(weekly_df if not weekly_df.empty else "No data", use_container_width=True)

# ---------------- SEARCH ----------------
search = st.text_input("🔎 Search Item")

if search:
    if not daily_df.empty:
        st.dataframe(daily_df[daily_df["Item Name"].str.contains(search, case=False, na=False)])

    if not weekly_df.empty:
        st.dataframe(weekly_df[weekly_df["Item Name"].str.contains(search, case=False, na=False)])

# ---------------- DOWNLOADS ----------------
if not daily_df.empty:
    st.download_button("📥 Daily CSV", daily_df.to_csv(index=False), "daily.csv")

if not weekly_df.empty:
    st.download_button("📥 Weekly CSV", weekly_df.to_csv(index=False), "weekly.csv")
