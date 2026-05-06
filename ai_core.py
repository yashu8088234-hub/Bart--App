import streamlit as st
from openai import OpenAI
import time

# ---------------- GET KEY FROM STREAMLIT SECRETS ----------------
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found in Streamlit secrets!")

client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = """
You are a natural, human-like assistant.
Speak casually, clearly, and intelligently like ChatGPT.
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
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8
        )

        return response.choices[0].message.content

    except Exception as e:
        # 👇 THIS IS IMPORTANT FOR DEBUGGING
        return f"ERROR: {str(e)}"
