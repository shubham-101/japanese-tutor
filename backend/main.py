from fastapi import FastAPI, HTTPException, UploadFile, File, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import json
import requests
import time
import re
from collections import defaultdict
from datetime import datetime, timedelta

app = FastAPI(title="Japanese Tutor API", version="0.1.0")

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "japanese-tutor:latest"  # Use the Japanese tutor model

# Security configuration
RATE_LIMIT_REQUESTS = 10  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds
rate_limit_storage = defaultdict(list)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
    return response

# Trusted host middleware (allow localhost for development)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "*.local", "*.localhost"]
)

# Input sanitization function
def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS attacks"""
    if not text:
        return text

    # HTML escape common characters
    replacements = {
        '&': '&',
        '<': '<',
        '>': '>',
        '"': '"',
        "'": "'",
        '/': '&#x2F;',
        '`': '&#x60;',
        '=': '&#x3D;'
    }

    for char, escape in replacements.items():
        text = text.replace(char, escape)

    return text

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for health checks and docs
    if request.url.path in ["/", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    # Get client identifier (IP address for simplicity)
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.now()

    # Clean old requests
    rate_limit_storage[client_ip] = [
        req_time for req_time in rate_limit_storage[client_ip]
        if now - req_time < timedelta(seconds=RATE_LIMIT_WINDOW)
    ]

    # Check rate limit
    if len(rate_limit_storage[client_ip]) >= RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )

    # Add current request
    rate_limit_storage[client_ip].append(now)

    response = await call_next(request)
    return response

def call_ollama(prompt: str, system_prompt: str = None) -> str:
    """Call Ollama API to generate a response"""
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False
        }

        # Debug logging (safe for console)
        print(f"Calling Ollama at {OLLAMA_BASE_URL}/api/chat with model {OLLAMA_MODEL}")

        response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=30)
        print(f"Ollama response status: {response.status_code}")

        response.raise_for_status()

        result = response.json()
        content = result.get("message", {}).get("content", "I'm sorry, I couldn't generate a response.")
        return content
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return f"I'm having trouble connecting to my knowledge base. Please try again later."

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
study_sessions: Dict[str, Dict] = {}
conversations: Dict[str, Dict] = {}
files: Dict[str, Dict] = {}  # file_id -> file data

# Study modes endpoint
@app.get("/study/modes")
async def get_study_modes():
    return [
        {"id": "conversation", "title": "Conversation", "description": "Practice natural Japanese conversation."},
        {"id": "grammar", "title": "Grammar", "description": "Practice Japanese grammar."},
        {"id": "vocabulary", "title": "Vocabulary", "description": "Build your Japanese vocabulary."},
        {"id": "kanji", "title": "Kanji", "description": "Practice kanji readings and meanings."},
        {"id": "jlpt", "title": "JLPT", "description": "Practice JLPT-style questions."}
    ]

# Study session models
class StudySessionCreate(BaseModel):
    mode: str
    jlpt_level: str

class StudySessionResponse(BaseModel):
    session_id: str
    mode: str
    jlpt_level: str
    question: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None

# Create study session
@app.post("/study")
async def create_study_session(session: StudySessionCreate):
    session_id = str(uuid.uuid4())

    # Generate a realistic question using Ollama based on mode and level
    try:
        # Create a prompt for generating educational study content
        prompt = f"""Generate a realistic {session.mode} study question for JLPT level {session.jlpt_level}.

        Requirements:
        1. Create an authentic Japanese language learning question appropriate for {session.jlpt_level}
        2. For vocabulary, kanji, and jlpt modes: provide 4 multiple choice options (A-D)
        3. For conversation and grammar modes: provide a question that tests understanding
        4. Include the correct answer
        5. Provide a clear explanation of why the answer is correct
        6. Format your response as JSON with these keys:
           - "question": the question text
           - "options": array of 4 strings (for vocabulary, kanji, jlpt) or null (for conversation, grammar)
           - "correct_answer": the correct answer string
           - "explanation": detailed explanation of the answer

        Make sure the content is educationally sound and appropriate for the JLPT {session.jlpt_level} level."""

        system_prompt = "You are an expert Japanese language educator creating study materials. Generate accurate, level-appropriate content."

        # Call Ollama to generate the study question
        ai_response = call_ollama(prompt, system_prompt)

        # Try to parse the AI response as JSON
        import re
        # Extract JSON from response (handle cases where AI might add extra text)
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            study_data = json.loads(json_match.group())
            # Validate required fields
            required_fields = ["question", "options", "correct_answer", "explanation"]
            if all(field in study_data for field in required_fields):
                # Ensure options is a list or null
                if study_data["options"] is not None and not isinstance(study_data["options"], list):
                    study_data["options"] = ["Option A", "Option B", "Option C", "Option D"]
                elif study_data["options"] is None and session.mode in ["vocabulary", "kanji", "jlpt"]:
                    study_data["options"] = ["Option A", "Option B", "Option C", "Option D"]

                study_data["session_id"] = session_id
                study_data["mode"] = session.mode
                study_data["jlpt_level"] = session.jlpt_level
                return study_data
    except Exception as e:
        print(f"Error generating AI study question: {e}")
        # Fall through to fallback method

    # Fallback: Generate a question based on mode and level (enhanced samples)
    question_templates = {
        "conversation": f"What would you say in Japanese when you want to politely ask for help in a store? (JLPT {session.jlpt_level})",
        "grammar": f"Which particle correctly completes this sentence: 本を___読みます。 (JLPT {session.jlpt_level})",
        "vocabulary": f"What is the Japanese word for 'important' that you would need to know for JLPT {session.jlpt_level}?",
        "kanji": f"What is the meaning and reading of the kanji '明' which appears in JLPT {session.jlpt_level}?",
        "jlpt": f"Choose the grammatically correct sentence appropriate for JLPT {session.jlpt_level}."
    }

    question = question_templates.get(session.mode, f"Sample {session.mode} question for {session.jlpt_level}")

    # Enhanced sample options based on mode
    if session.mode == "vocabulary":
        options = ["重要 (じゅうよう) - important", "可能 (かのう) - possible", "必要 (ひつよう) - necessary", "便利 (べんり) - convenient"]
        correct_answer = options[0]
        explanation = "重要 (じゅうよう) means 'important' and is a key vocabulary word for JLPT N4 and above."
    elif session.mode == "kanji":
        options = ["明 (あか) - bright", "明 (めい) - bright/clear", "明 (あきら) - bright", "明 (みん) - clear"]
        correct_answer = options[1]
        explanation = "The kanji 明 has the reading めい (mei) meaning 'bright' or 'clear', as in 明るい (akarui - bright)."
    elif session.mode == "jlpt":
        options = ["私は毎日朝ご飯を食べます。", "私は毎日朝ご飯を食べる。", "私は毎日朝ご飯を食べました。", "私は毎日朝ご飯を食べたい。"]
        correct_answer = options[0]
        explanation = "This sentence uses the correct present habitual form for JLPT N4/N5 level."
    elif session.mode == "grammar":
        options = ["を", "に", "が", "は"]
        correct_answer = options[2]
        explanation = "The particle が is used to mark the subject of the sentence. 本が読みます。→ 'As for books, [I] read them.'"
    else:  # conversation
        options = ["すみません、手伝っていただけますか？", "手伝ってください", "助けて", "どうぞ"]
        correct_answer = options[0]
        explanation = "すみません、手伝っていただけますか？ is the polite way to ask for help in a store or public situation."

    study_data = {
        "session_id": session_id,
        "mode": session.mode,
        "jlpt_level": session.jlpt_level,
        "question": question,
        "options": options if session.mode in ["vocabulary", "kanji", "jlpt"] else None,
        "correct_answer": correct_answer,
        "explanation": explanation
    }

    study_sessions[session_id] = study_data
    return study_data

# Answer study session
@app.post("/study/{session_id}/answer")
async def answer_study_session(session_id: str, answer: str):
    if session_id not in study_sessions:
        raise HTTPException(status_code=404, detail="Study session not found")

    session = study_sessions[session_id]
    is_correct = answer.strip().lower() == session["correct_answer"].strip().lower()

    result = {
        "correct": is_correct,
        "correct_answer": session["correct_answer"],
        "explanation": session["explanation"]
    }

    return result

# Conversation models
class ConversationCreate(BaseModel):
    title: Optional[str] = None
    jlpt_level: Optional[str] = None
    scenario: Optional[str] = None

class ConversationResponse(BaseModel):
    id: str
    title: str
    jlpt_level: str
    scenario: Optional[str] = None
    created_at: str

# Create conversation
@app.post("/conversations")
async def create_conversation(conversation: ConversationCreate):
    conversation_id = str(uuid.uuid4())
    now = "2026-08-17T00:00:00Z"  # Simplified timestamp

    data = {
        "id": conversation_id,
        "title": conversation.title or "Japanese Conversation",
        "jlpt_level": conversation.jlpt_level or "N4",
        "scenario": conversation.scenario,
        "created_at": now
    }

    conversations[conversation_id] = data
    return data

# Get conversations
@app.get("/conversations")
async def get_conversations():
    return list(conversations.values())

# Get conversation
@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversations[conversation_id]

# Chat message model
class ChatMessage(BaseModel):
    conversation_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

# Send chat message
@app.post("/chat")
async def send_chat_message(chat: ChatMessage):
    if chat.conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[chat.conversation_id]
    # Sanitize user input to prevent XSS
    user_message = sanitize_input(chat.message)

    # Build conversation history for context
    # For now, we'll use a simple approach - in a real app, you'd store message history
    conversation_history = ""  # Would be populated from stored messages

    # Create tutoring-specific system prompt based on JLPT level
    jlpt_level = conversation.get("jlpt_level", "N4")
    system_prompt = f"""You are a helpful Japanese language tutor. The student's current JLPT level is {jlpt_level}.
    Provide helpful, encouraging responses to help them learn Japanese.
    If they make mistakes, gently correct them with explanations.
    If they ask about grammar, vocabulary, or culture, provide clear, accurate information.
    Keep your responses appropriate for their level ({jlpt_level}).
    """

    # Add context from uploaded files if available
    file_context = ""
    # In a real implementation, you would check for uploaded files related to this conversation

    # Combine user message with any context
    full_prompt = user_message
    if file_context:
        full_prompt = f"Context from uploaded materials:\n{file_context}\n\nStudent message: {user_message}"

    # Get response from Ollama
    bot_response = call_ollama(full_prompt, system_prompt)

    return {"response": bot_response}

# File upload models
class FileUpload(BaseModel):
    conversation_id: str
    filename: str
    file_type: str
    content: str

class FileResponse(BaseModel):
    id: str
    conversation_id: str
    filename: str
    file_type: str
    uploaded_at: str

# Upload file
@app.post("/conversations/{conversation_id}/upload")
async def upload_file(conversation_id: str, filename: str, file_type: str, content: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    file_id = str(uuid.uuid4())
    now = "2026-08-17T00:00:00Z"

    file_data = {
        "id": file_id,
        "conversation_id": conversation_id,
        "filename": filename,
        "file_type": file_type,
        "content": content,
        "uploaded_at": now
    }

    files[file_id] = file_data
    return file_data

# Get conversation files
@app.get("/conversations/{conversation_id}/files")
async def get_conversation_files(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv_files = [f for f in files.values() if f["conversation_id"] == conversation_id]
    return conv_files

# Delete file
@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    if file_id not in files:
        raise HTTPException(status_code=404, detail="File not found")

    del files[file_id]
    return {"message": "File deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)