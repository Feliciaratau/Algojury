import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import httpx

from .assessment import assess
from .rag import source_map

app = FastAPI(title="AlgoJury Live", version="1.0.0")

class Incident(BaseModel):
    description: str = Field(min_length=3, max_length=10000)
    platform: str = Field(default="", max_length=200)
    relationship: str = Field(default="", max_length=100)
    immediate_danger: bool = False
    consent_status: str = Field(default="unknown", max_length=50)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    return response

@app.get("/")
def index():
    return FileResponse("frontend/index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "algojury", "version": "1.0.0"}

@app.get("/api/sources")
def sources():
    return list(source_map().values())

async def llm_enhance(incident: Incident, result: dict):
    url = os.getenv("ALGOJURY_LLM_URL", "").strip()
    model = os.getenv("ALGOJURY_LLM_MODEL", "").strip()
    if not url or not model:
        return None

    context = []
    for item in result["retrieved_sources"]:
        context.append({
            "source_id": item.get("source_id"),
            "locator": item.get("locator"),
            "text": item.get("text")
        })

    system = (
        "You assist with digital-harm issue spotting. Do not determine guilt, do not invent law, "
        "do not present allegations as facts, and do not give definitive legal advice. "
        "Use only the supplied retrieved passages. Return concise JSON with keys: summary, "
        "uncertainties, evidence_to_preserve, safer_next_steps."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps({
                "incident": incident.model_dump(),
                "deterministic_assessment": result,
                "retrieved_passages": context
            })}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception:
        return None

@app.post("/api/assess")
async def assess_incident(incident: Incident):
    result = assess(incident.model_dump())
    llm = await llm_enhance(incident, result)
    if llm:
        result["llm_assistance"] = llm
        result["llm_mode"] = "local_or_configured"
    else:
        result["llm_mode"] = "deterministic_fallback"
    return JSONResponse(result)
