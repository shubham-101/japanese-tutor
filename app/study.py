from .student import STUDY_MODES


VALID_LEVELS = {
    "N5",
    "N4",
    "N3",
    "N2",
    "N1",
}


def validate_study_mode(mode: str) -> bool:
    return mode in STUDY_MODES


def validate_jlpt_level(level: str) -> bool:
    return level.upper() in VALID_LEVELS


def build_study_prompt(
    mode: str,
    jlpt_level: str,
) -> str:

    mode_description = STUDY_MODES[mode]

    prompts = {

        "conversation": """
Have a natural Japanese conversation with the student.

Encourage the student to produce Japanese.
Ask one question at a time.
Keep the conversation appropriate for the student's JLPT level.
Correct important mistakes naturally.
""",

        "grammar": """
Focus on Japanese grammar practice.

Present one grammar exercise at a time.
Ask the student to answer.
Do not immediately reveal the answer.
After the student answers, explain whether it is correct
and explain the grammar briefly.
""",

        "vocabulary": """
Focus on Japanese vocabulary.

Test the student's vocabulary through meanings,
readings, sentence completion, and usage.

Use vocabulary appropriate for the student's JLPT level.
Ask one question at a time.
""",

        "kanji": """
Focus on kanji practice.

Test kanji readings, meanings, and usage.
Use kanji appropriate for the student's JLPT level.
Ask one question at a time.
""",

        "jlpt": """
Act as a JLPT practice examiner.

Generate questions appropriate for the selected JLPT level.

Use a mixture of:
- vocabulary
- grammar
- reading
- kanji

Ask one question at a time.
Do not reveal the answer until the student responds.
""",

        "mistakes": """
Focus specifically on the student's recurring mistakes.

Use the student's learning memory to create exercises
that target weak areas.

Do not simply repeat the original mistake.
Create a new example testing the same concept.
""",

        "review": """
Run a spaced-repetition review session.

Prioritize items that are due for review and items
with low mastery.

Ask one question at a time.
Do not reveal the answer before the student responds.
""",
    }

    return f"""
You are a Japanese language tutor.

Student level:
{jlpt_level}

Study mode:
{mode}

Mode description:
{mode_description}

{prompts[mode]}

General rules:

1. Teach at the student's JLPT level.
2. Do not unnecessarily use advanced vocabulary.
3. Keep questions focused.
4. Ask only one question at a time.
5. Do not reveal answers before the student responds.
6. Encourage active recall.
7. Keep explanations concise.
"""