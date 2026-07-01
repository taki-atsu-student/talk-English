"""
Talk English Tutor - FastAPI Backend v3.1
Enhanced with translation, grammar feedback, and error handling

Features:
- Groq API (llama-3.1-8b-instant)
- Caching, session management
- Google Translate integration
- Grammar checking with gentle feedback
- Error handling with automatic retry
- Dark mode support
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import logging
import time
import hashlib
import re
import asyncio
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
app = FastAPI(title="Talk English Tutor API v3.1", version="3.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# =====================================================================
# SETTINGS
# =====================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_TOKENS = 150
REQUEST_TIMEOUT = 0.9
CACHE_TTL = 3600
MAX_HISTORY = 20
MAX_RETRIES = 3
RETRY_DELAY = 0.5

if not GROQ_API_KEY:
    logger.error("⚠️ GROQ_API_KEY not set")

# =====================================================================
# DATA MODELS
# =====================================================================
class ChatRequest(BaseModel):
    text: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    feedback: Optional[str] = None

class TranslateRequest(BaseModel):
    text: str

class TranslateResponse(BaseModel):
    translation: str

class ResetRequest(BaseModel):
    session_id: Optional[str] = None

class CacheEntry:
    def __init__(self, response: str, feedback: Optional[str], timestamp: float):
        self.response = response
        self.feedback = feedback
        self.timestamp = timestamp
    
    def is_expired(self) -> bool:
        return time.time() - self.timestamp > CACHE_TTL

# =====================================================================
# CACHE
# =====================================================================
class ResponseCache:
    def __init__(self):
        self.cache = {}
    
    def _get_key(self, text: str) -> str:
        return hashlib.md5(text.lower().strip().encode()).hexdigest()
    
    def get(self, text: str) -> tuple:
        key = self._get_key(text)
        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired():
                logger.info(f"✓ Cache hit: {text[:30]}...")
                return entry.response, entry.feedback
            else:
                del self.cache[key]
        return None, None
    
    def set(self, text: str, response: str, feedback: Optional[str] = None) -> None:
        key = self._get_key(text)
        self.cache[key] = CacheEntry(response, feedback, time.time())

cache = ResponseCache()

# =====================================================================
# SESSION
# =====================================================================
class ConversationSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history = []
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
    
    def add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        if len(self.history) > MAX_HISTORY * 2:
            self.history = self.history[-MAX_HISTORY*2:]
        self.last_accessed = datetime.now()
    
    def get_history(self) -> List[dict]:
        return self.history[-20:]
    
    def is_expired(self, ttl: int = 3600) -> bool:
        return (datetime.now() - self.last_accessed).seconds > ttl

sessions = {}

def get_or_create_session(session_id: Optional[str] = None) -> ConversationSession:
    if session_id and session_id in sessions:
        return sessions[session_id]
    new_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()
    session = ConversationSession(new_id)
    sessions[new_id] = session
    return session

def cleanup_expired_sessions() -> None:
    expired = [sid for sid, s in sessions.items() if s.is_expired()]
    for sid in expired:
        del sessions[sid]
    if expired:
        logger.info(f"Cleaned up {len(expired)} sessions")

# =====================================================================
# GROQ API
# =====================================================================
async def call_groq_api(user_message: str, history: List[dict]) -> Optional[str]:
    system_prompt = """You are a friendly English conversation partner. 
