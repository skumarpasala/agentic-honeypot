# memory.py

sessions = {}

def get_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [],
            "stage": 0,
            "is_scam": False
        }
    return sessions[session_id]


def add_message(session_id: str, role: str, content: str):
    get_session(session_id)["messages"].append({
        "role": role,
        "content": content
    })


def get_history(session_id: str):
    return get_session(session_id)["messages"]


def get_stage(session_id: str) -> int:
    return get_session(session_id)["stage"]


def advance_stage(session_id: str):
    session = get_session(session_id)
    session["stage"] = min(session["stage"] + 1, 3)


# 🔒 PERMANENT SCAM LOCK
def mark_scam(session_id: str):
    get_session(session_id)["is_scam"] = True


def is_scam_session(session_id: str) -> bool:
    return get_session(session_id)["is_scam"]


def reset_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
