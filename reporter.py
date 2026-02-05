import json
import os
import time
import re
from memory import get_history
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)


def generate_and_save_report(session_id: str):
    history = get_history(session_id)
    text = " ".join(msg["content"] for msg in history)

    report = {
        "session_id": session_id,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_messages": len(history),
        "bank_accounts": re.findall(r"\b\d{9,18}\b", text),
        "upi_ids": re.findall(r"[a-zA-Z0-9.\-_]+@[a-zA-Z]+", text),
        "urls": re.findall(r"https?://\S+", text),
        "conversation": history
    }

    # 1️⃣ JSON
    json_path = os.path.join(REPORT_DIR, f"{session_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # 2️⃣ HTML timeline
    generate_html_timeline(report, session_id)

    # 3️⃣ PDF timeline
    generate_pdf_timeline(report, session_id)

    return report


def generate_html_timeline(report, session_id):
    rows = []

    for msg in report["conversation"]:
        icon = "🧑" if msg["role"] == "scammer" else "🤖"
        rows.append(
            f"<p><b>{icon} {msg['role'].title()}:</b> {msg['content']}</p>"
        )

    html = f"""
    <html>
    <head>
        <title>Scam Timeline</title>
        <style>
            body {{ font-family: Arial; background:#f4f4f4; }}
            .box {{ background:white; padding:20px; max-width:800px; margin:auto; }}
        </style>
    </head>
    <body>
        <div class="box">
            <h2>Scam Conversation Timeline</h2>
            <p><b>Session:</b> {session_id}</p>
            <p><b>Generated:</b> {report['generated_at']}</p>
            <hr>
            {''.join(rows)}
        </div>
    </body>
    </html>
    """

    path = os.path.join(REPORT_DIR, f"{session_id}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def generate_pdf_timeline(report, session_id):
    path = os.path.join(REPORT_DIR, f"{session_id}.pdf")
    c = canvas.Canvas(path, pagesize=A4)

    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Scam Conversation Timeline")
    y -= 25

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Session: {session_id}")
    y -= 15
    c.drawString(40, y, f"Generated: {report['generated_at']}")
    y -= 30

    for msg in report["conversation"]:
        if y < 80:
            c.showPage()
            y = height - 50

        label = "Scammer:" if msg["role"] == "scammer" else "Agent:"
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, label)
        y -= 12

        c.setFont("Helvetica", 10)
        text = c.beginText(50, y)
        for line in msg["content"].split("\n"):
            text.textLine(line)
            y -= 12
        c.drawText(text)
        y -= 10

    c.save()
