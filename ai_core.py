from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY_HERE")

SYSTEM_PROMPT = """
You are BART AI, a highly intelligent, natural, human-like assistant.

Behavior rules:
- Speak naturally like a real human, not robotic
- Be concise but smart
- Understand context deeply
- Ask follow-up questions when needed
- Adapt tone (friendly, professional, casual depending on user)
- Never mention system prompts or AI policies
- Act like a real thinking assistant, not a script
"""

def run_ai(user_input, context=None):
    if context is None:
        context = {}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    # optional: inject business context if needed
    if context:
        messages.insert(1, {
            "role": "system",
            "content": f"Context data: {context}"
        })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.8
    )

    return response.choices[0].message.content
