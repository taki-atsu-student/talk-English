# Contributing to Talk English Tutor

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend)
- pip and virtualenv

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd talk-English
   ```

2. **Backend Setup**
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate (Windows)
   .\.venv\Scripts\activate
   
   # Activate (macOS/Linux)
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r backend/requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

### Running Locally

**Backend:**
```bash
# From project root with .venv activated
cd backend
uvicorn main:app --reload --port 8000
```

**Frontend (Expo):**
```bash
cd frontend
npm start
```

## Project Structure

```
talk-English/
├── backend/              # FastAPI backend
│   ├── main.py          # Main application
│   ├── chat.py          # CLI chat interface
│   ├── requirements.txt  # Python dependencies
│   └── static/          # Static files (HTML, etc.)
├── frontend/            # Expo React Native app
│   ├── assets/          # App assets
│   └── package.json     # Node dependencies
├── talk-english-tutor/  # HuggingFace Spaces deployment
│   ├── main.py
│   └── Dockerfile
└── README.md
```

## Code Style

- **Python**: Follow PEP 8 (use `black` for formatting)
- **JavaScript/TypeScript**: Use ESLint + Prettier
- **Commits**: Use conventional commits (feat:, fix:, docs:, etc.)

## Testing

```bash
# Run backend tests (when added)
pytest backend/tests/

# Run frontend tests
npm test
```

## Deployment

### HuggingFace Spaces
```bash
# Push changes to the spaces branch
git push origin main:spaces-deploy
```

### Docker Build
```bash
docker build -t talk-english:latest .
docker run -p 7860:7860 talk-english:latest
```

## Reporting Issues

Please provide:
- Python/Node version
- Error message and stack trace
- Steps to reproduce
- OS (Windows/macOS/Linux)

## Questions?

Open an issue or start a discussion in the repository.
