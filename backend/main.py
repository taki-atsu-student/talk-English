from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
model_name = "microsoft/DialoGPT-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

system_prompt = (
    "You are an English conversation tutor. Have natural, fluent English conversation. "
    "Keep responses concise but meaningful. Correct grammar mistakes in Japanese only if needed."
)
conversation_history = []

class ChatRequest(BaseModel):
    text: str

@app.get("/", response_class=HTMLResponse)
async def root():
    return (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")

@app.post("/chat")
async def chat(request: ChatRequest):
    user_text = request.text.strip()
    if not user_text:
        return {"response": "", "grammar": ""}

    grammar_feedback = check_and_explain_grammar(user_text)
    if grammar_feedback.lower().startswith("correct") or "no error" in grammar_feedback.lower():
        grammar_feedback = ""

    conversation_history.append({"role": "user", "text": user_text})
    prompt = build_prompt(conversation_history)
    response = generate_response(prompt)
    conversation_history.append({"role": "assistant", "text": response})

    if len(conversation_history) > 40:
        conversation_history[:] = conversation_history[-40:]

    return {"response": response, "grammar": grammar_feedback}

@app.get("/static/{path:path}")
async def static(path: str):
    return HTMLResponse((BASE_DIR / "static" / path).read_text(encoding="utf-8"))


def build_prompt(history):
    lines = [system_prompt]
    for item in history[-15:]:
        role = "User" if item["role"] == "user" else "AI"
        lines.append(f"{role}: {item['text']}")
    lines.append("AI:")
    return "\n".join(lines)


def check_and_explain_grammar(text):
    prompt = f"Is this English correct? '{text}' Yes or No, then brief explanation in Japanese."
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=256)
    outputs = model.generate(
        **inputs,
        max_new_tokens=64,
        pad_token_id=tokenizer.eos_token_id,
        do_sample=False,
    )
    explanation = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
    return explanation.strip()


def generate_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=768)
    outputs = model.generate(
        **inputs,
        max_new_tokens=160,
        pad_token_id=tokenizer.eos_token_id,
        do_sample=True,
        top_k=50,
        top_p=0.92,
        temperature=0.85,
        repetition_penalty=1.1,
    )
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
    return response.strip()
