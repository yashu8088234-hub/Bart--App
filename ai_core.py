import streamlit as st
from groq import Groq

# ---------------- KEY ----------------
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    raise ValueError("Missing GROQ_API_KEY in Streamlit secrets")

client = Groq(api_key=api_key)

# ---------------- SYSTEM STYLE ----------------
SYSTEM_PROMPT = """
You are BART AI, a highly intelligent and natural assistant.

Rules:
- Respond like ChatGPT (clean, human, natural)
- No technical messages
- No error outputs
- Be concise but helpful
"""

# ---------------- MAIN FUNCTION ----------------
def run_ai(user_input, context=None):
    if context is None:
        context = {}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.8
        )

        return response.choices[0].message.content.strip()

    except Exception:
        # ❗ CLEAN fallback (no errors shown to user)
        return "I’m having a small issue right now — please try again in a moment."
