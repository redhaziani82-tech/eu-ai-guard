from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.auth import verify_customer_api_key

client = TestClient(app)

def test_dashboard_loads():
    res = client.get("/")
    assert res.status_code == 200
    assert "EU AI Guard" in res.text

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200

def test_preview_redact_endpoint():
    res = client.post("/api/preview-redact", json={
        "text": "Email alice@company.ie and PPSN 1234567T"
    })
    assert res.status_code == 200
    data = res.json()
    assert "[EMAIL_1]" in data["redacted_text"]
    assert "[PPSN_OR_TAX_ID_1]" in data["redacted_text"]
    assert "EMAIL" in data["detected_types"]
    assert "PPSN_OR_TAX_ID" in data["detected_types"]

def test_chat_completions_requires_auth():
    def reject_unauthenticated():
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    app.dependency_overrides[verify_customer_api_key] = reject_unauthenticated
    try:
        res = client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "Hello"}]
        })
        assert res.status_code == 401
    finally:
        app.dependency_overrides.clear()
