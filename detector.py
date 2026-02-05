from memory import get_history

# 🔥 STRONG scam indicators only (intent-based)
SCAM_SIGNALS = [
    "send money",
    "transfer money",
    "pay now",
    "urgent",
    "otp",
    "upi",
    "account blocked",
    "verify now",
    "click link",
    "bank account",
    "kyc update",
    "pin",
    "cvv"
]

def privacy_safe_check(session_id: str, message: str) -> bool:
    """
    Scam is detected ONLY if:
    1. The current message shows strong scam intent
    OR
    2. Recent messages in THIS SAME session show strong scam intent

    This prevents:
    - Cross-session contamination
    - Normal messages being flagged
    - Permanent scam poisoning
    """

    msg = message.lower().strip()

    # --------------------------------------------------
    # 1️⃣ Check CURRENT message (highest priority)
    # --------------------------------------------------
    if any(signal in msg for signal in SCAM_SIGNALS):
        return True

    # --------------------------------------------------
    # 2️⃣ Check ONLY RECENT history (session-isolated)
    # --------------------------------------------------
    history = get_history(session_id)

    # Look at last 3 scammer messages only
    recent_messages = [
        m for m in history if m["role"] == "scammer"
    ][-3:]

    for m in recent_messages:
        text = m["content"].lower()
        if any(signal in text for signal in SCAM_SIGNALS):
            return True

    # --------------------------------------------------
    # 3️⃣ Otherwise → NOT a scam
    # --------------------------------------------------
    return False
