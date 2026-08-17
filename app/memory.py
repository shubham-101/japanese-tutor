from sqlalchemy.orm import Session

from .models import Mistake, Vocabulary, GrammarPoint, Kanji


def get_learning_memory(
    db: Session,
    limit: int = 10,
) -> dict:
    """
    Retrieve the student's recent learning history.
    """

    mistakes = (
        db.query(Mistake)
        .order_by(Mistake.created_at.desc())
        .limit(limit)
        .all()
    )

    vocabulary = (
        db.query(Vocabulary)
        .order_by(Vocabulary.created_at.desc())
        .limit(limit)
        .all()
    )

    grammar = (
        db.query(GrammarPoint)
        .order_by(
            GrammarPoint.mastery.asc(),
            GrammarPoint.created_at.desc(),
        )
        .limit(limit)
        .all()
    )

    kanji = (
        db.query(Kanji)
        .order_by(
            Kanji.mastery.asc(),
            Kanji.created_at.desc(),
        )
        .limit(limit)
        .all()
    )

    return {
        "mistakes": mistakes,
        "vocabulary": vocabulary,
        "grammar": grammar,
        "kanji": kanji,
    }


def build_learning_context(
    db: Session,
) -> str:

    memory = get_learning_memory(db)

    lines = []

    lines.append(
        "STUDENT LEARNING MEMORY"
    )

    lines.append(
        "Use this information to adapt the conversation."
    )

    # --------------------------------------------------------
    # Mistakes
    # --------------------------------------------------------

    if memory["mistakes"]:

        lines.append(
            "\nRECENT MISTAKES:"
        )

        for mistake in memory["mistakes"]:

            lines.append(
                f"- Category: {mistake.category}"
            )

            lines.append(
                f"  Original: {mistake.original}"
            )

            lines.append(
                f"  Correction: {mistake.correction}"
            )

            if mistake.explanation:
                lines.append(
                    f"  Explanation: {mistake.explanation}"
                )

    # --------------------------------------------------------
    # Vocabulary
    # --------------------------------------------------------

    if memory["vocabulary"]:

        lines.append(
            "\nRECENT VOCABULARY:"
        )

        for vocab in memory["vocabulary"]:

            lines.append(
                f"- {vocab.word}"
                f" ({vocab.reading or ''})"
                f": {vocab.meaning or ''}"
            )

    # --------------------------------------------------------
    # Grammar
    # --------------------------------------------------------

    if memory["grammar"]:

        lines.append(
            "\nGRAMMAR TO REINFORCE:"
        )

        for grammar in memory["grammar"]:

            lines.append(
                f"- {grammar.grammar}"
                f": {grammar.meaning or ''}"
                f" | JLPT: {grammar.jlpt_level or 'unknown'}"
                f" | Mastery: {grammar.mastery}"
            )

    # --------------------------------------------------------
    # Kanji
    # --------------------------------------------------------

    if memory["kanji"]:

        lines.append(
            "\nKANJI TO REINFORCE:"
        )

        for kanji in memory["kanji"]:

            lines.append(
                f"- {kanji.character}"
                f" ({kanji.reading or ''})"
                f": {kanji.meaning or ''}"
                f" | Mastery: {kanji.mastery}"
            )

    return "\n".join(lines)