import re
import json
import datetime
import streamlit as st
from rapidfuzz import fuzz, process
import dateparser
from groq import Groq

# =========================================================
# 🔐 GROQ CLIENT
# =========================================================
client = Groq(api_key=st.secrets["GROQ_API_KEY"])


# =========================================================
# 🧠 NORMALIZATION
# =========================================================
def normalize(text):
    if not text:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r"[^a-zA-Z0-9\u0600-\u06FF ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# =========================================================
# 🤖 IDENTITY CHECK
# =========================================================
def is_identity_question(text):
    text = normalize(text)
    keywords = [
        "who are you",
        "what are you",
        "introduce yourself",
        "your name"
    ]
    return any(k in text for k in keywords)


# =========================================================
# 📅 SMART DATE PARSER
# =========================================================
def parse_date(text):
    parsed = dateparser.parse(text)
    if parsed:
        return parsed.strftime("%Y-%m-%d")

    return datetime.date.today().strftime("%Y-%m-%d")


# =========================================================
# 🏢 FIND BRANCH
# =========================================================
def find_branch(user_input, branch_list):
    if not branch_list:
        return None

    match = process.extractOne(
        user_input,
        branch_list,
        scorer=fuzz.token_set_ratio
    )

    if match and match[1] > 60:
        return match[0]

    return None


# =========================================================
# 📦 FIND ITEM
# =========================================================
def find_item(user_input, item_list):
    if not item_list:
        return None

    match = process.extractOne(
        user_input,
        item_list,
        scorer=fuzz.token_set_ratio
    )

    if match and match[1] > 55:
        return match[0]

    return None


# =========================================================
# 📊 STOCK EXTRACTION
# =========================================================
def extract_stock_data(all_data, item_name, target_date, target_branch=None):

    results = []

    for branch_name, raw in all_data:

        if target_branch and normalize(branch_name) != normalize(target_branch):
            continue

        if not raw or len(raw) < 2:
            continue

        headers = raw[0]

        if target_date not in headers:
            continue

        date_index = headers.index(target_date)

        for row in raw[1:]:

            if not row or not row[0]:
                continue

            row_item = str(row[0]).strip()

            score = fuzz.token_set_ratio(item_name, row_item)

            if score < 60:
                continue

            try:
                qty = float(row[date_index]) if len(row) > date_index else 0
            except:
                qty = 0

            results.append({
                "branch": branch_name,
                "item": row_item,
                "qty": qty,
                "date": target_date
            })

    return results


# =========================================================
# 🚨 INSIGHTS ENGINE
# =========================================================
def generate_insights(total_stock, branch_summary):

    insights = []

    if total_stock <= 0:
        insights.append("🚨 CRITICAL: Out of stock")
    elif total_stock < 10:
        insights.append("⚠️ LOW STOCK: Immediate restock needed")
    elif total_stock < 50:
        insights.append("📦 MODERATE STOCK: Monitor levels")
    else:
        insights.append("✅ STOCK HEALTHY")

    if len(branch_summary) == 1:
        insights.append("📍 Risk: Stock in only one branch")
    elif len(branch_summary) > 3:
        insights.append("🌍 Distributed across multiple branches")

    return insights


# =========================================================
# 🤖 MAIN AI FUNCTION
# =========================================================
def run_ai(user_input, context):

    try:

        # =========================================================
        # 🤖 IDENTITY MODE (NEW FEATURE)
        # =========================================================
        if is_identity_question(user_input):

            normal_response = (
                "I am an AI assistant designed to help you with general questions and support."
            )

            stock_ai_response = (
                "📦 STOCK AI MODE: I specialize in inventory tracking, stock analysis, "
                "and business decision support for warehouses and retail systems."
            )

            return f"{normal_response}\n\n{stock_ai_response}"

        # =========================================================
        # 📦 LOAD DATA
        # =========================================================
        all_data = context.get("cache_data", [])
        branch_list = context.get("branch_list", [])
        master_items = context.get("master_items", [])

        if not all_data:
            return "⚠️ No stock data loaded."

        # =========================================================
        # 🔍 PARSE INPUT
        # =========================================================
        target_date = parse_date(user_input)
        matched_branch = find_branch(user_input, branch_list)
        matched_item = find_item(user_input, master_items)

        if not matched_item:
            return "❌ Item not found in inventory database."

        # =========================================================
        # 📊 STOCK CALCULATION
        # =========================================================
        stock_results = extract_stock_data(
            all_data,
            matched_item,
            target_date,
            matched_branch
        )

        total_stock = sum(x["qty"] for x in stock_results)

        branch_summary = {}
        for x in stock_results:
            branch_summary[x["branch"]] = branch_summary.get(x["branch"], 0) + x["qty"]

        insights = generate_insights(total_stock, branch_summary)

        # =========================================================
        # 📦 PAYLOAD
        # =========================================================
        payload = {
            "query": user_input,
            "item": matched_item,
            "branch": matched_branch,
            "date": target_date,
            "total_stock": total_stock,
            "branch_summary": branch_summary,
            "insights": insights
        }

        # =========================================================
        # 🤖 AI PROMPT
        # =========================================================
        prompt = f"""
You are STOCK AI — an inventory management intelligence system.

RULES:
- Use ONLY provided JSON data
- Do NOT guess missing values
- Be precise and business focused
- Provide actionable insights

FORMAT:

1. 📊 Summary
2. 📦 Stock Status
3. 🏬 Branch Breakdown
4. 🚨 Insights
5. 🎯 Action Plan (max 3)
6. ⚠️ Risk Level

DATA:
{json.dumps(payload, indent=2, ensure_ascii=False)}
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert inventory and supply chain AI assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ System Error: {str(e)}"
