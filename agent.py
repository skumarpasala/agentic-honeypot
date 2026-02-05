from dotenv import load_dotenv
import os
from openai import OpenAI
from memory import (
    add_message,
    get_history,
    get_stage,
    advance_stage,
    is_scam_session,
    mark_scam
)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_HISTORY = 8

# 🔐 HARD RESPONSE MAP (used only at later stages)
HARD_RESPONSES = {
    "credentials": "I’m not sharing any bank, card, or personal details.",
    "money": "I’m not sending money. Why are you asking?",
    "link": "I’m not clicking any link. What is it for?",
}

def classify_scammer_message(text: str) -> str:
    t = text.lower().strip()

    if any(x in t for x in ["send money", "transfer", "pay", "payment", "rupees", "rs", "inr"]):
        return "money"

    if any(x in t for x in ["bank details", "account number", "upi id", "upi", "card", "cvv", "pin", "otp"]):
        return "credentials"

    if "http" in t or "click" in t:
        return "link"

    if any(x in t for x in ["kyc", "verify", "blocked", "suspended", "urgent", "immediately"]):
        return "threat"

    if t in ["hi", "hello", "hey", "how are you", "good morning", "good evening"]:
        return "greeting"

    return "other"

def claims_identity_shift(text: str) -> bool:
    return any(x in text.lower() for x in [
        "your friend", "this is your friend", "bank officer",
        "customer care", "support team"
    ])

def extract_text(response) -> str:
    try:
        return response.output_text.strip()
    except Exception:
        return ""

def run_agent(session_id: str, scammer_message: str):

    # Store incoming message
    add_message(session_id, "scammer", scammer_message)

    msg_type = classify_scammer_message(scammer_message)

    # 🚩 Mark scam signals early
    if msg_type in ["money", "credentials", "link", "threat"] or claims_identity_shift(scammer_message):
        mark_scam(session_id)

    scam_active = is_scam_session(session_id)
    stage = get_stage(session_id)

    # Friendly greeting if clean
    if msg_type == "greeting" and not scam_active:
        reply = "Hey 🙂 How’s it going?"
        add_message(session_id, "agent", reply)
        return reply

    EMOTIONS = [
        "calm but attentive",
        "slightly confused",
        "worried and cautious",
        "firm and demanding clarity"
    ]
    emotion = EMOTIONS[min(stage, 3)]

    intent = "ask for clarification"

    system_prompt = f"""
You are a real human chatting on WhatsApp.

Emotional state: {emotion}

Last message:
"{scammer_message}"

Rules:
- Reply ONLY to the last message
- Ask at most ONE question
- Sound firm once suspicious
- Never mention AI, scams, police, fraud

Intent: {intent}
"""

    history = get_history(session_id)[-MAX_HISTORY:]
    messages = [{"role": "system", "content": system_prompt}]

    for msg in history:
        messages.append({
            "role": "user" if msg["role"] == "scammer" else "assistant",
            "content": msg["content"]
        })

    # 🚫 HARD CONTROL (ONLY AFTER STAGE 2)
    if msg_type in HARD_RESPONSES and stage >= 2:
        reply = HARD_RESPONSES[msg_type]
    else:
        try:
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=messages,
                temperature=0.9,
                max_output_tokens=120
            )
            reply = extract_text(response)
        except Exception:
            reply = ""

    # 🛟 FALLBACK (always meaningful)
    if not reply:
        fallback = {
            "credentials": "I’m not comfortable sharing any bank or personal details.",
            "money": "Why do you need money from me? What is this for?",
            "link": "I don’t click random links. What is it related to?",
            "threat": "Who exactly are you and which organization is this?",
            "other": "Can you explain what you mean?"
        }
        reply = fallback.get(msg_type, "What exactly are you trying to say?")

    add_message(session_id, "agent", reply)

    if scam_active:
        advance_stage(session_id)

    return reply
