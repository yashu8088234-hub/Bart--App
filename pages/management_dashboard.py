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

st.set_page_config(
    layout="wide",
    page_title="Stock Overview"
)

st.title("📦 BART - Stock Management (All Branches)")

# ========================================================
# GOOGLE AUTH
# ========================================================

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
# RESTORED CATEGORY SETS (MATCHED TO PDF WITH '-')
# ========================================================

FOOD_SKUS = {
    "-", "B034", "F066", "B032", "B029", "F081", "B019", "B018", "CF007", 
    "CF006", "F148", "B028", "K072", "K176", "CB036", "K265", "B016", 
    "CB078", "K154", "CB054", "K226", "CB074", "M&M", "B014", "K242", 
    "S019", "B006", "CB055", "B017", "CB076", "CB056", "B026", "CB037", 
    "K087", "CB043", "CB009", "CB043", "K063"
}

DRY_SKUS = {
    "C013", "IC013", "P244", "P245", "P254", "P095", "P296", "P343", 
    "P343(1)", "P012", "P091", "P155", "P081", "P253", "P101", "P218", 
    "P132", "P264", "P219", "P338", "P341", "P342", "P210", "P320", 
    "P322", "P321", "P082", "P318", "P208", "P315", "C014", "F070", 
    "P298", "P178", "CB009", "C015", "CF009", "P145", "P133", "P156", 
    "RS002", "C011", "C012", "P189", "P160", "C005", "P157", "C010", 
    "C007", "CB010", "P161", "P039", "P125", "C045", "RS001", "P084", 
    "P163", "P162", "C016", "C017", "P158", "C048", "P083"
}

MISC_SKUS = {
    "K063", "T063", "T060", "T066", "TOY1", "ΤΟΥ1", "T026", "SVP", 
    "F089", "P130"
}

# ========================================================
# CACHE
# ========================================================

branch_cache = {}

# ========================================================
# FETCH BRANCH
# ========================================================

def fetch_branch(branch):
    name = branch["BranchName"]
    try:
        ws = client.open_by_key(branch["SheetID"]).worksheet("Stocks")
        data = ws.get_all_values()
        branch_cache[name] = data
        return name, data
    except Exception:
        return name, branch_cache.get(name, [])

# ========================================================
# LOAD ALL DATA (WITH RETRY SYSTEM)
# ========================================================

MAX_RETRIES = 10
RETRY_DELAY = 30

@st.cache_data(ttl=None)
def load_all_data(branches):
    completed = {}
    failed = []

    progress = st.progress(0)
    status = st.empty()

    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(fetch_branch, b): b for b in branches}
        done = 0

        for f in as_completed(futures):
            name, data = f.result()
            if data:
                completed[name] = data
            else:
                failed.append(futures[f])
            done += 1
            progress.progress(done / len(branches))

    round_no = 1
    while failed and round_no <= MAX_RETRIES:
        failed_names = [b["BranchName"] for b in failed]

        with status.container():
            st.info(
                f"Retry {round_no}/{MAX_RETRIES} → "
                f"{', '.join(failed_names)}"
            )

        time.sleep(RETRY_DELAY)
        new_failed = []

        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = {ex.submit(fetch_branch, b): b for b in failed}
            for f in as_completed(futures):
                name, data = f.result()
                if data:
                    completed[name] = data
                else:
                    new_failed.append(futures[f])

        failed = new_failed
        round_no += 1

    if failed:
        status.warning("Some branches still failed after retries")
    else:
        status.success("All branches loaded successfully")
        time.sleep(0.5)
        status.empty()

    return [
        (b["BranchName"], completed.get(b["BranchName"], []))
        for b in branches
    ]

# ========================================================
# REFRESH
# ========================================================

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.cache_resource.clear()
    branch_cache.clear()
    st.rerun()

# ========================================================
# DATE
# ========================================================

selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# ========================================================
# PROCESS STOCK
# ========================================================

@st.cache_data(ttl=None)
def process_stock(all_data, selected_date_str, branch_names):
    daily = {}
    weekly = {}

    for branch_name, raw in all_data:
        if not raw or len(raw) < 2:
            continue

        headers = [str(x).strip() for x in raw[0]]

        date_index = None
        for i, h in enumerate(headers):
            if h == selected_date_str:
                date_index = i
                break

        mode = None

        for row in raw:
            if not row or len(row) < 2:
                continue

            # Check raw string layout text safely
            text = " ".join(str(x) for x in row).lower().strip()

            if "daily item" in text:
                mode = "daily"
                continue

            if "weekly item" in text:
                mode = "weekly"
                continue

            if not mode:
                continue

            # Hard sanitation to remove hidden spaces/newlines inside cells
            item = str(row[0]).strip()
            sku = str(row[1]).replace(" ", "").strip()
            uom = str(row[2]).strip() if len(row) > 2 else ""

            # Drop system header repetitions or pure spacer rows
            if not item or item.lower() in ["item name", "sku", "uom", "", "none"]:
                continue

            key = f"{item}_{sku}_{uom}"
            target = daily if mode == "daily" else weekly

            if key not in target:
                target[key] = {
                    "Item Name": item,
                    "SKU": sku,
                    "UOM": uom
                }
                for b in branch_names:
                    target[key][b] = 0

            qty = 0
            try:
                if date_index is not None and len(row) > date_index:
                    val = str(row[date_index]).strip()
                    qty = 0 if val in ["", None, "-", "None", "nan"] else float(val)
            except:
                qty = 0

            target[key][branch_name] = qty

    return daily, weekly

