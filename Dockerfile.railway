FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY ai_engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy AI engine code
COPY ai_engine/ .

# Create directories
RUN mkdir -p /app/generated_websites /app/logs

# Use PORT env var from Railway
ENV PORT=8001
EXPOSE 8001

# Start command - Railway sets PORT env var
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
