from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "microsoft/DialoGPT-large"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

def check_and_explain_grammar(text):
    prompt = f"Check this English sentence for grammar errors: '{text}'. If there are errors, explain them in Japanese and provide the corrected version. If correct, say 'Correct'. Keep it brief."
    inputs = tokenizer.encode(prompt + tokenizer.eos_token, return_tensors="pt")
    attention_mask = (inputs != tokenizer.pad_token_id).long()
    outputs = model.generate(inputs, attention_mask=attention_mask, max_length=300, pad_token_id=tokenizer.eos_token_id, do_sample=True, top_p=0.9, temperature=0.7)
    explanation = tokenizer.decode(outputs[0][inputs.shape[-1]:], skip_special_tokens=True)
    return explanation

print("AI: Hello! I'm here to help you practice English at a master level. I'll automatically check your grammar and explain in Japanese.\n")

chat_history_ids = None
conversation_history = []

while True:
    user_input = input("You: ").strip()
    
    if user_input.lower() == 'exit':
        break
    
    grammar_feedback = check_and_explain_grammar(user_input)
    if not grammar_feedback.lower().startswith('correct'):
        print(f"\n✗ Grammar check: {grammar_feedback}\n")
    
    conversation_history.append(f"User: {user_input}")
    
    context = " ".join(conversation_history[-50:])
    new_input_ids = tokenizer.encode(context + tokenizer.eos_token, return_tensors="pt")
    attention_mask = (new_input_ids != tokenizer.pad_token_id).long()
    
    chat_history_ids = model.generate(
        new_input_ids,
        attention_mask=attention_mask,
        max_length=1500,
        pad_token_id=tokenizer.eos_token_id,
        do_sample=True,
        top_k=50,
        top_p=0.92,
        temperature=0.85,
        repetition_penalty=1.1
    )
    
    response = tokenizer.decode(chat_history_ids[0][new_input_ids.shape[-1]:], skip_special_tokens=True)
    print(f"AI: {response}\n")
    conversation_history.append(f"AI: {response}")

