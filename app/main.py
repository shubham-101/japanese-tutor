from .memory import build_learning_context
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import (
    Conversation,
    Message,
    Mistake,
    ReviewSession,
    Vocabulary,
    GrammarPoint,
    Kanji,
    StudySession,
    FileUpload,
)
from .ollama_client import chat
from .analyzer import analyze_japanese
from .schemas import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
)
from datetime import datetime

from .srs import calculate_next_review

from .review import generate_review_question

from .student import STUDY_MODES

from .student import STUDY_MODES
from .study import (
    validate_jlpt_level,
    validate_study_mode,
    build_study_prompt,
)
from .schemas import StudySessionCreate

import json

from .study_engine import generate_study_question
from .memory import build_learning_context
from fastapi.middleware.cors import CORSMiddleware

# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Japanese Tutor API",
    version="1.0.0",
    description="Local AI Japanese learning system powered by Ollama.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "Japanese Tutor API",
        "status": "running",
        "model": "japanese-tutor",
    }


# ============================================================
# CONVERSATIONS
# ============================================================

@app.post("/conversations")
def create_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db),
):
    conversation = Conversation(
    title=request.title,
    scenario=request.scenario,
    jlpt_level=request.jlpt_level,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "scenario": conversation.scenario,
        "jlpt_level": conversation.jlpt_level,
        "created_at": conversation.created_at,
    }

@app.get("/conversations")
def get_conversations(
    db: Session = Depends(get_db),
):
    conversations = (
        db.query(Conversation)
        .order_by(Conversation.created_at.desc())
        .all()
    )

    return [
        {
            "id": conversation.id,
            "title": conversation.title,
            "scenario": conversation.scenario,
            "created_at": conversation.created_at,
        }
        for conversation in conversations
    ]


@app.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .all()
    )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "scenario": conversation.scenario,
        "created_at": conversation.created_at,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }


# ============================================================
# CHAT
# ============================================================

