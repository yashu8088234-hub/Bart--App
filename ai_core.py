import json
import streamlit as st
from groq import Groq

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# =========================================================
# TOOL
# =========================================================
def get_raw_data():

    return {
        "cache_data": st.session_state.get("all_data"),
        "branches": st.session_state.get("branches"),
        "daily_items": st.session_state.get("DAILY_ITEMS"),
        "weekly_items": st.session_state.get("WEEKLY_ITEMS")
    }

# =========================================================
# JSON PARSER
# =========================================================
def extract_json(text):

    try:
        text = text.replace("```json", "").replace("```", "")
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == -1:
            return None
        return json.loads(text[start:end])
    except:
        return None

# =========================================================
# AI ENGINE
# =========================================================
def run_ai(user_input):

    system_prompt = """
You are STOCK AI.

RULES:
- You MUST use tool when needed
- If tool returns empty → STOP and say "NO DATA AVAILABLE"
- NEVER hallucinate stock values
- Only analyze real data

TOOL:
{"tool":"get_raw_data"}
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

                # 🚨 HARD STOP IF EMPTY
                if not tool_data or not tool_data.get("cache_data"):

                    return (
                        "⚠️ NO DATA AVAILABLE IN SYSTEM\n\n"
                        "Please load stock data before asking queries."
                    )

                messages.append({
                    "role": "assistant",
                    "content": reply
                })

                messages.append({
                    "role": "user",
                    "content": f"TOOL_RESULT:\n{json.dumps(tool_data)}"
                })

                continue

            return reply

        return "⚠️ AI loop limit reached."

    except Exception as e:
        return f"⚠️ System Error: {str(e)}"
