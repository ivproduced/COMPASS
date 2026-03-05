# ============================================================
# COMPASS Backend — Cloud Run Dockerfile
# ============================================================
FROM python:3.12-slim AS base

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY backend/ ./backend/

# Knowledge base (corpus files, if present)
COPY backend/knowledge/ ./backend/knowledge/

# ---- Runtime ----
ENV ENV=production
ENV HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080

# Use exec form for graceful shutdown signal passing
CMD ["python", "-m", "uvicorn", "backend.app:app", \
     "--host", "0.0.0.0", "--port", "8080", \
     "--workers", "1", "--log-level", "info"]
