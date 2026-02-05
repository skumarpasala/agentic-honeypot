from pydantic import BaseModel
from typing import Optional, Dict, Any


class ScamRequest(BaseModel):
    session_id: str
    message: str


class ScamResponse(BaseModel):
    scam_detected: bool
    reply: Optional[str] = None
    intelligence: Dict[str, Any] = {}
