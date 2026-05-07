# =========================
# 🧠 BART AI STOCK ENGINE
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

    # exact / contains match
    for k, v in items_map.items():
        if k in user_text_n:
            return v

    # fuzzy match fallback
    matches = get_close_matches(user_text_n, items_map.keys(), n=1, cutoff=0.6)

    if matches:
        return items_map[matches[0]]

    return None


# ---------------- BRANCH MATCHER ----------------
def match_branch(user_text, branches):

    text = normalize(user_text)

    # direct contains match first
    for b in branches:
        if normalize(b) in text:
            return b

    # fuzzy fallback
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


# ---------------- CORE AI ENGINE ----------------
def query_stock(user_query, cache_data, master_items, branch_list):

    """
    cache_data format:
    [
        ("Branch A", raw_sheet),
        ("Branch B", raw_sheet)
    ]
    """

    # ---------------- EXTRACT ITEM ----------------
    item = match_item(user_query, master_items)

    if not item:
        return "❌ Item not found in system."

    # ---------------- EXTRACT DATE ----------------
    date = resolve_date(user_query)

    if not date:
        return "❌ Please specify date (today/yesterday)."

    # ---------------- EXTRACT BRANCH (optional) ----------------
    branch = match_branch(user_query, branch_list)

    total = 0
    breakdown = {}

    # ---------------- SCAN CACHE ----------------
    for branch_name, raw in cache_data:

        if not raw or len(raw) < 2:
            continue

        # if user specified branch → filter only that
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

    text += f"🔢 Total Stock: {result['total']}\n\n"
    text += "📍 Breakdown:\n"

    for branch, qty in result["breakdown"].items():
        text += f"- {branch}: {qty}\n"

    return text
