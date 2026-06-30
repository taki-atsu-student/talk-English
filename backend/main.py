"""
Talk English Tutor - FastAPI Backend v2.1
Enhanced Conversational Flow & Context Awareness

改善点：
- 会話履歴を最大限活用（10往復まで）
- トピック・文脈追跡
- ビームサーチで多様な応答
- 動的パラメータ調整
- システムプロンプト最適化
- 会話の自然さと一貫性を重視
"""

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import language_tool_python
import logging
import os
from typing import Optional, List

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Talk English Tutor API",
    version="2.1.0",
    description="Enhanced conversational AI with natural dialogue flow"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

# ============= モデル設定 =============
MODEL_NAME = os.getenv("MODEL_NAME", "microsoft/DialoGPT-large")
tokenizer = None
model = None
tool = None

# ============= グローバル会話管理 =============
class ConversationContext:
    """会話コンテキストを管理するクラス"""
    def __init__(self):
        self.messages: List[dict] = []
        self.topics: List[str] = []
        self.last_ai_response: str = ""
        self.user_level: str = "intermediate"
        self.conversation_turn: int = 0
    
    def add_message(self, role: str, text: str):
        """メッセージを追加"""
        self.messages.append({"role": role, "text": text})
        if len(self.messages) > 20:
            self.messages = self.messages[-20:]
    
    def extract_topics(self, text: str):
        """トピックを抽出"""
        keywords = ['like', 'want', 'think', 'learn', 'about', 'going', 'help']
        found = [kw for kw in keywords if kw.lower() in text.lower()]
        if found:
            self.topics.extend(found)
            self.topics = self.topics[-5:]
    
    def get_context_string(self, max_messages: int = 10) -> str:
        """コンテキスト文字列を生成"""
        recent = self.messages[-max_messages:]
        lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Tutor"
            lines.append(f"{role}: {msg['text']}")
        return "\n".join(lines)
    
    def reset(self):
        self.messages = []
        self.topics = []
        self.conversation_turn = 0

conversation = ConversationContext()

# ============= 改善されたシステムプロンプト =============
ADVANCED_SYSTEM_PROMPT = """You are a friendly English conversation partner and tutor. Your key responsibilities:

1. NATURAL DIALOGUE: Keep conversations flowing naturally. Ask follow-up questions. Show genuine interest.
   - Use contractions: "I'm", "don't", "it's", "you're"
   - Use conversational patterns: "Well...", "You know...", "Actually...", "I mean..."
   - Vary sentence structure

2. BUILD ON CONTEXT: Reference previous points. Create continuity between exchanges.
   - "That's similar to what you mentioned earlier..."
   - "Oh right, like when you said..."
   - Connect ideas together

3. RESPOND AUTHENTICALLY: React first, then add thoughts:
   - Show you understood: "Oh, so you're saying..."
   - Express reactions: "That's cool!", "I totally get that"
   - Ask natural follow-ups

4. RESPONSE PATTERN (2-3 sentences):
   - 1st: React/acknowledge what they said
   - 2nd: Add related information or your perspective  
   - 3rd: Ask a follow-up question

Good example:
User: "I'm learning Python"
You: "Oh nice! Python's really fun to learn. I use it all the time for different stuff, you know? What kind of projects are you working on?"

Bad example:
User: "I'm learning Python"
You: "Python is a programming language. It is used for many purposes. What is your purpose?"

Always prioritize NATURAL, FLOWING CONVERSATION."""