# ========================================================
# BUILD DF
# ========================================================

def build_df(data_dict, branch_names):
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

# ========================================================
# CATEGORY LOGIC
# ========================================================

def normalize_sku(value):
    return str(value).replace(" ", "").strip().upper()

def detect_category(sku):
    s = normalize_sku(sku)
    
    # Catch empty strings or single dashes immediately
    if not s or s in ["-", "NONE", "NAN", "null"]:
        return "FOOD ITEMS"
        
    # 1. Exact matches
    if s in FOOD_SKUS:
        return "FOOD ITEMS"
    if s in DRY_SKUS:
        return "DRY ITEMS"
    if s in MISC_SKUS:
        return "MISC ITEMS"
        
    # 2. Strict Prefix Pattern matching
    if s.startswith(('B', 'F', 'K', 'CB', 'CF', 'S')):
        return "FOOD ITEMS"
    if s.startswith(('C', 'P', 'IC', 'RS')):
        return "DRY ITEMS"
    if s.startswith(('T', 'SVP', 'TOY', 'ΤΟΥ')):
        return "MISC ITEMS"
        
    return "UNCATEGORIZED DETECTED"

def build_category_dfs(df):
    cats = {
        "FOOD ITEMS": pd.DataFrame(columns=df.columns),
        "DRY ITEMS": pd.DataFrame(columns=df.columns),
        "MISC ITEMS": pd.DataFrame(columns=df.columns),
        "UNCATEGORIZED DETECTED": pd.DataFrame(columns=df.columns)
    }
    
    if df.empty:
        return cats

    category_series = df["SKU"].apply(detect_category)
    
    for cat_name in list(cats.keys()):
        sub_df = df[category_series == cat_name]
        cats[cat_name] = sub_df.sort_values(by="Item Name", key=lambda col: col.str.lower())
        
    if cats["UNCATEGORIZED DETECTED"].empty:
        del cats["UNCATEGORIZED DETECTED"]
        
    return cats

# ========================================================
# AGGRID (STABLE STATE RENDER ENGINE)
# ========================================================

def make_grid(df, key):
    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        resizable=False,
        sortable=True,
        filter=True,
        editable=False,
        wrapText=False,
        autoHeight=False,
        cellStyle={
            "display": "flex",
            "alignItems": "center",
            "fontSize": "13px"
        }
    )

    gb.configure_column("Item Name", pinned="left", lockPinned=True, width=250)
    gb.configure_column("SKU", pinned="left", lockPinned=True, width=100)
    gb.configure_column("UOM", pinned="left", lockPinned=True, width=100)

    for b in branch_names:
        gb.configure_column(
            b,
            type=["numericColumn"],
            wrapText=False,
            width=120,
            cellStyle={
                "textAlign": "center",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "fontSize": "13px"
            }
        )

    gb.configure_grid_options(
        headerHeight=38,
        rowHeight=32,
        suppressHorizontalScroll=False,
        alwaysShowHorizontalScroll=True,
        alwaysShowVerticalScroll=True
    )

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        fit_columns_on_grid_load=False,
        enable_enterprise_modules=False,
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        reload_data=True,
        height=500,
        width="100%",
        key=key
    )

# ========================================================
# PIPELINE RUN
# ========================================================

all_data = load_all_data(branches)

daily_items, weekly_items = process_stock(
    all_data,
    selected_date_str,
    branch_names
)

daily_df = build_df(daily_items, branch_names)
weekly_df = build_df(weekly_items, branch_names)

# ========================================================
# CATEGORY VIEW (FIXED VIA CONTAINER SCOPING)
# ========================================================

st.subheader("📊 Category Wise Stock Overview")

category_dfs = build_category_dfs(daily_df)

tab_titles = [f"📂 {cat} ({len(sub_df)})" for cat, sub_df in category_dfs.items()]
tabs = st.tabs(tab_titles)

for i, (cat, sub_df) in enumerate(category_dfs.items()):
    with tabs[i]:
        if not sub_df.empty:
            if cat == "UNCATEGORIZED DETECTED":
                st.warning("⚠️ These items do not match explicit SKU sets or prefix codes:")
            
            # THE MAGIC FIX FOR TABS: Injecting selection constraints directly into 
            # the programmatic key forces a clean layout reset upon switching views.
            grid_key = f"grid_tab_{cat.replace(' ', '_').lower()}_{selected_date_str}"
            
            make_grid(sub_df, grid_key)
        else:
            st.info(f"No items in {cat}")

# ========================================================
# MAIN TABLES
# ========================================================

def render(df, title):
    st.subheader(title)
    if df.empty:
        st.warning("No Data")
        return
    fixed_render_key = f"main_grid_{title.replace(' ', '_').lower()}_{selected_date_str}"
    make_grid(df, fixed_render_key)

render(daily_df, "📦 Daily Items Stock")
render(weekly_df, "📦 Weekly Items Stock")
