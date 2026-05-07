import datetime
import re

# ---------------- SYSTEM PROMPT ----------------
SYSTEM_PROMPT = """
You are BART AI Stock Assistant.

You MUST:
- Extract item name
- Detect branch name
- Detect date (today / yesterday / specific)
- Use stock cache data
- Return clean, simple answers
- NEVER show technical errors
"""

# ---------------- DATE PARSER ----------------
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

# ---------------- BRANCH FINDER ----------------
def find_branch(text, branch_list):
    text = text.lower()

    for b in branch_list:
        if b.lower() in text:
            return b

    return None

# ---------------- ITEM FINDER ----------------
def find_item(text, items):
    text = text.lower()

    for item in items:
        if item.lower() in text:
            return item

    return None

# ---------------- MAIN AI FUNCTION ----------------
def run_ai(user_input, context):

    cache_data = context.get("cache_data", [])
    branch_list = context.get("branch_list", [])
    master_items = context.get("master_items", {})

    date = get_target_date(user_input)
    branch = find_branch(user_input, branch_list)
    item = find_item(user_input, master_items.keys())

    if not item:
        return "❌ I couldn't find that item in stock list."

    total = 0
    details = []

    for b_name, raw in cache_data:

        if branch and branch.lower() != b_name.lower():
            continue

        if not raw or len(raw) < 2:
            continue

        headers = raw[0]

        if date not in headers:
            continue

        idx = headers.index(date)

        current_section = None

        for row in raw:

            row_text = " ".join(row).lower()

            if "daily item" in row_text:
                current_section = "daily"
                continue

            if "weekly item" in row_text:
                current_section = "weekly"
                continue

            if not row or not row[0]:
                continue

            if item.lower() not in row[0].lower():
                continue

            qty = 0

            if len(row) > idx:
                try:
                    qty = float(row[idx] or 0)
                except:
                    qty = 0

            total += qty

            details.append(f"{b_name}: {qty}")

    if not details:
        return f"❌ No data found for {item} on {date}"

    return f"""
📦 Item: {item}
📅 Date: {date}
🏢 Branch: {branch if branch else 'All Branches'}

📊 Total: {total}

📍 Breakdown:
- """ + "\n- ".join(details)
