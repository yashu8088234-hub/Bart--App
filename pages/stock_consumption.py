import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from rapidfuzz import process, fuzz
from background import set_background
import time

# -----------------------------
# Background & UI Setup
# -----------------------------
set_background("barthomepage.jpg")
st.set_page_config(page_title="Daily Stock Consumption", layout="wide")

# Hide Streamlit UI + remove number input spinners
hide_streamlit = """
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stToolbar"] {display:none;}
[data-testid="stSidebar"] {display:none;}
.block-container {padding:0 !important; margin:0 auto !important; max-width: 100% !important;}
.stApp {background: linear-gradient(135deg,#eef2f7,#d6e4ff);}
div.stButton > button{height:60px;font-size:20px;border-radius:10px;transition:0.3s;}
div.stButton > button:hover{background-color:#ff4b4b;color:white;}
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }
</style>
"""
st.markdown(hide_streamlit, unsafe_allow_html=True)

# -----------------------------
# Page Title
# -----------------------------
branch_name_display = st.session_state.get("selected_branch", "Unknown Branch")
st.markdown(f"<h1 style='text-align:center; color:red; font-size:60px;'>{branch_name_display} - Daily Stock Consumption</h1>", unsafe_allow_html=True)

# -----------------------------
# Google Sheets Setup
# -----------------------------
try:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"Error connecting to Google API: {e}")
    st.stop()

# -----------------------------
# Dynamic Branch Sheet & Tab
# -----------------------------
if "sheet_id" not in st.session_state or "tab_name" not in st.session_state:
    st.error("No branch or tab selected. Please go back to Staff Dashboard.")
    st.stop()

branch_sheet = client.open_by_key(st.session_state.sheet_id)
sheet = branch_sheet.worksheet(st.session_state.tab_name)
st.write(f"Using tab: {sheet.title}")

# -----------------------------
# Cached Sheet Data
# -----------------------------
@st.cache_data(ttl=300)
def load_sheet(_sheet):
    data = _sheet.get_all_values()
    headers = data[0]
    items = [row[0].strip() for row in data[1:]]
    items_lower = [i.lower() for i in items]
    return data, headers, items, items_lower

try:
    sheet_data, headers, existing_items_list, existing_items_lower = load_sheet(sheet)
except Exception as e:
    st.error(f"Error loading sheet data: {e}")
    st.stop()

# -----------------------------
# Session States
# -----------------------------
if "pending_updates" not in st.session_state:
    st.session_state.pending_updates = []

if "selected_items" not in st.session_state:
    st.session_state.selected_items = {}

if "pending_checkbox_state" not in st.session_state:
    st.session_state.pending_checkbox_state = {}

if "inventory_mode" not in st.session_state:
    st.session_state.inventory_mode = "paste"

if "smart_review_ready" not in st.session_state:
    st.session_state.smart_review_ready = False

# -----------------------------
# Date Input + Smart Inventory Button
# -----------------------------
col1, col2 = st.columns(2)
with col1:
    date = st.date_input("Select Inventory Date")
    date_str = str(date)
with col2:
    if st.button("🧠 Smart Inventory"):
        st.session_state.inventory_mode = "smart"
        st.session_state.smart_review_ready = False
        st.rerun()
st.info(f"Inventory will be recorded under date: {date_str}")

# -----------------------------
# Smart Inventory Mode
# -----------------------------
if st.session_state.inventory_mode == "smart":
    st.markdown("## 🧠 Smart Inventory Entry")
    search = st.text_input("🔍 Search Item", placeholder="Type to filter items...")
    smart_inputs = {}
    filtered_items = [item for item in existing_items_list if search.lower() in item.lower()] if search else existing_items_list
    st.write(f"Showing {len(filtered_items)} items")

    # 4 columns side-by-side
    for i in range(0, len(filtered_items), 4):
        cols = st.columns(4)
        for j, col in enumerate(cols):
            if i + j < len(filtered_items):
                item = filtered_items[i + j]
                qty = col.number_input(
                    f"{item}",
                    min_value=0,
                    step=1,
                    format="%g",
                    key=f"smart_{item}"
                )
                if qty != 0:
                    smart_inputs[item] = qty

    # Review
    if st.button("Review Smart Inventory"):
        st.session_state.smart_review_ready = True
        st.session_state.smart_inputs_to_submit = smart_inputs
        st.rerun()

    if st.session_state.smart_review_ready:
        st.markdown("### Review Inventory Before Submit")
        review_cols = st.columns(2)
        left_col, right_col = review_cols
        for idx, (item, qty) in enumerate(st.session_state.smart_inputs_to_submit.items()):
            col = left_col if idx % 2 == 0 else right_col
            col.write(f"{item} → {qty}")

        if st.button("Submit Smart Inventory"):
            try:
                sheet_data, headers, existing_items_list, existing_items_lower = load_sheet(sheet)
                if date_str in headers:
                    col_index = headers.index(date_str)
                else:
                    col_index = len(headers)
                    sheet.update_cell(1, col_index + 1, date_str)
                    headers.append(date_str)

                updates = []
                for item_name, qty in st.session_state.smart_inputs_to_submit.items():
                    if item_name not in existing_items_list:
                        st.warning(f"{item_name} not found in master inventory. Skipped.")
                        continue
                    row_index = existing_items_list.index(item_name) + 1
                    try:
                        cell_value = sheet_data[row_index][col_index]
                    except:
                        cell_value = ""
                    if cell_value:
                        st.warning(f"{item_name} already has data for {date_str}. Skipped.")
                        continue
                    cell = gspread.utils.rowcol_to_a1(row_index + 1, col_index + 1)
                    updates.append({"range": cell, "values": [[qty]]})

                if updates:
                    sheet.batch_update(updates)
                    st.success(f"{len(updates)} items updated successfully.")
                else:
                    st.info("No updates needed.")

                # Wait 2 seconds then go back to dashboard
                time.sleep(4)
                st.session_state.smart_review_ready = False
                st.session_state.smart_inputs_to_submit = {}
                st.session_state.inventory_mode = "paste"
                st.switch_page("pages/staff_dashboard.py")
            except Exception as e:
                st.error(f"Error submitting updates: {e}")
                st.switch_page("pages/staff_dashboard.py")

    col1, col2 = st.columns(2)
    with col2:
        if st.button("⬅ Back to Paste Inventory"):
            st.session_state.inventory_mode = "paste"
            st.session_state.smart_review_ready = False
            st.session_state.smart_inputs_to_submit = {}
            st.rerun()
    st.stop()

