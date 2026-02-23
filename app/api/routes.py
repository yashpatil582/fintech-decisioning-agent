"""API routes: /decide, /ingest, /agent/tools"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import DecisionRequest, DecisionResponse, IngestRequest, IngestResponse

logger = logging.getLogger(__name__)
router = APIRouter()
_agent = None
_ingestor = None

def get_agent():
    global _agent
    if _agent is None:
        from app.agents.decisioning_agent import DecisioningAgent
        _agent = DecisioningAgent()
    return _agent

def get_ingestor():
    global _ingestor
    if _ingestor is None:
        from app.rag.ingestion import RagIngestionService
        _ingestor = RagIngestionService()
    return _ingestor

@router.post("/decide", response_model=DecisionResponse)
async def make_decision(request: DecisionRequest) -> DecisionResponse:
    """Run the LangChain decisioning agent on a financial application."""
    try:
        return await get_agent().run(request)
    except Exception as exc:
        logger.exception("Agent execution failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(request: IngestRequest, background_tasks: BackgroundTasks) -> IngestResponse:
    """Ingest policy documents into the vector store (background task)."""
    background_tasks.add_task(get_ingestor().ingest, request.documents)
    return IngestResponse(message=f"Ingestion queued for {len(request.documents)} document(s).", document_count=len(request.documents))

@router.get("/agent/tools")
async def list_tools():
    """List all tools registered with the decisioning agent."""
    return {"tools": [t.name for t in get_agent().tools]}