@app.post("/chat", response_model=ChatResponse)
def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # Find conversation
    # --------------------------------------------------------

    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == request.conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    # --------------------------------------------------------
    # Save user's message
    # --------------------------------------------------------

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # --------------------------------------------------------
    # Get conversation history
    # --------------------------------------------------------

    history = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation.id
        )
        .order_by(Message.created_at)
        .all()
    )

    # --------------------------------------------------------
    # Convert history to Ollama format
    # --------------------------------------------------------

    ollama_messages = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in history
    ]

    # --------------------------------------------------------
    # Generate tutor response
    # --------------------------------------------------------

    try:
        learning_context = build_learning_context(db)

        # Get uploaded files for context
        files = (
            db.query(FileUpload)
            .filter(FileUpload.conversation_id == conversation.id)
            .all()
        )

        file_context = ""
        if files:
            file_context = "\n\nUploaded documents for reference:\n"
            for f in files:
                file_context += f"\n--- {f.filename} ({f.file_type}) ---\n{f.content}\n"

        combined_context = learning_context + file_context if learning_context else file_context

        response = chat(
            ollama_messages,
            learning_context=combined_context,
            jlpt_level=conversation.jlpt_level,
            scenario=conversation.scenario,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ollama error: {str(e)}",
        )

    # --------------------------------------------------------
    # Save tutor response
    # --------------------------------------------------------

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response,
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    # --------------------------------------------------------
    # Analyze student's Japanese
    # --------------------------------------------------------

    try:
        analysis = analyze_japanese(request.message)

    except Exception as e:
        # Analysis failure should NOT destroy the conversation.
        #
        # The tutor response has already been generated.
        # We simply continue without learning analysis.
        analysis = {
            "mistakes": [],
            "vocabulary": [],
            "grammar": [],
            "kanji": [],
        }

        print(
            f"Learning analysis failed: {e}"
        )

    # ========================================================
    # SAVE MISTAKES
    # ========================================================

    mistakes_saved = 0

    for mistake in analysis.get("mistakes", []):

        category = mistake.get(
            "category",
            "unknown",
        )

        original = mistake.get(
            "original",
            "",
        )

        correction = mistake.get(
            "correction",
            "",
        )

        explanation = mistake.get(
            "explanation",
            "",
        )

        # Ignore malformed analyzer results
        if not original or not correction:
            continue

        db.add(
            Mistake(
                category=category,
                original=original,
                correction=correction,
                explanation=explanation,
            )
        )

        mistakes_saved += 1

    # ========================================================
    # SAVE VOCABULARY
    # ========================================================

    vocabulary_saved = 0

    for vocab in analysis.get("vocabulary", []):

        word = vocab.get(
            "word",
            "",
        )

        if not word:
            continue

        # Avoid duplicate vocabulary entries
        existing = (
            db.query(Vocabulary)
            .filter(Vocabulary.word == word)
            .first()
        )

        if existing:
            continue

        db.add(
            Vocabulary(
                word=word,
                reading=vocab.get("reading"),
                meaning=vocab.get("meaning"),
                jlpt_level=vocab.get("jlpt_level"),
            )
        )

        vocabulary_saved += 1

    # ========================================================
    # SAVE GRAMMAR
    # ========================================================

    grammar_saved = 0

    for grammar in analysis.get("grammar", []):

        grammar_name = grammar.get(
            "grammar",
            "",
        )

        if not grammar_name:
            continue

        existing = (
            db.query(GrammarPoint)
            .filter(
                GrammarPoint.grammar == grammar_name
            )
            .first()
        )

        if existing:
            existing.times_seen += 1

            continue

        db.add(
            GrammarPoint(
                grammar=grammar_name,
                meaning=grammar.get("meaning"),
                jlpt_level=grammar.get("jlpt_level"),
                mastery=0,
                times_seen=1,
                times_correct=0,
            )
        )

        grammar_saved += 1

    # ========================================================
    # SAVE KANJI
    # ========================================================

    kanji_saved = 0

    for kanji in analysis.get("kanji", []):

        character = kanji.get(
            "character",
            "",
        )

        if not character:
            continue

        existing = (
            db.query(Kanji)
            .filter(
                Kanji.character == character
            )
            .first()
        )

        if existing:
            existing.times_seen += 1

            continue

        db.add(
            Kanji(
                character=character,
                meaning=kanji.get("meaning"),
                reading=kanji.get("reading"),
                jlpt_level=kanji.get("jlpt_level"),
                mastery=0,
                times_seen=1,
            )
        )

        kanji_saved += 1

    # ========================================================
    # FINAL DATABASE COMMIT
    # ========================================================

    db.commit()

    # ========================================================
    # RESPONSE
    # ========================================================

    return ChatResponse(
        conversation_id=conversation.id,
        response=response,
    )


# ============================================================
# MISTAKES
# ============================================================

@app.get("/mistakes")
def get_mistakes(
    db: Session = Depends(get_db),
):
    mistakes = (
        db.query(Mistake)
        .order_by(Mistake.created_at.desc())
        .all()
    )

    return [
        {
            "id": mistake.id,
            "category": mistake.category,
            "original": mistake.original,
            "correction": mistake.correction,
            "explanation": mistake.explanation,
            "created_at": mistake.created_at,
        }
        for mistake in mistakes
    ]


# ============================================================
# VOCABULARY
# ============================================================

@app.get("/vocabulary")
def get_vocabulary(
    db: Session = Depends(get_db),
):
    vocabulary = (
        db.query(Vocabulary)
        .order_by(Vocabulary.created_at.desc())
        .all()
    )

    return [
        {
            "id": vocab.id,
            "word": vocab.word,
            "reading": vocab.reading,
            "meaning": vocab.meaning,
            "jlpt_level": vocab.jlpt_level,
            "created_at": vocab.created_at,
        }
        for vocab in vocabulary
    ]


# ============================================================
# GRAMMAR
# ============================================================

@app.get("/grammar")
def get_grammar(
    db: Session = Depends(get_db),
):
    grammar_points = (
        db.query(GrammarPoint)
        .order_by(GrammarPoint.created_at.desc())
        .all()
    )

    return [
        {
            "id": grammar.id,
            "grammar": grammar.grammar,
            "meaning": grammar.meaning,
            "jlpt_level": grammar.jlpt_level,
            "mastery": grammar.mastery,
            "times_seen": grammar.times_seen,
            "times_correct": grammar.times_correct,
            "created_at": grammar.created_at,
        }
        for grammar in grammar_points
    ]


# ============================================================
# KANJI
# ============================================================

