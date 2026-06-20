import os
import json
from openai import OpenAI

# Инициализатсияи клиент
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def analyze_student_level(
    subject_name: str,
    easy: int,
    medium: int,
    hard: int,
    correct: int,
    total: int,
    percent: float,
):
    """
    Таҳлили сатҳи дониши хонанда бо баргардонидани JSON
    """

    prompt = f"""
Таҳлил кун сатҳи дониши хонанда.

Фан: {subject_name}

Маълумоти воқеӣ:
- Шумораи умумии саволҳо: {total}
- Ҷавобҳои дуруст: {correct}
- Фоиз: {percent}%
- Саволҳои осон (дуруст): {easy}
- Саволҳои миёна (дуруст): {medium}
- Саволҳои мушкил (дуруст): {hard}

Қоидаҳо:
- Танҳо JSON баргардон
- Ҳеҷ матни иловагӣ нанавис
- Забон: тоҷикӣ
- Маълумотро тағйир надеҳ

Формат:
{{
  "level": "паст | миёна | хуб | аъло",
  "description": "тавсифи кӯтоҳ бо рақамҳои дуруст",
  "recommendation": "тавсияи омӯзишӣ"
}}
"""

    try:
        response = client.responses.create(
            model="gpt-4.1",
            input=prompt
        )

        text = response.output_text.strip()

        # Тафтиш: JSON бошад
        return json.loads(text)

    except Exception as e:
        print("AI ERROR:", e)

        # fallback (агар AI хато кунад)
        return {
            "level": "Хато",
            "description": f"Таҳлил иҷро нашуд. Ҷавобҳои дуруст: {correct} аз {total}.",
            "recommendation": "Баъдтар дубора кӯшиш кунед."
        }