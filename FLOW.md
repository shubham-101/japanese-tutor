# System Flow Documentation: Enhanced Japanese Tutor

This document describes the data and control flow throughout the enhanced Japanese tutor system, from user interaction to AI response generation.

## Overview

The system follows a client-server architecture where:
- **Frontend**: React/Vite application handling user interface
- **Backend**: FastAPI server processing requests and interfacing with Ollama
- **Ollama**: Local LLM service generating intelligent responses
- **Storage**: In-memory dictionaries for sessions, conversations, and files

---

## 1. User Interaction Flow

### 1.1 Starting the Application
```
User opens browser → Frontend loads (http://localhost:5173) → 
Frontend makes initial API calls → Backend responds with study modes → 
UI displays options → User selects study mode and JLPT level
```

### 1.2 Chat Flow (Primary Enhancement)
```
1. User types message in chat interface
2. Frontend sends POST request to /chat endpoint:
   - Conversation ID (from session/storage)
   - User message text
3. Backend receives request at /chat endpoint
4. Backend validates conversation exists
5. Backend constructs tutoring system prompt (using JLPT level from conversation)
6. Backend calls Ollama API with user message + system prompt
7. Ollama processes request using japanese-tutor:latest model
8. Ollama generates contextual, educational response
9. Backend receives Ollama response
10. Backend extracts response content and returns to frontend
11. Frontend displays assistant message in chat interface
12. User sees AI tutor response and can continue conversation
```

### 1.3 File Upload Flow
```
1. User selects file to upload
2. Frontend reads file as text
3. Frontend sends POST to /conversations/{id}/upload:
   - Conversation ID
   - Filename
   - File type
   - File content (text)
4. Backend validates conversation exists
5. Backend stores file in memory with metadata
6. Backend returns file object with ID
7. Frontend updates uploaded files display
8. (Future) File content can be incorporated into chat context
```

### 1.4 Study Session Flow
```
1. User selects study mode and JLPT level from menu
2. Frontend sends POST to /study:
   - Mode (conversation, grammar, vocabulary, kanji, jlpt)
   - JLPT level
3. Backend generates sample question based on mode/level
4. Backend creates study session record with:
   - Session ID
   - Question
   - Options (if applicable)
   - Correct answer
   - Explanation
5. Backend returns session data
6. Frontend displays question and answer interface
7. User submits answer
8. Frontend sends POST to /study/{session_id}/answer:
   - Session ID
   - User answer
9. Backend validates session exists
10. Backend checks answer correctness
11. Backend returns result (correct/incorrect + explanation)
12. Frontend displays feedback and next question button
```

---

## 2. Backend Processing Flow

### 2.1 Request Handling Flow
```
HTTP Request arrives → 
FastAPI routes to appropriate endpoint → 
Endpoint validates request data and authentication → 
Endpoint performs business logic → 
Endpoint returns JSON response → 
FastAPI converts to HTTP response → 
Client receives response
```

### 2.2 Chat Endpoint Detailed Flow
```
POST /chat
├── 1. Extract conversation_id and message from request body
├── 2. Validate conversation exists in memory store
│   └── If not found: return 404 error
├── 3. Retrieve conversation details (specifically jlpt_level)
├── 4. Construct tutoring system prompt:
│   ├── Base: "You are a helpful Japanese language tutor..."
│   ├── Level-specific: "Keep responses appropriate for N4 level"
│   ├── Instruction: "Gently correct mistakes with explanations"
│   └── Format: Encouraging, supportive tone
├── 5. Prepare Ollama API payload:
│   ├── Model: japanese-tutor:latest
│   ├── Messages: [system prompt, user message]
│   ├── Stream: false (non-sequential response)
│   └── Use default parameters
├── 6. Make HTTP POST to Ollama API (/api/chat)
├── 7. Wait for Ollama response (with timeout)
├── 8. Parse Ollama JSON response:
│   ├── Extract message.content from response
│   ├── Handle missing content with fallback
│   └── Log any errors for debugging
├── 9. Return structured response to frontend:
│   ├── {"response": "AI generated text"}
│   └── Include appropriate HTTP status
└── 10. Handle exceptions gracefully:
    ├── Network errors → fallback message
    ├── Timeout errors → fallback message  
    └── Ollama unavailable → fallback message
```

