"""
RAG retrieval layer — loads credit policy documents into FAISS
and exposes a retriever for use by the agent.
"""

import os
import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import boto3

logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).parent.parent.parent / "data" / "policy_docs"
INDEX_DIR = Path(__file__).parent.parent.parent / "data" / "faiss_index"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


def _get_embeddings() -> BedrockEmbeddings:
    session = boto3.Session(region_name=AWS_REGION)
    return BedrockEmbeddings(
        client=session.client("bedrock-runtime"),
        model_id="amazon.titan-embed-text-v1",
    )


def build_vector_store(force_rebuild: bool = False) -> FAISS:
    """Build (or load cached) FAISS index from policy documents."""
    embeddings = _get_embeddings()

    if INDEX_DIR.exists() and not force_rebuild:
        logger.info("Loading cached FAISS index from %s", INDEX_DIR)
        return FAISS.load_local(str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True)

    logger.info("Building FAISS index from %s", DOCS_DIR)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    _seed_sample_docs()

    loader = DirectoryLoader(str(DOCS_DIR), glob="**/*.txt", loader_cls=TextLoader)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    splits = splitter.split_documents(docs)

    store = FAISS.from_documents(splits, embeddings)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    store.save_local(str(INDEX_DIR))
    logger.info("FAISS index built: %d chunks", len(splits))
    return store


def get_retriever(k: int = 4):
    """Return a retriever backed by the FAISS vector store."""
    store = build_vector_store()
    return store.as_retriever(search_kwargs={"k": k})


def _seed_sample_docs():
    """Write sample policy documents so the repo works out of the box."""
    policies = {
        "credit_policy.txt": """
CREDIT DECISIONING POLICY v2.1

Minimum Requirements — Personal Loan:
- Credit score >= 650 for standard approval
- Credit score 600-649 triggers manual review (REFER)
- Credit score < 600: automatic decline
- Debt-to-income ratio must not exceed 0.43
- Applicant must have >= 1 year of employment history
- No defaults in the last 24 months

Loan-to-Income Limits:
- Personal loan: max 5x annual income
- Mortgage: max 4x annual income
- SME loan: max 3x annual income
- Credit card: max 30% of annual income as credit limit

Risk Score Bands:
- 0-30: Low risk — APPROVE
- 31-60: Medium risk — APPROVE with conditions
- 61-80: High risk — REFER to underwriter
- 81-100: Very high risk — DECLINE
""",
        "regulatory_guidelines.txt": """
REGULATORY COMPLIANCE GUIDELINES

Fair Lending Act Requirements:
- All decisions must be explainable and documented
- Prohibited basis: race, color, religion, national origin, sex, marital status, age
- Adverse action notices required for all declines within 30 days
- Equal Credit Opportunity Act (ECOA) compliance mandatory

AML / KYC Requirements:
- Identity verification required for loans > $10,000
- Source of funds documentation for loans > $50,000
- Suspicious activity reporting threshold: $5,000

Data Retention:
- All decision records must be retained for 7 years
- Audit logs must be immutable and time-stamped
""",
        "risk_model_guide.txt": """
RISK SCORING METHODOLOGY

Component Weights:
- Payment history: 35%
- Credit utilisation: 30%
- Length of credit history: 15%
- New credit enquiries: 10%
- Credit mix: 10%

Stress Testing:
- Base case: current DTI
- Stress case: DTI + 10% (rate shock scenario)
- Severe case: DTI + 20% (unemployment scenario)

Override Criteria:
- Senior underwriter may override REFER decisions
- DECLINE overrides require credit committee approval
- All overrides must be documented with business justification
""",
    }
    for filename, content in policies.items():
        (DOCS_DIR / filename).write_text(content.strip())
    logger.info("Seeded %d sample policy documents", len(policies))
