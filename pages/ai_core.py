import json
import streamlit as st
from groq import Groq

# =========================================================
# 🔐 GROQ CLIENT
# =========================================================
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# =========================================================
# 📦 TOOL: GET RAW DATA (AI-OWNED CONTEXT)
# =========================================================
def get_raw_data():

    return {
        "cache_data": st.session_state.get("all_data", []),
        "branches": st.session_state.get("branches", []),
        "daily_items": st.session_state.get("DAILY_ITEMS", {}),
        "weekly_items": st.session_state.get("WEEKLY_ITEMS", {})
    }

# =========================================================
# 🧼 SAFE JSON EXTRACTOR (FIXES YOUR ERROR)
# =========================================================
def extract_json(text):

    try:
        text = text.replace("```json", "").replace("```", "").strip()

        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end == -1:
            return None

        return json.loads(text[start:end])

    except:
        return None

# =========================================================
# 🧠 AI CORE ENGINE
# =========================================================
def run_ai(user_input):

    system_prompt = """
You are STOCK AI, an autonomous inventory intelligence system.

You control all reasoning.

TOOLS AVAILABLE:
1. get_raw_data

RULES:
- Decide when to use tools
- Do all analysis yourself
- Never ask Python for calculations
- Always return final structured answer

TOOL FORMAT (STRICT):
{"tool":"get_raw_data"}

FINAL FORMAT:
- Summary
- Stock Status
- Branch Breakdown
- Insights
- Action Plan
- Risk Level
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    try:

        # =====================================================
        # TOOL LOOP
        # =====================================================
        for _ in range(5):

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.2,
                max_tokens=1200
            )

            reply = response.choices[0].message.content.strip()

            tool_request = extract_json(reply)

            # =================================================
            # TOOL CALL DETECTED
            # =================================================
            if (
                isinstance(tool_request, dict)
                and tool_request.get("tool") == "get_raw_data"
            ):

                tool_data = get_raw_data()

                messages.append({
                    "role": "assistant",
                    "content": reply
                })

                messages.append({
                    "role": "user",
                    "content": f"TOOL_RESULT:\n{json.dumps(tool_data)}"
                })

                continue

            # =================================================
            # FINAL RESPONSE
            # =================================================
            return reply

        return "⚠️ AI loop limit reached."

    except Exception as e:
        return f"⚠️ System Error: {str(e)}"
