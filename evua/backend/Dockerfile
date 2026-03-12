FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (git is required by gitpython)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Configure git identity for automated commits
RUN git config --global user.email "evua@system.local" && \
    git config --global user.name "evua-system"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application
COPY app/ ./app/

# The engine is mounted at runtime via Docker volume ./engine:/app/engine
# (see docker-compose.yml).  Set PYTHONPATH so `import engine` resolves.
ENV PYTHONPATH=/app
ENV STORAGE_DIR=/app/storage

# Create persistent storage directories
RUN mkdir -p /app/storage/uploads /app/storage/versions

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
