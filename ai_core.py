import os
import time
from openai import OpenAI

# ---------------- SAFE CLIENT INIT ----------------
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY is missing. Add it in Streamlit Secrets.")

client = OpenAI(api_key=api_key)

# ---------------- HUMAN-LIKE SYSTEM PROMPT ----------------
SYSTEM_PROMPT = """
You are BART AI, a highly intelligent, natural, human-like assistant.

Rules:
- Speak naturally like ChatGPT
- Be helpful, calm, and conversational
- Understand context deeply
- Avoid robotic or scripted answers
- Ask clarifying questions when needed
- Keep responses clean and useful
"""

# ---------------- MAIN AI FUNCTION ----------------
def run_ai(user_input, context=None):
    if context is None:
        context = {}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    # Optional context injection (sales, etc.)
    if context:
        messages.insert(1, {
            "role": "system",
            "content": f"Business context: {context}"
        })

    # ---------------- RETRY LOGIC (RATE LIMIT SAFE) ----------------
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.8
            )

            return response.choices[0].message.content

        except Exception as e:
            # small delay to avoid rate spikes
            time.sleep(1.5)

            last_error = str(e)

    # ---------------- FALLBACK (IF OPENAI FAILS) ----------------
    return (
        "I'm having a small technical delay right now 😅 "
        "Please try again in a moment."
    )
