import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from difflib import get_close_matches
from ai_core import run_ai

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

# =========================================================
# GOOGLE AUTH
# =========================================================

creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope
    )
    return gspread.authorize(creds)

client = get_client()

# =========================================================
# LOAD MASTER BRANCH SHEET
# =========================================================

@st.cache_data(ttl=600)
def load_branches():

    sheet = client.open("MASTERBRANCHSHEET").sheet1

    data = sheet.get_all_records()

    return [
        b for b in data
        if b.get("SheetID") and b.get("BranchName")
    ]

branches = load_branches()

branch_names = [b["BranchName"] for b in branches]

# =========================================================
# SHEET CACHE
# =========================================================

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

# =========================================================
# FETCH BRANCH DATA
# =========================================================

def fetch_branch(branch):

    try:

        sheet_id = branch.get("SheetID")

        if not sheet_id or sheet_id not in sheet_cache:
            return branch["BranchName"], None

        file = sheet_cache[sheet_id]

        ws = file.worksheet("Stocks")

        data = ws.get_all_values()

        return branch["BranchName"], data

    except:
        return branch["BranchName"], None

# =========================================================
# LOAD ALL DATA
# =========================================================

@st.cache_data(ttl=300)
def load_all_data(branches):

    with ThreadPoolExecutor(max_workers=3) as executor:
        return list(executor.map(fetch_branch, branches))

all_data = load_all_data(branches)

# =========================================================
# SESSION
# =========================================================

st.session_state.all_data = all_data
st.session_state.branches = branches

# =========================================================
# REFRESH BUTTON
# =========================================================

if st.button("🔄 Refresh Data"):

    st.cache_data.clear()

    st.rerun()

# =========================================================
# AI PANEL BUTTON
# =========================================================

if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

if st.button("🤖 AI Assistant"):
    st.session_state.ai_open = not st.session_state.ai_open

# =========================================================
# PROCESS STOCK
# =========================================================

@st.cache_data(ttl=300)
def process_stock(all_data, branch_names):

    daily = {}
    weekly = {}

    for branch_name, raw in all_data:

        if not raw or len(raw) < 2:
            continue

        current_section = None

        for row in raw:

            row_text = " ".join(row).lower()

            # DAILY SECTION
            if "daily item" in row_text:
                current_section = "daily"
                continue

            # WEEKLY SECTION
            if "weekly item" in row_text:
                current_section = "weekly"
                continue

            if current_section is None:
                continue

            # SKIP EMPTY ROWS
            if not row or not row[0]:
                continue

            item = str(row[0]).strip()

            # =================================================
            # TAKE DATA FROM 4TH COLUMN
            # IF EMPTY => 0
            # =================================================

            qty = 0

            try:
                if len(row) > 3:
                    qty = float(row[3] or 0)
            except:
                qty = 0

            # =================================================
            # DAILY ITEMS
            # =================================================

            if current_section == "daily":

                if item not in daily:

                    daily[item] = {
                        bn: 0 for bn in branch_names
                    }

                daily[item][branch_name] = qty

            # =================================================
            # WEEKLY ITEMS
            # =================================================

            elif current_section == "weekly":

                if item not in weekly:

                    weekly[item] = {
                        bn: 0 for bn in branch_names
                    }

                weekly[item][branch_name] = qty

    return daily, weekly

# =========================================================
# LOAD STOCK
# =========================================================

daily_items, weekly_items = process_stock(
    all_data,
    branch_names
)

# =========================================================
# SAVE FOR AI
# =========================================================

st.session_state.DAILY_ITEMS = daily_items
st.session_state.WEEKLY_ITEMS = weekly_items

# =========================================================
# CREATE DAILY DATAFRAME
# FIRST 3 COLUMNS FIXED
# FROM 4TH COLUMN BRANCH DATA
# =========================================================

daily_rows = []

for i, (item, values) in enumerate(daily_items.items()):

    row = {
        "Sl No": i + 1,
        "Item Name": item,
        "Type": "Daily"
    }

    # BRANCH COLUMNS
    for branch in branch_names:
        row[branch] = values.get(branch, 0)

    daily_rows.append(row)

daily_df = pd.DataFrame(daily_rows)

