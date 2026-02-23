"""Agent Tools: policy_retriever, credit_scorer, dti_calculator, fraud_check."""
from __future__ import annotations
import logging
from langchain.tools import tool

logger = logging.getLogger(__name__)

def build_tools(retriever) -> list:
    @tool
    def policy_retriever(query: str) -> str:
        """Retrieve relevant financial policy documents. Use before any credit/fraud decision."""
        docs = retriever.invoke(query)
        if not docs:
            return "No relevant policy documents found."
        results = []
        for i, doc in enumerate(docs[:4], 1):
            title = doc.metadata.get("title", f"Document {i}")
            results.append(f"[{i}] {title}:\n{doc.page_content[:500]}")
        return "\n\n".join(results)

    @tool
    def credit_scorer(credit_score: int, annual_income: float, loan_amount: float, existing_debt: float = 0.0) -> str:
        """Evaluate credit risk based on score, income, loan amount, and existing debt. Returns risk tier and key metrics."""
        dti = (existing_debt + loan_amount) / annual_income if annual_income > 0 else 1.0
        ltv = loan_amount / annual_income if annual_income > 0 else 1.0
        if credit_score >= 750 and dti < 0.36:
            tier = "LOW_RISK"
        elif credit_score >= 680 and dti < 0.43:
            tier = "MEDIUM_RISK"
        elif credit_score >= 620:
            tier = "HIGH_RISK"
        else:
            tier = "VERY_HIGH_RISK"
        return (f"Risk Tier: {tier}\nCredit Score: {credit_score}\n"
                f"Debt-to-Income Ratio: {dti:.2%}\nLoan-to-Income Ratio: {ltv:.2%}\n"
                f"Recommendation: {'Proceed' if tier in ('LOW_RISK','MEDIUM_RISK') else 'Caution'}")

    @tool
    def dti_calculator(monthly_income: float, monthly_existing_debt: float, proposed_monthly_payment: float) -> str:
        """Calculate front-end and back-end debt-to-income ratios. Thresholds: front-end <28%, back-end <43%."""
        if monthly_income <= 0:
            return "Invalid monthly income."
        front_end = proposed_monthly_payment / monthly_income
        back_end = (monthly_existing_debt + proposed_monthly_payment) / monthly_income
        front_ok = front_end < 0.28
        back_ok = back_end < 0.43
        return (f"Front-end DTI: {front_end:.2%} ({'OK' if front_ok else 'Exceeds 28% threshold'})\n"
                f"Back-end DTI:  {back_end:.2%} ({'OK' if back_ok else 'Exceeds 43% threshold'})\n"
                f"Overall DTI Assessment: {'PASS' if front_ok and back_ok else 'FAIL'}")

    @tool
    def fraud_check(applicant_id: str, loan_amount: float, annual_income: float) -> str:
        """Run lightweight fraud signal checks on an application."""
        signals = []
        if loan_amount > annual_income * 5:
            signals.append("Loan amount >5x annual income — unusually high")
        if annual_income < 15_000:
            signals.append("Annual income below poverty threshold")
        if loan_amount > 500_000:
            signals.append("High-value loan — requires enhanced due diligence")
        logger.info("Fraud velocity check for applicant_id=%s", applicant_id)
        if not signals:
            return "No fraud signals detected. Application appears clean."
        return "Fraud signals detected:\n" + "\n".join(f"- {s}" for s in signals)

    return [policy_retriever, credit_scorer, dti_calculator, fraud_check]
