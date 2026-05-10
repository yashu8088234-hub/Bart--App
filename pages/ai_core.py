import json
import streamlit as st
from groq import Groq

# =========================================================
# 🔐 GROQ CLIENT
# =========================================================
client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)

# =========================================================
# 📦 RAW DATA TOOL
# AI HANDLES CONTEXT ITSELF
# =========================================================
def get_raw_data():

    return {

        # FULL RAW CACHE
        "cache_data": st.session_state.get(
            "all_data",
            []
        ),

        # BRANCHES
        "branches": st.session_state.get(
            "branches",
            []
        ),

        # DAILY ITEMS
        "daily_items": st.session_state.get(
            "DAILY_ITEMS",
            {}
        ),

        # WEEKLY ITEMS
        "weekly_items": st.session_state.get(
            "WEEKLY_ITEMS",
            {}
        )
    }

# =========================================================
# 🧠 AI AGENT
# =========================================================
def run_ai(user_input):

    system_prompt = """
You are STOCK AI, an autonomous inventory intelligence system.

You fully control reasoning and analysis.

You may request tools ONLY using valid JSON.

AVAILABLE TOOLS:
1. get_raw_data

RULES:
- You decide when data is needed
- You do all filtering and calculations yourself
- Never ask Python to analyze stock
- Always return a final answer
- Never stop after tool calls

STRICT TOOL FORMAT:
{"tool":"get_raw_data"}

FINAL RESPONSE FORMAT:
# Summary
# Stock Status
# Branch Breakdown
# Insights
# Action Plan
# Risk Level
"""

    messages = [

        {
            "role": "system",
            "content": system_prompt
        },

        {
            "role": "user",
            "content": user_input
        }
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

            reply = (
                response
                .choices[0]
                .message.content
                .strip()
            )

            # =================================================
            # TOOL CALL CHECK
            # =================================================
            try:

                tool_request = json.loads(reply)

                # ---------------------------------------------
                # GET RAW DATA TOOL
                # ---------------------------------------------
                if (
                    isinstance(tool_request, dict)
                    and tool_request.get("tool")
                    == "get_raw_data"
                ):

                    tool_data = get_raw_data()

                    # SAVE TOOL REQUEST
                    messages.append({

                        "role": "assistant",

                        "content": reply
                    })

                    # SEND TOOL RESULT
                    messages.append({

                        "role": "user",

                        "content":
                        f"TOOL_RESULT:\n"
                        f"{json.dumps(tool_data)}"
                    })

                    continue

            except:
                pass

            # =================================================
            # FINAL RESPONSE
            # =================================================
            return reply

        return "⚠️ AI loop limit reached."

    except Exception as e:

        return (
            f"⚠️ System Error:\n{str(e)}"
        )
