from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class DecisionType(str, Enum):
    CREDIT = "credit"
    FRAUD = "fraud"
    KYC = "kyc"
    LOAN = "loan"

class ApplicantData(BaseModel):
    applicant_id: str
    credit_score: int | None = Field(None, ge=300, le=850)
    annual_income: float | None = None
    loan_amount: float | None = None
    loan_purpose: str | None = None
    existing_debt: float | None = None
    employment_years: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class DecisionRequest(BaseModel):
    session_id: str
    decision_type: DecisionType = DecisionType.CREDIT
    applicant: ApplicantData
    query: str

class DecisionResponse(BaseModel):
    session_id: str
    decision: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    risk_factors: list[str] = Field(default_factory=list)
    retrieved_policies: list[str] = Field(default_factory=list)
    raw_agent_output: str | None = None

class DocumentInput(BaseModel):
    doc_id: str
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class IngestRequest(BaseModel):
    documents: list[DocumentInput]

class IngestResponse(BaseModel):
    message: str
    document_count: int
