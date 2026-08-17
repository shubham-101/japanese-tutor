from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str = "Japanese Conversation"
    scenario: str | None = None
    jlpt_level: str = "N4"


class ChatRequest(BaseModel):
    conversation_id: int
    message: str


class ChatResponse(BaseModel):
    conversation_id: int
    response: str

class StudySessionCreate(BaseModel):
    mode: str
    jlpt_level: str = "N4"


class FileUploadResponse(BaseModel):
    id: int
    conversation_id: int
    filename: str
    file_type: str
    created_at: str