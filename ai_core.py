import re
import datetime
from difflib import get_close_matches

# =========================================================
# 🧠 CORE AI FUNCTION
# =========================================================

def run_ai(user_input, context):

    text = user_input.lower()

    all_data = context.get("cache_data", [])
    branches = context.get("branch_list", [])
    daily_items = context.get("master_items", [])

    # =====================================================
    # 🧠 1. DATE PARSER (FIXED + SAFE)
    # =====================================================
    def parse_date(text):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)

        if "yesterday" in text:
            return yesterday.strftime("%Y-%m-%d")

        if "today" in text:
            return today.strftime("%Y-%m-%d")

        match = re.search(r"\d{4}-\d{2}-\d{2}", text)
        if match:
            return match.group()

        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
            "may": 5, "jun": 6, "jul": 7, "aug": 8,
            "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }

        match = re.search(r"(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", text)

        if match:
            day = int(match.group(1))
            month = month_map[match.group(2)]
            year = today.year

            try:
                return datetime.date(year, month, day).strftime("%Y-%m-%d")
            except:
                return None

        return today.strftime("%Y-%m-%d")  # safe default

    target_date = parse_date(text)

    # =====================================================
    # 📦 2. FUZZY ITEM MATCH
    # =====================================================
    def match_item(text):
        items = list(daily_items.keys()) if isinstance(daily_items, dict) else daily_items

        match = get_close_matches(text.upper(), [i.upper() for i in items], n=1, cutoff=0.4)

        if match:
            for i in items:
                if i.upper() == match[0]:
                    return i

        return None

    item = match_item(text)

    if not item:
        return "❌ I couldn’t find the item. Please check the name or try a simpler version."

    # =====================================================
    # 🏢 3. FUZZY BRANCH MATCH
    # =====================================================
    def match_branch(text):
        match = get_close_matches(text.lower(), [b.lower() for b in branches], n=1, cutoff=0.4)

        if match:
            for b in branches:
                if b.lower() == match[0]:
                    return b

        return None

    branch = match_branch(text)

    # =====================================================
    # 📊 4. SEARCH IN CACHE DATA
    # =====================================================
    def get_stock(item, branch, date):

        total = 0
        breakdown = {}

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

                row_item = str(row[0]).strip()

                if item.lower() not in row_item.lower():
                    continue

                qty = 0

                try:
                    if len(row) > date_index:
                        qty = float(row[date_index] or 0)
                except:
                    qty = 0

                # branch filter
                if branch and branch.lower() not in branch_name.lower():
                    continue

                total += qty

                breakdown[branch_name] = breakdown.get(branch_name, 0) + qty

        return total, breakdown

    total, breakdown = get_stock(item, branch, target_date)

    # =====================================================
    # ❓ 5. RESPONSE BUILDER
    # =====================================================

    response = f"📦 Item: {item}\n📅 Date: {target_date}\n"

    if branch:
        response += f"🏢 Branch: {branch}\n"

    response += f"\n📊 Total Stock: {total}\n"

    if breakdown:
        response += "\n📍 Branch Breakdown:\n"
        for b, v in breakdown.items():
            response += f"- {b}: {v}\n"

    return response
