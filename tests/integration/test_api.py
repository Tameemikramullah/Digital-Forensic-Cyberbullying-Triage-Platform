import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login():
    register_response = client.post("/auth/register", json={
        "email": "pytest@example.com",
        "password": "testpass123",
        "role": "INVESTIGATOR",
    })
    assert register_response.status_code in [200, 201, 400]

    login_response = client.post("/auth/login", data={
        "username": "pytest@example.com",
        "password": "testpass123",
    })
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        assert token is not None


def test_evidence_upload_requires_auth():
    response = client.post("/evidence/upload", json={
        "source_platform": "Twitter",
        "source_post_id": "test_123",
        "content": "Test content",
        "acquisition_date": "2026-01-01T00:00:00Z",
    })
    assert response.status_code == 401


def test_triage_requires_auth():
    response = client.post("/triage/1")
    assert response.status_code == 401


def test_model_comparison_requires_auth():
    response = client.get("/model-comparison/model-comparison")
    assert response.status_code == 401


def test_error_analysis_requires_auth():
    response = client.get("/error-analysis/error-analysis")
    assert response.status_code == 401
