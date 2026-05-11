import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from st_aggrid import AgGrid, GridOptionsBuilder
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
# BRANCHES
# =========================================================

@st.cache_data(ttl=600)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# =========================================================
# SHEET CACHE
# =========================================================

@st.cache_resource
def get_sheets(branches):
    cache = {}
    for b in branches:
        sid = b.get("SheetID")
        if sid:
            try:
                cache[sid] = client.open_by_key(sid)
            except:
                pass
    return cache

sheet_cache = get_sheets(branches)

# =========================================================
# FAST FETCH
# =========================================================

@st.cache_data(ttl=600)
def fetch_sheet_range(sheet_id):
    try:
        ws = sheet_cache[sheet_id].worksheet("Stocks")
        return ws.get("A1:Z500")
    except:
        return None

def fetch_branch(branch):
    sid = branch.get("SheetID")
    if not sid or sid not in sheet_cache:
        return branch["BranchName"], None

    return branch["BranchName"], fetch_sheet_range(sid)

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data(ttl=300)
def load_all_data(branches):
    with ThreadPoolExecutor(max_workers=10) as ex:
        return list(ex.map(fetch_branch, branches))

# =========================================================
# 🔄 REFRESH BUTTON
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# =========================================================
# AI STATE BUTTONS
# =========================================================

if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

with col2:
    if st.button("🤖 AI Assistant"):
        st.session_state.ai_open = True

with col3:
    if st.button("🔙 Back"):
        st.session_state.ai_open = False

# =========================================================
# LOAD DATA
# =========================================================

all_data = load_all_data(branches)

# =========================================================
# DATE
# =========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# =========================================================
# PROCESS STOCK (UNCHANGED)
# =========================================================

@st.cache_data(ttl=300)
def process_stock(all_data, selected_date_str, branch_names):

    daily = {}
    weekly = {}

    for branch_name, raw in all_data:

        if not raw or len(raw) < 2:
            continue

        headers = [str(h).strip() for h in raw[0]]

        date_index = None
        for i, h in enumerate(headers):
            if h == selected_date_str:
                date_index = i
                break

        current_section = None

        for row in raw:

            if not row:
                continue

            text = " ".join(row).lower()

            if "daily item" in text:
                current_section = "daily"
                continue

            if "weekly item" in text:
                current_section = "weekly"
                continue

            if current_section is None:
                continue

            item = row[0].strip() if len(row) > 0 else ""
            sku = row[1].strip() if len(row) > 1 else ""
            uom = row[2].strip() if len(row) > 2 else ""

            if not item:
                continue

            key = f"{item}_{sku}_{uom}"

            target = daily if current_section == "daily" else weekly

            if key not in target:

                target[key] = {
                    "Item Name": item,
                    "SKU": sku,
                    "UOM": uom
                }

                for bn in branch_names:
                    target[key][bn] = 0

            qty = 0
            try:
                if date_index is not None and len(row) > date_index:
                    qty = float(row[date_index] or 0)
            except:
                qty = 0

            target[key][branch_name] = qty

    return daily, weekly

# =========================================================
# RUN
# =========================================================

daily_items, weekly_items = process_stock(
    all_data,
    selected_date_str,
    branch_names
)

# =========================================================
# DATAFRAME
# =========================================================

def build_df(data_dict):

    rows = []

    for _, v in data_dict.items():

        row = {
            "Item Name": v["Item Name"],
            "SKU": v["SKU"],
            "UOM": v["UOM"]
        }

        for b in branch_names:
            row[b] = v.get(b, 0)

        rows.append(row)

    return pd.DataFrame(rows)

daily_df = build_df(daily_items)
weekly_df = build_df(weekly_items)

# =========================================================
# SAFE WIDTH FUNCTION
# =========================================================

def get_width(series, min_width):

    try:
        series = series.fillna("").astype(str)
        max_len = series.map(len).max()

        if pd.isna(max_len):
            return min_width

        return max(min_width, int(max_len * 5 + 25))

    except:
        return min_width

# =========================================================
# AI HELPER
# =========================================================

def find_best_item(user_input, items_dict):

    keys = list(items_dict.keys())

    for k in keys:
        if user_input.lower() in k.lower():
            return k

    match = get_close_matches(user_input, keys, n=1, cutoff=0.5)
    return match[0] if match else None

# =========================================================
# AI PANEL
# =========================================================

if st.session_state.ai_open:

    st.markdown("## 🤖 Stock AI Assistant")

    combined = {}
    combined.update(daily_items)
    combined.update(weekly_items)

    if not combined:
        st.warning("No stock data available.")
    else:

        user_input = st.text_input("Ask about stock...", key="ai_input")

        col1, col2 = st.columns(2)

        send = col1.button("Send")
        clear = col2.button("Clear Chat")

        if "chat" not in st.session_state:
            st.session_state.chat = []

        if clear:
            st.session_state.chat = []
            st.rerun()

        if send and user_input.strip():

            matched = find_best_item(user_input, combined)

            context = {
                "cache_data": all_data,
                "branch_list": branch_names,
                "master_items": list(combined.keys())
            }

            if not matched:
                response = "❌ Item not found in stock database."
            else:
                with st.spinner("Analyzing stock... 🤖"):
                    response = run_ai(user_input, context)

            st.session_state.chat.append(("You", user_input))
            st.session_state.chat.append(("AI", response))

            st.rerun()

        for role, msg in st.session_state.chat:
            st.write(f"**{role}:** {msg}")

# =========================================================
# GRID RENDER
# =========================================================

def render_grid(df, title):

    st.subheader(title)

    if df.empty:
        st.warning("No Data")
        return

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_column("Item Name", pinned="left", minWidth=120)
    gb.configure_column("SKU", pinned="left", minWidth=60)
    gb.configure_column("UOM", pinned="left", minWidth=60)

    for col in branch_names:
        if col in df.columns:
            gb.configure_column(col, minWidth=100)

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True
    )

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        fit_columns_on_grid_load=False
    )

# =========================================================
# DISPLAY TABLES
# =========================================================

render_grid(daily_df, "📦 Daily Items Stock")
render_grid(weekly_df, "📦 Weekly Items Stock")

# =========================================================
# DOWNLOAD
# =========================================================

st.download_button(
    "📥 Download Daily CSV",
    daily_df.to_csv(index=False),
    file_name="daily_stock.csv",
    mime="text/csv"
)

st.download_button(
    "📥 Download Weekly CSV",
    weekly_df.to_csv(index=False),
    file_name="weekly_stock.csv",
    mime="text/csv"
)
