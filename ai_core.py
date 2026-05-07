# =========================
# 🧠 BART AI CORE ENGINE
# =========================

import re
from datetime import datetime, timedelta
from difflib import get_close_matches


# ---------------- NORMALIZER ----------------
def normalize(text):
    return re.sub(r'\s+', ' ', text.lower().strip())


# ---------------- DATE RESOLVER ----------------
def resolve_date(text):

    text = text.lower()
    today = datetime.today().date()

    if "today" in text:
        return today.strftime("%Y-%m-%d")

    if "yesterday" in text:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")

    if "tomorrow" in text:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    return None


# ---------------- ITEM MATCHER ----------------
def match_item(user_text, items):

    user_text_n = normalize(user_text)

    items_map = {normalize(i): i for i in items}

    # direct match / contains
    for k, v in items_map.items():
        if k in user_text_n:
            return v

    # fuzzy match
    matches = get_close_matches(user_text_n, items_map.keys(), n=1, cutoff=0.6)

    if matches:
        return items_map[matches[0]]

    return None


# ---------------- BRANCH MATCHER ----------------
def match_branch(user_text, branches):

    text = normalize(user_text)

    for b in branches:
        if normalize(b) in text:
            return b

    matches = get_close_matches(
        text,
        [normalize(b) for b in branches],
        n=1,
        cutoff=0.5
    )

    if matches:
        for b in branches:
            if normalize(b) == matches[0]:
                return b

    return None


# ---------------- MAIN STOCK ENGINE ----------------
def query_stock(user_query, cache_data, master_items, branch_list):

    # -------- ITEM --------
    item = match_item(user_query, master_items)
    if not item:
        return "❌ Item not found."

    # -------- DATE --------
    date = resolve_date(user_query)
    if not date:
        return "❌ Please mention date (today/yesterday)."

    # -------- BRANCH (optional) --------
    branch = match_branch(user_query, branch_list)

    total = 0
    breakdown = {}

    # -------- CACHE SCAN --------
    for branch_name, raw in cache_data:

        if not raw or len(raw) < 2:
            continue

        # filter branch if specified
        if branch and normalize(branch_name) != normalize(branch):
            continue

        headers = raw[0]

        if date not in headers:
            continue

        date_index = headers.index(date)

        for row in raw:

            if not row or row[0] != item:
                continue

            try:
                qty = float(row[date_index] or 0)
            except:
                qty = 0

            breakdown[branch_name] = qty
            total += qty

    return {
        "item": item,
        "date": date,
        "branch": branch if branch else "ALL BRANCHES",
        "total": total,
        "breakdown": breakdown
    }


# ---------------- RESPONSE FORMATTER ----------------
def format_response(result):

    if isinstance(result, str):
        return result

    text = f"📦 Item: {result['item']}\n"
    text += f"📅 Date: {result['date']}\n"
    text += f"🏢 Branch: {result['branch']}\n\n"

    text += f"🔢 Total: {result['total']}\n\n"
    text += "📍 Breakdown:\n"

    for b, q in result["breakdown"].items():
        text += f"- {b}: {q}\n"

    return text


# ---------------- WRAPPER (THIS FIXES YOUR IMPORT ERROR) ----------------
def run_ai(user_query, cache_data, master_items, branch_list):
    result = query_stock(user_query, cache_data, master_items, branch_list)
    return format_response(result)
