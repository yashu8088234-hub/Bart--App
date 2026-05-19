import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import time
import re

# ========================================================
# PAGE CONFIG
# ========================================================

st.set_page_config(layout="wide", page_title="Stock Overview")
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
# BRANCHES
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
# RETRY SYSTEM
# ========================================================

MAX_RETRIES = 10
RETRY_DELAY = 60

branch_cache = {}

def fetch_branch(branch):

    name = branch["BranchName"]

    try:
        ws = client.open_by_key(branch["SheetID"]).worksheet("Stocks")
        data = ws.get_all_values()

        branch_cache[name] = data

        return {
            "branch": name,
            "success": True,
            "data": data
        }

    except Exception:

        if name in branch_cache:
            return {
                "branch": name,
                "success": False,
                "data": branch_cache[name]
            }

        return {
            "branch": name,
            "success": False,
            "data": []
        }

@st.cache_data(ttl=None)
def load_all_data(branches):

    completed = {}
    failed = []

    progress = st.progress(0)
    status = st.empty()

    with ThreadPoolExecutor(max_workers=3) as ex:

        futures = {
            ex.submit(fetch_branch, b): b
            for b in branches
        }

        done = 0

        for f in as_completed(futures):

            r = f.result()
            name = r["branch"]

            if r["success"] or r["data"]:
                completed[name] = r["data"]
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

            futures = {
                ex.submit(fetch_branch, b): b
                for b in failed
            }

            for f in as_completed(futures):

                r = f.result()
                name = r["branch"]

                if r["success"] or r["data"]:
                    completed[name] = r["data"]
                else:
                    new_failed.append(futures[f])

        failed = new_failed
        round_no += 1

    if failed:
        status.warning("Some branches still failed")
    else:
        status.empty()

    return [
        (
            b["BranchName"],
            completed.get(b["BranchName"], [])
        )
        for b in branches
    ]

all_data = load_all_data(branches)

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
# CLEANING ENGINE
# ========================================================

def clean_text(text):

    text = str(text).lower()

    # remove arabic
    text = re.sub(r"[\u0600-\u06FF]+", " ", text)

    # normalize symbols
    text = re.sub(r"[^a-z0-9]", " ", text)

    # remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text

def normalize_tokens(text):
    return set(clean_text(text).split())

# ========================================================
# ROBUST MATCHING ENGINE
# ========================================================

def robust_match(item_name, category_item):

    a = clean_text(item_name)
    b = clean_text(category_item)

    # exact clean match
    if a == b:
        return True

    # token matching
    a_tokens = normalize_tokens(a)
    b_tokens = normalize_tokens(b)

    if not a_tokens or not b_tokens:
        return False

    intersection = a_tokens.intersection(b_tokens)

    ratio_a = len(intersection) / len(a_tokens)
    ratio_b = len(intersection) / len(b_tokens)

    # robust matching threshold
    if ratio_a >= 0.8 and ratio_b >= 0.8:
        return True

    # contains match
    if a in b or b in a:
        return True

    return False

# ========================================================
# STOCK PROCESSING
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

            if not row:
                continue

            text = " ".join(str(x) for x in row).lower()

            if "daily item" in text:
                mode = "daily"
                continue

            if "weekly item" in text:
                mode = "weekly"
                continue

            if not mode:
                continue

            item = str(row[0]).strip() if len(row) > 0 else ""
            sku = str(row[1]).strip() if len(row) > 1 else ""
            uom = str(row[2]).strip() if len(row) > 2 else ""

            if not item:
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

                    val = row[date_index]

                    qty = 0 if val in ["", None] else float(val)

            except:
                qty = 0

            target[key][branch_name] = qty

    return daily, weekly

daily_items, weekly_items = process_stock(
    all_data,
    selected_date_str,
    branch_names
)

# ========================================================
# DATAFRAME BUILDER
# ========================================================

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

# ========================================================
# CATEGORY LISTS
# ========================================================

FOOD_ITEMS = set([
"ARWA Water 330ML","BART French Toast Brioche",
"BELCHOCO Feuilletine Flakes","Berry Ice Tea",
"Bidfood - EMBORG Cooking Cream 12*1L",
"CARLEX Spray Release Agent 6 x 600 ML",
"Chocolate Pudding Cup","Cinnamon powder",
"Code Blue Syrup","Code Red Syrup",
"Coffee - Blend DR - DR","Coffee - Blend U- U",
"Crunchy Chocolate Cake Slice","DAM Dubai Filling",
"FRICHILI Cooking Cream 20% FAT 12x1Kg",
"Frozen Whole Egg Liquid","Galaxy Chocolate Bars",
"Hibiscus Ice Tea","Igloo Evens Chocolate",
"KDD Vanilla Soft Ice Cream","Kinder Sauce",
"KitKat 18x36x20.5g","Lotus Crumble 250gm",
"M&M's Chocolate (24*45gm)","Mango Juice Gallon",
"Nadec - UHT Milk FF 12 x 1L","Nestle Sauce",
"Nutella Sauce","Peach Ice Tea Syrup",
"Pecan Sauce","Pudding Sauce",
"Red Bull Watermelon Slush","Roasted Kunafa",
"Salt SASA 750 gm","Vanilla Powder"
])

