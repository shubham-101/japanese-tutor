import json

from ollama import Client

from .models import Vocabulary, Kanji, GrammarPoint, Mistake


client = Client(
    host="http://localhost:11434"
)

MODEL_NAME = "japanese-tutor"


REVIEW_PROMPT = """
You are a Japanese language test generator.

Create ONE Japanese learning question based on the
student's weak area.

Return ONLY valid JSON.

Schema:

{
  "type": "vocabulary|kanji|grammar|mistake",
  "question": "",
  "options": [],
  "correct_answer": "",
  "explanation": "",
  "difficulty": "easy|medium|hard"
}

Rules:

1. The question must test the supplied learning item.
2. There must be exactly one correct answer.
3. If options are used, provide exactly 4 options.
4. Do not reveal the answer in the question.
5. Keep the question appropriate for the item's JLPT level.
6. For vocabulary, test meaning, reading, or usage.
7. For kanji, test reading, meaning, or usage.
8. For grammar, test correct usage.
9. For mistakes, create a question specifically targeting
   the student's previous mistake.
10. Return JSON only.
"""


def generate_review_question(item_type, item):
    if item_type == "vocabulary":

        item_data = {
            "word": item.word,
            "reading": item.reading,
            "meaning": item.meaning,
            "jlpt_level": item.jlpt_level,
        }

    elif item_type == "kanji":

        item_data = {
            "character": item.character,
            "reading": item.reading,
            "meaning": item.meaning,
            "jlpt_level": item.jlpt_level,
        }

    elif item_type == "grammar":

        item_data = {
            "grammar": item.grammar,
            "meaning": item.meaning,
            "jlpt_level": item.jlpt_level,
            "mastery": item.mastery,
        }

    elif item_type == "mistake":

        item_data = {
            "category": item.category,
            "original": item.original,
            "correction": item.correction,
            "explanation": item.explanation,
        }

    else:
        raise ValueError(
            f"Unknown review type: {item_type}"
        )

    response = client.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": REVIEW_PROMPT,
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "type": item_type,
                        "item": item_data,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        format="json",
    )

    content = response["message"]["content"]

    return json.loads(content)