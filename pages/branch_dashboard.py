import streamlit as st
import gspread
import pandas as pd
import time

st.set_page_config(page_title="Branch Dashboard", layout="wide")

# ---------------- SESSION CHECK ----------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login first")
    st.stop()

branch_info = st.session_state.branch_info

# ---------------- REFRESH ----------------
def refresh_activity():
    st.session_state.last_activity = time.time()

# ---------------- STOCK RECORD BUTTON ----------------
def stock_record():
    if st.button("📦 Stock Record"):
        refresh_activity()
        st.switch_page("pages/stock_consumption.py")

# ---------------- STOCK VIEW ----------------
def stock_view(client, branch_info):

    refresh_activity()

    sheet = client.open_by_key(branch_info["SheetID"])
    ws = sheet.worksheet("Stocks")

    data = ws.get_all_values()

    headers = data[0]
    date_columns = headers[1:]

    daily = []
    weekly = []

    current_section = None

    for row in data:

        row_text = " ".join(row).strip().lower()

        if "daily item" in row_text:
            current_section = "daily"
            continue

        if "weekly item" in row_text:
            current_section = "weekly"
            continue

        if current_section is None:
            continue

        if not row or not row[0]:
            continue

        item = row[0].strip()

        values = row[1:]
        values += [""] * (len(date_columns) - len(values))

        cleaned = []
        total = 0

        for i, v in enumerate(values):

            if i < 3:
                cleaned.append(v)
                continue

            try:
                num = float(v) if v != "" else 0
            except:
                num = 0

            cleaned.append(num)
            total += num

        row_dict = {"Item": item}

        for i, col in enumerate(date_columns):
            row_dict[col] = cleaned[i]

        row_dict["Total"] = total

        if current_section == "daily":
            daily.append(row_dict)
        else:
            weekly.append(row_dict)

    st.subheader("📦 Daily Items Stock")
    st.dataframe(pd.DataFrame(daily), use_container_width=True, height=400)

    st.subheader("📦 Weekly Items Stock")
    st.dataframe(pd.DataFrame(weekly), use_container_width=True, height=400)

# ---------------- UI ----------------
st.title("🏬 Branch Dashboard")

col1, col2 = st.columns(2)

with col1:
    stock_record()

with col2:
    if st.button("🔍 Stock View"):
        stock_view(st.session_state.client, branch_info)