DRY_ITEMS = set([
"Apron","BART Cinnamoroll Ice Cream Holder",
"BART MM Ice Cream Holder",
"BART PPG Paper Cup 12 Oz (Dark Pink)",
"BART PPG Paper Cup 12 Oz (Green)",
"BART PPG Paper Cup 12 Oz (Light Pink)",
"BART Plastic Cold Cup 12oz",
"BART White Paper Cup 16oz","Baladiya Bag",
"Bart Galaxy Paper Cup 12 Oz",
"Black Plastic Knife (pp)",
"Black Straw 4 ML (20 x 200 Pcs)",
"Black Straw 8 ML (20 x 100 Pcs)",
"Cloudy Gift Cup 16Oz (INNER WHITE CUP)",
"Cloudy Gift Cup 16Oz (OUTER GRAPHIC CUP)",
"Coffee Filter Papers","Cup 2 Tray- Bart",
"Cup 4 Tray- Bart","Cups for Ice Cream Test",
"Date Sticker","Flat Lid for Cold Cup",
"French Toast Holder 2 Holes - Bart","Gloves",
"HDPE Poly Gloves (100 Packet x 50 Pcs)",
"HK French Toast Holder 2 Holes - Bart",
"Hair Net","Ice Cream Black Spoon",
"Ice Cream Plastic Cup",
"Ice Cream Plastic Cup 3 Oz",
"Ice Cream Plastic Cup Cover",
"Injection Lid for Paper Cup",
"Kinder Paper Cup 12oz",
"Kinder Sticker Label",
"Kitchen Tissue Roll",
"Lid for Ice Cream Plastic Cup 3 Oz",
"Lid for Ice Cream Test Cup",
"⁠Nutella Sticker Label","Mask",
"POS Roll",
"PP Flat Black Lid for 12 Oz Plastic Cup",
"Plastic Cups 12 Oz",
"Plastic Fork Black (20*50)(pp)",
"Printed Paper Bag W/ Handle - Bart",
"Printed Paper Cup 12oz - Bart",
"SCOTCH FOR SAJ",
"Scotch Bright",
"Shrink Naylon Film",
"Small Cake Box",
"Sticker BART",
"T. NAP 30X30 1P",
"Thermal Coffee Container",
"Trash bags 20 Gallon",
"White Lid for Paper Cup 12oz - Bart"
])

MISC_ITEMS = set([
"BART PPG Figurine",
"BART PPG Figurines (Toys)",
"BART Stainless Steel Forks",
"Bart Black Shovel Spoon",
"Cloudy Figurine Toy",
"Kuromi Sanrio Acrylic Keychain",
"Shovel Spoon",
"Staff Chicken Strips Bag",
"Wooden Coffee Stirrers - Bart"
])

# ========================================================
# CATEGORY ENGINE
# ========================================================

def detect_category(name):

    # FOOD
    for item in FOOD_ITEMS:
        if robust_match(name, item):
            return "FOOD ITEMS"

    # DRY
    for item in DRY_ITEMS:
        if robust_match(name, item):
            return "DRY ITEMS"

    # MISC
    for item in MISC_ITEMS:
        if robust_match(name, item):
            return "Miscellaneous"

    return "Miscellaneous"

# ========================================================
# CATEGORY BUILDER
# ========================================================

def build_category(df):

    cats = {
        "FOOD ITEMS": [],
        "DRY ITEMS": [],
        "Miscellaneous": []
    }

    for _, row in df.iterrows():

        cat = detect_category(row["Item Name"])

        cats[cat].append(row)

    for k in cats:

        cats[k] = sorted(
            cats[k],
            key=lambda x: clean_text(x["Item Name"])
        )

    return cats

# ========================================================
# AGGRID
# ========================================================

def make_grid(df, key):

    gb = GridOptionsBuilder.from_dataframe(df)

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True,
        wrapText=False,
        autoHeight=False
    )

    # ====================================================
    # FIX FIRST 3 COLUMNS
    # ====================================================

    gb.configure_column(
        "Item Name",
        pinned="left",
        width=300
    )

    gb.configure_column(
        "SKU",
        pinned="left",
        width=140
    )

    gb.configure_column(
        "UOM",
        pinned="left",
        width=100
    )

    # ====================================================
    # AUTO SIZE FOR BRANCHES
    # ====================================================

    for b in branch_names:
        gb.configure_column(
            b,
            width=110,
            type=["numericColumn"]
        )

    # ====================================================
    # GRID OPTIONS
    # ====================================================

    gb.configure_grid_options(
        domLayout='normal',
        suppressHorizontalScroll=False,
        alwaysShowHorizontalScroll=True,
        alwaysShowVerticalScroll=True
    )

    AgGrid(
        df,
        gridOptions=gb.build(),
        theme="streamlit",
        enable_enterprise_modules=False,
        fit_columns_on_grid_load=False,
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        reload_data=False,
        height=500,
        width='100%',
        key=key
    )

# ========================================================
# CATEGORY UI
# ========================================================

st.subheader("📊 Category Wise Stock Overview")

category_data = build_category(daily_df)

for cat, rows in category_data.items():

    with st.expander(f"📂 {cat} ({len(rows)})", expanded=False):

        if not rows:
            st.info("No items")
            continue

        df = pd.DataFrame(rows)

        # ====================================================
        # SHOW COUNTS
        # ====================================================

        if cat == "FOOD ITEMS":
            st.caption(f"Expected Around: 35 Items | Found: {len(df)}")

        elif cat == "DRY ITEMS":
            st.caption(f"Expected Around: 53 Items | Found: {len(df)}")

        elif cat == "Miscellaneous":
            st.caption(f"Expected Around: 9 Items | Found: {len(df)}")

        # ====================================================
        # SCROLLABLE GRID
        # ====================================================

        make_grid(df, f"cat_{cat}")

# ========================================================
# DAILY / WEEKLY TABLES
# ========================================================

def render(df, title):

    st.subheader(title)

    if df.empty:
        st.warning("No Data")
        return

    make_grid(df, title)

render(daily_df, "📦 Daily Items Stock")
render(weekly_df, "📦 Weekly Items Stock")
