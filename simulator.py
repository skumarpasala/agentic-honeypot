import random

NORMAL_MESSAGES = [
    "Hi",
    "Hello there",
    "How are you?",
    "Good morning",
    "Are you available today?"
]

SCAM_MESSAGES = [
    "Your bank account is blocked",
    "Verify your KYC immediately",
    "Click this link to verify account",
    "Share your UPI ID to unlock account",
    "Urgent action required"
]


def generate_message():
    """
    Randomly returns a normal or scam message.
    """
    is_scam = random.random() < 0.6  # 60% chance scam

    if is_scam:
        return random.choice(SCAM_MESSAGES), True
    else:
        return random.choice(NORMAL_MESSAGES), False