# =========================================================
# CREATE WEEKLY DATAFRAME
# =========================================================

weekly_rows = []

for i, (item, values) in enumerate(weekly_items.items()):

    row = {
        "Sl No": i + 1,
        "Item Name": item,
        "Type": "Weekly"
    }

    # BRANCH COLUMNS
    for branch in branch_names:
        row[branch] = values.get(branch, 0)

    weekly_rows.append(row)

weekly_df = pd.DataFrame(weekly_rows)

# =========================================================
# DISPLAY DAILY TABLE
# =========================================================

st.subheader("📦 Daily Items Stock")

if not daily_df.empty:

    st.dataframe(
        daily_df,
        use_container_width=True
    )

else:
    st.warning("No Daily Data Found")

# =========================================================
# DISPLAY WEEKLY TABLE
# =========================================================

st.subheader("📦 Weekly Items Stock")

if not weekly_df.empty:

    st.dataframe(
        weekly_df,
        use_container_width=True
    )

else:
    st.warning("No Weekly Data Found")

# =========================================================
# SEARCH
# =========================================================

search = st.text_input("🔎 Search Item")

if search:

    st.subheader("🔍 Search Results")

    if not daily_df.empty:

        filtered_daily = daily_df[
            daily_df["Item Name"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

        if not filtered_daily.empty:

            st.write("### Daily Items")

            st.dataframe(
                filtered_daily,
                use_container_width=True
            )

    if not weekly_df.empty:

        filtered_weekly = weekly_df[
            weekly_df["Item Name"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

        if not filtered_weekly.empty:

            st.write("### Weekly Items")

            st.dataframe(
                filtered_weekly,
                use_container_width=True
            )

# =========================================================
# DOWNLOAD BUTTONS
# =========================================================

if not daily_df.empty:

    st.download_button(
        "📥 Download Daily CSV",
        daily_df.to_csv(index=False),
        file_name="daily_stock.csv",
        mime="text/csv"
    )

if not weekly_df.empty:

    st.download_button(
        "📥 Download Weekly CSV",
        weekly_df.to_csv(index=False),
        file_name="weekly_stock.csv",
        mime="text/csv"
    )

# =========================================================
# AI FUNCTIONS
# =========================================================

def find_best_item(user_input, items_dict):

    if not items_dict:
        return None

    keys = list(items_dict.keys())

    user_input = user_input.lower().strip()

    # DIRECT MATCH
    for k in keys:
        if user_input in k.lower():
            return k

    # FUZZY MATCH
    match = get_close_matches(
        user_input,
        keys,
        n=1,
        cutoff=0.5
    )

    return match[0] if match else None

# =========================================================
# AI PANEL
# =========================================================

if st.session_state.ai_open:

    st.markdown("## 🤖 Stock AI Assistant")

    combined = {}

    combined.update(
        st.session_state.get("DAILY_ITEMS", {})
    )

    combined.update(
        st.session_state.get("WEEKLY_ITEMS", {})
    )

    if not combined:

        st.warning("No stock data available.")

    else:

        user_input = st.text_input(
            "Ask about stock...",
            key="ai_input"
        )

        col1, col2 = st.columns(2)

        send = col1.button("Send")

        clear = col2.button("Clear Chat")

        if "chat" not in st.session_state:
            st.session_state.chat = []

        # CLEAR CHAT
        if clear:

            st.session_state.chat = []

            st.rerun()

        # SEND MESSAGE
        if send and user_input.strip():

            matched = find_best_item(
                user_input,
                combined
            )

            context = {
                "cache_data": st.session_state.all_data,
                "branch_list": branch_names,
                "master_items": list(combined.keys())
            }

            if not matched:

                response = "❌ Item not found in stock database."

            else:

                with st.spinner("Analyzing stock... 🤖"):

                    response = run_ai(
                        user_input,
                        context
                    )

            st.session_state.chat.append(
                ("You", user_input)
            )

            st.session_state.chat.append(
                ("AI", response)
            )

            st.rerun()

        # DISPLAY CHAT
        for sender, msg in st.session_state.chat:

            if sender == "You":

                st.markdown(
                    f"🧑 **You:** {msg}"
                )

            else:

                st.markdown(
                    f"🤖 **AI:** {msg}"
                )
