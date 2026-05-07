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
# 🏢 SMART BRANCH MATCHING (FUZZY + SUGGESTIONS)
# =========================================================
def find_branch(text, branch_list):
    text = text.lower().strip()
    text_words = text.split()

    best_match = None
    best_score = 0
    suggestions = []

    for branch in branch_list:

        b = branch.lower()

        score = 0

        # word overlap scoring
        for w in text_words:
            if w in b:
                score += 2

        # substring match boost
        if text in b:
            score += 3

        # reverse match
        for w in b.split():
            if w in text:
                score += 1

        if score > 0:
            suggestions.append((branch, score))

        if score > best_score:
            best_score = score
            best_match = branch

    if best_score == 0:
        return None, []

    suggestions.sort(key=lambda x: x[1], reverse=True)

    return best_match, suggestions[:3]


# =========================================================
# 🧠 SMART ITEM MATCHING (FUZZY)
# =========================================================
def fuzzy_match(text, items):
    text = text.lower().strip()

    best_match = None
    best_score = 0

    words = text.split()

    for item in items:

        item_low = item.lower()

        score = 0

        # word overlap
        for w in words:
            if w in item_low:
                score += 1

        # substring boost
        if text in item_low:
            score += 2

        # shared words boost
        item_words = item_low.split()
        common = set(words) & set(item_words)
        score += len(common)

        if score > best_score:
            best_score = score
            best_match = item

    return best_match


# =========================================================
# 🧠 MAIN AI ENGINE
# =========================================================
def run_ai(user_input, context):

    cache_data = context.get("cache_data", [])
    branch_list = context.get("branch_list", [])
    master_items = context.get("master_items", {})

    # ---------------- extract intent ----------------
    date = get_target_date(user_input)

    branch, branch_suggestions = find_branch(user_input, branch_list)

    item = fuzzy_match(user_input, master_items.keys())

    # =====================================================
    # ❌ NO ITEM FOUND
    # =====================================================
    if not item:
        return "❌ I couldn't find that item. Try rephrasing."

    # =====================================================
    # ❌ NO BRANCH FOUND (SMART HELP)
    # =====================================================
    if branch is None and "branch" in user_input.lower():

        if branch_suggestions:
            options = ", ".join([b[0] for b in branch_suggestions])

            return f"""
❌ I couldn't find that branch.

👉 Did you mean:
{options}

Please try again with correct branch name.
"""

        return "❌ No matching branch found. Please check branch name."

    # =====================================================
    # 🔍 SEARCH STOCK DATA
    # =====================================================
    total = 0
    breakdown = []

    for b_name, raw in cache_data:

        if branch and branch.lower() != b_name.lower():
            continue

        if not raw or len(raw) < 2:
            continue

        headers = raw[0]

        if date not in headers:
            continue

        idx = headers.index(date)

        for row in raw:

            if not row or not row[0]:
                continue

            # item match (loose)
            if item.lower() not in row[0].lower():
                continue

            qty = 0

            if len(row) > idx:
                try:
                    qty = float(row[idx] or 0)
                except:
                    qty = 0

            total += qty
            breakdown.append(f"{b_name}: {qty}")

    # =====================================================
    # ❌ NO DATA FOUND
    # =====================================================
    if not breakdown:
        return f"❌ No stock found for '{item}' on {date}"

    # =====================================================
    # ✅ FINAL RESPONSE
    # =====================================================
    return f"""
📦 Item: {item}
📅 Date: {date}
🏢 Branch: {branch if branch else "All Branches"}

📊 Total Quantity: {total}

📍 Breakdown:
- """ + "\n- ".join(breakdown)
