FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

LABEL maintainer="yashpatil582@gmail.com" \
      version="0.1.0" \
      description="Fintech AI decisioning agent for real-time credit risk assessment"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
RUN mkdir -p data/faiss_index
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health/ready || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
