import json
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types
from app.config import settings
from app.redactor import PIIRedactor
from app.classifier import EUAIActClassifier

app = FastAPI(
    title="EU AI Guard",
    description="Open-Source EU AI Act Compliance & Guardrail Proxy for LLMs",
    version="1.0.0",
)

redactor = PIIRedactor()
classifier = EUAIActClassifier()
llm_client = (
    genai.Client(api_key=settings.gemini_api_key)
    if settings.gemini_api_key
    else None
)


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = settings.default_model
    messages: List[Message]
    temperature: Optional[float] = 0.7
    restore_pii_in_response: Optional[bool] = True


def log_audit_event(payload: dict):
    with open(settings.audit_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0", "eu_ai_act_engine": "active"}


@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    request_id = f"eu-guard-{uuid.uuid4().hex[:12]}"
    start_time = time.perf_counter()

    user_messages = [m.content for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="Request must contain a user message.")

    raw_prompt = user_messages[-1]

    sanitized_prompt, pii_map, pii_types = redactor.redact(raw_prompt)
    compliance_result = classifier.evaluate(sanitized_prompt)
    risk_level = compliance_result.get("risk_level", "MINIMAL_RISK")

    if settings.enable_strict_blocking and risk_level == "PROHIBITED":
        log_audit_event({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "action": "BLOCKED",
            "pii_detected": pii_types,
            "compliance": compliance_result,
        })
        raise HTTPException(
            status_code=403,
            detail={
                "error": "EU_AI_ACT_PROHIBITED_PRACTICE",
                "article": compliance_result.get("article_reference"),
                "reason": compliance_result.get("reason"),
            },
        )

    if not llm_client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing on server.")

    response = llm_client.models.generate_content(
        model=request.model,
        contents=sanitized_prompt,
        config=types.GenerateContentConfig(temperature=request.temperature),
    )

    output_text = response.text or ""

    if request.restore_pii_in_response and pii_map:
        output_text = redactor.restore(output_text, pii_map)

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    log_audit_event({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "action": "ALLOWED",
        "model": request.model,
        "pii_detected": pii_types,
        "compliance": compliance_result,
        "latency_ms": latency_ms,
    })

    return {
        "id": request_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": output_text},
                "finish_reason": "stop",
            }
        ],
        "eu_ai_act_audit": {
            "request_id": request_id,
            "pii_redacted_types": pii_types,
            "risk_classification": compliance_result,
            "latency_ms": latency_ms,
        },
    }
