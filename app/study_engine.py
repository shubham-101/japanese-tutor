import json
from ollama import Client

from .student import STUDY_MODES


client = Client(
    host="http://localhost:11434"
)

MODEL_NAME = "japanese-tutor"


def generate_study_question(
    mode: str,
    jlpt_level: str,
    learning_context: str = "",
):
    mode_instructions = {
        "conversation": """
Start a natural Japanese conversation.
Ask exactly one question.
Encourage the student to answer in Japanese.
Do not provide multiple-choice options.
""",

        "grammar": """
Create one Japanese grammar question.
Use four multiple-choice options.
There must be exactly one correct answer.
""",

        "vocabulary": """
Create one Japanese vocabulary question.
Test meaning, reading, or usage.
Use four multiple-choice options.
""",

        "kanji": """
Create one Japanese kanji question.
Test reading, meaning, or usage.
Use four multiple-choice options.
""",

        "jlpt": """
Create one JLPT-style Japanese question.
Use four multiple-choice options.
The question must match the requested JLPT level.
""",

        "mistakes": """
Create one question targeting a recurring mistake
from the student's learning history.

Do NOT copy the original mistake.
Create a new sentence testing the same concept.

Use four multiple-choice options.
""",

        "review": """
Create one spaced-repetition review question.

Prioritize the student's weakest learning items.

Use four multiple-choice options unless the item
is better tested through direct recall.
""",
    }

    instruction = mode_instructions.get(
        mode,
        mode_instructions["conversation"],
    )

    prompt = f"""
You are an expert Japanese language tutor.

Student JLPT level:
{jlpt_level}

Study mode:
{mode}

{instruction}

Student learning history:

{learning_context}

IMPORTANT:

- Match the student's JLPT level.
- Do not use unnecessarily advanced grammar.
- Do not reveal the answer in the question.
- Generate exactly ONE question.
- Return ONLY valid JSON.

Return this exact structure:

{{
    "question": "question here",
    "options": [
        "option 1",
        "option 2",
        "option 3",
        "option 4"
    ],
    "correct_answer": "correct option",
    "explanation": "short explanation",
    "difficulty": "easy|medium|hard",
    "skill_type": "grammar",
    "skill": "て-form",
}}
"""

    response = client.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        format="json",
    )

    content = response["message"]["content"]

    return json.loads(content)