import requests

# ---------------- FREE MODEL (NO API KEY NEEDED) ----------------
API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"

SYSTEM_PROMPT = """
You are a natural, human-like assistant.
Speak casually, clearly, and intelligently like ChatGPT.
"""

def run_ai(user_input, context=None):
    if context is None:
        context = {}

    # combine system style + user input (since free model doesn't support system roles)
    prompt = f"{SYSTEM_PROMPT}\nUser: {user_input}\nAI:"

    try:
        response = requests.post(
            API_URL,
            json={"inputs": prompt}
        )

        data = response.json()

        # HuggingFace response handling
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]

        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]

        return "I'm thinking 🤔 try again..."

    except Exception as e:
        return f"ERROR: {str(e)}"
