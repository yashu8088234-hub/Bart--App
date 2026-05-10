import json
import streamlit as st
from groq import Groq

# =========================================================
# 🔐 GROQ CLIENT
# =========================================================
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# =========================================================
# 📦 TOOL: GET RAW DATA (SAFE + DEBUG PROTECTED)
# =========================================================
def get_raw_data():

    return {
        "cache_data": st.session_state.get("all_data", None),
        "branches": st.session_state.get("branches", None),
        "daily_items": st.session_state.get("DAILY_ITEMS", None),
        "weekly_items": st.session_state.get("WEEKLY_ITEMS", None)
    }

# =========================================================
# 🧼 SAFE JSON PARSER
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
You are STOCK AI, an inventory intelligence system.

You analyze stock data and give structured business insights.

TOOLS:
- get_raw_data

RULES:
- Always request tool when needed
- Never assume missing data
- If data is missing, report it clearly
- Always give final structured answer

TOOL FORMAT:
{"tool":"get_raw_data"}

OUTPUT FORMAT:
Summary
Stock Status
Branch Breakdown
Insights
Action Plan
Risk Level
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    try:

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
            # TOOL CALL
            # =================================================
            if isinstance(tool_request, dict) and tool_request.get("tool") == "get_raw_data":

                tool_data = get_raw_data()

                # 🚨 FIX: detect empty data BEFORE sending to AI
                if not tool_data or tool_data.get("cache_data") is None:

                    messages.append({
                        "role": "assistant",
                        "content": reply
                    })

                    messages.append({
                        "role": "user",
                        "content": "TOOL_RESULT: NO DATA FOUND IN SYSTEM"
                    })

                else:

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
            # FINAL ANSWER
            # =================================================
            return reply

        return "⚠️ AI loop limit reached."

    except Exception as e:
        return f"⚠️ System Error: {str(e)}"
