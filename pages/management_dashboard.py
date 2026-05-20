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
scope = ["https://spreadsheets.google.com/feeds", "https://googleapis.com/auth/drive"]

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
    branches = []
    for b in data:
        if b.get("SheetID") and b.get("BranchName"):
            branches.append({
                "BranchName": str(b["BranchName"]).strip(),
                "SheetID": str(b["SheetID"]).strip()
            })
    return branches

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# ========================================================
# SKU SETS
# ========================================================
FOOD_SKUS = {"-", "B034", "F066", "B032", "B029", "F081", "B019", "B018", "CF007", "CF006", "F148", "B028", "K072", "K176", "CB036", "K265", "B016", "CB078", "K154", "CB054", "K226", "CB074", "M&M", "B014", "K242", "S019", "B006", "CB055", "B017", "CB076", "CB056", "B026", "CB037", "K087", "CB043", "CB009", "CB043", "K063"}
DRY_SKUS = {"C013", "IC013", "P244", "P245", "P254", "P095", "P296", "P343", "P343(1)", "P012", "P091", "P155", "P081", "P253", "P101", "P218", "P132", "P264", "P219", "P338", "P341", "P342", "P210", "P320", "P322", "P321", "P082", "P318", "P208", "P315", "C014", "F070", "P298", "P178", "CB009", "C015", "CF009", "P145", "P133", "P156", "RS002", "C011", "C012", "P189", "P160", "C005", "P157", "C010", "C007", "CB010", "P161", "P039", "P125", "C045", "RS001", "P084", "P163", "P162", "C016", "C017", "P158", "C048", "P083"}
MISC_SKUS = {"K063", "T063", "T060", "T066", "TOY1", "ΤΟΥ1", "T026", "SVP", "F089", "P130"}

branch_cache = {}

def fetch_branch(branch):
    name = branch["BranchName"]
    try:
        ws = client.open_by_key(branch["SheetID"]).worksheet("Stocks")
        data = ws.get_all_values()
        branch_cache[name] = data
        return name, data
    except Exception:
        return name, branch_cache.get(name, [])

@st.cache_data(ttl=None)
def load_all_data(branches):
    completed = {}
    failed = []
    progress = st.progress(0)
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(fetch_branch, b): b for b in branches}
        done = 0
        for f in as_completed(futures):
            name, data = f.result()
            if data: completed[name] = data
            else: failed.append(futures[f])
            done += 1
            progress.progress(done / len(branches))
    return [(b["BranchName"], completed.get(b["BranchName"], [])) for b in branches]

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

@st.cache_data(ttl=None)
def process_stock(all_data, selected_date_str, branch_names):
    daily, weekly = {}, {}
    for branch_name, raw in all_data:
        if not raw or len(raw) < 2: continue
        headers = [str(x).strip() for x in raw[0]]
        date_index = next((i for i, h in enumerate(headers) if h == selected_date_str), None)
        mode = None
        for row in raw:
            if not row: continue
            text = " ".join(str(x) for x in row).lower()
            if "daily item" in text: mode = "daily"; continue
            if "weekly item" in text: mode = "weekly"; continue
            if not mode: continue
            item, sku, uom = str(row[0]).strip(), str(row[1]).replace(" ", "").strip(), str(row[2]).strip()
            if not item: continue
            key = f"{item}_{sku}_{uom}"
            target = daily if mode == "daily" else weekly
            if key not in target:
                target[key] = {"Item Name": item, "SKU": sku, "UOM": uom, **{b: 0 for b in branch_names}}
            try:
                if date_index is not None and len(row) > date_index:
                    val = str(row[date_index]).strip()
                    target[key][branch_name] = 0 if val in ["", None, "-", "None"] else float(val)
            except: pass
    return daily, weekly

def build_df(data_dict, branch_names):
    return pd.DataFrame([{"Item Name": v["Item Name"], "SKU": v["SKU"], "UOM": v["UOM"], **{b: v.get(b, 0) for b in branch_names}} for v in data_dict.values()])

def detect_category(sku):
    s = str(sku).replace(" ", "").strip().upper()
    if not s or s in ["-", "NONE", "NAN"]: return "FOOD ITEMS"
    if s in FOOD_SKUS: return "FOOD ITEMS"
    if s in DRY_SKUS: return "DRY ITEMS"
    if s in MISC_SKUS: return "MISC ITEMS"
    if s.startswith(('B', 'F', 'K', 'CB', 'CF', 'S')): return "FOOD ITEMS"
    if s.startswith(('C', 'P', 'IC', 'RS')): return "DRY ITEMS"
    if s.startswith(('T', 'SVP', 'TOY', 'ΤΟΥ')): return "MISC ITEMS"
    return "UNCATEGORIZED DETECTED"

def build_category_dfs(df):
    cats = {c: pd.DataFrame(columns=df.columns) for c in ["FOOD ITEMS", "DRY ITEMS", "MISC ITEMS", "UNCATEGORIZED DETECTED"]}
    if df.empty: return cats
    cat_series = df["SKU"].apply(detect_category)
    for cat in cats:
        cats[cat] = df[cat_series == cat].sort_values(by="Item Name", key=lambda x: x.str.lower())
    return {k: v for k, v in cats.items() if not v.empty}

# ========================================================
# FIXED AGGRID
# ========================================================
def make_grid(df, key):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(resizable=False, sortable=True, filter=True, editable=False)
    gb.configure_column("Item Name", pinned="left", width=250)
    gb.configure_column("SKU", pinned="left", width=100)
    gb.configure_column("UOM", pinned="left", width=100)
    # FORCE SCROLLING WITH PAGINATION AND DOM LAYOUT
    gb.configure_pagination(paginationPageSize=50)
    gb.configure_grid_options(
        headerHeight=38, rowHeight=32, 
        domLayout='normal', # Prevents squashing
        alwaysShowHorizontalScroll=True
    )
    AgGrid(
        df, gridOptions=gb.build(), height=500, 
        theme="streamlit", key=key, update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True
    )

# ========================================================
# RUN PIPELINE
# ========================================================
all_data = load_all_data(branches)
daily_items, weekly_items = process_stock(all_data, selected_date_str, branch_names)
daily_df, weekly_df = build_df(daily_items, branch_names), build_df(weekly_items, branch_names)

st.subheader("📊 Category Wise Stock Overview")
combined_stock = pd.concat([daily_df, weekly_df], ignore_index=True).drop_duplicates()
category_dfs = build_category_dfs(combined_stock)
tabs = st.tabs([f"📂 {cat}" for cat in category_dfs])

for i, (cat, sub_df) in enumerate(category_dfs.items()):
    with tabs[i]:
        make_grid(sub_df, f"tab_{cat}_{selected_date_str}")

st.subheader("📦 Daily/Weekly Tables")
make_grid(daily_df, f"daily_{selected_date_str}")
make_grid(weekly_df, f"weekly_{selected_date_str}")