def load_models():
    """モデルを遅延読み込み"""
    global tokenizer, model, tool
    try:
        if tokenizer is None:
            logger.info(f"Loading tokenizer from {MODEL_NAME}...")
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
        
        if model is None:
            logger.info(f"Loading model {MODEL_NAME}...")
            model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
        
        if tool is None:
            logger.info("Initializing grammar tool...")
            tool = language_tool_python.LanguageTool('en-US')
        
        logger.info("✅ All models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise


@app.on_event("startup")
async def startup_event():
    """アプリ起動時にモデルを読み込む"""
    try:
        load_models()
    except Exception as e:
        logger.error(f"Startup warning: {e}")


# ============= リクエスト/レスポンスモデル =============
class ChatRequest(BaseModel):
    text: str
    user_level: Optional[str] = "intermediate"


class ChatResponse(BaseModel):
    response: str
    grammar_check: str = ""
    corrections: list = []
    slang_notes: str = ""
    naturalness_score: int = 0


# ============= API エンドポイント =============
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main HTML interface"""
    try:
        html_path = BASE_DIR / "static" / "index.html"
        return html_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found")
    except Exception as e:
        logger.error(f"Error serving root: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Enhanced chat endpoint with improved conversational flow"""
    try:
        if tokenizer is None or model is None:
            load_models()
        
        user_text = request.text.strip()
        if not user_text:
            return ChatResponse(response="", grammar_check="")
        
        if len(user_text) > 500:
            return ChatResponse(response="Text too long (max 500 chars)", grammar_check="")

        # コンテキスト更新
        conversation.user_level = request.user_level or "intermediate"
        conversation.add_message("user", user_text)
        conversation.extract_topics(user_text)
        conversation.conversation_turn += 1
        
        # 改善: より長い履歴とトピック情報を含むプロンプト
        prompt = build_improved_prompt(conversation)
        
        # 文法チェック
        grammar_result = check_grammar_detailed(user_text)

        # 改善: より自然な応答生成
        response = generate_natural_response(
            prompt,
            conversation.user_level,
            previous_response=conversation.last_ai_response
        )
        
        conversation.add_message("assistant", response)
        conversation.last_ai_response = response

        return ChatResponse(
            response=response,
            grammar_check=grammar_result.get("summary", ""),
            corrections=grammar_result.get("corrections", []),
            slang_notes=grammar_result.get("slang_notes", ""),
            naturalness_score=grammar_result.get("naturalness_score", 0)
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.1.0",
        "models_loaded": tokenizer is not None and model is not None,
        "grammar_tool_ready": tool is not None,
        "conversation_turn": conversation.conversation_turn,
        "model_name": MODEL_NAME
    }


@app.post("/reset")
async def reset_conversation():
    """会話をリセット"""
    conversation.reset()
    return {"status": "reset", "message": "Conversation context cleared"}


@app.get("/static/{path:path}")
async def static(path: str):
    """Serve static files"""
    try:
        file_path = BASE_DIR / "static" / path
        if not file_path.resolve().is_relative_to(BASE_DIR / "static"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        
        return HTMLResponse(file_path.read_text(encoding="utf-8"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving static file {path}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============= 改善されたプロンプト構築 =============
def build_improved_prompt(context: ConversationContext) -> str:
    """改善されたプロンプト構築"""
    lines = [
        ADVANCED_SYSTEM_PROMPT,
        "\n" + "="*50,
        "CONVERSATION HISTORY:",
        "="*50,
        ""
    ]
    
    # 過去10メッセージを含める
    history = context.get_context_string(max_messages=10)
    lines.append(history)
    
    # 現在のトピック情報
    if context.topics:
        lines.append(f"\n[Topics: {', '.join(set(context.topics))}]")
    
    # ユーザーレベルに応じた指示
    if context.user_level == "beginner":
        lines.append("[Use simple, clear English. Explain any difficult words.]")
    elif context.user_level == "advanced":
        lines.append("[Feel free to use idioms, slang, complex expressions.]")
    
    lines.append("\nContinue the conversation naturally:")
    
    return "\n".join(lines)


# ============= 改善されたレスポンス生成 =============
def generate_natural_response(
    prompt: str,
    user_level: str = "intermediate",
    previous_response: str = ""
) -> str:
    """より自然な応答を生成"""
    if not tokenizer or not model:
        return "I'm sorry, I'm not ready to chat yet. Please try again in a moment."
    
    try:
        # ユーザーレベルに応じたパラメータ
        params = {
            "beginner": {
                "max_new_tokens": 60,
                "num_beams": 3,
                "temperature": 0.9,
                "top_p": 0.85,
            },
            "intermediate": {
                "max_new_tokens": 80,
                "num_beams": 4,
                "temperature": 0.95,
                "top_p": 0.88,
            },
            "advanced": {
                "max_new_tokens": 100,
                "num_beams": 5,
                "temperature": 1.0,
                "top_p": 0.9,
            }
        }
        
        p = params.get(user_level, params["intermediate"])
        
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        )
        
        # ビームサーチで多様な応答を生成
        outputs = model.generate(
            **inputs,
            max_new_tokens=p["max_new_tokens"],
            num_beams=p["num_beams"],
            early_stopping=True,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,
            temperature=p["temperature"],
            top_p=p["top_p"],
            repetition_penalty=1.2,
            no_repeat_ngram_size=2,
            length_penalty=0.8,  # 適度な長さを促す
        )
        
        response = tokenizer.decode(
            outputs[0][inputs.input_ids.shape[-1]:],
            skip_special_tokens=True
        ).strip()
        
        # クリーンアップ
        if "User:" in response:
            response = response.split("User:")[0].strip()
        if response.lower().startswith("ai") or response.lower().startswith("tutor"):
            response = response[2:].strip()
        
        # 最小長チェック
        if len(response) < 8:
            response = "I like that! Tell me more about it."
        
        return response
    
    except Exception as e:
        logger.error(f"Response generation failed: {e}", exc_info=True)
        return "I had trouble generating a response. Could you try rephrasing that?"


# ============= 文法チェック & スラング検出 =============
def check_grammar_detailed(text: str) -> dict:
    """文法チェック"""
    if not tool:
        return {
            "summary": "",
            "corrections": [],
            "slang_notes": "",
            "naturalness_score": 0
        }
    
    try:
        matches = tool.check(text)
        corrections = []
        summary_parts = []
        slang_notes = ""
        naturalness_score = 10
        
        if not matches:
            return {
                "summary": "✅ 完璧です！",
                "corrections": [],
                "slang_notes": "",
                "naturalness_score": 10
            }
        
        for i, match in enumerate(matches[:3]):
            try:
                error_text = text[match.offset:match.offset + match.errorLength]
                suggestions = match.replacements[:1] if match.replacements else [""]
                suggestion = suggestions[0] if suggestions[0] else error_text
                
                explanation_ja = generate_grammar_explanation_ja(
                    error_text, match.message, suggestion
                )
                
                corrections.append({
                    "error": error_text,
                    "correction": suggestion,
                    "explanation_ja": explanation_ja
                })
                
                summary_parts.append(
                    f"⚠️ 「{error_text}」 → 「{suggestion}\"\n"
                    f"   💡 {explanation_ja}"
                )
                naturalness_score -= 2
                
            except (IndexError, AttributeError):
                continue
        
        slang_result = detect_slang_and_informal(text)
        if slang_result:
            slang_notes = slang_result
        
        summary = "\n".join(summary_parts) if summary_parts else "✅ 完璧です！"
        
        return {
            "summary": summary,
            "corrections": corrections,
            "slang_notes": slang_notes,
            "naturalness_score": max(1, naturalness_score)
        }
        
    except Exception as e:
        logger.warning(f"Grammar check failed: {e}")
        return {
            "summary": "",
            "corrections": [],
            "slang_notes": "",
            "naturalness_score": 0
        }


def generate_grammar_explanation_ja(error: str, message: str, correction: str) -> str:
    """文法説明"""
    explanation_map = {
        "Possible typo": f"綴り間違い",
        "Agreement": f"主語と時制が一致していません",
        "Tense": f"時制が不適切です",
        "Article": f"冠詞の使い方に誤りがあります",
        "Punctuation": f"句読点の使い方に誤りがあります",
    }
    
    for key, ja_msg in explanation_map.items():
        if key.lower() in message.lower():
            return ja_msg
    
    return f"「{correction}」の方が正しいです"


def detect_slang_and_informal(text: str) -> str:
    """スラング検出"""
    slang_dict = {
        "gonna": "going to",
        "wanna": "want to",
        "gotta": "have got to",
        "kinda": "kind of",
        "sorta": "sort of",
    }
    
    detected = []
    text_lower = text.lower()
    
    for slang, formal in slang_dict.items():
        if slang in text_lower:
            detected.append(f"📝 {slang} = {formal} (カジュアル表現)")
    
    return "\n".join(detected) if detected else ""


@app.post("/set-level")
async def set_user_level(level: str):
    """ユーザーレベル設定"""
    valid_levels = ["beginner", "intermediate", "advanced"]
    if level not in valid_levels:
        raise HTTPException(status_code=400, detail=f"Invalid level")
    conversation.user_level = level
    return {"status": "ok", "user_level": conversation.user_level}


@app.get("/level")
async def get_user_level():
    """ユーザーレベル取得"""
    return {"user_level": conversation.user_level}
