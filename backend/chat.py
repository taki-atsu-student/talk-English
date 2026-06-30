"""
Talk English Tutor - CLI Chat Interface (Enhanced Version)
=========================================

Advanced features:
- DialoGPT-large for better conversation
- Slang and informal language support
- Detailed grammar checking with Japanese explanations
- Natural speaker responses

Usage:
    python chat.py

Commands:
    - Type English text to chat
    - 'level' to set your learning level (beginner/intermediate/advanced)
    - 'exit' to quit
"""

from transformers import AutoModelForCausalLM, AutoTokenizer
import language_tool_python
import logging
from colorama import init, Fore, Style

# カラー出力初期化
init(autoreset=True)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# ============= モデル設定 =============
MODEL_NAME = "microsoft/DialoGPT-large"
user_level = "intermediate"

logger.info(f"{Fore.CYAN}🔄 Loading model: {MODEL_NAME}...{Style.RESET_ALL}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

logger.info(f"{Fore.GREEN}✅ Model loaded successfully!{Style.RESET_ALL}\n")

# 文法チェッカー初期化
logger.info(f"{Fore.CYAN}🔄 Loading grammar checker...{Style.RESET_ALL}")
tool = language_tool_python.LanguageTool('en-US')
logger.info(f"{Fore.GREEN}✅ Grammar checker ready!{Style.RESET_ALL}\n")

# ============= グローバル設定 =============
SYSTEM_PROMPT = """You are an expert English tutor with deep knowledge of:
- Colloquial English and slang
- Native speaker patterns
- Formal and informal expressions
- American and British English variations

Respond naturally like a native speaker. Use contractions, idioms, and casual language when appropriate.
Keep responses concise and conversational (2-3 sentences max)."""

conversation_history = []

# ============= スラング辞書 =============
SLANG_DICT = {
    "gonna": {"formal": "going to", "note": "カジュアルな会話で使用される短縮形"},
    "wanna": {"formal": "want to", "note": "インフォーマルな表現"},
    "gotta": {"formal": "have got to / must", "note": "スラング的な表現"},
    "y'all": {"formal": "you all", "note": "南部英語やカジュアルな表現"},
    "ain't": {"formal": "am not / is not", "note": "非標準文法だが会話でよく使われます"},
    "lemme": {"formal": "let me", "note": "カジュアルな短縮形"},
    "sup": {"formal": "what is up", "note": "友人同士の挨拶"},
    "yeah": {"formal": "yes", "note": "カジュアルな言い方"},
    "nope": {"formal": "no", "note": "カジュアルな言い方"},
    "kinda": {"formal": "kind of", "note": "口語的な短縮形"},
    "sorta": {"formal": "sort of", "note": "カジュアルな表現"},
    "dunno": {"formal": "don't know", "note": "非常にカジュアルな表現"},
    "ya": {"formal": "you", "note": "会話体での「you」"},
    "imma": {"formal": "I am going to", "note": "スラング的な表現"},
    "bruh": {"formal": "bro", "note": "友人との非常にカジュアルな表現"},
}


def check_grammar_with_explanation(text: str) -> str:
    """文法チェック with 日本語詳細解説"""
    try:
        matches = tool.check(text)
        
        if not matches:
            return f"{Fore.GREEN}✅ 完璧です！{Style.RESET_ALL}"
        
        feedbacks = []
        for i, match in enumerate(matches[:3]):
            try:
                error_text = text[match.offset:match.offset + match.errorLength]
                suggestions = match.replacements[:2] if match.replacements else ["No suggestions"]
                
                explanation = generate_grammar_explanation_ja(
                    error_text, match.message, suggestions[0]
                )
                
                feedbacks.append(
                    f"{Fore.RED}⚠️ 【{i+1}】「{error_text}」 → 「{suggestions[0]}\"{Style.RESET_ALL}\n"
                    f"   {Fore.YELLOW}💡 {explanation}{Style.RESET_ALL}"
                )
            except (IndexError, AttributeError):
                continue
        
        return "\n".join(feedbacks) if feedbacks else ""
    
    except Exception as e:
        logger.error(f"{Fore.RED}Grammar check error: {e}{Style.RESET_ALL}")
        return ""


def generate_grammar_explanation_ja(error: str, message: str, correction: str) -> str:
    """文法エラーの日本語説明生成"""
    explanation_map = {
        "Possible typo": f"「{error}」は綴り間違いの可能性があります",
        "Agreement": f"主語と時制が一致していません。「{correction}」が正しいです",
        "Tense": f"時制が不適切です。「{correction}」を使う方が自然です",
        "Article": f"冠詞「{error}」は不要、または「{correction}」が適切です",
        "Punctuation": f"句読点「{error}」を「{correction}」に変更してください",
        "Word": f"「{error}」ではなく「{correction}」を使用してください",
    }
    
    for key, ja_msg in explanation_map.items():
        if key.lower() in message.lower():
            return ja_msg
    
    return f"「{error}」の代わりに「{correction}」を使用してください"


def detect_slang_and_informal(text: str) -> str:
    """スラングと口語表現を検出"""
    detected = []
    text_lower = text.lower()
    
    for slang, info in SLANG_DICT.items():
        if slang in text_lower:
            detected.append(
                f"{Fore.CYAN}📝 スラング「{slang}」 → 正式には「{info['formal']}\"{Style.RESET_ALL}\n"
                f"   ℹ️ {info['note']}"
            )
    
    return "\n".join(detected) if detected else ""


def build_prompt(history: list) -> str:
    """プロンプト構築"""
    lines = [SYSTEM_PROMPT, "\n--- Conversation History ---\n"]
    
    for item in history:
        role = "User" if item["role"] == "user" else "AI Tutor"
        lines.append(f"{role}: {item['text']}")
    
    lines.append("\nAI Tutor:")
    return "\n".join(lines)


def generate_response(prompt: str) -> str:
    """応答生成"""
    try:
        level_params = {
            "beginner": {"max_tokens": 50, "top_k": 30, "temp": 0.7},
            "intermediate": {"max_tokens": 60, "top_k": 40, "temp": 0.75},
            "advanced": {"max_tokens": 80, "top_k": 50, "temp": 0.8},
        }
        
        params = level_params.get(user_level, level_params["intermediate"])
        
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        outputs = model.generate(
            **inputs,
            max_new_tokens=params["max_tokens"],
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,
            top_k=params["top_k"],
            top_p=0.87,
            temperature=params["temp"],
            repetition_penalty=1.2,
        )
        
        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
        
        if "AI" in response:
            response = response.split("AI")[0]
        if "User:" in response:
            response = response.split("User:")[0]
        
        return response.strip()
    
    except Exception as e:
        logger.error(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return "Sorry, something went wrong."


def main():
    """メインチャットループ"""
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}🤖 Talk English Tutor - CLI Mode{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")
    
    print(f"{Fore.MAGENTA}📚 Current Level: {user_level}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Type 'level' to change, 'exit' to quit\n{Style.RESET_ALL}")
    
    global conversation_history
    
    try:
        while True:
            try:
                user_input = input(f"{Fore.BLUE}👤 You: {Style.RESET_ALL}").strip()
                
                if not user_input:
                    continue
                
                # コマンド処理
                if user_input.lower() == "exit":
                    print(f"\n{Fore.GREEN}👋 Thank you for practicing! Goodbye!{Style.RESET_ALL}\n")
                    break
                
                if user_input.lower() == "level":
                    new_level = input(
                        f"{Fore.YELLOW}Choose level (beginner/intermediate/advanced): {Style.RESET_ALL}"
                    ).strip().lower()
                    if new_level in ["beginner", "intermediate", "advanced"]:
                        globals()["user_level"] = new_level
                        print(f"{Fore.GREEN}✅ Level set to: {new_level}{Style.RESET_ALL}\n")
                    continue
                
                # 文法チェック
                print()  # 改行
                grammar_feedback = check_grammar_with_explanation(user_input)
                if grammar_feedback and "完璧" not in grammar_feedback:
                    print(grammar_feedback)
                    print()  # 改行
                
                # スラング検出
                slang_feedback = detect_slang_and_informal(user_input)
                if slang_feedback:
                    print(slang_feedback)
                    print()  # 改行
                
                # 会話履歴追加
                conversation_history.append({"role": "user", "text": user_input})
                
                # プロンプト構築と応答生成
                prompt = build_prompt(conversation_history[-6:])
                response = generate_response(prompt)
                conversation_history.append({"role": "assistant", "text": response})
                
                # 履歴管理
                if len(conversation_history) > 20:
                    conversation_history = conversation_history[-20:]
                
                print(f"{Fore.GREEN}🤖 AI Tutor: {response}{Style.RESET_ALL}\n")
            
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}⚠️  Interrupted by user.{Style.RESET_ALL}")
                print(f"{Fore.GREEN}👋 Goodbye!{Style.RESET_ALL}\n")
                break
            except Exception as e:
                logger.error(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                continue
    
    except Exception as e:
        logger.error(f"{Fore.RED}Fatal error: {e}{Style.RESET_ALL}")
        raise


if __name__ == "__main__":
    main()