Keep responses concise (1-2 sentences). Be natural and encouraging.
Understand slang: wanna, gonna, lol, omg, btw, etc."""
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(
                    GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": GROQ_MODEL,
                        "messages": messages,
                        "max_tokens": MAX_TOKENS,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"API error: {response.status_code}")
        except httpx.TimeoutException:
            logger.warning(f"Timeout (attempt {attempt + 1}/{MAX_RETRIES})")
        except Exception as e:
            logger.error(f"API error: {str(e)}")
        
        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
    
    return None

# =====================================================================
# GRAMMAR CHECK & FEEDBACK
# =====================================================================
def check_grammar_gentle(text: str) -> Optional[str]:
    """Check grammar and provide gentle feedback"""
    issues = []
    normalized = text.strip()

    # Check 1: "is" instead of "are"
    if re.search(r'\b(you|we|they|these|those)\s+is\b', normalized, re.IGNORECASE):
        issues.append("💡 Tip: 'you/we/they' usually use 'are' instead of 'is'.")

    # Check 2: Missing subject
    if re.search(r'^(going|learning|studying|working)\s+', normalized, re.IGNORECASE):
        issues.append("💡 Tip: Try adding a subject like 'I'm' or 'We're' at the start.")

    # Check 3: Missing article
    if re.search(r'\b(a|an|the)\s+\w+\s+\b(interesting|idea|thing|problem)\b', normalized, re.IGNORECASE) is None and re.search(r'\b(interesting|idea|thing|problem)\b', normalized, re.IGNORECASE):
        issues.append("💡 Tip: Use 'a' or 'the' before nouns: 'an interesting idea' or 'the problem'.")

    # Check 4: Double negation
    if re.search(r"\bno\s+\w*n't\b|\bdon't\s+\w*not\b", normalized, re.IGNORECASE):
        issues.append("💡 Tip: Avoid double negatives—use either 'no' or 'don't', not both.")

    # Check 5: Common mistakes
    mistakes = {
        r"\btheir\s+are\b": "'their are' → use 'there are'.",
        r"\byour\s+wrong\b": "'your wrong' → use 'you're wrong'.",
        r"\bits\s+me\b": "'its me' → use 'it's me'.",
        r"\bi\s+is\b": "'I is' is incorrect—use 'I am'.",
    }

    for pattern, correction in mistakes.items():
        if re.search(pattern, normalized, re.IGNORECASE):
            issues.append(f"💡 {correction}")

    return issues[0] if issues else None

def extract_translation_friendly(text: str) -> str:
    """Extract important phrases for translation"""
    words = text.split()
    return ' '.join(words[:15]) if len(words) > 15 else text

# =====================================================================
# TRANSLATION
# =====================================================================
async def translate_text(text: str) -> str:
    """Translate English to Japanese using Google Translate API or fallback"""
    try:
        # Use free Google Translate API
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(
                "https://translate.googleapis.com/translate_a/single",
                params={
                    "client": "gtx",
                    "sl": "en",
                    "tl": "ja",
                    "dt": "t",
                    "q": text[:200]
                }
            )
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result and result[0]:
                        return result[0][0][0]
                except:
                    pass
    except:
        pass
    
    return "(Translation unavailable)"

# =====================================================================
# ENDPOINTS
# =====================================================================
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_text = request.text.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty text")
    
    session = get_or_create_session(request.session_id)
    
    # Check cache
    cached_response, cached_feedback = cache.get(user_text)
    if cached_response:
        session.add_message("user", user_text)
        session.add_message("assistant", cached_response)
        return ChatResponse(
            response=cached_response,
            session_id=session.session_id,
            timestamp=datetime.now().isoformat(),
            feedback=cached_feedback
        )
    
    # Check grammar
    grammar_feedback = check_grammar_gentle(user_text)
    
    # Get AI response
    history = session.get_history()
    assistant_response = await call_groq_api(user_text, history)
    
    if not assistant_response:
        assistant_response = "I'm sorry, I didn't understand. Could you rephrase that?"
    
    session.add_message("user", user_text)
    session.add_message("assistant", assistant_response)
    cache.set(user_text, assistant_response, grammar_feedback)
    cleanup_expired_sessions()
    
    return ChatResponse(
        response=assistant_response,
        session_id=session.session_id,
        timestamp=datetime.now().isoformat(),
        feedback=grammar_feedback
    )

@app.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """Translate selected text to Japanese"""
    if not request.text or len(request.text) > 300:
        raise HTTPException(status_code=400, detail="Invalid text")
    
    translation = await translate_text(request.text)
    return TranslateResponse(translation=translation)

@app.post("/reset")
async def reset_session(request: ResetRequest):
    if request.session_id and request.session_id in sessions:
        del sessions[request.session_id]
    return {"status": "success"}

@app.get("/")
async def root():
    return {
        "app": "Talk English Tutor v3.1",
        "status": "running",
        "features": ["Chat", "Translation", "Grammar Feedback", "Dark Mode", "Error Retry"]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "api": "configured" if GROQ_API_KEY else "missing",
        "sessions": len(sessions),
        "cache": len(cache.cache)
    }

# =====================================================================
# STATIC FILES
# =====================================================================
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    import asyncio
    port = int(os.getenv("BACKEND_PORT", 8000))
    logger.info(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
