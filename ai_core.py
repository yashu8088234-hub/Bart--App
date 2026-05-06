from openai import OpenAI

client = OpenAI(api_key="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")

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
