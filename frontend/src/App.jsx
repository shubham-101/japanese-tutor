import { useState } from "react";
import {
  createStudySession,
  answerStudySession,
  createConversation,
  getConversation,
  sendChatMessage,
  uploadFile,
  getConversationFiles,
  deleteFile,
} from "./api";

function App() {
  const [screen, setScreen] = useState("home");

  const [mode, setMode] = useState("grammar");
  const [jlptLevel, setJlptLevel] = useState("N4");

  const [session, setSession] = useState(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [questionCount, setQuestionCount] = useState(0);

  // Chat state
  const [conversationId, setConversationId] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatJlptLevel, setChatJlptLevel] = useState("N4");
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const startStudy = async () => {
    setLoading(true);
    setResult(null);
    setAnswer("");
    setError(null);
    setSuccess(null);

    try {
      const data = await createStudySession(
        mode,
        jlptLevel
      );

      if (!data || !data.session_id) {
        throw new Error("Invalid session data received");
      }

      setSession(data);
      setQuestionCount(questionCount + 1);
      setScreen("study");
    } catch (err) {
      console.error(err);
      const errorMsg = err.message || "Could not start study session.";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!answer.trim()) {
      setError("Please provide an answer before submitting.");
      return;
    }

    if (!session || !session.session_id) {
      setError("Session expired. Please start a new study session.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const data = await answerStudySession(
        session.session_id,
        answer
      );

      if (!data) {
        throw new Error("Invalid response from server");
      }

      setResult(data);
      if (data.correct) {
        setSuccess("Great job! That's correct!");
      }
    } catch (err) {
      console.error(err);
      const errorMsg = err.message || "Could not submit answer. Please try again.";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const startNewQuestion = async () => {
    if (loading) return;
    setResult(null);
    setAnswer("");
    setError(null);
    await startStudy();
  };

  const startChat = async (level) => {
    setLoading(true);
    setChatJlptLevel(level);
    setChatMessages([]);
    setUploadedFiles([]);
    setError(null);

    try {
      const data = await createConversation(
        "Japanese Conversation",
        level,
        null
      );

      if (!data || !data.id) {
        throw new Error("Failed to create conversation");
      }

      setConversationId(data.id);
      setScreen("chat");

      // Fetch existing files for this conversation
      try {
        const files = await getConversationFiles(data.id);
        setUploadedFiles(files);
      } catch (err) {
        console.log("No files yet or error fetching files");
      }
    } catch (err) {
      console.error(err);
      setError(err.message || "Could not start chat.");
    } finally {
      setLoading(false);
    }
  };

  const sendChatMessageHandler = async (message) => {
    if (!message.trim()) {
      setError("Please enter a message.");
      return;
    }

    if (!conversationId) {
      setError("Chat session expired. Please start a new chat.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Add user message to UI immediately
      setChatMessages([
        ...chatMessages,
        { role: "user", content: message },
      ]);

      // Send to API
      const data = await sendChatMessage(conversationId, message);

      if (!data || !data.response) {
        throw new Error("Invalid response from server");
      }

      // Add assistant response
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response },
      ]);
    } catch (err) {
      console.error(err);
      const errorMsg =
        err.message || "Could not send message. Please try again.";
      setError(errorMsg);
      // Remove the user message if it failed
      setChatMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    if (!conversationId) {
      setError("Chat session expired. Please start a new chat.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const text = await file.text();

      const data = await uploadFile(
        conversationId,
        file.name,
        file.type || "text/plain",
        text
      );

      if (!data || !data.id) {
        throw new Error("Failed to upload file");
      }

      // Add to uploaded files list
      setUploadedFiles([...uploadedFiles, data]);
      setError(null);
    } catch (err) {
      console.error(err);
      setError(err.message || "Could not upload file. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFile = async (fileId) => {
    setLoading(true);
    setError(null);

    try {
      await deleteFile(fileId);
      setUploadedFiles(uploadedFiles.filter((f) => f.id !== fileId));
    } catch (err) {
      console.error(err);
      setError(err.message || "Could not delete file. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">

      <header className="header">
        <div className="logo">
          日本語 Tutor
        </div>

        <nav>
          <button
            onClick={() => setScreen("home")}
            className={screen === "home" ? "active" : ""}
          >
            Home
          </button>

          <button
            onClick={() => setScreen("study-menu")}
            className={screen === "study-menu" ? "active" : ""}
          >
            Study
          </button>

          <button
            onClick={() => setScreen("chat-menu")}
            className={screen === "chat-menu" ? "active" : ""}
          >
            Chat
          </button>
        </nav>
      </header>

      <main>

        {screen === "home" && (
          <Home
            onStudy={() =>
              setScreen("study-menu")
            }
          />
        )}

        {screen === "study-menu" && (
          <StudyMenu
            mode={mode}
            setMode={setMode}
            jlptLevel={jlptLevel}
            setJlptLevel={setJlptLevel}
            onStart={startStudy}
            loading={loading}
          />
        )}

        {screen === "study" && session && (
          <StudyScreen
            session={session}
            answer={answer}
            setAnswer={setAnswer}
            result={result}
            onSubmit={submitAnswer}
            onNext={startNewQuestion}
            loading={loading}
            error={error}
            setError={setError}
          />
        )}

        {screen === "chat-menu" && (
          <ChatMenu
            onStartChat={startChat}
            loading={loading}
            error={error}
            setError={setError}
          />
        )}

        {screen === "chat" && conversationId && (
          <ChatScreen
            conversationId={conversationId}
            messages={chatMessages}
            onSendMessage={sendChatMessageHandler}
            loading={loading}
            error={error}
            setError={setError}
            jlptLevel={chatJlptLevel}
            uploadedFiles={uploadedFiles}
            onFileUpload={handleFileUpload}
            onDeleteFile={handleDeleteFile}
          />
        )}

        {error && screen === "study-menu" && (
          <div className="error-banner">
            <p>{error}</p>
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}

      </main>

    </div>
  );
}


function Home({ onStudy }) {
  return (
    <section className="home">

      <div className="hero">

        <div>
          <p className="eyebrow">
            JAPANESE LANGUAGE TUTOR
          </p>

          <h1>
            Learn Japanese
            <br />
            through conversation.
          </h1>

          <p className="subtitle">
            Practice Japanese with your local
            Qwen-powered tutor.
          </p>

          <button
            className="primary"
            onClick={onStudy}
          >
            Start Learning
          </button>
        </div>

        <div className="hero-japanese">
          日本語
        </div>

      </div>

    </section>
  );
}


function StudyMenu({
  mode,
  setMode,
  jlptLevel,
  setJlptLevel,
  onStart,
  loading,
  error,
  setError,
}) {
  const modes = [
    {
      id: "conversation",
      title: "Conversation",
      description:
        "Practice natural Japanese conversation.",
    },
    {
      id: "grammar",
      title: "Grammar",
      description:
        "Practice Japanese grammar.",
    },
    {
      id: "vocabulary",
      title: "Vocabulary",
      description:
        "Build your Japanese vocabulary.",
    },
    {
      id: "kanji",
      title: "Kanji",
      description:
        "Practice kanji readings and meanings.",
    },
    {
      id: "jlpt",
      title: "JLPT",
      description:
        "Practice JLPT-style questions.",
    },
  ];

  return (
    <section className="study-menu">

      <h1>What do you want to study?</h1>
      
      <p className="section-subtitle">
        Choose a study mode and JLPT level to begin your practice session.
      </p>

      {error && (
        <div className="inline-error-alert">
          <span className="error-icon-inline">⚠️</span>
          <span>{error}</span>
          <button 
            className="close-inline"
            onClick={() => setError(null)}
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      )}

      <div className="level-selector">

        <span>JLPT Level</span>

        {["N5", "N4", "N3", "N2", "N1"].map(
          (level) => (
            <button
              key={level}
              className={
                jlptLevel === level
                  ? "selected"
                  : ""
              }
              onClick={() => {
                setJlptLevel(level);
                setError(null);
              }}
              title={`Select ${level} level`}
            >
              {level}
            </button>
          )
        )}

      </div>

      <div className="mode-grid">

        {modes.map((item) => (
          <button
            key={item.id}
            className={
              mode === item.id
                ? "mode-card selected"
                : "mode-card"
            }
            onClick={() =>
              setMode(item.id)
            }
          >
            <h3>{item.title}</h3>

            <p>
              {item.description}
            </p>
          </button>
        ))}

      </div>

      <button
        className="primary start-button"
        onClick={onStart}
        disabled={loading}
      >
        {loading
          ? "Starting..."
          : "Start Practice"}
      </button>

    </section>
  );
}


function StudyScreen({
  session,
  answer,
  setAnswer,
  result,
  onSubmit,
  onNext,
  loading,
  error,
  success,
  setError,
  questionCount,
}) {
  return (
    <section className="study-screen">

      <div className="study-header">
        <div className="header-left">
          <span className="mode-badge">{session?.mode || "Study Mode"}</span>
          <span className="level-badge">{session?.jlpt_level || "N4"}</span>
        </div>
        <div className="header-right">
          <span className="question-count">Question #{questionCount}</span>
        </div>
      </div>

      {success && (
        <div className="success-banner">
          <span className="success-icon">✓</span>
          <span>{success}</span>
        </div>
      )}

      <div className="question-card">

        <p className="question-label">
          QUESTION
        </p>

        <h2>
          {session?.question || "No question loaded"}
        </h2>

        {error && (
          <div className="error-message">
            <span className="error-icon-inline">⚠️</span>
            <p>{error}</p>
          </div>
        )}

        {Array.isArray(session?.options) &&
          session.options.length > 0 && (
            <div className="options">
              <p className="options-label">Select the correct answer:</p>
              {session.options.map((option, idx) => (
                <button
                  key={option}
                  className={
                    answer === option
                      ? "option selected"
                      : "option"
                  }
                  onClick={() => {
                    setAnswer(option);
                    setError(null);
                  }}
                  disabled={!!result}
                  title={`Option ${String.fromCharCode(65 + idx)}`}
                  aria-label={`Option ${String.fromCharCode(65 + idx)}: ${option}`}
                >
                  <span className="option-letter">{String.fromCharCode(65 + idx)}</span>
                  {option}
                </button>
              ))}
            </div>
          )}

        {(!Array.isArray(session?.options) ||
          session.options.length === 0) && (
          <div className="input-group">
            <label htmlFor="answer-input" className="input-label">
              Type your answer:
            </label>
            <input
              id="answer-input"
              className="answer-input"
              value={answer}
              onChange={(e) => {
                setAnswer(e.target.value);
                setError(null);
              }}
              placeholder="Enter your answer here..."
              disabled={!!result}
              autoFocus
              aria-label="Answer input"
            />
          </div>
        )}

        {!result && (
          <button
            className="primary"
            onClick={onSubmit}
            disabled={
              loading || !answer.trim()
            }
            title="Submit your answer for evaluation"
          >
            {loading
              ? "Checking..."
              : "Check Answer"}
          </button>
        )}

        {result && (
          <div
            className={
              result.correct
                ? "result correct"
                : "result incorrect"
            }
          >
            <div className="result-header">
              <span className="result-icon">
                {result.correct ? "✓" : "✕"}
              </span>
              <h3>
                {result.correct
                  ? "Correct!"
                  : "Not quite right"}
              </h3>
            </div>

            <div className="result-body">
              <p className="answer-label">
                Correct answer:
              </p>
              <p className="correct-answer">
                {result?.correct_answer || "N/A"}
              </p>

              <p className="explanation-label">
                Explanation:
              </p>
              <p className="explanation">
                {result?.explanation || "No explanation available"}
              </p>
            </div>

            <button
              className="primary"
              onClick={onNext}
              title="Load next question"
            >
              {loading ? "Loading..." : "Next Question"}
            </button>
          </div>
        )}

      </div>

    </section>
  );
}


function ChatMenu({ onStartChat, loading, error, setError }) {
  return (
    <section className="chat-menu">
      <h1>Chat with Tutor</h1>

      <p className="section-subtitle">
        Have a free-form conversation with your AI tutor. Your chat history is saved.
      </p>

      {error && (
        <div className="inline-error-alert">
          <span className="error-icon-inline">⚠️</span>
          <span>{error}</span>
          <button
            className="close-inline"
            onClick={() => setError(null)}
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      )}

      <div className="chat-level-selector">
        <span>Select JLPT Level:</span>
        <div className="button-group">
          {["N5", "N4", "N3", "N2", "N1"].map((level) => (
            <button
              key={level}
              className="level-button"
              onClick={() => onStartChat(level)}
              disabled={loading}
              title={`Start ${level} level chat`}
            >
              {level}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}


function ChatScreen({
  conversationId,
  messages,
  onSendMessage,
  loading,
  error,
  setError,
  jlptLevel,
  uploadedFiles,
  onFileUpload,
  onDeleteFile,
}) {
  const [inputValue, setInputValue] = useState("");
  const fileInputRef = useState(null);

  const handleSendClick = () => {
    onSendMessage(inputValue);
    setInputValue("");
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey && !loading) {
      e.preventDefault();
      handleSendClick();
    }
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileUpload(file);
      e.target.value = "";
    }
  };

  return (
    <section className="chat-screen">
      <div className="chat-header">
        <div className="header-content">
          <h1>Chat with Tutor</h1>
          <span className="chat-level">JLPT {jlptLevel}</span>
        </div>

        <div className="file-upload-area">
          <label htmlFor="file-input" className="file-upload-button" title="Upload a file for context">
            📎 Attach File
          </label>
          <input
            id="file-input"
            type="file"
            onChange={handleFileInputChange}
            disabled={loading}
            accept=".txt,.md,.pdf,.doc,.docx"
            style={{ display: "none" }}
            aria-label="File input"
          />
        </div>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="uploaded-files">
          <div className="files-label">📁 Uploaded Files:</div>
          <div className="files-list">
            {uploadedFiles.map((file) => (
              <div key={file.id} className="file-item">
                <span className="file-name" title={file.filename}>
                  📄 {file.filename}
                </span>
                <button
                  className="file-delete"
                  onClick={() => onDeleteFile(file.id)}
                  disabled={loading}
                  title="Delete file"
                  aria-label={`Delete ${file.filename}`}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          <span className="error-icon-inline">⚠️</span>
          <p>{error}</p>
        </div>
      )}

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <p className="welcome-text">
              👋 Hello! I'm your Japanese tutor. Feel free to ask me anything about Japanese language, culture, or grammar.
              {uploadedFiles.length > 0 && (
                <>
                  <br />
                  <br />
                  📄 I can also reference the files you've uploaded. Ask me questions about them!
                </>
              )}
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`message ${msg.role === "user" ? "user-message" : "assistant-message"}`}
          >
            <div className="message-bubble">
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant-message">
            <div className="message-bubble loading">
              <span className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input-area">
        <textarea
          className="chat-input"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setError(null);
          }}
          onKeyPress={handleKeyPress}
          placeholder="Type your message here... (Shift+Enter for new line)"
          disabled={loading}
          rows="3"
          aria-label="Chat message input"
        />
        <button
          className="primary"
          onClick={handleSendClick}
          disabled={loading || !inputValue.trim()}
          title="Send message"
        >
          {loading ? "Sending..." : "Send"}
        </button>
      </div>
    </section>
  );
}


export default App;