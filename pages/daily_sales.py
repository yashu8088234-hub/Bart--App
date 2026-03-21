import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from rapidfuzz import process, fuzz
from datetime import datetime
import time

# ---------------- Page Config ----------------
st.set_page_config(layout="wide", page_title="BART - Daily Sales")

# ---------------- Hide Streamlit UI ----------------
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}
div.stButton > button {height:65px; font-size:20px; border-radius:12px; margin:8px; width:230px;}
div.stButton > button:hover {background-color:#ff4b4b; color:white;}
</style>
""", unsafe_allow_html=True)

# ---------------- Load Valid Items ----------------
with open("bart_items.txt", "r", encoding="utf-8") as f:
    valid_items = [line.strip() for line in f.readlines()]

# ---------------- Google Sheets Setup ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Master Inventory").worksheet("Daily Sales")
except Exception as e:
    st.error(f"Google Sheets connection error: {e}")
    st.stop()

# ---------------- Page Title ----------------
st.markdown("<h1 style='text-align:center; color:red;'>Daily Sales Entry</h1>", unsafe_allow_html=True)

# ---------------- Date Input ----------------
date = st.date_input("Select Sales Date", value=datetime.today())
date_str = date.strftime("%Y-%m-%d")
st.info(f"Sales will be recorded under date: {date_str}")

# ---------------- Sales Input ----------------
sales_text = st.text_area(
    "Paste daily sales here (format: Item - Quantity - Unit Price)",
    height=300
)

# ---------------- Parse Sales ----------------
sales_today = []

if sales_text:
    lines = sales_text.split("\n")

    for line in lines:
        line = line.strip()

        if not line or "-" not in line:
            continue

        try:
            item, qty, price = line.rsplit("-", 2)

            item = item.strip()
            qty = float(qty.strip())
            price = float(price.strip())

            sales_today.append((item, qty, price))

        except:
            st.warning(f"Invalid format: {line}")

# ---------------- Session State ----------------
if "pending_sales" not in st.session_state:
    st.session_state.pending_sales = []

if "confirm_items" not in st.session_state:
    st.session_state.confirm_items = {}

# ---------------- Match Items ----------------
for item_name, qty, price in sales_today:

    if item_name not in st.session_state.confirm_items and \
       not any(item_name == x[0] for x in st.session_state.pending_sales):

        matches = process.extract(
            item_name,
            valid_items,
            scorer=fuzz.token_set_ratio,
            limit=len(valid_items)
        )

        best_matches = [m for m in matches if m[1] > 70]

        if not best_matches:

            st.warning(f"Item '{item_name}' not recognized")

        elif len(best_matches) == 1:

            st.session_state.pending_sales.append(
                (best_matches[0][0], qty, price)
            )

            st.success(f"{best_matches[0][0]} added automatically")

        else:

            options = [m[0] for m in best_matches]

            st.session_state.confirm_items[item_name] = st.radio(
                f"Select correct item for '{item_name}' ({qty} @ {price})",
                options,
                key=f"match_{item_name}"
            )

# ---------------- Confirm Selections ----------------
if st.session_state.confirm_items:

    if st.button("✅ Confirm All Selected Items"):

        for item_name, selected_item in st.session_state.confirm_items.items():

            qty, price = next(
                (q, p) for i, q, p in sales_today if i == item_name
            )

            st.session_state.pending_sales.append(
                (selected_item, qty, price)
            )

        st.success("Items confirmed")

        st.session_state.confirm_items.clear()

# ---------------- Show Pending ----------------
if st.session_state.pending_sales:

    st.markdown("### Pending Sales")

    for i, (iname, qty, price) in enumerate(st.session_state.pending_sales):

        st.checkbox(
            f"{iname} → Qty: {qty} | Price: {price} | Total: {qty*price}",
            value=True,
            key=f"chk_{i}"
        )

# ---------------- Submit Function ----------------
def safe_append(row):

    for attempt in range(3):

        try:
            sheet.append_row(row)
            return True

        except Exception as e:

            if attempt < 2:
                time.sleep(2)  # retry delay
            else:
                st.error(f"Google API error: {e}")
                return False

# ---------------- Submit ----------------
if st.button("Submit Pending Sales"):

    success = True

    for i, (iname, qty, price) in enumerate(st.session_state.pending_sales):

        if st.session_state.get(f"chk_{i}", True):

            row = [date_str, iname, qty, price, qty * price]

            if not safe_append(row):
                success = False

    if success:
        st.success("Sales successfully uploaded to Google Sheet ✅")
        st.session_state.pending_sales = []

# ---------------- Back Button ----------------
if st.button("⬅ Back"):
    st.switch_page("pages/staff_dashboard.py")