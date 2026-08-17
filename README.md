# 🇯🇵 Japanese Tutor

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![Vite](https://img.shields.io/badge/Vite-latest-brightgreen.svg)](https://vitejs.dev/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange.svg)](https://ollama.com/)
[![Security Headers](https://img.shields.io/badge/Security-Headers-red.svg)](https://owasp.org/www-project-secure-headers/)

An intelligent Japanese language learning tutor powered by local LLMs (Ollama) with contextual awareness, security enhancements, and JLPT-level appropriate content.

## ✨ Features

- 🤖 **AI-Powered Conversations**: Context-aware tutoring using Ollama's `japanese-tutor:latest` model
- 📚 **Enhanced Study Mode**: AI-generated questions with explanations for vocabulary, kanji, grammar, conversation, and JLPT practice
- 🔒 **Security-First**: 
  - Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
  - Rate limiting (10 requests/minute/IP)
  - Input sanitization (XSS prevention)
  - Trusted host middleware
  - CORS configuration
- 📁 **File Upload Context**: Upload documents for document-aware tutoring sessions
- 🎯 **JLPT Integration**: Content adapted to JLPT levels N5 through N1
- 💻 **Modern Stack**: FastAPI backend + React/Vite frontend
- 🔄 **Local-First Privacy**: All processing via your local Ollama instance
- 📱 **Responsive Design**: Works on desktop and mobile devices

## 📂 Project Structure

```
japanese-tutor/
├── backend/              # FastAPI server
│   ├── main.py          # API endpoints with Ollama integration
│   └── requirements.txt # Python dependencies
├── frontend/            # React/Vite application
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   ├── pages/       # Page components
│   │   └── api.js       # API service layer
├── data/                # Data storage (in development)
├── tests/               # Test files
├── .gitignore           # Git ignore rules
├── DECISIONS.md         # Technical decisions made during development
├── DESIGN_IMPROVEMENTS.md # UI/UX improvement plans
├── FLOW.md              # System architecture and data flow
├── RUN.md               # Setup and execution instructions
├── TEST_RESULTS.md      # Test results and verification
├── UX_IMPROVEMENTS.md   # User experience enhancement notes
└── README.md            # This file
```

## 🚀 Getting Started

### Prerequisites
- [Python 3.13+](https://www.python.org/downloads/release/python-3130/)
- [Node.js 18+](https://nodejs.org/) (for frontend)
- [Ollama](https://ollama.com/) with `japanese-tutor:latest` model

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/shubham-101/japanese-tutor.git
   cd japanese-tutor
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Ollama Setup**
   ```bash
   # Install Ollama if not already installed
   # Download from: https://ollama.com/download
   
   # Pull the Japanese tutor model
   ollama pull japanese-tutor:latest
   
   # Start Ollama service
   ollama serve
   ```

### Running the Application

1. **Start the Backend** (from backend directory)
   ```bash
   python main.py
   ```
   Server runs on http://localhost:8080

2. **Start the Frontend** (from frontend directory)
   ```bash
   npm run dev
   ```
   Application runs on http://localhost:5173

3. **Access the Application**
   Open your browser to http://localhost:5173

## 🔧 Configuration

### Backend (`backend/main.py`)
- `OLLAMA_BASE_URL`: Ollama server address (default: `http://localhost:11434`)
- `OLLAMA_MODEL`: Model to use (default: `japanese-tutor:latest`)
- `RATE_LIMIT_REQUESTS`: Requests per minute per IP (default: 10)
- `RATE_LIMIT_WINDOW`: Rate limit window in seconds (default: 60)

### Frontend (`frontend/src/api.js`)
- `baseURL`: API endpoint (default: `http://localhost:5173` points to Vite dev server proxy)

## 🛡️ Security Features

- **HTTP Security Headers**: 
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'`
- **Rate Limiting**: 10 requests per minute per IP address
- **Input Sanitization**: HTML escaping for user-generated content
- **Trusted Hosts**: Restricts allowed hosts for development
- **CORS**: Configured for frontend integration

## 📚 Learning Modes

1. **Conversation**: Practice natural Japanese dialogue with contextual tutoring
2. **Grammar**: Learn Japanese particles, sentence structure, and verb conjugations
3. **Vocabulary**: Build your Japanese word bank with JLPT-appropriate terms
4. **Kanji**: Study kanji readings, meanings, and usage
5. **JLPT**: Prepare for the Japanese Language Proficiency Test with authentic-style questions

## 🤖 AI Capabilities

The tutor uses Ollama's `japanese-tutor:latest` model to provide:
- Context-aware responses based on conversation history
- JLPT-level appropriate explanations and corrections
- Cultural notes when relevant
- Gentle mistake correction with learning opportunities
- File-aware tutoring when documents are uploaded
- Adaptive difficulty based on user proficiency

## 🧪 Testing

See [TEST_RESULTS.md](TEST_RESULTS.md) for detailed test results and verification steps.

Run tests with:
```bash
# Backend tests
cd backend
python -m pytest test_application.py -v

# Frontend tests (if implemented)
cd frontend
npm test
```

## 📝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- [Ollama](https://ollama.com/) for enabling local LLM usage
- [FastAPI](https://fastapi.tiangolo.com/) for the high-performance backend
- [React](https://reactjs.org/) and [Vite](https://vitejs.dev/) for the modern frontend
- The open-source Japanese language learning community

## 📞 Support

For questions, issues, or feature requests, please:
1. Check the [issues](https://github.com/shubham-101/japanese-tutor/issues) page
2. Open a new issue if needed
3. Contribute fixes or improvements via pull requests

---

<p align="center">
  Made with ❤️ for Japanese language learners everywhere
</p>
