import json

from ollama import Client

client = Client(host="http://localhost:11434")

MODEL_NAME = "japanese-tutor"


ANALYSIS_PROMPT = """
You are a Japanese language learning analyzer.

Analyze the student's Japanese response.

Return ONLY valid JSON.

Do not use markdown.
Do not use ```json.
Do not include explanations outside the JSON.

JSON schema:

{
  "mistakes": [
    {
      "category": "grammar|particle|vocabulary|conjugation|kanji|naturalness|register",
      "original": "",
      "correction": "",
      "explanation": ""
    }
  ],
  "vocabulary": [
    {
      "word": "",
      "reading": "",
      "meaning": "",
      "jlpt_level": ""
    }
  ],
  "grammar": [
    {
      "grammar": "",
      "meaning": "",
      "jlpt_level": ""
    }
  ],
  "kanji": [
    {
      "character": "",
      "meaning": "",
      "reading": "",
      "jlpt_level": ""
    }
  ]
}

Rules:

1. Only identify genuine mistakes.
2. Do not invent mistakes.
3. Do not classify stylistic differences as errors unless they materially affect naturalness.
4. Extract useful vocabulary from the student's response.
5. Extract meaningful grammar points.
6. Extract kanji actually present in the student's response.
7. Keep explanations concise.
8. Use Japanese terminology where appropriate.
"""


def analyze_japanese(text: str) -> dict:
    response = client.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": ANALYSIS_PROMPT,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        format="json",
    )

    content = response["message"]["content"]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "mistakes": [],
            "vocabulary": [],
            "grammar": [],
            "kanji": [],
        }