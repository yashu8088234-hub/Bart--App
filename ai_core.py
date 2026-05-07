import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor
from groq import Groq

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide", page_title="Stock Overview")
st.title("📦 BART - Stock Management System")

# ---------------- GROQ AI ----------------
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    raise ValueError("Missing GROQ_API_KEY")

ai_client = Groq(api_key=api_key)

# ---------------- GOOGLE AUTH ----------------
creds_dict = st.secrets["GOOGLE_CREDS_JSON"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_gs_client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

gs_client = get_gs_client()

# ---------------- MASTER BRANCH LIST (CACHED) ----------------
@st.cache_data(ttl=600)
def load_branches():
    sheet = gs_client.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()

    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# ---------------- DATE ----------------
selected_date = st.date_input("📅 Select Stock Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# =========================================================
# 📊 MANAGEMENT DATA LOADER (CACHED FOR SPEED)
# =========================================================

@st.cache_data(ttl=300)
def load_management_data():
    daily_items = {}
    weekly_items = {}

    def fetch_branch(branch):
        try:
            sheet = gs_client.open_by_key(branch["SheetID"])
            ws = sheet.worksheet("Stocks")
            return branch["BranchName"], ws.get_all_values()
        except:
            return branch["BranchName"], None

    all_data = list(ThreadPoolExecutor(max_workers=5).map(fetch_branch, branches))

    for branch_name, raw in all_data:

        if not raw or len(raw) < 2:
            continue

        headers = raw[0]

        if selected_date_str not in headers:
            continue

        date_index = headers.index(selected_date_str)
        current_section = None

        for row in raw:

            row_text = " ".join(row).lower()

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

            item = str(row[0]).strip()
            qty = row[date_index] if len(row) > date_index else 0

            try:
                qty = float(qty) if qty != "" else 0
            except:
                qty = 0

            target = daily_items if current_section == "daily" else weekly_items

            if item not in target:
                target[item] = {bn: 0 for bn in branch_names}

            target[item][branch_name] = qty

    daily_df = pd.DataFrame([{"Item Name": k, **v} for k, v in daily_items.items()])
    weekly_df = pd.DataFrame([{"Item Name": k, **v} for k, v in weekly_items.items()])

    return daily_df, weekly_df


# =========================================================
# 🤖 AI DATA LOADER (ALWAYS FRESH - NO CACHE)
# =========================================================

def get_ai_fresh_stock():

    daily_items = {}
    weekly_items = {}

    def fetch_branch(branch):
        try:
            sheet = gs_client.open_by_key(branch["SheetID"])
            ws = sheet.worksheet("Stocks")
            return branch["BranchName"], ws.get_all_values()
        except:
            return branch["BranchName"], None

    all_data = list(ThreadPoolExecutor(max_workers=5).map(fetch_branch, branches))

    for branch_name, raw in all_data:

        if not raw or len(raw) < 2:
            continue

        headers = raw[0]

        if selected_date_str not in headers:
            continue

        date_index = headers.index(selected_date_str)
        current_section = None

        for row in raw:

            row_text = " ".join(row).lower()

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

            item = str(row[0]).strip()
            qty = row[date_index] if len(row) > date_index else 0

            try:
                qty = float(qty) if qty != "" else 0
            except:
                qty = 0

            target = daily_items if current_section == "daily" else weekly_items

            if item not in target:
                target[item] = {}

            target[item][branch_name] = qty

    daily_df = pd.DataFrame([{"Item Name": k, **v} for k, v in daily_items.items()])
    weekly_df = pd.DataFrame([{"Item Name": k, **v} for k, v in weekly_items.items()])

    return daily_df, weekly_df


# =========================================================
# 📊 MANAGEMENT UI
# =========================================================

daily_df, weekly_df = load_management_data()

st.subheader("📦 Daily Stock")
st.dataframe(daily_df if not daily_df.empty else "No data", use_container_width=True)

st.subheader("📦 Weekly Stock")
st.dataframe(weekly_df if not weekly_df.empty else "No data", use_container_width=True)


# =========================================================
# 🤖 AI FUNCTION (LIVE DATA ONLY)
# =========================================================

def run_ai(user_input):

    daily_df_ai, weekly_df_ai = get_ai_fresh_stock()

    stock_data = {
        "daily": daily_df_ai.fillna(0).to_dict(orient="records") if not daily_df_ai.empty else [],
        "weekly": weekly_df_ai.fillna(0).to_dict(orient="records") if not weekly_df_ai.empty else []
    }

    system_prompt = """
You are BART AI Stock Assistant.

Rules:
- Always use live stock data
- Understand messy human questions
- Match similar item names even with typos
- Sum quantities across branches if needed
- If not found: say "Item not found in stock"
- Never guess missing values
"""

    try:
        response = ai_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Stock Data:\n{stock_data}\n\nQuestion:\n{user_input}"}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    except:
        return "AI error. Try again."


# =========================================================
# 🤖 AI UI
# =========================================================

st.divider()
st.subheader("🤖 AI Stock Assistant (Live Data)")

question = st.text_input("Ask anything about stock")

if st.button("Ask AI") or question:

    if question:
        with st.spinner("Fetching live stock data..."):
            answer = run_ai(question)

        st.success(answer)


# =========================================================
# 🔎 SEARCH (MANUAL)
# =========================================================

search = st.text_input("🔎 Search Item")

if search:

    if not daily_df.empty:
        st.subheader("Daily Search")
        st.dataframe(daily_df[daily_df["Item Name"].str.contains(search, case=False, na=False)])

    if not weekly_df.empty:
        st.subheader("Weekly Search")
        st.dataframe(weekly_df[weekly_df["Item Name"].str.contains(search, case=False, na=False)])


# =========================================================
# 📥 DOWNLOADS
# =========================================================

if not daily_df.empty:
    st.download_button("📥 Download Daily", daily_df.to_csv(index=False), "daily.csv")

if not weekly_df.empty:
    st.download_button("📥 Download Weekly", weekly_df.to_csv(index=False), "weekly.csv")
