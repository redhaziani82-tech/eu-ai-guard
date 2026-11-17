from fastapi import Header, HTTPException
from supabase import create_client, Client
from app.config import settings


def get_supabase() -> Client | None:
    if settings.supabase_url and settings.supabase_service_key:
        return create_client(settings.supabase_url, settings.supabase_service_key)
    return None


def verify_customer_api_key(authorization: str = Header(None)) -> dict:
    sb = get_supabase()
    if not sb:
        return {"customer_id": None, "plan": "local_open"}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header. Expected: Bearer eug_live_...",
        )

    token = authorization.replace("Bearer ", "").strip()

    key_res = (
        sb.table("api_keys")
        .select("customer_id, is_active, customers(id, email, plan, status, monthly_quota, requests_used)")
        .eq("api_key", token)
        .eq("is_active", True)
        .execute()
    )

    if not key_res.data:
        raise HTTPException(status_code=401, detail="Invalid or revoked EU AI Guard API key.")

    record = key_res.data[0]
    customer = record.get("customers") or {}

    if customer.get("status") != "active":
        raise HTTPException(status_code=403, detail="Subscription inactive. Please update billing.")

    if customer.get("requests_used", 0) >= customer.get("monthly_quota", 0):
        raise HTTPException(status_code=429, detail="Monthly API quota exceeded. Please upgrade plan.")

    return customer
