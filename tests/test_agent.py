"""
Test suite for the Fintech Decisioning Agent.
Covers tools, policy logic, and API endpoints.
Uses pytest + pytest-asyncio.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.agents.tools import calculate_risk_score, check_policy_compliance, lookup_regulatory_requirement
from app.schemas.decision import ApplicantProfile, DecisionRequest


# ─── Tool unit tests ──────────────────────────────────────────────────────────

class TestCalculateRiskScore:
    def test_low_risk_applicant(self):
        result = calculate_risk_score.invoke({
            "credit_score": 780,
            "debt_to_income_ratio": 0.15,
            "employment_years": 5.0,
            "existing_defaults": 0,
            "loan_to_income_ratio": 2.0,
        })
        assert result["risk_score"] <= 30
        assert result["risk_band"] == "LOW"

    def test_high_risk_applicant(self):
        result = calculate_risk_score.invoke({
            "credit_score": 550,
            "debt_to_income_ratio": 0.45,
            "employment_years": 0.5,
            "existing_defaults": 2,
            "loan_to_income_ratio": 6.0,
        })
        assert result["risk_score"] >= 61
        assert result["risk_band"] in ("HIGH", "VERY_HIGH")

    def test_medium_risk_applicant(self):
        result = calculate_risk_score.invoke({
            "credit_score": 660,
            "debt_to_income_ratio": 0.30,
            "employment_years": 2.0,
            "existing_defaults": 0,
            "loan_to_income_ratio": 3.5,
        })
        assert 31 <= result["risk_score"] <= 60
        assert result["risk_band"] == "MEDIUM"

    def test_score_bounded_0_to_100(self):
        result = calculate_risk_score.invoke({
            "credit_score": 300,
            "debt_to_income_ratio": 1.0,
            "employment_years": 0,
            "existing_defaults": 10,
            "loan_to_income_ratio": 10.0,
        })
        assert 0 <= result["risk_score"] <= 100


class TestPolicyCompliance:
    def test_clean_application_passes(self):
        result = check_policy_compliance.invoke({
            "credit_score": 720,
            "debt_to_income_ratio": 0.30,
            "loan_amount": 20_000,
            "annual_income": 80_000,
            "existing_defaults": 0,
            "product_type": "personal_loan",
        })
        assert result["passes_policy"] is True
        assert result["hard_decline"] is False
        assert result["flags"] == []

    def test_low_credit_score_hard_decline(self):
        result = check_policy_compliance.invoke({
            "credit_score": 580,
            "debt_to_income_ratio": 0.25,
            "loan_amount": 10_000,
            "annual_income": 60_000,
            "existing_defaults": 0,
            "product_type": "personal_loan",
        })
        assert result["hard_decline"] is True
        assert "CREDIT_SCORE_BELOW_MINIMUM" in result["flags"]

    def test_dti_exceeds_limit(self):
        result = check_policy_compliance.invoke({
            "credit_score": 700,
            "debt_to_income_ratio": 0.50,
            "loan_amount": 15_000,
            "annual_income": 70_000,
            "existing_defaults": 0,
            "product_type": "personal_loan",
        })
        assert "DTI_EXCEEDS_LIMIT" in result["flags"]
        assert result["hard_decline"] is True

    def test_loan_to_income_flag(self):
        result = check_policy_compliance.invoke({
            "credit_score": 720,
            "debt_to_income_ratio": 0.28,
            "loan_amount": 500_000,
            "annual_income": 60_000,
            "existing_defaults": 0,
            "product_type": "personal_loan",
        })
        # 500k / 60k = 8.3x — exceeds 5x limit
        assert any("LOAN_TO_INCOME" in f for f in result["flags"])

    def test_refer_band_credit_score(self):
        result = check_policy_compliance.invoke({
            "credit_score": 625,
            "debt_to_income_ratio": 0.30,
            "loan_amount": 10_000,
            "annual_income": 60_000,
            "existing_defaults": 0,
            "product_type": "personal_loan",
        })
        assert "CREDIT_SCORE_REFER_BAND" in result["flags"]
        assert result["hard_decline"] is False  # soft flag only


class TestRegulatoryTool:
    def test_personal_loan_us(self):
        result = lookup_regulatory_requirement.invoke({
            "product_type": "personal_loan",
            "jurisdiction": "US",
        })
        assert "ECOA" in result or "FCRA" in result

    def test_unknown_jurisdiction_returns_fallback(self):
        result = lookup_regulatory_requirement.invoke({
            "product_type": "personal_loan",
            "jurisdiction": "UNKNOWN",
        })
        assert "compliance" in result.lower()


# ─── Schema validation tests ──────────────────────────────────────────────────

class TestSchemas:
    def test_valid_applicant_profile(self):
        profile = ApplicantProfile(
            applicant_id="AP001",
            annual_income=75_000,
            credit_score=720,
            debt_to_income_ratio=0.28,
            employment_years=3.0,
            loan_amount_requested=15_000,
            loan_purpose="home improvement",
        )
        assert profile.applicant_id == "AP001"

    def test_credit_score_bounds(self):
        with pytest.raises(Exception):
            ApplicantProfile(
                applicant_id="AP002",
                annual_income=50_000,
                credit_score=200,  # invalid — below 300
                debt_to_income_ratio=0.25,
                employment_years=2.0,
                loan_amount_requested=10_000,
                loan_purpose="auto",
            )


# ─── API integration tests (mocked agent) ─────────────────────────────────────

@pytest.fixture
def client():
    """Return a TestClient with a mocked agent injected."""
    from app.main import app

    mock_agent = AsyncMock()
    from app.schemas.decision import DecisionResult
    from datetime import datetime

    mock_agent.decide.return_value = DecisionResult(
        applicant_id="AP001",
        decision="APPROVE",
        confidence=0.87,
        risk_score=22.5,
        reasoning="Clean application: credit score 720, DTI 0.28, no defaults.",
        policy_flags=[],
        timestamp=datetime.utcnow(),
        agent_trace=[],
    )

    app.state.agent = mock_agent
    return TestClient(app, raise_server_exceptions=False)


def test_decide_endpoint_approve(client):
    payload = {
        "applicant": {
            "applicant_id": "AP001",
            "annual_income": 75000,
            "credit_score": 720,
            "debt_to_income_ratio": 0.28,
            "employment_years": 3.0,
            "loan_amount_requested": 15000,
            "loan_purpose": "home improvement",
        },
        "product_type": "personal_loan",
        "explain": True,
    }
    response = client.post("/api/v1/decide", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "APPROVE"
    assert "applicant_id" in data
    assert 0 <= data["confidence"] <= 1


def test_products_endpoint(client):
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    assert "personal_loan" in response.json()["products"]


def test_health_endpoint_structure(client):
    with patch("app.api.health.ping_bedrock", return_value=True):
        response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "bedrock_connected" in data
