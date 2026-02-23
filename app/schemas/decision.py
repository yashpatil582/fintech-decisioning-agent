"""Pydantic schemas for decisioning API."""

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class ApplicantProfile(BaseModel):
    applicant_id: str = Field(..., description="Unique applicant identifier")
    annual_income: float = Field(..., ge=0, description="Annual income in USD")
    credit_score: int = Field(..., ge=300, le=850)
    debt_to_income_ratio: float = Field(..., ge=0, le=1)
    employment_years: float = Field(..., ge=0)
    loan_amount_requested: float = Field(..., gt=0)
    loan_purpose: str = Field(..., description="e.g. mortgage, auto, personal")
    existing_defaults: int = Field(default=0, ge=0)


class DecisionRequest(BaseModel):
    applicant: ApplicantProfile
    product_type: Literal["personal_loan", "credit_card", "mortgage", "sme_loan"] = "personal_loan"
    explain: bool = Field(default=True, description="Include reasoning in response")


class DecisionResult(BaseModel):
    applicant_id: str
    decision: Literal["APPROVE", "DECLINE", "REFER"]
    confidence: float = Field(..., ge=0, le=1)
    risk_score: float = Field(..., ge=0, le=100)
    reasoning: str | None = None
    policy_flags: list[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_trace: list[str] = []


class HealthStatus(BaseModel):
    status: str
    bedrock_connected: bool
    vector_store_ready: bool
    version: str = "1.0.0"
