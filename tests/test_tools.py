"""Unit tests for agent tools — no AWS credentials required."""
import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document

def _mock_retriever(docs):
    r = MagicMock()
    r.invoke.return_value = docs
    return r

class TestPolicyRetriever:
    def test_returns_formatted_docs(self):
        from app.agents.tools import build_tools
        docs = [Document(page_content="Loan policy content.", metadata={"title": "Loan Policy"})]
        tool = next(t for t in build_tools(_mock_retriever(docs)) if t.name == "policy_retriever")
        result = tool.invoke({"query": "credit score requirements"})
        assert "Loan Policy" in result and "Loan policy content." in result

    def test_empty_retrieval(self):
        from app.agents.tools import build_tools
        tool = next(t for t in build_tools(_mock_retriever([])) if t.name == "policy_retriever")
        assert "No relevant" in tool.invoke({"query": "anything"})

class TestCreditScorer:
    def _tool(self):
        from app.agents.tools import build_tools
        return next(t for t in build_tools(_mock_retriever([])) if t.name == "credit_scorer")

    def test_low_risk(self):
        assert "LOW_RISK" in self._tool().invoke({"credit_score": 780, "annual_income": 120000.0, "loan_amount": 30000.0, "existing_debt": 10000.0})

    def test_high_risk(self):
        result = self._tool().invoke({"credit_score": 610, "annual_income": 40000.0, "loan_amount": 35000.0, "existing_debt": 15000.0})
        assert "HIGH_RISK" in result or "VERY_HIGH_RISK" in result

    def test_dti_in_output(self):
        assert "Debt-to-Income" in self._tool().invoke({"credit_score": 700, "annual_income": 80000.0, "loan_amount": 20000.0})

class TestDtiCalculator:
    def _tool(self):
        from app.agents.tools import build_tools
        return next(t for t in build_tools(_mock_retriever([])) if t.name == "dti_calculator")

    def test_passing_dti(self):
        assert "PASS" in self._tool().invoke({"monthly_income": 10000.0, "monthly_existing_debt": 500.0, "proposed_monthly_payment": 1000.0})

    def test_failing_dti(self):
        assert "FAIL" in self._tool().invoke({"monthly_income": 5000.0, "monthly_existing_debt": 2000.0, "proposed_monthly_payment": 1500.0})

    def test_zero_income(self):
        assert "Invalid" in self._tool().invoke({"monthly_income": 0.0, "monthly_existing_debt": 0.0, "proposed_monthly_payment": 500.0})

class TestFraudCheck:
    def _tool(self):
        from app.agents.tools import build_tools
        return next(t for t in build_tools(_mock_retriever([])) if t.name == "fraud_check")

    def test_clean_application(self):
        assert "No fraud signals" in self._tool().invoke({"applicant_id": "APP-001", "loan_amount": 20000.0, "annual_income": 80000.0})

    def test_high_loan_to_income(self):
        result = self._tool().invoke({"applicant_id": "APP-002", "loan_amount": 600000.0, "annual_income": 50000.0})
        assert "Fraud signals" in result

    def test_high_value_loan(self):
        result = self._tool().invoke({"applicant_id": "APP-003", "loan_amount": 600000.0, "annual_income": 200000.0})
        assert "enhanced due diligence" in result.lower()
