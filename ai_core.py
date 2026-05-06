import streamlit as st
from groq import Groq

# ---------------- GET KEY ----------------
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in Streamlit secrets!")

client = Groq(api_key=api_key)

SYSTEM_PROMPT = """
You are BART AI, a natural, human-like assistant.
Speak casually like ChatGPT.
Be helpful, smart, and conversational.
"""

def run_ai(user_input, context=None):
    if context is None:
        context = {}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages,
            temperature=0.8
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI error 😅: {str(e)}"
