import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor
from groq import Groq

# ---------------- PAGE ----------------
st.set_page_config(layout="wide", page_title="Stock AI System")
st.title("📦 BART Stock Management + AI")

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
def get_gs():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

gs = get_gs()

# ---------------- BRANCHES ----------------
@st.cache_data(ttl=600)
def load_branches():
    sheet = gs.open("MASTERBRANCHSHEET").sheet1
    data = sheet.get_all_records()
    return [b for b in data if b.get("SheetID") and b.get("BranchName")]

branches = load_branches()
branch_names = [b["BranchName"] for b in branches]

# ---------------- DATE ----------------
selected_date = st.date_input("📅 Select Date")
selected_date_str = selected_date.strftime("%Y-%m-%d")

# =====================================================
# 📊 MANAGEMENT DATA (CACHED)
# =====================================================

@st.cache_data(ttl=300)
def load_management():

    daily = {}
    weekly = {}

    def fetch(b):
        try:
            sheet = gs.open_by_key(b["SheetID"])
            ws = sheet.worksheet("Stocks")
            return b["BranchName"], ws.get_all_values()
        except:
            return b["BranchName"], None

    data = list(ThreadPoolExecutor(max_workers=5).map(fetch, branches))

    for branch, raw in data:

        if not raw or len(raw) < 2:
            continue

        headers = raw[0]

        if selected_date_str not in headers:
            continue

        idx = headers.index(selected_date_str)
        section = None

        for row in raw:

            txt = " ".join(row).lower()

            if "daily item" in txt:
                section = "daily"
                continue

            if "weekly item" in txt:
                section = "weekly"
                continue

            if section is None:
                continue

            if not row or not row[0]:
                continue

            item = str(row[0]).strip()

            qty = row[idx] if len(row) > idx else 0

            try:
                qty = float(qty) if qty != "" else 0
            except:
                qty = 0

            target = daily if section == "daily" else weekly

            if item not in target:
                target[item] = {bn: 0 for bn in branch_names}

            target[item][branch] = qty

    daily_df = pd.DataFrame([{"Item Name": k, **v} for k, v in daily.items()])
    weekly_df = pd.DataFrame([{"Item Name": k, **v} for k, v in weekly.items()])

    return daily_df, weekly_df


daily_df, weekly_df = load_management()

st.subheader("📦 Daily Stock")
st.dataframe(daily_df if not daily_df.empty else "No data", use_container_width=True)

st.subheader("📦 Weekly Stock")
st.dataframe(weekly_df if not weekly_df.empty else "No data", use_container_width=True)

# =====================================================
# 🤖 AI FRESH DATA (NO CACHE)
# =====================================================

def get_ai_stock():

    daily = {}
    weekly = {}

    def fetch(b):
        try:
            sheet = gs.open_by_key(b["SheetID"])
            ws = sheet.worksheet("Stocks")
            return b["BranchName"], ws.get_all_values()
        except:
            return b["BranchName"], None

    data = list(ThreadPoolExecutor(max_workers=5).map(fetch, branches))

    for branch, raw in data:

        if not raw or len(raw) < 2:
            continue

        headers = raw[0]

        if selected_date_str not in headers:
            continue

        idx = headers.index(selected_date_str)
        section = None

        for row in raw:

            txt = " ".join(row).lower()

            if "daily item" in txt:
                section = "daily"
                continue

            if "weekly item" in txt:
                section = "weekly"
                continue

            if section is None:
                continue

            if not row or not row[0]:
                continue

            item = str(row[0]).strip()

            qty = row[idx] if len(row) > idx else 0

            try:
                qty = float(qty) if qty != "" else 0
            except:
                qty = 0

            target = daily if section == "daily" else weekly

            if item not in target:
                target[item] = {}

            target[item][branch] = qty

    daily_df_ai = pd.DataFrame([{"Item Name": k, **v} for k, v in daily.items()])
    weekly_df_ai = pd.DataFrame([{"Item Name": k, **v} for k, v in weekly.items()])

    return daily_df_ai, weekly_df_ai

# =====================================================
# 🤖 AI ENGINE (FIXED FUNCTION SIGNATURE)
# =====================================================

def run_ai(user_input):

    daily_ai, weekly_ai = get_ai_stock()

    stock_data = {
        "daily": daily_ai.fillna(0).to_dict(orient="records") if not daily_ai.empty else [],
        "weekly": weekly_ai.fillna(0).to_dict(orient="records") if not weekly_ai.empty else []
    }

    system_prompt = """
You are a STRICT STOCK ENGINE.

RULES:
- NEVER ask questions
- NEVER behave like chatbot
- ALWAYS find stock value
- If unclear, try best match
- If multiple matches, sum values
- If not found, say: "Item not found in stock"

OUTPUT:
Item Name = quantity units
"""

    try:
        response = ai_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
Stock Data:
{stock_data}

Question:
{user_input}
"""}
            ],
            temperature=0.1
        )

        return response.choices[0].message.content.strip()

    except:
        return "AI error. Try again."

# =====================================================
# 🤖 AI UI (FIXED CALL)
# =====================================================

st.divider()
st.subheader("🤖 AI Stock Assistant")

question = st.text_input("Ask anything about stock")

if st.button("Ask AI") or question:

    if question:
        with st.spinner("Checking live stock..."):
            answer = run_ai(question)

        st.success(answer)

# =====================================================
# 🔎 SEARCH
# =====================================================

search = st.text_input("🔎 Search Item")

if search:

    if not daily_df.empty:
        st.subheader("Daily Search")
        st.dataframe(daily_df[daily_df["Item Name"].str.contains(search, case=False, na=False)])

    if not weekly_df.empty:
        st.subheader("Weekly Search")
        st.dataframe(weekly_df[weekly_df["Item Name"].str.contains(search, case=False, na=False)])
