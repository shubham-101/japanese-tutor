from pydantic import BaseModel


class StudentProfile(BaseModel):
    jlpt_level: str = "N4"
    native_language: str = "English"
    target_level: str = "N3"
    learning_mode: str = "balanced"

from pydantic import BaseModel


STUDY_MODES = {
    "conversation": "Free Japanese conversation",
    "grammar": "Focused grammar practice",
    "vocabulary": "Vocabulary practice",
    "kanji": "Kanji practice",
    "jlpt": "JLPT-style questions",
    "mistakes": "Practice recurring mistakes",
    "review": "Spaced repetition review",
}


class StudentProfile(BaseModel):
    jlpt_level: str = "N4"
    native_language: str = "English"
    target_level: str = "N3"
    learning_mode: str = "balanced"