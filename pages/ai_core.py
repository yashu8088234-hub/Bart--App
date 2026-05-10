import json
import datetime
import streamlit as st
from groq import Groq

# =========================================================
# 🔐 GROQ CLIENT
# =========================================================
client = Groq(api_key=st.secrets["GROQ_API_KEY"])


# =========================================================
# 📦 RAW DATA TOOL (NO LOGIC)
# =========================================================
def get_raw_data(context):
    return {
        "cache_data": context.get("cache_data", []),
        "branches": context.get("branch_list", []),
        "items": context.get("master_items", [])
    }


# =========================================================
# 🧠 AI AGENT (TOOL-CALL LOOP)
# =========================================================
def run_ai(user_input, context):

    system_prompt = """
You are STOCK AI, an autonomous inventory intelligence system.

You control the full reasoning process.

You can request tools using JSON format ONLY:

TOOLS AVAILABLE:
1. get_raw_data → returns full inventory dataset

RULES:
- You decide everything
- You request raw data when needed
- You perform filtering, matching, and calculations yourself
- You do NOT ask Python to filter or guess anything
- You must always return a final answer

TOOL FORMAT (STRICT):
{"tool": "get_raw_data"}

FINAL ANSWER FORMAT:
Return a structured response:
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

        # =========================================================
        # 🔁 TOOL LOOP (AI DRIVEN)
        # =========================================================
        for _ in range(3):  # prevent infinite loop

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.2,
                max_tokens=800
            )

            reply = response.choices[0].message.content.strip()

            # =========================================================
            # 🛠️ CHECK IF AI REQUESTS TOOL
            # =========================================================
            if reply.startswith("{") and "tool" in reply:

                tool_request = json.loads(reply)

                if tool_request["tool"] == "get_raw_data":
                    tool_data = get_raw_data(context)

                    messages.append({
                        "role": "assistant",
                        "content": reply
                    })

                    messages.append({
                        "role": "user",
                        "content": f"TOOL_RESULT:\n{json.dumps(tool_data)}"
                    })

                    continue

            # =========================================================
            # ✅ FINAL ANSWER
            # =========================================================
            return reply

        return "⚠️ AI loop limit reached."

    except Exception as e:
        return f"⚠️ System Error: {str(e)}"