### 2.3 Ollama Interaction Flow
```
Backend prepares request → 
HTTP POST to http://localhost:11434/api/chat →
Ollama service receives request →
Ollama loads japanese-tutor:latest model (if not in memory) →
Ollama processes prompt with system and user messages →
Ollama generates token-by-token response →
Ollama assembles complete response →
Ollama returns JSON with:
{
  "model": "japanese-tutor:latest",
  "created_at": "timestamp",
  "message": {
    "role": "assistant",
    "content": "Generated response text"
  },
  "done": true
} →
Backend extracts content →
Backend returns to frontend
```

---

## 3. Data Flow and Storage

### 3.1 In-Memory Storage Structures
```
study_sessions: {
  session_id: {
    session_id: string,
    mode: string,
    jlpt_level: string,
    question: string,
    options: [string] | null,
    correct_answer: string | null,
    explanation: string | null
  }
}

conversations: {
  conversation_id: {
    id: string,
    title: string,
    jlpt_level: string,
    scenario: string | null,
    created_at: string
  }
}

files: {
  file_id: {
    id: string,
    conversation_id: string,
    filename: string,
    file_type: string,
    content: string,
    uploaded_at: string
  }
}
```

### 3.2 Data Lifecycle
```
Creation:
├── Conversation created via POST /conversations
│   → Generated UUID + timestamp stored
│   → Returned to frontend for session storage
│
├── Study session created via POST /study  
│   → Generated UUID + question data
│   → Returned to frontend
│
└── File uploaded via POST /conversations/{id}/upload
    → Generated UUID + file metadata
    → Associated with conversation ID
    → Returned to frontend

Usage:
├── Conversations retrieved via GET /conversations/{id}
│   → Used to validate chat requests
│   → Used to get JLPT level for prompting
│
├── Files retrieved via GET /conversations/{id}/files
│   → Displayed in UI for reference
│   → (Future) Used to enhance chat context
│
└ study sessions used via GET/POST /study/{id}
   → Validate session exists
   → Check answer correctness
   → Return feedback

Cleanup:
├── Currently: Data persists for application lifetime
├── No automatic cleanup implemented
└── (Future) Could implement TTL or explicit delete endpoints
```

---

## 4. Error Handling Flow

### 4.1 Backend Error Handling
```
Request processing error occurs →
├── Validation errors (missing data, invalid IDs):
│   → Return 400/404 with descriptive message
│
├── Business logic errors:
│   → Return 500 with generic message (for security)
│   → Log detailed error server-side
│
├── External service errors (Ollama):
│   → Catch exception
│   → Return user-friendly fallback message
│   → Log technical details for debugging
│
└── Unexpected errors:
   → Catch all exceptions
   → Return generic error message
   → Log full traceback
```

### 4.2 Specific Chat Error Cases
```
1. Invalid conversation ID:
   Request → Validate conversation exists → Not found → 
   Return: {"detail": "Conversation not found"} (404)
   
2. Ollama service unavailable:
   Request → Prepare payload → Call Ollama → 
   Connection refused/timeout → Catch exception →
   Return: {"response": "I'm having trouble connecting to my knowledge base. Please try again later."}
   
3. Ollama returns error:
   Request → Call Ollama → HTTP error status → 
   Raise for status → Catch HTTPError →
   Return: Fallback message with technical details logged
   
4. Malformed Ollama response:
   Request → Call Ollama → Get response → 
   Missing expected fields → Use defaults with logging →
   Return: Available content or fallback
```

---

