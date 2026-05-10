import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from ai_core import run_ai

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(layout="wide", page_title="Stock Overview")

st.title("📦 BART - Stock Management (AI Controlled)")

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
# LOAD BRANCHES
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

branch_names = [
    b["BranchName"]
    for b in branches
]

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
# FETCH BRANCH
# =========================================================
def fetch_branch(branch):

    try:
        sheet_id = branch.get("SheetID")

        if not sheet_id:
            return branch["BranchName"], None

        if sheet_id not in sheet_cache:
            return branch["BranchName"], None

        file = sheet_cache[sheet_id]

        ws = file.worksheet("Stocks")

        return branch["BranchName"], ws.get_all_values()

    except:
        return branch["BranchName"], None

# =========================================================
# LOAD ALL DATA
# =========================================================
@st.cache_data(ttl=300)
def load_all_data(branches):

    with ThreadPoolExecutor(max_workers=3) as executor:

        return list(
            executor.map(fetch_branch, branches)
        )

all_data = load_all_data(branches)

# =========================================================
# DATE
# =========================================================
selected_date = st.date_input("📅 Select Stock Date")

selected_date_str = selected_date.strftime("%Y-%m-%d")

# =========================================================
# REFRESH
# =========================================================
if st.button("🔄 Refresh Data"):

    st.cache_data.clear()

    st.rerun()

# =========================================================
# PROCESS STOCK
# =========================================================
@st.cache_data(ttl=300)
def process_stock(
    all_data,
    selected_date_str,
    branch_names
):

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

            # ---------------- DAILY ----------------
            if "daily item" in row_text:

                current_section = "daily"

                continue

            # ---------------- WEEKLY ----------------
            if "weekly item" in row_text:

                current_section = "weekly"

                continue

            if current_section is None:
                continue

            if not row:
                continue

            if not row[0]:
                continue

            item = str(row[0]).strip()

            qty = 0

            try:

                if len(row) > date_index:
                    qty = float(row[date_index] or 0)

            except:
                qty = 0

            # ---------------- STORE DAILY ----------------
            if current_section == "daily":

                if item not in daily:

                    daily[item] = {
                        bn: 0
                        for bn in branch_names
                    }

                daily[item][branch_name] = qty

            # ---------------- STORE WEEKLY ----------------
            elif current_section == "weekly":

                if item not in weekly:

                    weekly[item] = {
                        bn: 0
                        for bn in branch_names
                    }

                weekly[item][branch_name] = qty

    return daily, weekly

daily_items, weekly_items = process_stock(
    all_data,
    selected_date_str,
    branch_names
)

# =========================================================
# DATAFRAMES
# =========================================================
daily_df = pd.DataFrame([
    {
        "Sl No": i + 1,
        "Item Name": item,
        **values
    }
    for i, (item, values)
    in enumerate(daily_items.items())
])

weekly_df = pd.DataFrame([
    {
        "Sl No": i + 1,
        "Item Name": item,
        **values
    }
    for i, (item, values)
    in enumerate(weekly_items.items())
])

# =========================================================
# AI CHAT STATE
# =========================================================
if "chat" not in st.session_state:
    st.session_state.chat = []

if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

# =========================================================
# AI PANEL TOGGLE
# =========================================================
if st.button("🤖 AI Assistant"):

    st.session_state.ai_open = (
        not st.session_state.ai_open
    )

# =========================================================
# AI PANEL
# =========================================================
if st.session_state.ai_open:

    st.markdown("## 🤖 Stock AI Assistant")

    # -----------------------------------------------------
    # CHAT HISTORY
    # -----------------------------------------------------
    for role, msg in st.session_state.chat:

        if role == "You":

            st.markdown(
                f"🧑 **You:** {msg}"
            )

        else:

            st.markdown(
                f"🤖 **AI:** {msg}"
            )

    st.divider()

    # -----------------------------------------------------
    # USER INPUT
    # -----------------------------------------------------
    user_input = st.text_input(
        "Ask anything about stock..."
    )

    col1, col2 = st.columns(2)

    # -----------------------------------------------------
    # SEND
    # -----------------------------------------------------
    with col1:

        send = st.button("Send")

    # -----------------------------------------------------
    # CLEAR CHAT
    # -----------------------------------------------------
    with col2:

        clear = st.button("🧹 Clear Chat")

    # -----------------------------------------------------
    # CLEAR ACTION
    # -----------------------------------------------------
    if clear:

        st.session_state.chat = []

        st.rerun()

    # -----------------------------------------------------
    # AI EXECUTION
    # -----------------------------------------------------
    if send and user_input.strip():

        with st.spinner(
            "AI analyzing inventory... 🤖"
        ):

            # IMPORTANT:
            # AI now controls context itself
            response = run_ai(user_input)

        # STORE CHAT
        st.session_state.chat.append(
            ("You", user_input)
        )

        st.session_state.chat.append(
            ("AI", response)
        )

        st.rerun()

# =========================================================
# TABLES
# =========================================================
st.subheader("📦 Daily Items Stock")

if not daily_df.empty:

    st.dataframe(
        daily_df,
        use_container_width=True
    )

else:

    st.warning("No daily data available")

# ---------------------------------------------------------

st.subheader("📦 Weekly Items Stock")

if not weekly_df.empty:

    st.dataframe(
        weekly_df,
        use_container_width=True
    )

else:

    st.warning("No weekly data available")

# =========================================================
# SEARCH
# =========================================================
search = st.text_input("🔎 Search Item")

if search:

    # -----------------------------------------------------
    # DAILY SEARCH
    # -----------------------------------------------------
    if not daily_df.empty:

        filtered_daily = daily_df[
            daily_df["Item Name"]
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

        st.subheader("Daily Search Results")

        st.dataframe(
            filtered_daily,
            use_container_width=True
        )

    # -----------------------------------------------------
    # WEEKLY SEARCH
    # -----------------------------------------------------
    if not weekly_df.empty:

        filtered_weekly = weekly_df[
            weekly_df["Item Name"]
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

        st.subheader("Weekly Search Results")

        st.dataframe(
            filtered_weekly,
            use_container_width=True
        )

# =========================================================
# DOWNLOADS
# =========================================================
if not daily_df.empty:

    st.download_button(
        "📥 Download Daily CSV",
        daily_df.to_csv(index=False),
        file_name="daily_stock.csv",
        mime="text/csv"
    )

# ---------------------------------------------------------

if not weekly_df.empty:

    st.download_button(
        "📥 Download Weekly CSV",
        weekly_df.to_csv(index=False),
        file_name="weekly_stock.csv",
        mime="text/csv"
    )
