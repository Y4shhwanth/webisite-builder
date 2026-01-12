# AI Website Builder - Setup Guide

## Prerequisites

1. **Docker Desktop**
   - Download: https://www.docker.com/products/docker-desktop
   - Ensure Docker is running before proceeding

2. **OpenRouter API Key** (required)
   - Get from: https://openrouter.ai/keys
   - This provides access to Claude and Gemini models

## Step 1: Configure API Keys

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenRouter API key:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   ```

3. (Optional) Add fallback API keys:
   ```env
   GEMINI_API_KEY=your-gemini-key      # Direct Gemini fallback
   ANTHROPIC_API_KEY=your-anthropic-key # Direct Claude fallback
   ```

## Step 2: Start Services

```bash
docker compose up -d --build
```

This starts 5 services:
- PostgreSQL (database)
- Redis (caching)
- Backend (Django, port 8000)
- AI Engine (FastAPI, port 8001)
- Playwright (DOM editing, port 3001)

## Step 3: Run Database Migrations

Wait 30 seconds for PostgreSQL to initialize, then:

```bash
docker exec ai_website_builder_backend python manage.py migrate
```

## Step 4: Verify Services

Check all services are running:

```bash
docker compose ps
```

Test health endpoints:

```bash
curl http://localhost:8000/health/   # Backend
curl http://localhost:8001/health    # AI Engine
curl http://localhost:3001/health    # Playwright
```

## Step 5: Start Frontend

```bash
cd simple-frontend
python3 -m http.server 3000
```

Or simply open `simple-frontend/index.html` in your browser.

## Step 6: Test the System

1. Enter a Topmate username (e.g., "yashwanth")
2. Select a template
3. Click "Generate Website"
4. Wait 30-60 seconds
5. Preview and edit the generated website

## Troubleshooting

### Services won't start

```bash
docker compose logs -f ai_engine
docker compose restart
```

### API key errors

1. Verify `.env` has correct keys
2. Restart services:
   ```bash
   docker compose down
   docker compose up -d
   ```

### Database issues

Reset database (destroys data):

```bash
docker compose down -v
docker compose up -d --build
docker exec ai_website_builder_backend python manage.py migrate
```

### Playwright not responding

```bash
docker compose up -d --build playwright
docker compose logs playwright
```

## Useful Commands

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f ai_engine

# Restart a service
docker compose restart ai_engine

# Stop all services
docker compose down

# Check resource usage
docker stats
```

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Single HTML file |
| Backend | 8000 | Django REST API |
| AI Engine | 8001 | FastAPI + AI generation/editing |
| Playwright | 3001 | Fast DOM manipulation |
| PostgreSQL | 5433 | Database |
| Redis | 6379 | Caching |

## Model Priority

The system tries models in order:
1. Claude Sonnet 4 (via OpenRouter)
2. Claude 3.5 Sonnet (via OpenRouter)
3. Gemini 2.0 Flash (via OpenRouter)
4. Direct Gemini API (if GEMINI_API_KEY set)
