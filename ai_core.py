
# ---------------- AI CORE ----------------

DEV_MODE = True  # 🔁 change to False later

def run_ai(query, context):
    q = query.lower()

    total_revenue = context.get("revenue", 0)
    total_items = context.get("items", 0)
    sales = context.get("sales", [])

    # ---- revenue ----
    if "revenue" in q:
        return f"💰 Revenue: SAR {total_revenue:.2f}"

    # ---- items ----
    if "items" in q:
        return f"📦 Total items: {total_items}"

    # ---- find ----
    if "find" in q:
        keyword = q.replace("find", "").strip()
        results = [x for x in sales if keyword in x[0].lower()]
        if results:
            return "\n".join([f"{r[0]} → {r[1]} x {r[2]}" for r in results])
        return "❌ Item not found"

    # ---- suggestions ----
    if "suggest" in q:
        if not sales:
            return "No data available"
        top_item = max(sales, key=lambda x: x[1])
        return f"🔥 Top item: {top_item[0]} ({top_item[1]} sold)"

    return "🤖 DEV MODE: Command recognized"
