"""
AIと話そう！ - FastAPI Backend v3.1
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
from fastapi.responses import FileResponse, JSONResponse
from fastapi import Request
from pydantic import BaseModel
import os
import logging
import time
import hashlib
import re
import asyncio
from typing import Optional, List, Any
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import httpx

try:
    from transformers import pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
app = FastAPI(title="AIと話そう！ API v3.1", version="3.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# =====================================================================
# SETTINGS
# =====================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "google/flan-t5-small")
USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "").lower() in ("1", "true")
MAX_TOKENS = 150
REQUEST_TIMEOUT = 0.9
CACHE_TTL = 3600
MAX_HISTORY = 20
MAX_RETRIES = 3
RETRY_DELAY = 0.5

if not GROQ_API_KEY:
    logger.warning("⚠️ GROQ_API_KEY not set; cloud LLM will be disabled unless local model is used")

local_model_pipeline: Optional[Any] = None


def should_use_cloud_llm() -> bool:
    """Return True when cloud LLM usage is enabled and GROQ key is present."""
    return bool(os.getenv("USE_CLOUD_LLM", "").lower() in ("1", "true") and GROQ_API_KEY)


def should_use_local_model() -> bool:
    """Return True when a local model should be used."""
    return USE_LOCAL_MODEL and TRANSFORMERS_AVAILABLE


def load_models() -> None:
    """Load optional local model for fallback responses."""
    global local_model_pipeline
    if should_use_local_model():
        try:
            device = 0 if torch.cuda.is_available() else -1
            logger.info(f"Loading local model: {LOCAL_MODEL_NAME} (device={device})")
            local_model_pipeline = pipeline(
                "text2text-generation",
                model=LOCAL_MODEL_NAME,
                device=device,
                framework="pt"
            )
            logger.info("Local model loaded successfully.")
        except Exception as e:
            logger.warning(f"Failed to load local model: {e}")
            local_model_pipeline = None
    elif USE_LOCAL_MODEL:
        logger.warning("USE_LOCAL_MODEL=1 but transformers/torch is unavailable.")
    else:
        logger.info("Local model loading skipped.")


def generate_local_response(user_text: str, history: Optional[List[dict]] = None, user_level: Optional[str] = None) -> str:
    if local_model_pipeline is None:
        return local_fallback_response(user_text, user_level)

    prompt = f"You are an English tutor. Respond briefly and helpfully. User: {user_text}\nTutor:"
    try:
        result = local_model_pipeline(prompt, max_length=128, num_return_sequences=1, do_sample=False)
        if result and isinstance(result, list):
            text = result[0].get("generated_text") if isinstance(result[0], dict) else None
            if text:
                return text.strip()
    except Exception as exc:
        logger.warning(f"Local model generation failed: {exc}")

    return local_fallback_response(user_text, user_level)


def generate_natural_response(user_text: str, history: Optional[List[dict]] = None, user_level: Optional[str] = None) -> str:
    """Synchronous compatibility wrapper that tries cloud LLM, then local model, then fallback."""
    text = user_text.strip()
    if not text:
        return "Please write something so we can chat."

    if should_use_cloud_llm() and GROQ_API_KEY:
        try:
            resp = httpx.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": text}],
                    "max_tokens": MAX_TOKENS,
                    "temperature": 0.7,
                    "top_p": 0.9,
                },
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"].strip()
            else:
                logger.warning(f"Cloud LLM request failed: {resp.status_code}")
        except Exception as exc:
            logger.debug(f"generate_natural_response: cloud call failed or unavailable: {exc}")

    if should_use_local_model():
        return generate_local_response(text, history, user_level)

    return local_fallback_response(text, user_level)


def local_fallback_response(text: str, user_level: Optional[str] = None) -> str:
    """Generate a simple friendly response when cloud LLM is unavailable."""
    normalized = text.lower().strip()
    if re.search(r"\bhello\b|\bhi\b|\bhey\b", normalized):
        return "Hi there! How can I help you practise English today?"
    if re.search(r"\bhow are you\b|\bhow's it going\b|\bwhat's up\b", normalized):
        return "I'm doing great, thanks! What would you like to talk about?"
    if re.search(r"\bwhy\b", normalized):
        return "Why is a great question. Could you tell me more about what you want to know?"
    if re.search(r"\bthank\b", normalized):
        return "You're welcome! I'm happy to help. What else would you like to practise?"
    if re.search(r"\bdo you\b.*\benglish\b|\bcan you\b.*\benglish\b", normalized):
        return "Yes, I can help you practise English. What would you like to talk about?"
    if re.search(r"\bwhat(?:'s| is) your name\b|\byour name\b", normalized):
        return "I'm AIと話そう！. Nice to meet you! What's your name?"
    if re.search(r"\bmy name\b", normalized):
        return "Nice to meet you! How can I help you practise English today?"
    if re.search(r"\bi(?:'m| am)\b.*\b(learning|studying|studying English|study English)\b|\bi wanna\b.*\bstudy\b", normalized):
        return "Great! I can help you study English. What topic or phrase do you want to practise?"
    if re.search(r"\bhello\b|\bhi\b|\bhey\b", normalized):
        return "Hello! Let's practise English together. What would you like to say?"
    if re.search(r"\bhow are you\b|\bhow's it going\b|\bwhat's up\b", normalized):
        return "I'm fine, thank you! How about you?"
    if re.search(r"\bwhere\b|\bwhen\b|\bwhat\b|\bwho\b|\bhow\b", normalized) and len(normalized.split()) > 2:
        return "That's an interesting question. Can you say more about what you want to practise in English?"
    if len(normalized.split()) <= 2:
        return "Please tell me more so I can help you better."
    return "I can help with English practice. Please ask me a question or say something more specific."

# =====================================================================
# DATA MODELS
# =====================================================================
class ChatRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    user_level: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    feedback: Optional[str] = None

class TranslateRequest(BaseModel):
    text: str

class TranslateResponse(BaseModel):
    translation: str


class GrammarRequest(BaseModel):
    text: str


class GrammarResponse(BaseModel):
    tip: Optional[str] = None


class ExplainRequest(BaseModel):
    text: str


class ExplainResponse(BaseModel):
    explanation: Optional[str] = None

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
    """Extract important phrases for translation (kept for compatibility)."""
    words = text.split()
    return ' '.join(words[:15]) if len(words) > 15 else text

# =====================================================================
# TRANSLATION
# =====================================================================
async def _chunk_text(text: str, max_chars: int = 1000):
    """Yield text chunks not exceeding max_chars, breaking on spaces when possible."""
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        if end < length:
            # try to roll back to last space to avoid cutting words
            last_space = text.rfind(' ', start, end)
            if last_space > start:
                end = last_space
        yield text[start:end].strip()
        start = end


async def translate_text(text: str) -> str:
    """Translate English to Japanese by chunking long texts and joining results.

    Uses the unofficial Google Translate web endpoint for small chunks. This
    function will split long input into safe-sized pieces and concatenate
    translated segments to support long-text translation.
    """
    if not text or not text.strip():
        return ""

    translated_parts = []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            async for chunk in _chunk_text(text, max_chars=1200):
                try:
                    response = await client.get(
                        "https://translate.googleapis.com/translate_a/single",
                        params={
                            "client": "gtx",
                            "sl": "en",
                            "tl": "ja",
                            "dt": "t",
                            "q": chunk
                        }
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result and result[0]:
                            translated_segments = [seg[0] for seg in result[0] if seg and len(seg) > 0]
                            translated_parts.append("".join(translated_segments))
                        else:
                            translated_parts.append("")
                    else:
                        translated_parts.append("")
                except Exception:
                    translated_parts.append("")
    except Exception:
        return "(Translation unavailable)"

    # Join with double newlines between chunks to preserve paragraph breaks
    final = "\n\n".join(p.strip() for p in translated_parts if p is not None)
    return final.strip() if final else "(Translation unavailable)"

# =====================================================================
# ENDPOINTS
# =====================================================================
@app.post("/chat")
async def chat(request: ChatRequest):
    user_text = request.text.strip()
    # Allow empty text (tests expect 200 for empty submissions)
    if not user_text:
        session = get_or_create_session(request.session_id)
        return {
            "response": "",
            "session_id": session.session_id,
            "timestamp": datetime.now().isoformat(),
            "feedback": "",
            "grammar_check": "",
            "corrections": [],
            "slang_notes": "",
            "naturalness_score": 0,
        }
    
    session = get_or_create_session(request.session_id)
    
    # Check cache
    cached_response, cached_feedback = cache.get(user_text)
    if cached_response:
        session.add_message("user", user_text)
        session.add_message("assistant", cached_response)
        return {
            "response": cached_response,
            "session_id": session.session_id,
            "timestamp": datetime.now().isoformat(),
            "feedback": cached_feedback or "",
            "grammar_check": cached_feedback or "",
            "corrections": [],
            "slang_notes": "",
            "naturalness_score": 0,
        }
    
    # Check grammar
    grammar_feedback = check_grammar_gentle(user_text)
    
    # Get AI response via compatibility wrapper (sync) so tests can patch it
    history = session.get_history()
    assistant_response = generate_natural_response(user_text, history, request.user_level)
    
    if not assistant_response:
        assistant_response = "I'm sorry, I didn't understand. Could you rephrase that?"
    
    session.add_message("user", user_text)
    session.add_message("assistant", assistant_response)
    cache.set(user_text, assistant_response, grammar_feedback)
    cleanup_expired_sessions()
    
    return {
        "response": assistant_response,
        "session_id": session.session_id,
        "timestamp": datetime.now().isoformat(),
        "feedback": grammar_feedback or "",
        "grammar_check": grammar_feedback or "",
        "corrections": [],
        "slang_notes": "",
        "naturalness_score": 0,
    }

@app.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """Translate selected text to Japanese. Long text is supported via chunking."""
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Invalid text")

    translation = await translate_text(request.text)
    return TranslateResponse(translation=translation)


@app.post("/grammar_check", response_model=GrammarResponse)
async def grammar_check(request: GrammarRequest):
    """Return a short English tip if a grammar issue is detected, otherwise empty."""
    if not request.text or not request.text.strip():
        return GrammarResponse(tip="")

    tip = check_grammar_gentle(request.text)
    return GrammarResponse(tip=tip or "")


@app.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest):
    """Return a Japanese explanation when incorrect usage is detected."""
    if not request.text or not request.text.strip():
        return ExplainResponse(explanation="")

    tip = check_grammar_gentle(request.text)
    if not tip:
        return ExplainResponse(explanation="")

    # Translate the tip to Japanese for user-friendly explanation
    try:
        jp = await translate_text(tip)
        return ExplainResponse(explanation=jp)
    except Exception:
        return ExplainResponse(explanation="")

@app.post("/reset")
async def reset_session(request: ResetRequest):
    if request.session_id and request.session_id in sessions:
        del sessions[request.session_id]
    return {"status": "success"}

@app.get("/")
async def root():
    return {
        "app": "AIと話そう！ v3.1",
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
# Middleware: inspect raw ASGI path to block traversal attempts early
@app.middleware("http")
async def block_traversal_middleware(request: Request, call_next):
    raw = request.scope.get('raw_path', b'')
    try:
        raw_s = raw.decode('utf-8', errors='ignore')
    except Exception:
        raw_s = str(raw)
    if request.url.path.endswith('.env'):
        return JSONResponse(status_code=403, content={'detail': 'Forbidden'})

    if ('..' in raw_s) or ('%2e%2e' in raw_s.lower()):
        if '/static' in raw_s:
            return JSONResponse(status_code=403, content={'detail': 'Forbidden'})
    return await call_next(request)
# Protect against path traversal for static files
@app.get('/static/{file_path:path}')
async def static_protect(file_path: str, request: Request):
    # Inspect raw path to detect attempts like /static/../../.env or encoded variants
    raw = request.scope.get('raw_path', b'')
    try:
        raw_s = raw.decode('utf-8', errors='ignore')
    except Exception:
        raw_s = str(raw)
    if '..' in file_path or '..' in raw_s or '%2e%2e' in raw_s.lower() or file_path.startswith('/') or file_path.startswith('\\'):
        raise HTTPException(status_code=403, detail='Forbidden')
    full = static_dir / file_path
    if full.exists() and full.is_file():
        return FileResponse(str(full))
    raise HTTPException(status_code=404, detail="Not found")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
def startup_event():
    load_models()

if __name__ == "__main__":
    import uvicorn
    import asyncio
    port = int(os.getenv("BACKEND_PORT", 8000))
    logger.info(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
