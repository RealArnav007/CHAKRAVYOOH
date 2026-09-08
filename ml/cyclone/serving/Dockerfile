# ==============================================================================
# CHAKRAVYUH CYCLONE INTELLIGENCE SERVICE CONTAINER
# ==============================================================================
# Lightweight CPU-optimized container running the FastAPI replay service 
# and streaming producer engine.
#
# Build:
#   docker build -t chakravyuh-cyclone-service -f ml/cyclone/serving/Dockerfile .
#
# Run (FastAPI Replay Server on Port 8000):
#   docker run -p 8000:8000 chakravyuh-cyclone-service
#
# Run (Live Stream Producer pushing to Harshit's endpoint):
#   docker run --rm \
#     -e CYCLONE_PRODUCER_ENDPOINT=http://host.docker.internal:8080/api/v1/cyclone/intelligence \
#     chakravyuh-cyclone-service \
#     python -m ml.cyclone.export.producer --storm Amphan --mode post --speed 1.0
# ==============================================================================

FROM python:3.11-slim

LABEL maintainer="Chakravyuh ML Operations <ops@chakravyuh.ai>"
LABEL description="Chakravyuh Multi-Modal Cyclone Intelligence & Replay Serving Engine"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    TORCH_DEVICE=cpu

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency locks and install python packages
COPY ml/cyclone/requirements.lock.txt /app/ml/cyclone/requirements.lock.txt
COPY ml/cyclone/requirements.txt /app/ml/cyclone/requirements.txt
RUN pip install --no-cache-dir -r ml/cyclone/requirements.txt fastapi uvicorn httpx

# Copy source tree, configurations, and serialized artifacts
COPY ml/ /app/ml/
COPY config/ /app/config/
COPY artifacts/ /app/artifacts/
COPY replay/ /app/replay/
COPY eval/ /app/eval/
COPY scripts/ /app/scripts/
COPY PRD.md MODEL_CARD.md pyproject.toml /app/

# Expose HTTP service port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Default entrypoint: Start FastAPI Replay & Intelligence Service
CMD ["uvicorn", "ml.cyclone.serving.service:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