@app.get("/kanji")
def get_kanji(
    db: Session = Depends(get_db),
):
    kanji_list = (
        db.query(Kanji)
        .order_by(Kanji.created_at.desc())
        .all()
    )

    return [
        {
            "id": kanji.id,
            "character": kanji.character,
            "meaning": kanji.meaning,
            "reading": kanji.reading,
            "jlpt_level": kanji.jlpt_level,
            "mastery": kanji.mastery,
            "times_seen": kanji.times_seen,
            "created_at": kanji.created_at,
        }
        for kanji in kanji_list
    ]


# ============================================================
# PROGRESS
# ============================================================

@app.get("/progress")
def get_progress(
    db: Session = Depends(get_db),
):
    total_conversations = (
        db.query(Conversation).count()
    )

    total_messages = (
        db.query(Message).count()
    )

    total_mistakes = (
        db.query(Mistake).count()
    )

    total_vocabulary = (
        db.query(Vocabulary).count()
    )

    total_grammar = (
        db.query(GrammarPoint).count()
    )

    total_kanji = (
        db.query(Kanji).count()
    )

    return {
        "conversations": total_conversations,
        "messages": total_messages,
        "mistakes": total_mistakes,
        "vocabulary": total_vocabulary,
        "grammar_points": total_grammar,
        "kanji": total_kanji,
    }

