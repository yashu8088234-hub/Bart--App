import re
import datetime
import streamlit as st
from groq import Groq

# =========================================================
# 🔐 SAFE GROQ CLIENT (STREAMLIT SECRETS)
# =========================================================
client = Groq(api_key=st.secrets["GROQ_API_KEY"])


# =========================================================
# 🧠 DATE PARSER (ROBUST)
# =========================================================
def parse_date(text):

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    text = text.lower()

    # ---- keywords ----
    if "yesterday" in text:
        return yesterday.strftime("%Y-%m-%d")

    if "today" in text:
        return today.strftime("%Y-%m-%d")

    # ---- ISO date ----
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if match:
        return match.group()

    # ---- "06 may" format ----
    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4,
        "may": 5, "jun": 6, "jul": 7, "aug": 8,
        "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }

    match = re.search(
        r"(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
        text
    )

    if match:
        day = int(match.group(1))
        month = month_map[match.group(2)]
        year = today.year

        try:
            return datetime.date(year, month, day).strftime("%Y-%m-%d")
        except:
            return today.strftime("%Y-%m-%d")

    # fallback safe
    return today.strftime("%Y-%m-%d")


# =========================================================
# 🤖 MAIN AI FUNCTION
# =========================================================
def run_ai(user_input, context):

    all_data = context.get("cache_data", [])
    branches = context.get("branch_list", [])

    # ---------------- parse date ----------------
    date = parse_date(user_input)

    result_data = []

    # =====================================================
    # 📦 PYTHON DATA ENGINE (TRUTH LAYER)
    # =====================================================
    for branch_name, raw in all_data:

        if not raw or len(raw) < 2:
            continue

        headers = raw[0]

        if date not in headers:
            continue

        date_index = headers.index(date)

        for row in raw:

            if not row or len(row) == 0:
                continue

            item_name = str(row[0]).strip()

            qty = 0
            try:
                if len(row) > date_index:
                    qty = float(row[date_index] or 0)
            except:
                qty = 0

            # skip empty stock
            if qty == 0:
                continue

            result_data.append({
                "branch": branch_name,
                "item": item_name,
                "qty": qty,
                "date": date
            })

    # =====================================================
    # 🤖 GROQ CHATGPT-STYLE RESPONSE
    # =====================================================
    prompt = f"""
You are BART AI, a smart inventory assistant.

User query:
{user_input}

Resolved date:
{date}

Stock data (DO NOT INVENT ANYTHING):
{result_data}

Rules:
- Be natural like ChatGPT
- Summarize clearly
- Show totals + breakdown
- If empty data, say "No stock found"
- Never hallucinate or guess data
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful inventory assistant for a cafe chain. Always use provided data only."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )

        return response.choices[0].message.content.strip()

    except Exception:
        return "⚠️ AI service temporarily unavailable. Please try again."
