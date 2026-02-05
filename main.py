from fastapi import FastAPI, HTTPException, Depends
from fastapi.openapi.utils import get_openapi
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

from models import ScamResponse
from agent import run_agent
from reporter import generate_and_save_report
from detector import privacy_safe_check

import gradio as gr
import json
import tempfile

# ======================================================
# UTILITIES
# ======================================================
def save_json_to_file(json_text: str):
    file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    file.write(json_text.encode("utf-8"))
    file.close()
    return file.name


# 🧠 SESSION HISTORY (UI ONLY)
SESSION_HISTORY = {}


# ======================================================
# CONFIG
# ======================================================
API_KEY = "test-key-123"
API_KEY_NAME = "x-api-key"

api_key_header = APIKeyHeader(
    name=API_KEY_NAME,
    auto_error=False
)

app = FastAPI(title="Agentic HoneyPot API")


# ======================================================
# SECURITY
# ======================================================
def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")


# ======================================================
# REQUEST MODEL
# ======================================================
class ManualIngestRequest(BaseModel):
    session_id: str
    message: str


# ======================================================
# MANUAL INGEST API
# ======================================================
@app.post(
    "/ingest/manual",
    response_model=ScamResponse,
    dependencies=[Depends(verify_api_key)]
)
def ingest_manual(req: ManualIngestRequest):

    is_scam = privacy_safe_check(req.session_id, req.message)

    if not is_scam:
        return ScamResponse(
            scam_detected=False,
            reply=None,
            intelligence={}
        )

    reply = run_agent(req.session_id, req.message)
    report = generate_and_save_report(req.session_id)

    return ScamResponse(
        scam_detected=True,
        reply=reply,
        intelligence=report
    )


# ======================================================
# HEALTH CHECK
# ======================================================
@app.get("/health")
def health():
    return {"status": "ok"}


# ======================================================
# GRADIO UI
# ======================================================
with gr.Blocks(theme=gr.themes.Soft()) as gradio_ui:

    gr.Markdown("## 🕵️ Agentic HoneyPot – Scam Interaction Demo")
    gr.Markdown(
        "Each **Session ID** represents a separate investigation. "
        "Switching session IDs loads its own conversation history."
    )

    # 🔑 SESSION ID INPUT
    session_input = gr.Textbox(
        label="Session ID",
        placeholder="e.g. case-001, investigation-A",
        value="session-1"
    )

    message_input = gr.Textbox(
        label="Message from Stranger",
        placeholder="Paste a suspicious message here...",
        lines=3
    )

    agent_output = gr.Textbox(
        label="Agent Response (Raw JSON)",
        lines=6,
        interactive=False
    )

    with gr.Accordion("📄 Raw Intelligence (JSON)", open=False):
        raw_json = gr.Textbox(
            label="Raw JSON Output",
            lines=12,
            interactive=False
        )
        download_json = gr.File(label="Download JSON")

    with gr.Accordion("🕓 Conversation History (Current Session)", open=False):
        history_box = gr.Textbox(
            label="Session History",
            lines=14,
            interactive=False
        )

    analyze_btn = gr.Button("Analyze Message")


    # ==================================================
    # UI HANDLER (SESSION-AWARE)
    # ==================================================
    def ui_handler(session_id: str, message: str):

        if session_id not in SESSION_HISTORY:
            SESSION_HISTORY[session_id] = []

        # Store incoming message
        SESSION_HISTORY[session_id].append(
            f"🧑 Stranger: {message}"
        )

        is_scam = privacy_safe_check(session_id, message)

        if not is_scam:
            result = json.dumps({
                "scam_detected": False,
                "reply": None,
                "intelligence": {}
            }, indent=2)
        else:
            reply = run_agent(session_id, message)
            report = generate_and_save_report(session_id)
            result = json.dumps({
                "scam_detected": True,
                "reply": reply,
                "intelligence": report
            }, indent=2)

        # Store agent output
        SESSION_HISTORY[session_id].append(
            f"🤖 Agent: {result}"
        )

        history_text = "\n\n".join(SESSION_HISTORY[session_id])

        return (
            result,
            result,
            save_json_to_file(result),
            history_text
        )


    analyze_btn.click(
        fn=ui_handler,
        inputs=[session_input, message_input],
        outputs=[
            agent_output,
            raw_json,
            download_json,
            history_box
        ]
    )


# ======================================================
# ENABLE AUTHORIZE BUTTON IN SWAGGER
# ======================================================
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Agentic HoneyPot API",
        version="1.0.0",
        description="AI-powered honeypot that chats only with scammers",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": API_KEY_NAME,
        }
    }

    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [
                {"ApiKeyAuth": []}
            ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


# ======================================================
# MOUNT GRADIO (MUST BE LAST)
# ======================================================
app = gr.mount_gradio_app(app, gradio_ui, path="/")
