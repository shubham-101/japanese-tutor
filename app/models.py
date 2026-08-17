from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        default="Japanese Conversation",
    )

    scenario: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    jlpt_level: Mapped[str] = mapped_column(
    String(10),
    default="N4",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"),
    )

    role: Mapped[str] = mapped_column(
        String(20),
    )

    content: Mapped[str] = mapped_column(
        Text,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    conversation = relationship(
        "Conversation",
        back_populates="messages",
    )


class Mistake(Base):
    __tablename__ = "mistakes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    category: Mapped[str] = mapped_column(
        String(100),
    )

    original: Mapped[str] = mapped_column(
        Text,
    )

    correction: Mapped[str] = mapped_column(
        Text,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    times_seen: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    last_seen: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    word: Mapped[str] = mapped_column(
        String(100),
    )

    reading: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    meaning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    jlpt_level: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    times_seen: Mapped[int] = mapped_column(
    Integer,
    default=0,
    )

    times_correct: Mapped[int] = mapped_column(
    Integer,
    default=0,
    )

    mastery: Mapped[int] = mapped_column(
    Integer,
    default=0,
    )

    next_review: Mapped[datetime | None] = mapped_column(
    DateTime,
    nullable=True,
    )

class GrammarPoint(Base):
    __tablename__ = "grammar_points"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    grammar: Mapped[str] = mapped_column(
        String(100),
    )

    meaning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    jlpt_level: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    mastery: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    times_seen: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    times_correct: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


class Kanji(Base):
    __tablename__ = "kanji"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    character: Mapped[str] = mapped_column(
        String(10),
    )

    meaning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reading: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    jlpt_level: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    mastery: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    times_seen: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    times_correct: Mapped[int] = mapped_column(
    Integer,
    default=0,
    )

    mastery: Mapped[int] = mapped_column(
    Integer,
    default=0,
    )

    next_review: Mapped[datetime | None] = mapped_column(
    DateTime,
    nullable=True,
    )


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
    )

    item: Mapped[str] = mapped_column(
        String(200),
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

class ReviewSession(Base):
    __tablename__ = "review_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    item_type: Mapped[str] = mapped_column(
        String(50),
    )

    item_id: Mapped[int] = mapped_column(
        Integer,
    )

    question: Mapped[str] = mapped_column(
        Text,
    )

    correct_answer: Mapped[str] = mapped_column(
        Text,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    completed: Mapped[bool] = mapped_column(
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    mode: Mapped[str] = mapped_column(
        String(50),
    )

    jlpt_level: Mapped[str] = mapped_column(
        String(10),
    )

    question: Mapped[str] = mapped_column(
        Text,
    )

    options: Mapped[str] = mapped_column(
        Text,
    )

    correct_answer: Mapped[str] = mapped_column(
        Text,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    skill_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    skill_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    completed: Mapped[bool] = mapped_column(
        default=False,
    )

    correct: Mapped[bool | None] = mapped_column(
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


class FileUpload(Base):
    __tablename__ = "file_uploads"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"),
    )

    filename: Mapped[str] = mapped_column(
        String(255),
    )

    file_type: Mapped[str] = mapped_column(
        String(50),
    )

    content: Mapped[str] = mapped_column(
        Text,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    conversation = relationship(
        "Conversation",
        backref="files",
    )