import datetime
import re

# =========================================================
# 🧠 DATE DETECTION
# =========================================================
def get_target_date(text):
    text = text.lower()

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    if "yesterday" in text:
        return yesterday.strftime("%Y-%m-%d")

    if "today" in text:
        return today.strftime("%Y-%m-%d")

    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if match:
        return match.group()

    return today.strftime("%Y-%m-%d")


# =========================================================
# 🏢 BRANCH DETECTION
# =========================================================
def find_branch(text, branch_list):
    text = text.lower()

    for b in branch_list:
        if b.lower() in text:
            return b

    return None


# =========================================================
# 🧠 SMART FUZZY ITEM MATCHING (IMPORTANT UPGRADE)
# =========================================================
def fuzzy_match(text, items):
    text = text.lower().strip()

    best_match = None
    best_score = 0

    words = text.split()

    for item in items:

        item_low = item.lower()

        score = 0

        # word overlap scoring
        for w in words:
            if w in item_low:
                score += 1

        # boost if direct substring exists
        if text in item_low:
            score += 2

        # stronger boost if key words match heavily
        item_words = item_low.split()
        common = set(words) & set(item_words)
        score += len(common)

        if score > best_score:
            best_score = score
            best_match = item

    return best_match


# =========================================================
# 🧠 MAIN AI FUNCTION
# =========================================================
def run_ai(user_input, context):

    cache_data = context.get("cache_data", [])
    branch_list = context.get("branch_list", [])
    master_items = context.get("master_items", {})

    # ---------------- extract info ----------------
    date = get_target_date(user_input)
    branch = find_branch(user_input, branch_list)

    item = fuzzy_match(user_input, master_items.keys())

    if not item:
        return "❌ I couldn't find a matching item. Try rephrasing."

    total = 0
    breakdown = []

    # =========================================================
    # 🔍 SEARCH IN CACHE
    # =========================================================
    for b_name, raw in cache_data:

        if branch and branch.lower() != b_name.lower():
            continue

        if not raw or len(raw) < 2:
            continue

        headers = raw[0]

        if date not in headers:
            continue

        date_index = headers.index(date)

        for row in raw:

            if not row or not row[0]:
                continue

            # match item loosely (not strict)
            if item.lower() not in row[0].lower():
                continue

            qty = 0

            if len(row) > date_index:
                try:
                    qty = float(row[date_index] or 0)
                except:
                    qty = 0

            total += qty
            breakdown.append(f"{b_name}: {qty}")

    # =========================================================
    # ❌ NO DATA FOUND
    # =========================================================
    if not breakdown:
        return f"❌ No stock found for '{item}' on {date}"

    # =========================================================
    # ✅ FINAL RESPONSE
    # =========================================================
    return f"""
📦 Item: {item}
📅 Date: {date}
🏢 Branch: {branch if branch else "All Branches"}

📊 Total Quantity: {total}

📍 Breakdown:
- """ + "\n- ".join(breakdown)
