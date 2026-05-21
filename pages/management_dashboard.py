import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import time
import hashlib

# ========================================================
# PAGE CONFIG
# ========================================================
st.set_page_config(page_title="Management Panel", layout="wide", initial_sidebar_state="collapsed")

st.title("📦 BART - Stock Management (All Branches)")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
        
        /* AG-GRID SCROLLBAR STYLING */
        .ag-body-viewport::-webkit-scrollbar, 
        .ag-body-horizontal-scroll-viewport::-webkit-scrollbar {
            height: 12px !important;
            width: 12px !important;
            background: #f1f1f1 !important;
        }
        .ag-body-viewport::-webkit-scrollbar-thumb,
        .ag-body-horizontal-scroll-viewport::-webkit-scrollbar-thumb {
            background: #888 !important;
            border-radius: 6px !important;
        }
        .ag-body-viewport::-webkit-scrollbar-thumb:hover,
        .ag-body-horizontal-scroll-viewport::-webkit-scrollbar-thumb:hover {
            background: #555 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ========================================================
# GOOGLE AUTH & DATA LOADING
# ========================================================
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

client = get_client()

@st.cache_data(ttl=None)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    return [{"BranchName": str(b["BranchName"]).strip(), "SheetID": str(b["SheetID"]).strip()} 
            for b in sheet.get_all_records() if b.get("SheetID") and b.get("BranchName")]

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# Category definitions
FOOD_SKUS = {"-", "B034", "F066", "B032", "B029", "F081", "B019", "B018", "CF007", "CF006", "F148", "B028", "K072", "K176", "CB036", "K265", "B016", "CB078", "K154", "CB054", "K226", "CB074", "M&M", "B014", "K242", "S019", "B006", "CB055", "B017", "CB076", "CB056", "B026", "CB037", "K087", "CB043", "CB009", "CB043", "K063"}
DRY_SKUS = {"C013", "IC013", "P244", "P245", "P254", "P095", "P296", "P343", "P343(1)", "P012", "P091", "P155", "P081", "P253", "P101", "P218", "P132", "P264", "P219", "P338", "P341", "P342", "P210", "P320", "P322", "P321", "P082", "P318", "P208", "P315", "C014", "F070", "P298", "P178", "CB009", "C015", "CF009", "P145", "P133", "P156", "RS002", "C011", "C012", "P189", "P160", "C005", "P157", "C010", "C007", "CB010", "P161", "P039", "P125", "C045", "RS001", "P084", "P163", "P162", "C016", "C017", "P158", "C048", "P083"}
MISC_SKUS = {"K063", "T063", "T060", "T066", "TOY1", "ΤΟΥ1", "T026", "SVP", "F089", "P130"}

def fetch_branch(branch):
    try:
        ws = client.open_by_key(branch["SheetID"]).worksheet("Stocks")
        return branch["BranchName"], ws.get_all_values()
    except: return branch["BranchName"], []

@st.cache_data(ttl=None)
def load_all_data(branches):
    completed = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(fetch_branch, b): b for b in branches}
        for f in as_completed(futures):
            name, data = f.result()
            if data: completed[name] = data
    return [(b["BranchName"], completed.get(b["BranchName"], [])) for b in branches]

if st.button("🔄 Refresh Data"): st.cache_data.clear(); st.cache_resource.clear(); st.rerun()

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# ========================================================
# LOGIC & PROCESSING
# ========================================================
def process_stock(all_data, selected_date_str, branch_names):
    daily, weekly = {}, {}
    for branch_name, raw in all_data:
        if len(raw) < 2: continue
        headers = [str(x).strip() for x in raw[0]]
        date_index = next((i for i, h in enumerate(headers) if h == selected_date_str), None)
        mode = None
        for row in raw:
            text = " ".join(str(x) for x in row).lower()
            if "daily item" in text: mode = "daily"; continue
            if "weekly item" in text: mode = "weekly"; continue
            if not mode or not row[0]: continue
            item, sku, uom = str(row[0]).strip(), str(row[1]).replace(" ", "").strip(), str(row[2]).strip()
            key = f"{item}_{sku}_{uom}"
            target = daily if mode == "daily" else weekly
            if key not in target:
                target[key] = {"Item Name": item, "SKU": sku, "UOM": uom, **{b: 0 for b in branch_names}}
            try:
                val = str(row[date_index]).strip() if date_index and len(row) > date_index else "0"
                target[key][branch_name] = float(val) if val not in ["", "-", "None"] else 0
            except: pass
    return daily, weekly

def build_df(data_dict, branch_names):
    return pd.DataFrame(data_dict.values())

all_data = load_all_data(branches)
daily_items, weekly_items = process_stock(all_data, selected_date_str, branch_names)
daily_df = build_df(daily_items, branch_names)
weekly_df = build_df(weekly_items, branch_names)

# ========================================================
# GRID FUNCTION
# ========================================================
def make_grid(df, key):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(resizable=False, sortable=True, filter=True, editable=False)
    gb.configure_column("Item Name", pinned="left", width=250)
    gb.configure_column("SKU", pinned="left", width=100)
    gb.configure_column("UOM", pinned="left", width=100)
    gb.configure_grid_options(
        headerHeight=38, rowHeight=32,
        suppressHorizontalScroll=False,
        alwaysShowHorizontalScroll=True,
        alwaysShowVerticalScroll=True
    )
    AgGrid(df, gridOptions=gb.build(), theme="streamlit", height=500, key=key, update_mode=GridUpdateMode.NO_UPDATE)

def stable_key(prefix, name, df=None):
    return f"{prefix}_{name}_{hash(str(df.shape))}"

# ========================================================
# UI SECTIONS
# ========================================================
st.subheader("📊 Category Wise Stock Overview")

def detect_category(sku):
    s = str(sku).replace(" ", "").upper()
    if s in FOOD_SKUS or s.startswith(('B', 'F', 'K', 'CB', 'CF', 'S')): return "FOOD ITEMS"
    if s in DRY_SKUS or s.startswith(('C', 'P', 'IC', 'RS')): return "DRY ITEMS"
    return "MISC ITEMS"

combined = pd.concat([daily_df, weekly_df], ignore_index=True).drop_duplicates(subset=["SKU"])
combined["Cat"] = combined["SKU"].apply(detect_category)
category_dfs = {cat: combined[combined["Cat"] == cat] for cat in combined["Cat"].unique()}

tab_labels = [f"📂 {cat} ({len(sub_df)})" for cat, sub_df in category_dfs.items()]
selected_tab = st.radio("Category", tab_labels, horizontal=True, label_visibility="collapsed")
active_cat = next(cat for cat in category_dfs if f"📂 {cat}" in selected_tab)

make_grid(category_dfs[active_cat].drop(columns=["Cat"]), f"grid_{active_cat}")

# Final CSS for Radio Tabs
st.markdown("""
    <style>
    div[role="radiogroup"] { display: flex; border-bottom: 2px solid #ddd; }
    div[role="radiogroup"] > label { padding: 10px 20px; cursor: pointer; font-weight: 600; }
    div[role="radiogroup"] > label > div:first-of-type { display: none; }
    div[role="radiogroup"] > label:has(input:checked) { border-bottom: 3px solid #ff4b4b; color: #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

render = lambda df, title: (st.subheader(title), make_grid(df, stable_key("grid", title, df)))
render(daily_df, "📦 Daily Items Stock")
render(weekly_df, "📦 Weekly Items Stock")
