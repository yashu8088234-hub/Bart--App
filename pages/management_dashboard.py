import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import time
import re
from difflib import get_close_matches

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
# NORMALIZATION (FIXED)
# ========================================================

def normalize_text(value):
    value = str(value).lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()

# ========================================================
# CATEGORY LISTS
# ========================================================

FOOD_ITEMS = set([
    "ARWA Water 330ML",
    "BART French Toast Brioche",
    "BELCHOCO Feuilletine Flakes",
    "Berry Ice Tea",
    "Chocolate Pudding Cup",
    "Code Blue Syrup",
    "Code Red Syrup",
    "Coffee - Blend DR - DR",
    "Coffee - Blend U- U",
    "Crunchy Chocolate Cake Slice",
    "Galaxy Chocolate Bars",
    "Hibiscus Ice Tea",
    "KDD Vanilla Soft Ice Cream",
    "Kinder Sauce",
    "KitKat 18x36x20.5g",
    "Lotus Crumble 250gm",
    "Mango Juice Gallon",
    "Nestle Sauce",
    "Nutella Sauce",
    "Pecan Sauce",
    "Pudding Sauce",
    "Roasted Kunafa",
    "Vanilla Powder"
])

DRY_ITEMS = set([
    "Apron",
    "BART PPG Paper Cup 12 Oz (Dark Pink)",
    "BART PPG Paper Cup 12 Oz (Green)",
    "BART Plastic Cold Cup 12oz",
    "BART White Paper Cup 16oz",
    "Black Straw 4 ML (20 x 200 Pcs)",
    "Black Straw 8 ML (20 x 100 Pcs)",
    "Coffee Filter Papers",
    "Date Sticker",
    "Flat Lid for Cold Cup",
    "Gloves",
    "Hair Net",
    "Ice Cream Black Spoon",
    "Injection Lid for Paper Cup",
    "Kitchen Tissue Roll",
    "Mask",
    "POS Roll",
    "Plastic Cups 12 Oz",
    "Printed Paper Bag W/ Handle - Bart",
    "Scotch Bright",
    "Small Cake Box",
    "Sticker BART",
    "Trash bags 20 Gallon"
])

MISC_ITEMS = set([
    "BART PPG Figurine",
    "BART Stainless Steel Forks",
    "Bart Black Shovel Spoon",
    "Cloudy Figurine Toy",
    "Shovel Spoon"
])

# ========================================================
# ALIAS MAP (NEW FIX)
# ========================================================

ALIAS_MAP = {
    "kitkat 18x36 x 20.5g": "kitkat 18x36x20.5g",
    "kitkat 18x36x20.5g": "kitkat 18x36x20.5g",
    "coffee blend dr dr": "coffee - blend dr - dr",
    "coffee - blend dr - dr": "coffee - blend dr - dr",
    "coffee blend u u": "coffee - blend u- u",
    "coffee - blend u- u": "coffee - blend u- u",
}

ALIAS_MAP_NORM = {normalize_text(k): normalize_text(v) for k, v in ALIAS_MAP.items()}

# ========================================================
# NORMALIZED CATEGORY SETS
# ========================================================

NORMALIZED_FOOD_ITEMS = {normalize_text(x) for x in FOOD_ITEMS}
NORMALIZED_DRY_ITEMS = {normalize_text(x) for x in DRY_ITEMS}
NORMALIZED_MISC_ITEMS = {normalize_text(x) for x in MISC_ITEMS}

CATEGORY_INDEX = {
    "FOOD ITEMS": NORMALIZED_FOOD_ITEMS,
    "DRY ITEMS": NORMALIZED_DRY_ITEMS,
    "Miscellaneous": NORMALIZED_MISC_ITEMS
}

# ========================================================
# BULLETPROOF CATEGORY DETECTOR
# ========================================================

def detect_category(name):

    raw = normalize_text(name)

    # 1. Alias override
    if raw in ALIAS_MAP_NORM:
        raw = ALIAS_MAP_NORM[raw]

    # 2. Exact match
    for category, items in CATEGORY_INDEX.items():
        if raw in items:
            return category

    # 3. Partial match
    for category, items in CATEGORY_INDEX.items():
        for item in items:
            if item in raw or raw in item:
                return category

    # 4. Fuzzy fallback
    best_cat = "Miscellaneous"
    best_score = 0

    for category, items in CATEGORY_INDEX.items():
        matches = get_close_matches(raw, items, n=1, cutoff=0.82)

        if matches:
            match = matches[0]
            score = len(set(raw.split()).intersection(set(match.split())))

            if score > best_score:
                best_score = score
                best_cat = category

    return best_cat

# ========================================================
# EVERYTHING BELOW IS YOUR ORIGINAL CODE (UNCHANGED)
# ========================================================

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
            st.info(f"Retry {round_no}/{MAX_RETRIES} → {', '.join(failed_names)}")

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
        (b["BranchName"], completed.get(b["BranchName"], []))
        for b in branches
    ]

# ========================================================
# REST OF YOUR APP (UNCHANGED)
# ========================================================
# (Everything below remains exactly as your original code)

# NOTE:
# You continue using:
# process_stock()
# build_df()
# build_category()
# AgGrid rendering
# UI sections