@app.get("/review")
def get_review_items(
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()

    vocabulary = (
        db.query(Vocabulary)
        .filter(
            Vocabulary.next_review.is_(None)
            | (Vocabulary.next_review <= now)
        )
        .order_by(Vocabulary.mastery.asc())
        .limit(10)
        .all()
    )

    kanji = (
        db.query(Kanji)
        .filter(
            Kanji.next_review.is_(None)
            | (Kanji.next_review <= now)
        )
        .order_by(Kanji.mastery.asc())
        .limit(10)
        .all()
    )

    return {
        "vocabulary": [
            {
                "id": item.id,
                "word": item.word,
                "reading": item.reading,
                "meaning": item.meaning,
                "mastery": item.mastery,
            }
            for item in vocabulary
        ],
        "kanji": [
            {
                "id": item.id,
                "character": item.character,
                "reading": item.reading,
                "meaning": item.meaning,
                "mastery": item.mastery,
            }
            for item in kanji
        ],
    }

@app.post("/review/vocabulary/{vocabulary_id}")
def review_vocabulary(
    vocabulary_id: int,
    correct: bool,
    db: Session = Depends(get_db),
):
    vocabulary = (
        db.query(Vocabulary)
        .filter(
            Vocabulary.id == vocabulary_id
        )
        .first()
    )

    if not vocabulary:
        raise HTTPException(
            status_code=404,
            detail="Vocabulary not found",
        )

    vocabulary.times_seen += 1

    if correct:
        vocabulary.times_correct += 1

    vocabulary.mastery, vocabulary.next_review = (
        calculate_next_review(
            vocabulary.mastery,
            correct,
        )
    )

    db.commit()

    return {
        "word": vocabulary.word,
        "correct": correct,
        "mastery": vocabulary.mastery,
        "next_review": vocabulary.next_review,
    }

@app.post("/review/kanji/{kanji_id}")
def review_kanji(
    kanji_id: int,
    correct: bool,
    db: Session = Depends(get_db),
):
    kanji = (
        db.query(Kanji)
        .filter(
            Kanji.id == kanji_id
        )
        .first()
    )

    if not kanji:
        raise HTTPException(
            status_code=404,
            detail="Kanji not found",
        )

    kanji.times_seen += 1

    if correct:
        kanji.times_correct += 1

    kanji.mastery, kanji.next_review = (
        calculate_next_review(
            kanji.mastery,
            correct,
        )
    )

    db.commit()

    return {
        "character": kanji.character,
        "correct": correct,
        "mastery": kanji.mastery,
        "next_review": kanji.next_review,
    }

@app.get("/review")
def get_review(
    db: Session = Depends(get_db),
):
    from datetime import datetime

    now = datetime.utcnow()

    # --------------------------------------------------------
    # Find due vocabulary
    # --------------------------------------------------------

    vocabulary = (
        db.query(Vocabulary)
        .filter(
            Vocabulary.next_review.is_(None)
            | (Vocabulary.next_review <= now)
        )
        .order_by(
            Vocabulary.mastery.asc()
        )
        .first()
    )

    if vocabulary:
        question = generate_review_question(
            "vocabulary",
            vocabulary,
        )
    session = ReviewSession(
        item_type="vocabulary",
        item_id=vocabulary.id,
        question=question["question"],
        correct_answer=question["correct_answer"],
        explanation=question.get("explanation"),
        )
    db.add(session)
    db.commit()
    db.refresh(session)
    

    return {
        "session_id": session.id,
        "item_type": "vocabulary",
        "item_id": vocabulary.id,
        "question": question["question"],
        "options": question.get("options", []),
        "difficulty": question.get(
            "difficulty",
            "medium",
        ),
    }

    # --------------------------------------------------------
    # Find due kanji
    # --------------------------------------------------------

    kanji = (
        db.query(Kanji)
        .filter(
            Kanji.next_review.is_(None)
            | (Kanji.next_review <= now)
        )
        .order_by(
            Kanji.mastery.asc()
        )
        .first()
    )

    if kanji:
        question = generate_review_question(
            "kanji",
            kanji,
        )

        return {
            "item_type": "kanji",
            "item_id": kanji.id,
            "question": question["question"],
            "options": question.get("options", []),
            "difficulty": question.get(
                "difficulty",
                "medium",
            ),
        }

    # --------------------------------------------------------
    # Find weak grammar
    # --------------------------------------------------------

    grammar = (
        db.query(GrammarPoint)
        .order_by(
            GrammarPoint.mastery.asc()
        )
        .first()
    )

    if grammar:
        question = generate_review_question(
            "grammar",
            grammar,
        )

        return {
            "item_type": "grammar",
            "item_id": grammar.id,
            "question": question["question"],
            "options": question.get("options", []),
            "difficulty": question.get(
                "difficulty",
                "medium",
            ),
        }

    # --------------------------------------------------------
    # Nothing to review
    # --------------------------------------------------------

    return {
        "message": "No review items available."
    }

@app.post("/review/{session_id}/answer")
def answer_review(
    session_id: int,
    answer: str,
    db: Session = Depends(get_db),
):
    session = (
        db.query(ReviewSession)
        .filter(
            ReviewSession.id == session_id
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Review session not found",
        )

    if session.completed:
        raise HTTPException(
            status_code=400,
            detail="Review session already completed",
        )

    correct = (
        answer.strip().lower()
        == session.correct_answer.strip().lower()
    )

    # --------------------------------------------------------
    # Update learning item
    # --------------------------------------------------------

    if session.item_type == "vocabulary":

        item = (
            db.query(Vocabulary)
            .filter(
                Vocabulary.id == session.item_id
            )
            .first()
        )

        if item:
            item.times_seen += 1

            if correct:
                item.times_correct += 1

            item.mastery, item.next_review = (
                calculate_next_review(
                    item.mastery,
                    correct,
                )
            )

    elif session.item_type == "kanji":

        item = (
            db.query(Kanji)
            .filter(
                Kanji.id == session.item_id
            )
            .first()
        )

        if item:
            item.times_seen += 1

            if correct:
                item.times_correct += 1

            item.mastery, item.next_review = (
                calculate_next_review(
                    item.mastery,
                    correct,
                )
            )

    elif session.item_type == "grammar":

        item = (
            db.query(GrammarPoint)
            .filter(
                GrammarPoint.id == session.item_id
            )
            .first()
        )

        if item:
            item.times_seen += 1

            if correct:
                item.times_correct += 1

            item.mastery, item.next_review = (
                calculate_next_review(
                    item.mastery,
                    correct,
                )
            )

    session.completed = True

    db.commit()

    return {
        "correct": correct,
        "correct_answer": session.correct_answer,
        "explanation": session.explanation,
    }


# ============================================================
# STUDY MODES
# ============================================================

@app.get("/study/modes")
def get_study_modes():
    return STUDY_MODES


@app.post("/study")
def create_study_session(
    request: StudySessionCreate,
    db: Session = Depends(get_db),
):
    mode = request.mode.lower()
    jlpt_level = request.jlpt_level.upper()

    if not validate_study_mode(mode):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid study mode",
                "available_modes": list(
                    STUDY_MODES.keys()
                ),
            },
        )

    if not validate_jlpt_level(jlpt_level):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid JLPT level",
                "available_levels": [
                    "N5",
                    "N4",
                    "N3",
                    "N2",
                    "N1",
                ],
            },
        )

    # Get student's current weaknesses
    learning_context = build_learning_context(db)

    # Ask Qwen to generate a question
    question = generate_study_question(
        mode=mode,
        jlpt_level=jlpt_level,
        learning_context=learning_context,
    )

    # Save session
    session = StudySession(
        mode=mode,
        jlpt_level=jlpt_level,
        question=question["question"],
        options=json.dumps(
            question.get("options", []),
            ensure_ascii=False,
        ),
        correct_answer=question["correct_answer"],
        explanation=question.get(
            "explanation"
        ),
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    # DO NOT send correct_answer to frontend
    return {
        "session_id": session.id,
        "mode": mode,
        "jlpt_level": jlpt_level,
        "question": question["question"],
        "options": question.get(
            "options",
            [],
        ),
        "difficulty": question.get(
            "difficulty",
            "medium",
        ),
    }

@app.post("/study/{session_id}/answer")
def answer_study_session(
    session_id: int,
    answer: str,
    db: Session = Depends(get_db),
):
    session = (
        db.query(StudySession)
        .filter(
            StudySession.id == session_id
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Study session not found",
        )

    if session.completed:
        raise HTTPException(
            status_code=400,
            detail="Study session already completed",
        )

    correct = (
        answer.strip().lower()
        == session.correct_answer.strip().lower()
    )

    session.completed = True
    session.correct = correct

    db.commit()

    return {
        "correct": correct,
        "correct_answer": session.correct_answer,
        "explanation": session.explanation,
    }


# ============================================================
# FILE UPLOADS
# ============================================================

@app.post("/conversations/{conversation_id}/upload")
def upload_file(
    conversation_id: int,
    filename: str,
    file_type: str,
    content: str,
    db: Session = Depends(get_db),
):
    """Upload a file to a conversation for context"""
    
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    file_upload = FileUpload(
        conversation_id=conversation_id,
        filename=filename,
        file_type=file_type,
        content=content,
    )

    db.add(file_upload)
    db.commit()
    db.refresh(file_upload)

    return {
        "id": file_upload.id,
        "conversation_id": file_upload.conversation_id,
        "filename": file_upload.filename,
        "file_type": file_upload.file_type,
        "created_at": file_upload.created_at.isoformat(),
    }


@app.get("/conversations/{conversation_id}/files")
def get_conversation_files(
    conversation_id: int,
    db: Session = Depends(get_db),
):
    """Get all files uploaded to a conversation"""
    
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    files = (
        db.query(FileUpload)
        .filter(FileUpload.conversation_id == conversation_id)
        .order_by(FileUpload.created_at.desc())
        .all()
    )

    return [
        {
            "id": f.id,
            "filename": f.filename,
            "file_type": f.file_type,
            "created_at": f.created_at.isoformat(),
        }
        for f in files
    ]


@app.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    """Delete a file from a conversation"""
    
    file_upload = (
        db.query(FileUpload)
        .filter(FileUpload.id == file_id)
        .first()
    )

    if not file_upload:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    db.delete(file_upload)
    db.commit()

    return {"success": True, "message": "File deleted"}

# @app.post("/study")
# def create_study_session(
#     request: StudySessionCreate,
# ):
#     mode = request.mode.lower()
#     jlpt_level = request.jlpt_level.upper()

#     if not validate_study_mode(mode):
#         raise HTTPException(
#             status_code=400,
#             detail={
#                 "error": "Invalid study mode",
#                 "available_modes": list(
#                     STUDY_MODES.keys()
#                 ),
#             },
#         )

#     if not validate_jlpt_level(jlpt_level):
#         raise HTTPException(
#             status_code=400,
#             detail={
#                 "error": "Invalid JLPT level",
#                 "available_levels": [
#                     "N5",
#                     "N4",
#                     "N3",
#                     "N2",
#                     "N1",
#                 ],
#             },
#         )

#     prompt = build_study_prompt(
#         mode=mode,
#         jlpt_level=jlpt_level,
#     )

#     return {
#         "mode": mode,
#         "jlpt_level": jlpt_level,
#         "prompt": prompt,
#     }