## 5. Performance and Scaling Considerations

### 5.1 Current Limitations (In-Memory Storage)
```
- All data lost when backend restarts
- No persistence across sessions
- Memory usage grows with active conversations/files
- No concurrent user limits implemented
- Suitable for single-user/local development
```

### 5.2 Future Scaling Improvements
```
Database Storage:
├── Replace in-memory dicts with persistent database
├── PostgreSQL or SQLite for simplicity
├── Enable multi-user support
├── Add data persistence across restarts

Caching Layer:
├── Redis for conversation history caching
├── Ollama response caching for repeated queries
├── Session storage optimization

Horizontal Scaling:
├── Stateless backend design (mostly achieved)
├── Load balancing capable
├── Shared database/session store needed
```

### 5.3 Current Performance Characteristics
```
Request Latency:
├── Local network: <5ms overhead
├── Ollama processing: 1-5 seconds (model dependent)
├── Total response time: ~1-6 seconds typically
├── Acceptable for tutoring use case

Memory Usage:
├── Minimal per conversation (~KB)
├── File storage scales with upload size
├── Model loaded in Ollama process separately
├── Backend process: ~50-100MB typical
```

---

## 6. Security Considerations

### 6.1 Implemented Security Features
```
CORS Configuration:
├── Restricted to localhost:5173 (frontend dev server)
├── Prevents unauthorized cross-origin requests
├── Can be expanded for production domains

Input Validation:
├── Pydantic models validate request structures
├── Type safety for all API endpoints
├── Automatic FastAPI validation & error responses

Error Message Sanitization:
├── Internal errors don't expose stack traces to users
├── Technical details logged server-side only
├── User-friendly fallback messages prevent info leakage
```

### 6.2 Future Security Enhancements
```
Authentication:
├── Add user login/session management
├── Protect endpoints with JWT or session cookies
├── Enable personalized learning paths

Rate Limiting:
├── Prevent abuse of Ollama API
├── Protect against excessive resource consumption
├── Implement per-user or IP-based limits

Input Sanitization:
├── Additional validation beyond Pydantic
├── HTML/script injection prevention
├── File type and size restrictions for uploads
```

---

## 7. Extension Points for Future Development

### 7.1 Conversation Context Enhancement
```
Current: Stateless prompting
Future: 
├── Store message history per conversation
├── Inject last N messages into Ollama context
├── Summarize old conversations to stay within token limits
├── Reference uploaded files in system prompt when relevant
├── Track learning objectives and adapt tutoring style
```

### 7.2 Advanced Tutoring Features
```
Current: General helpful tutoring
Future:
├── Error detection and correction mode
├── Vocabulary/kanji quiz generation
├── Pronunciation feedback (with audio integration)
├── Cultural notes expansion
├── Progress tracking and spaced repetition
├── Homework assignment generation
```

### 7.3 Infrastructure Improvements
```
Current: Simple in-memory, single port
Future:
├── Docker containerization
├── Environment-based configuration (dev/prod)
├── Health check endpoints
├── Structured logging (JSON format)
├── Metrics collection (response times, error rates)
├── Automated testing suite
```

---

## 8. Summary

The enhanced Japanese tutor implements a clean, modular flow that:
1. **Separates concerns** between frontend UI and backend logic
2. **Leverages existing Ollama investment** for AI capabilities
3. **Maintains backward compatibility** with minimal frontend changes
4. **Provides intelligent, educational responses** through prompt engineering
5. **Handles errors gracefully** to maintain user experience
6. **Operates completely locally** for privacy and cost-effectiveness
7. **Scales reasonably** for personal/small group use

The system flow demonstrates thoughtful engineering trade-offs favoring:
- Rapid delivery of core value (AI tutoring)
- Reliability over premature optimization
- Simplicity for maintainability
- User experience through clear error handling

This foundation enables straightforward extension to more advanced features while maintaining a solid, working baseline.