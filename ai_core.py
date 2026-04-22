# ---------------- AI CORE ----------------

import os

DEV_MODE = False  # 🔁 True = no API, False = real AI


def run_ai(query, context):
    q = query.lower()

    # ---------- DEV MODE (NO LIMITS) ----------
    if DEV_MODE:
        if "revenue" in q:
            return f"💰 Revenue: SAR {context.get('revenue', 0):.2f}"
        if "items" in q:
            return f"📦 Items: {context.get('items', 0)}"
        return "🤖 DEV MODE: AI working (no API used)"

    # ---------- REAL AI ----------
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        system_prompt = f"""
You are a smart assistant inside a cafe POS system.

You talk naturally like ChatGPT.

You help with:
- sales analysis
- errors
- items
- general conversation

DATA:
Revenue: {context.get('revenue', 0)}
Items: {context.get('items', 0)}
Sales: {context.get('sales', [])[:10]}

Be helpful and human-like.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ AI Error: {e}"
