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
st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management (All Branches)")

# ========================================================
# GOOGLE AUTH
# ========================================================
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

client = get_client()

# ========================================================
# LOAD BRANCHES
# ========================================================
@st.cache_data(ttl=None)
def load_branches():
    sheet = client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [{"BranchName": str(b["BranchName"]).strip(), "SheetID": str(b["SheetID"]).strip()} 
            for b in data if b.get("SheetID") and b.get("BranchName")]

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# ========================================================
# SKU SETS & DATA FETCHING
# ========================================================
FOOD_SKUS = {"-", "B034", "F066", "B032", "B029", "F081", "B019", "B018", "CF007", "CF006", "F148", "B028", "K072", "K176", "CB036", "K265", "B016", "CB078", "K154", "CB054", "K226", "CB074", "M&M", "B014", "K242", "S019", "B006", "CB055", "B017", "CB076", "CB056", "B026", "CB037", "K087", "CB043", "CB009", "K063"}
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
        futures = [ex.submit(fetch_branch, b) for b in branches]
        for f in as_completed(futures):
            name, data = f.result()
            if data: completed[name] = data
    return [(b["BranchName"], completed.get(b["BranchName"], [])) for b in branches]

# ========================================================
# GRID FUNCTION (RESTORED SPACING & SCROLLING)
# ========================================================
def make_grid(df, key):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        resizable=False, sortable=True, filter=True, editable=False,
        cellStyle={"display": "flex", "alignItems": "center", "fontSize": "13px", "paddingTop": "0px", "paddingBottom": "0px"}
    )
    gb.configure_column("Item Name", pinned="left", lockPinned=True, width=250)
    gb.configure_column("SKU", pinned="left", lockPinned=True, width=100)
    gb.configure_column("UOM", pinned="left", lockPinned=True, width=100)
    
    for b in branch_names:
        gb.configure_column(b, type=["numericColumn"], width=120, cellStyle={"textAlign": "center", "display": "flex", "alignItems": "center", "justifyContent": "center", "fontSize": "13px", "paddingTop": "0px", "paddingBottom": "0px"})
    
    gb.configure_grid_options(
        headerHeight=38, rowHeight=32, domLayout='normal',
        alwaysShowHorizontalScroll=True, alwaysShowVerticalScroll=True
    )
    
    AgGrid(
        df, gridOptions=gb.build(), height=500, theme="streamlit", key=key,
        custom_css={
            ".ag-header-cell-label": {"justify-content": "center", "font-size": "12px", "font-weight": "600"},
            ".ag-header-cell": {"padding-top": "0px", "padding-bottom": "0px"},
            ".ag-cell": {"padding-top": "0px", "padding-bottom": "0px"},
            ".ag-body-viewport": {"overflow-y": "auto !important"}
        },
        update_mode=GridUpdateMode.NO_UPDATE, allow_unsafe_jscode=True
    )

# ========================================================
# PROCESSING
# ========================================================
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

selected_date = st.date_input("📅 Select Date").strftime("%Y-%m-%d")

def process_stock(all_data, date_str, branches):
    daily, weekly = {}, {}
    for b_name, raw in all_data:
        if len(raw) < 2: continue
        headers = [str(x).strip() for x in raw[0]]
        idx = next((i for i, h in enumerate(headers) if h == date_str), None)
        mode = None
        for row in raw:
            text = " ".join(str(x) for x in row).lower()
            if "daily item" in text: mode = "daily"; continue
            if "weekly item" in text: mode = "weekly"; continue
            if not mode or not row[0]: continue
            item, sku, uom = str(row[0]).strip(), str(row[1]).replace(" ", "").strip(), str(row[2]).strip()
            key = f"{item}_{sku}_{uom}"
            target = daily if mode == "daily" else weekly
            if key not in target: target[key] = {"Item Name": item, "SKU": sku, "UOM": uom, **{b: 0 for b in branches}}
            if idx and len(row) > idx:
                val = str(row[idx]).strip()
                target[key][b_name] = 0 if val in ["", "-", "None"] else float(val)
    return daily, weekly

def detect_cat(sku):
    s = str(sku).replace(" ", "").upper()
    if s in FOOD_SKUS or s.startswith(('B', 'F', 'K', 'CB', 'CF', 'S')): return "FOOD ITEMS"
    if s in DRY_SKUS or s.startswith(('C', 'P', 'IC', 'RS')): return "DRY ITEMS"
    if s in MISC_SKUS or s.startswith(('T', 'SVP', 'TOY', 'ΤΟΥ')): return "MISC ITEMS"
    return "UNCATEGORIZED"

# ========================================================
# RENDER
# ========================================================
all_data = load_all_data(branches)
daily_d, weekly_d = process_stock(all_data, selected_date, branch_names)
daily_df = pd.DataFrame([{"Item Name": v["Item Name"], "SKU": v["SKU"], "UOM": v["UOM"], **{b: v.get(b, 0) for b in branch_names}} for v in daily_d.values()])
weekly_df = pd.DataFrame([{"Item Name": v["Item Name"], "SKU": v["SKU"], "UOM": v["UOM"], **{b: v.get(b, 0) for b in branch_names}} for v in weekly_d.values()])

st.subheader("📊 Category Wise Stock Overview")
combined = pd.concat([daily_df, weekly_df]).drop_duplicates()
cats = {c: combined[combined["SKU"].apply(detect_cat) == c] for c in ["FOOD ITEMS", "DRY ITEMS", "MISC ITEMS", "UNCATEGORIZED"]}
tabs = st.tabs([f"📂 {c}" for c in cats if not cats[c].empty])

for i, (name, df) in enumerate([c for c in cats.items() if not c[1].empty]):
    with tabs[i]:
        make_grid(df, f"cat_{name}_{selected_date}")

st.subheader("📦 Daily Items Stock")
make_grid(daily_df, f"daily_{selected_date}")
st.subheader("📦 Weekly Items Stock")
make_grid(weekly_df, f"weekly_{selected_date}")
