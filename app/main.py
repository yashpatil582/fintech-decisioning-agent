"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger(__name__).info("Starting Fintech Decisioning Agent...")
    yield

app = FastAPI(title="Fintech Decisioning Agent", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "fintech-decisioning-agent"}
