# Fintech Decisioning Agent

![CI](https://github.com/yashpatil582/fintech-decisioning-agent/actions/workflows/ci-cd.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)

A production-grade AI decisioning service for real-time credit risk assessment. Built with **LangChain** agents on **AWS Bedrock**, a **FastAPI** backend, **FAISS** vector store for RAG-based policy retrieval, and deployed on **EKS** via **GitHub Actions** CI/CD.

## Architecture

```
Client → FastAPI (EKS)
              │
     DecisioningAgent (LangChain AgentExecutor)
         ├── Tool: calculate_risk_score
         ├── Tool: check_policy_compliance
         └── Tool: lookup_regulatory_requirement
              │
     ┌────────┴──────────┐
     AWS Bedrock LLM    FAISS RAG
     (Claude 3 Sonnet)  (policy docs)
```

## Features

- **APPROVE / DECLINE / REFER** with explainable reasoning
- **RAG policy engine** — credit policies retrieved per request via FAISS + Bedrock Embeddings
- **LangChain tool-calling agent** on AWS Bedrock (Claude 3 Sonnet)
- **Hard policy gates** — instant decline on DTI > 43%, credit score < 600
- **Risk scoring** — 0–100 score across LOW / MEDIUM / HIGH / VERY_HIGH bands
- **EKS deployment** — HPA autoscaling + CloudWatch observability + GitHub Actions CI/CD

## Quickstart

```bash
git clone https://github.com/yashpatil582/fintech-decisioning-agent
cd fintech-decisioning-agent

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1

uvicorn app.main:app --reload
# → Swagger UI: http://localhost:8000/docs
```

## Run Tests

```bash
pytest tests/ --cov=app --cov-report=term-missing -v
```

## API

**POST /api/v1/decide**

```json
{
  "applicant": {
    "applicant_id": "AP001",
    "annual_income": 75000,
    "credit_score": 720,
    "debt_to_income_ratio": 0.28,
    "employment_years": 3.0,
    "loan_amount_requested": 15000,
    "loan_purpose": "home improvement"
  },
  "product_type": "personal_loan",
  "explain": true
}
```

**Response:**
```json
{
  "decision": "APPROVE",
  "confidence": 0.91,
  "risk_score": 18.5,
  "reasoning": "Credit score 720 and DTI 28% are well within policy limits...",
  "policy_flags": []
}
```

## Deployment

GitHub Actions pipeline (`.github/workflows/ci-cd.yml`) automates:
1. **Test** — pytest with 80% coverage gate
2. **Build** — Docker image pushed to Amazon ECR
3. **Deploy** — `kubectl apply` to EKS
4. **Smoke test** — `/health/ready` probe

Required secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | AWS Bedrock — Claude 3 Sonnet |
| Agent | LangChain tool-calling agent |
| Vector Store | FAISS + Bedrock Titan Embeddings |
| API | FastAPI + Uvicorn |
| Container | Docker |
| Orchestration | Kubernetes EKS + HPA |
| CI/CD | GitHub Actions |
| Observability | AWS CloudWatch |
| Testing | pytest + pytest-cov |

## Project Structure

```
fintech-decisioning-agent/
├── app/
│   ├── main.py              # FastAPI app + health endpoints
│   ├── agent.py             # LangChain decisioning agent
│   ├── tools.py             # Risk score, policy, regulatory tools
│   ├── rag.py               # FAISS vector store + RAG retrieval
│   └── models.py            # Pydantic request/response schemas
├── data/
│   └── faiss_index/         # Persisted FAISS policy index
├── infra/
│   └── k8s/                 # Kubernetes manifests (EKS)
├── tests/                   # pytest test suite
├── scripts/                 # Utility scripts
├── Dockerfile
├── pyproject.toml
└── .github/workflows/       # CI/CD pipeline
```

## License

MIT © 2025 [Yash Patil](https://github.com/yashpatil582)
