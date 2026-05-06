import requests

API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"

SYSTEM_PROMPT = "You are a natural, human-like assistant."

def run_ai(user_input, context=None):
    if context is None:
        context = {}

    prompt = f"{SYSTEM_PROMPT}\nUser: {user_input}\nAI:"

    try:
        response = requests.post(
            API_URL,
            json={"inputs": prompt},
            timeout=20
        )

        # 🔥 IMPORTANT FIX: safe text read first
        raw = response.text

        # if API is loading or blocked
        if response.status_code != 200:
            return "AI is warming up ⏳ try again in a few seconds"

        # try JSON safely
        try:
            data = response.json()
        except:
            return "AI is busy right now 😅 try again"

        # extract response safely
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]

        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]

        return "Hmm 🤔 I didn't get a proper response"

    except Exception as e:
        return "AI offline 😅 please retry"
