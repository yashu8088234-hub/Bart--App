import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor
from groq import Groq

# ---------------- PAGE ----------------
st.set_page_config(layout="wide", page_title="Stock AI System")
st.title("📦 BART - Stock Management + AI")

# ---------------- GROQ ----------------
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
# 📊 MANAGEMENT DATA (cached for speed)
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
# 🤖 AI FRESH DATA LOADER (NO CACHE)
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

    daily_df = pd.DataFrame([{"Item Name": k, **v} for k, v in daily.items()])
    weekly_df = pd.DataFrame([{"Item Name": k, **v} for k, v in weekly.items()])

    return daily_df, weekly_df


# =====================================================
# 🤖 FIXED AI ENGINE (IMPORTANT PART)
# =====================================================

def run_ai(user_input):

    daily_ai, weekly_ai = get_ai_stock()

    stock_data = {
        "daily": daily_ai.fillna(0).to_dict(orient="records") if not daily_ai.empty else [],
        "weekly": weekly_ai.fillna(0).to_dict(orient="records") if not weekly_ai.empty else []
    }

    # 🔥 FIXED SYSTEM PROMPT (NO CHAT BEHAVIOR)
    system_prompt = """
You are a STRICT STOCK LOOKUP ENGINE.

YOU ARE NOT A CHATBOT.

RULES:
- NEVER ask questions back
- NEVER request clarification
- NEVER have conversation
- ALWAYS try to find stock value
- If user is unclear, guess best match from data
- If multiple matches, sum values
- If not found, respond EXACTLY: "Item not found in stock"

OUTPUT FORMAT:
Item Name = quantity units

EXAMPLES:
User: CRC Crunchy Cake count of Al Safa
Answer: CRC Crunchy Cake (Al Safa) = 18 units

User: milk stock
Answer: Milk = 120 units
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
        return "AI error. Try again later."


# =====================================================
# 🤖 AI UI
# =====================================================

st.divider()
st.subheader("🤖 AI Stock Assistant (Fixed Behavior)")

question = st.text_input("Ask anything about stock")

if st.button("Ask AI") or question:

    if question:

        with st.spinner("Checking live stock data..."):
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
