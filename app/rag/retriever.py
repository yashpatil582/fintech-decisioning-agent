"""RAG Retriever: FAISS (local/dev) or OpenSearch (production)."""
from __future__ import annotations
import logging
from pathlib import Path
from langchain_core.vectorstores import VectorStoreRetriever
from app.utils.config import settings

logger = logging.getLogger(__name__)
FAISS_INDEX_PATH = Path("data/faiss_index")

SEED_DOCUMENTS = [
    {"title": "Credit Policy — Standard Underwriting Guidelines",
     "content": "Applicants with FICO 720+ and DTI below 36% qualify for Tier-1 rates. Scores 680-719 with DTI below 43% qualify for Tier-2. Scores below 620 require manual review."},
    {"title": "Fraud Prevention Policy v2.3",
     "content": "Applications requesting loan amounts exceeding 5× annual income must be flagged. Velocity checks must be performed for multiple applications within 30 days."},
    {"title": "KYC / AML Compliance Requirements",
     "content": "All applicants must pass CIP checks. PEP screening and OFAC watchlist verification are mandatory. EDD is triggered for high-risk jurisdictions or transactions above $10,000."},
    {"title": "Loan Approval Matrix — Consumer Lending",
     "content": "Auto-approve: credit score ≥750, DTI <36%, verified income, no adverse history. Auto-decline: credit score <580, DTI >55%, recent bankruptcy. Otherwise REFER for review."},
]

def build_retriever() -> VectorStoreRetriever:
    try:
        from langchain_aws import BedrockEmbeddings
        embeddings = BedrockEmbeddings(model_id=settings.bedrock_embedding_model_id, region_name=settings.aws_region)
    except Exception:
        from langchain_community.embeddings import FakeEmbeddings
        logger.warning("BedrockEmbeddings unavailable, using FakeEmbeddings for local dev")
        embeddings = FakeEmbeddings(size=1536)

    if settings.vector_store == "opensearch":
        from langchain_community.vectorstores import OpenSearchVectorSearch
        store = OpenSearchVectorSearch(
            index_name=settings.opensearch_index,
            embedding_function=embeddings,
            opensearch_url=settings.opensearch_url,
            http_auth=(settings.opensearch_user, settings.opensearch_password),
        )
        return store.as_retriever(search_kwargs={"k": 4})

    from langchain_community.vectorstores import FAISS
    if FAISS_INDEX_PATH.exists():
        store = FAISS.load_local(str(FAISS_INDEX_PATH), embeddings, allow_dangerous_deserialization=True)
    else:
        texts = [d["content"] for d in SEED_DOCUMENTS]
        metas = [{"title": d["title"]} for d in SEED_DOCUMENTS]
        store = FAISS.from_texts(texts, embeddings, metadatas=metas)
        FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)
        store.save_local(str(FAISS_INDEX_PATH))
    return store.as_retriever(search_kwargs={"k": 4})
