import re
        if not stock_results:

            if matched_branch:
                return (
                    f"📦 No stock data found for '{matched_item}' at '{matched_branch}' on {target_date}."
                )

            return (
                f"📦 No stock data found for '{matched_item}' on {target_date}."
            )

        # --------------------------------------
        # totals
        # --------------------------------------
        total_stock = sum(x["qty"] for x in stock_results)

        # --------------------------------------
        # build structured payload for GROQ
        # --------------------------------------
        payload = {
            "user_query": user_input,
            "resolved_item": matched_item,
            "resolved_branch": matched_branch,
            "resolved_date": target_date,
            "total_stock": total_stock,
            "results": stock_results,
        }

        # --------------------------------------
        # GROQ PROMPT
        # --------------------------------------
        prompt = f"""
You are BART AI.

You are a smart inventory assistant for a cafe chain.

The Python system already fetched the REAL stock data.

IMPORTANT:
- NEVER invent stock
- NEVER change quantities
- NEVER add fake branches
- ONLY use provided JSON data

JSON DATA:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Response Rules:
- Sound natural like ChatGPT
- Be concise
- Mention resolved item clearly
- Mention resolved branch clearly if available
- Mention resolved date clearly
- If one branch requested, DO NOT show all branches
- If no branch requested, summarize all branches
- Use professional formatting
- Keep response readable
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are BART AI, a smart inventory assistant. "
                        "You must ONLY use provided stock data."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=500,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"
