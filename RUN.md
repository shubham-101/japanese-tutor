# How to Run the Enhanced Japanese Tutor Project

This guide provides step-by-step instructions to run the complete Japanese tutor application, including both the frontend and backend components.
uvicorn app.main:app --reload
## 📋 Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.8+** - For the backend server
2. **Node.js 16+** and **npm** - For the frontend React application
3. **Ollama** - For local LLM capabilities (https://ollama.com)
4. **Git** - To clone the repository (if applicable)

## 🔧 Setup Instructions

### 1. Clone or Obtain the Project

If you haven't already obtained the project files:

```bash
# Clone the repository (example)
git clone <repository-url>
cd japanese-tutor
```

Or ensure you have the project directory structure:
```
japanese-tutor/
├── backend/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
└── README.md (original)
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment (recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Start Ollama Service
The backend requires Ollama to be running with a Japanese-capable model:

```bash
# In a separate terminal window/tab:
ollama serve

# Verify it's running (should return JSON with model list)
curl http://localhost:11434/api/tags

# Ensure you have a Japanese model pulled (the japanese-tutor:latest model should already be available)
ollama list
# You should see japanese-tutor:latest and/or qwen3:8b in the list

# If needed, pull a model:
ollama pull japanese-tutor:latest
# or
ollama pull qwen3:8b
```

#### Start the Backend Server
```bash
# Ensure you're still in the backend directory with venv activated
python main.py

# You should see output like:
# INFO:     Started server process [XXXX]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)

# The backend API will be available at: http://localhost:8080
```

### 3. Frontend Setup

#### Install Frontend Dependencies
```bash
# In a new terminal window/tab, navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
```

#### Start the Frontend Development Server
```bash
# Still in the frontend directory
npm run dev

# You should see output like:
#  VITE vX.X.X  ready in XXX ms
#
#  ➜  Local:   http://localhost:5173/
#  ➜  Network: use --host to expose
#  ➜  press h + enter to show help

# The frontend application will be available at: http://localhost:5173
```

## 🧪 Testing the Application

Once both servers are running:

1. **Open your browser** to `http://localhost:5173`
2. **Navigate through the application**:
   - Click "Start Learning" on the home page
   - Select a study mode (e.g., "Conversation") and JLPT level (e.g., "N4")
   - Try the chat feature by clicking the "Chat" menu option
   - Send a message in Japanese like "こんにちは！" to test the AI tutor
   - Try uploading a text file via the chat interface to test file handling
   - Test different study modes to verify question generation

## 🔍 Verification Points

To confirm everything is working correctly:

### Backend API Tests
```bash
# Test study modes endpoint
curl http://localhost:8080/study/modes
# Should return JSON array of study modes

# Test conversation creation
curl -X POST http://localhost:8080/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "jlpt_level": "N4"}'
# Should return conversation object with ID

# Test chat endpoint (requires valid conversation ID from above)
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "<ID_FROM_PREVIOUS_STEP>", "message": "こんにちは"}'
# Should return intelligent Japanese response from Ollama
```

### Frontend Functionality
- UI loads without errors
- Study mode selection works
- Chat interface sends/receives messages
- File upload functionality works
- Error handling displays appropriately

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. "Ollama not running" or connection errors
- **Symptom**: Backend returns "I'm having trouble connecting to my knowledge base"
- **Solution**: 
  ```bash
  # Check if Ollama is running
  ollama list
  # If not running, start it in a separate terminal:
  ollama serve
  ```

#### 2. Port conflicts
- **Symptom**: Error when starting backend: "Address already in use"
- **Solution**:
  ```bash
  # Check what's using port 8080
  netstat -ano | findstr :8080   # Windows
  lsof -i :8080                  # macOS/Linux
  
  # Either kill the process or change backend port in main.py
  # Kill process (Windows example):
  taskkill /PID <process_id> /F
  ```

#### 3. Frontend cannot connect to backend
- **Symptom**: Console shows network errors or API calls fail
- **Solution**:
  - Verify backend is running on `http://localhost:8080`
  - Check that frontend/src/api.js has `baseURL: "http://127.0.0.1:8080"`
  - Check browser console for CORS errors
  - Ensure both are running on localhost (no mixed http/https)

#### 4. Missing dependencies
- **Symptom**: ModuleNotFoundError (Python) or npm ERR! (JavaScript)
- **Solution**:
  ```bash
  # Backend
  pip install -r requirements.txt
  
  # Frontend
  npm install
  ```

#### 5. Slow first response from Ollama
- **Symptom**: First chat message takes 10+ seconds to respond
- **Solution**: This is normal - Ollama loads the model into memory on first request. Subsequent requests will be faster.

## 📝 Production Considerations

For deployment beyond local development:

1. **Backend**:
   - Consider using a process manager like PM2 or systemd
   - Add environment configuration (different ports for dev/prod)
   - Implement proper logging (file-based or to external service)
   - Add health check endpoints
   - Consider using a database instead of in-memory storage

2. **Frontend**:
   - Build for production: `npm run build`
   - Serve built files via static file server (nginx, etc.)
   - Configure proper API URL for production environment

3. **Ollama**:
   - Ensure adequate RAM/VRAM for the model size
   - Consider GPU acceleration if available
   - Set up Ollama as a service that starts on boot

## 🛑 Stopping the Application

To stop the servers:

1. **Backend**: Press `CTRL+C` in the terminal where `python main.py` is running
2. **Frontend**: Press `CTRL+C` in the terminal where `npm run dev` is running  
3. **Ollama**: Press `CTRL+C` in the terminal where `ollama serve` is running
   - Or close the terminal window/tab

## ✅ Summary

When everything is running correctly, you should have:
- **Ollama server**: Running locally on port 11434
- **Backend API**: Running on `http://localhost:8080` 
- **Frontend app**: Running on `http://localhost:5173`
- **Communication**: Frontend ↔ Backend (API calls) ↔ Ollama (LLM queries)

The enhanced Japanese tutor now provides intelligent, context-aware responses through the Ollama integration, transforming it from a simple echo bot to a capable language learning tutor that can explain grammar, provide encouragement, and engage in meaningful Japanese conversations.

Enjoy your Japanese language learning journey! 🇯🇵📚