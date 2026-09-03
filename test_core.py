from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_intimate_image_retrieval():
    r = client.post("/api/assess", json={
        "description": "Someone shared my private nude image without my consent.",
        "relationship": "stranger",
        "platform": "WhatsApp"
    })
    assert r.status_code == 200
    data = r.json()
    assert "non_consensual_intimate_image" in data["categories"]
    assert any(x["source_id"] == "ZA-CYBERCRIMES-2020" for x in data["retrieved_sources"])

def test_harassment():
    r = client.post("/api/assess", json={
        "description": "My ex-partner keeps harassing and stalking me with constant electronic messages.",
        "relationship": "ex-partner",
        "platform": "WhatsApp"
    })
    data = r.json()
    assert "harassment_or_stalking" in data["categories"]
    assert data["gbv_relevant"] is True
    assert any(x["source_id"] == "ZA-PHA-2011" for x in data["retrieved_sources"])

def test_threat_is_high_urgency():
    r = client.post("/api/assess", json={
        "description": "I received a message threatening to kill me.",
        "relationship": "stranger",
        "platform": "Instagram"
    })
    assert r.json()["urgency"] == "high"

def test_deepfake():
    r = client.post("/api/assess", json={
        "description": "A deepfake video was created of me and posted online.",
        "platform": "TikTok"
    })
    data = r.json()
    assert "deepfake_or_synthetic_media" in data["categories"]
    assert any(x["source_id"] == "ZA-CYBERCRIMES-2020" for x in data["retrieved_sources"])
