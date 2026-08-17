import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8080",
});

export const getStudyModes = async () => {
  const response = await api.get("/study/modes");
  return response.data;
};

export const createStudySession = async (
  mode,
  jlptLevel
) => {
  const response = await api.post("/study", {
    mode,
    jlpt_level: jlptLevel,
  });

  return response.data;
};

export const answerStudySession = async (
  sessionId,
  answer
) => {
  const response = await api.post(
    `/study/${sessionId}/answer`,
    null,
    {
      params: {
        answer,
      },
    }
  );

  return response.data;
};

// ============================================================
// CHAT ENDPOINTS
// ============================================================

export const createConversation = async (title, jlptLevel, scenario) => {
  const response = await api.post("/conversations", {
    title: title || "Japanese Conversation",
    jlpt_level: jlptLevel || "N4",
    scenario: scenario || null,
  });
  return response.data;
};

export const getConversations = async () => {
  const response = await api.get("/conversations");
  return response.data;
};

export const getConversation = async (conversationId) => {
  const response = await api.get(`/conversations/${conversationId}`);
  return response.data;
};

export const sendChatMessage = async (conversationId, message) => {
  const response = await api.post("/chat", {
    conversation_id: conversationId,
    message,
  });
  return response.data;
};

// ============================================================
// FILE UPLOAD ENDPOINTS
// ============================================================

export const uploadFile = async (
  conversationId,
  filename,
  fileType,
  content
) => {
  const response = await api.post(
    `/conversations/${conversationId}/upload`,
    null,
    {
      params: {
        filename,
        file_type: fileType,
        content,
      },
    }
  );
  return response.data;
};

export const getConversationFiles = async (conversationId) => {
  const response = await api.get(`/conversations/${conversationId}/files`);
  return response.data;
};

export const deleteFile = async (fileId) => {
  const response = await api.delete(`/files/${fileId}`);
  return response.data;
};

export default api;