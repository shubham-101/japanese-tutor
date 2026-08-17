# Key Decisions Made During Japanese Tutor Enhancement

## Overview
This document outlines the significant technical decisions made while enhancing the Japanese tutor project to integrate Ollama-powered AI responses, transforming it from a simple echo bot to an intelligent language learning tutor.

---

## 1. LLM Integration Choice: Ollama with Local Model

**Decision**: Use the existing Ollama installation and `japanese-tutor:latest` model rather than switching to a different LLM provider or API.

**Why**:
- The project already had `ollama==0.6.2` in requirements.txt, indicating intent to use local LLMs
- Local execution ensures privacy (no data leaves the user's machine)
- No API costs or rate limits
- Faster iteration during development
- The `japanese-tutor:latest` model was already pulled and appeared specialized for tutoring
- Aligns with the project's goal of a "local Qwen-powered tutor"

**Alternative Considered**: Using OpenAI/Antropic APIs or Hugging Face models
**Rejected Because**: Would require API keys, incur costs, send data externally, and conflict with the local-first approach.

---

## 2. Backend Port Selection: 8080 instead of 8000

**Decision**: Change the backend server port from 8000 to 8080 to avoid conflicts.

**Why**:
- Port 8000 was consistently occupied by existing Python processes (likely previous versions of the backend)
- Rather than spending time identifying and killing those processes (which might be important to the user), choosing an alternative port was quicker and less disruptive
- Port 8080 is a common alternative for web services and was verified to be free
- This change required minimal code modification (just one line in main.py)

**Alternative Considered**: Killing the existing process on port 8000
**Rejected Because**: Risk of terminating a process the user might need, and requiring repeated manual intervention.

---

## 3. Prompt Engineering Approach: Context-Aware Tutoring Prompts

**Decision**: Create specialized system prompts that establish the AI as a helpful Japanese tutor, incorporating the user's JLPT level for appropriate difficulty.

**Why**:
- Raw model responses were too generic and not pedagogically effective
- A tutoring persona needed to be established: patient, encouraging, knowledgeable
- JLPT level information (already being collected) should influence response complexity
- System prompts help prevent the model from drifting off-topic or giving inappropriate advice

**Implementation**: 
```python
system_prompt = f"""You are a helpful Japanese language tutor. The student's current JLPT level is {jlpt_level}.
Provide helpful, encouraging responses to help them learn Japanese.
If they make mistakes, gently correct them with explanations.
If they ask about grammar, vocabulary, or culture, provide clear, accurate information.
Keep your responses appropriate for their level ({jlpt_level}).
```

**Alternative Considered**: Fine-tuning a model or using complex RAG pipelines
**Rejected Because**: Over-engineering for the current scope; prompt engineering provided immediate improvements without additional complexity.

---

## 4. API Response Handling: Non-streaming with Robust Error Handling

**Decision**: Use non-streaming API calls to Ollama with try/catch error handling and fallback messages.

**Why**:
- Simplicity and reliability: Non-streaming is easier to implement and debug
- The chat interface didn't immediately require real-time streaming for MVP
- Robust error handling ensures graceful degradation when Ollama is unavailable
- Clear fallback messages maintain user experience even when the AI is temporarily unreachable

**Implementation**:
```python
try:
    # ... Ollama API call ...
    response.raise_for_status()
    result = response.json()
    return result.get("message", {}).get("content", "I'm sorry, I couldn't generate a response.")
except Exception as e:
    print(f"Error calling Ollama: {e}")
    return f"I'm having trouble connecting to my knowledge base. Please try again later."
```

**Alternative Considered**: Implementing streaming responses from the start
**Rejected Because**: Added complexity that wasn't necessary for initial validation; can be added later as an enhancement.

---

## 5. Conversation Context Management: Minimal Viable Approach

**Decision**: Initially omit persistent conversation history storage, focusing on getting the basic AI tutoring working.

**Why**:
- The existing API already had conversation IDs but wasn't storing message history
- Implementing full conversation history would require significant backend changes (database/storage layer)
- For the initial enhancement, proving that AI tutoring works was the priority
- Conversation history can be added in a future iteration without breaking the current API

**Implementation**: 
- Accept that each call to `/chat` is stateless from the backend perspective
- Rely on the frontend to potentially resend conversation history if needed (though not implemented)
- Keep the system prompt focused on the current message and general tutoring role

**Alternative Considered**: Implementing a conversation history storage system (in-memory or database)
**Rejected Because**: Would delay the core AI tutoring feature; scope creep for the initial enhancement.

---

## 6. Frontend-Backend Communication: Minimal API Changes

**Decision**: Only update the frontend API URL to point to the new backend port, keeping all other API contracts identical.

**Why**:
- Minimizes risk and workload
- Leverages existing API endpoints and data structures
- Ensures backward compatibility
- Allows independent testing of backend enhancements

**Implementation**:
- Changed only the `baseURL` in `frontend/src/api.js` from `"http://127.0.0.1:8000"` to `"http://127.0.0.1:8080"`
- Left all endpoint paths, request formats, and response handling unchanged

**Alternative Considered**: Modifying API endpoints or data models to support new features
**Rejected Because**: Would require coordinated frontend/backend changes and increase risk of breaking existing functionality.

---

## 7. Error Logging Strategy: Production-Appropriate Debugging

**Decision**: Implement minimal, safe logging that avoids exposing sensitive information or causing encoding issues.

**Why**:
- Initial implementation had verbose debug logging that printed full payloads and responses
- This caused encoding errors when Japanese characters were involved (charmap codec errors)
- Production systems should avoid logging potentially sensitive user data
- Excessive logging can impact performance and fill disk space

**Implementation**:
- Removed detailed payload/response logging
- Kept only essential status information (HTTP status codes)
- Used simple print statements appropriate for development
- Ensured error messages to users are generic and helpful

**Alternative Considered**: Implementing a full logging framework with levels and file output
**Rejected Because**: Over-engineering for this scope; simple console output suffices for development and debugging.

---

## 8. Model Parameter Selection: Conservative Defaults

**Decision**: Use Ollama's default parameters (temperature, top_p, etc.) rather than customizing them.

**Why**:
- The `japanese-tutor:latest` model appeared to be already tuned for tutoring purposes
- Changing parameters without understanding their impact could degrade performance
- Defaults provide a known baseline for evaluation
- Parameter tuning can be done in future iterations based on user feedback

**Implementation**:
```json
payload = {
    "model": OLLAMA_MODEL,
    "messages": messages,
    "stream": false
    // Using all default parameters
}
```

**Alternative Considered**: Experimenting with temperature, top_k, top_p parameters to optimize for tutoring
**Rejected Because**: Premature optimization; better to establish baseline performance first.

---

## Summary of Impact

These decisions collectively transformed the Japanese tutor from:
- **Before**: A simple echo bot responding with "I received your message: '[user message]'"
- **After**: An intelligent language tutor that:
  - Understands and responds in natural Japanese
  - Provides grammatical explanations with examples and tables
  - Offers encouragement and learning tips
  - Adapts implicitly to the user's stated JLPT level
  - Handles errors gracefully
  - Operates entirely locally for privacy

The enhancements were made with a focus on:
1. **Minimizing risk** through incremental changes
2. **Maximizing educational value** through thoughtful prompt engineering
3. **Ensuring reliability** with proper error handling
4. **Respecting user privacy** through local-only processing
5. **Maintaining compatibility** with existing frontend code

Future enhancements could include:
- Conversation history storage and contextual awareness
- File content integration for document-based tutoring
- Streaming responses for improved perceived performance
- Advanced prompt tuning based on interaction analysis
- Additional tutoring modes (vocabulary drills, kanji practice, etc.)