"""FastAPI route tests — agent and ingestor are mocked, no AWS calls."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import DecisionResponse

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_response():
    return DecisionResponse(session_id="s1", decision="APPROVE", confidence=0.91,
                            reasoning="Strong profile.", risk_factors=[], retrieved_policies=[])

class TestHealth:
    def test_ok(self, client):
        assert client.get("/health").json()["status"] == "ok"

class TestDecide:
    def test_success(self, client, mock_response):
        mock_agent = MagicMock(); mock_agent.run = AsyncMock(return_value=mock_response); mock_agent.tools = []
        with patch("app.api.routes.get_agent", return_value=mock_agent):
            r = client.post("/api/v1/decide", json={"session_id": "s1", "decision_type": "credit",
                "applicant": {"applicant_id": "A1", "credit_score": 760, "annual_income": 95000.0, "loan_amount": 25000.0},
                "query": "Approve?"})
        assert r.status_code == 200 and r.json()["decision"] == "APPROVE"

    def test_missing_fields_422(self, client):
        assert client.post("/api/v1/decide", json={"session_id": "x"}).status_code == 422

    def test_agent_error_500(self, client):
        mock_agent = MagicMock(); mock_agent.run = AsyncMock(side_effect=RuntimeError("boom")); mock_agent.tools = []
        with patch("app.api.routes.get_agent", return_value=mock_agent):
            r = client.post("/api/v1/decide", json={"session_id": "e", "decision_type": "credit",
                "applicant": {"applicant_id": "A2"}, "query": "fail"})
        assert r.status_code == 500

class TestIngest:
    def test_queued(self, client):
        with patch("app.api.routes.get_ingestor", return_value=MagicMock()):
            r = client.post("/api/v1/ingest", json={"documents": [{"doc_id": "D1", "title": "T", "content": "..."}]})
        assert r.status_code == 200 and r.json()["document_count"] == 1

class TestToolsList:
    def test_lists_tools(self, client):
        mock_tool = MagicMock(); mock_tool.name = "policy_retriever"
        mock_agent = MagicMock(); mock_agent.tools = [mock_tool]
        with patch("app.api.routes.get_agent", return_value=mock_agent):
            r = client.get("/api/v1/agent/tools")
        assert "policy_retriever" in r.json()["tools"]