# -----------------------------
# Paste Inventory Workflow (unchanged)
# -----------------------------
inventory_text = st.text_area("Kindly paste the inventory here:", height=300)
items_today = []
if inventory_text:
    for line in inventory_text.split("\n"):
        line = line.strip()
        if not line or "-" not in line:
            continue
        item, qty = line.rsplit("-", 1)
        item = item.strip()
        qty = qty.strip()
        try:
            qty = float(qty)
        except:
            st.warning(f"Invalid quantity for line: {line}. Skipping.")
            continue
        items_today.append((item, qty))

for item_name, qty in items_today:
    try:
        matches = process.extract(
            item_name.lower(),
            existing_items_lower,
            scorer=fuzz.WRatio,
            limit=5
        )
        best_matches = [m for m in matches if m[1] > 50]
        if not best_matches:
            st.warning(f"Item '{item_name}' not found in inventory.")
            continue
        best_matches_original = [existing_items_list[existing_items_lower.index(m[0])] for m in best_matches]
        word_count = len(item_name.split())
        if word_count > 2 or len(best_matches_original) == 1:
            selected = best_matches_original[0]
            st.session_state.selected_items[item_name] = selected
            st.success(f"{selected} auto-selected")
        else:
            st.markdown(f"### Possible matches for '{item_name}' ({qty})")
            selected_option = None
            for option in best_matches_original:
                key = f"{item_name}_{option}"
                checked = st.checkbox(option, key=key,
                                      value=(st.session_state.selected_items.get(item_name) == option))
                if checked and selected_option is None:
                    selected_option = option
            if selected_option:
                st.session_state.selected_items[item_name] = selected_option
    except Exception as e:
        st.error(f"Error matching item '{item_name}': {e}")

if st.button("Add Inventory to Pending Updates"):
    try:
        for item_name, qty in items_today:
            if item_name in st.session_state.selected_items:
                selected = st.session_state.selected_items[item_name]
                if (selected, qty) not in st.session_state.pending_updates:
                    st.session_state.pending_updates.append((selected, qty))
                    st.session_state.pending_checkbox_state[selected] = True
        st.success("Selected items added to pending updates")
    except Exception as e:
        st.error(f"Error adding items: {e}")
        st.experimental_rerun()

if st.session_state.pending_updates:
    st.markdown("### Pending Updates (Check to update)")
    for i, (iname, qty) in enumerate(st.session_state.pending_updates):
        try:
            checked = st.checkbox(f"{iname} → {qty}", key=f"pending_{iname}",
                                  value=st.session_state.pending_checkbox_state.get(iname, True))
            st.session_state.pending_checkbox_state[iname] = checked
        except Exception as e:
            st.error(f"Error displaying pending update for {iname}: {e}")

if st.button("Submit Pending Updates"):
    try:
        sheet_data, headers, existing_items_list, existing_items_lower = load_sheet(sheet)
        if date_str in headers:
            col_index = headers.index(date_str)
        else:
            col_index = len(headers)
            sheet.update_cell(1, col_index + 1, date_str)
            headers.append(date_str)
        updates = []
        for item_name, qty in st.session_state.pending_updates:
            if not st.session_state.pending_checkbox_state.get(item_name, True):
                continue
            if item_name not in existing_items_list:
                st.warning(f"{item_name} not found in master inventory. Skipped.")
                continue
            row_index = existing_items_list.index(item_name) + 1
            try:
                cell_value = sheet_data[row_index][col_index]
            except:
                cell_value = ""
            if cell_value:
                st.warning(f"{item_name} already has data for {date_str}. Skipped.")
                continue
            cell = gspread.utils.rowcol_to_a1(row_index + 1, col_index + 1)
            updates.append({"range": cell, "values": [[qty]]})
        if updates:
            sheet.batch_update(updates)
            st.success(f"{len(updates)} items updated successfully.")
        else:
            st.info("No updates needed.")
        # Wait 4 seconds then back to dashboard
        time.sleep(4)
        st.session_state.pending_updates = []
        st.session_state.pending_checkbox_state = {}
        st.switch_page("pages/staff_dashboard.py")
    except Exception as e:
        st.error(f"Error submitting updates: {e}")
        st.switch_page("pages/staff_dashboard.py")

if st.button("⬅ Back"):
    st.switch_page("pages/staff_dashboard.py")