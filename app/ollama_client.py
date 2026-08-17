from ollama import Client


client = Client(
    host="http://localhost:11434"
)

MODEL_NAME = "japanese-tutor"


def chat(
    messages: list[dict],
    learning_context: str | None = None,
    jlpt_level: str = "N4",
    scenario: str | None = None,
) -> str:

    system_message = None

    if learning_context:

        system_message = {
            "role": "system",
            "content": f"""
        You are an expert Japanese language tutor.

        Student JLPT level:
        {jlpt_level}

        Conversation scenario:
        {scenario or "general conversation"}

        Teaching rules:

        1. Keep Japanese appropriate for the student's JLPT level.
        2. Prefer vocabulary and grammar appropriate for that level.
        3. Do not unnecessarily use advanced grammar.
        4. Introduce slightly challenging material when appropriate.
        5. Encourage the student to produce Japanese.
        6. Correct important mistakes naturally.
        7. Explain corrections clearly.
        8. Use Japanese examples whenever useful.
        9. Do not overwhelm the student with explanations.
        10. Adapt difficulty based on the student's performance.

        {learning_context or ""}
        """,
        }

    final_messages = [
    system_message,
    *messages,
    ]

    if system_message:
        final_messages.append(system_message)

    final_messages.extend(messages)

    response = client.chat(
        model=MODEL_NAME,
        messages=final_messages,
    )

    return response["message"]["content"]