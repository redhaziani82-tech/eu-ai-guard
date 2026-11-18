from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.redactor import PIIRedactor

router = APIRouter()
redactor = PIIRedactor()

class PreviewRequest(BaseModel):
    text: str

@router.post("/api/preview-redact")
def preview_redact(payload: PreviewRequest):
    redacted_text, mapping, detected_types = redactor.redact(payload.text)
    return {
        "redacted_text": redacted_text,
        "detected_types": detected_types,
        "placeholders_count": len(mapping),
    }

@router.get("/", response_class=HTMLResponse)
def dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>EU AI Guard — Compliance Proxy</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 16px; }
    .container { max-width: 720px; margin: 0 auto; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 18px; margin-bottom: 16px; }
    h1 { font-size: 1.4rem; margin: 0 0 6px; color: #38bdf8; }
    h2 { font-size: 1.05rem; margin: 0 0 10px; color: #e2e8f0; }
    p { color: #94a3b8; font-size: 0.9rem; margin: 0 0 12px; }
    textarea, input { width: 100%; box-sizing: border-box; background: #0f172a; color: #f8fafc; border: 1px solid #475569; border-radius: 8px; padding: 10px; font-size: 0.95rem; margin-bottom: 10px; }
    button { background: #0284c7; color: #fff; border: none; border-radius: 8px; padding: 10px 16px; font-weight: 600; cursor: pointer; width: 100%; }
    button:hover { background: #0369a1; }
    pre { background: #020617; border: 1px solid #334155; border-radius: 8px; padding: 12px; overflow-x: auto; font-size: 0.85rem; color: #34d399; white-space: pre-wrap; }
    .badge { display: inline-block; background: #065f46; color: #6ee7b7; padding: 3px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <span class="badge">EU AI Act + GDPR Ready</span>
      <h1>EU AI Guard</h1>
      <p>Zero-trust PII redaction and EU AI Act risk classification proxy for LLM workflows.</p>
    </div>

    <div class="card">
      <h2>1. Live GDPR PII Redaction Sandbox (No API Key Needed)</h2>
      <p>Test automatic masking of Emails, IBANs, Phone Numbers, and Irish PPSN / Tax IDs before data leaves the EU.</p>
      <textarea id="piiInput" rows="3">Contact John at john.doe@example.ie, PPSN 1234567AB, IBAN IE29AIBK93115212345678, or +353 87 123 4567.</textarea>
      <button onclick="testRedact()">Scan &amp; Redact PII</button>
      <pre id="piiOutput">Click "Scan & Redact PII" to preview...</pre>
    </div>

    <div class="card">
      <h2>2. Full EU AI Act + Gemini Proxy Playground</h2>
      <p>Send an authenticated request to <code>POST /v1/chat/completions</code>.</p>
      <input id="apiKey" type="password" placeholder="Bearer token (e.g. eug_live_...)" />
      <textarea id="chatInput" rows="2">Draft an HR candidate screening prompt for a software engineer role.</textarea>
      <button onclick="testChat()">Run Guarded Completion</button>
      <pre id="chatOutput">Response &amp; EU AI Act audit metadata will appear here...</pre>
    </div>
  </div>
  <script>
    async function testRedact() {
      const text = document.getElementById("piiInput").value;
      const res = await fetch("/api/preview-redact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      document.getElementById("piiOutput").textContent = JSON.stringify(await res.json(), null, 2);
    }
    async function testChat() {
      const key = document.getElementById("apiKey").value.trim();
      const content = document.getElementById("chatInput").value;
      const res = await fetch("/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": key.startsWith("Bearer ") ? key : "Bearer " + key
        },
        body: JSON.stringify({ messages: [{ role: "user", content }] })
      });
      document.getElementById("chatOutput").textContent = JSON.stringify(await res.json(), null, 2);
    }
  </script>
</body>
</html>"""
