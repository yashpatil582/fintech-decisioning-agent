"""RAG Ingestion Service: chunks documents and upserts into vector store."""
from __future__ import annotations
import logging
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.models.schemas import DocumentInput
from app.utils.config import settings

logger = logging.getLogger(__name__)
FAISS_INDEX_PATH = Path("data/faiss_index")

class RagIngestionService:
    def __init__(self):
        try:
            from langchain_aws import BedrockEmbeddings
            self.embeddings = BedrockEmbeddings(model_id=settings.bedrock_embedding_model_id, region_name=settings.aws_region)
        except Exception:
            from langchain_community.embeddings import FakeEmbeddings
            self.embeddings = FakeEmbeddings(size=1536)
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

    def ingest(self, documents: list[DocumentInput]) -> int:
        texts, metadatas = [], []
        for doc in documents:
            for chunk in self.splitter.split_text(doc.content):
                texts.append(chunk)
                metadatas.append({"doc_id": doc.doc_id, "title": doc.title, **doc.metadata})
        if not texts:
            return 0
        from langchain_community.vectorstores import FAISS
        if FAISS_INDEX_PATH.exists():
            store = FAISS.load_local(str(FAISS_INDEX_PATH), self.embeddings, allow_dangerous_deserialization=True)
            store.add_texts(texts, metadatas=metadatas)
        else:
            store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
        FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)
        store.save_local(str(FAISS_INDEX_PATH))
        logger.info("Ingested %d chunks from %d documents", len(texts), len(documents))
        return len(texts)
