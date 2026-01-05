# AI Website Builder - Setup Guide

## 🚀 Quick Start

This guide will help you set up and run the AI Website Builder from scratch.

## Prerequisites

1. **Docker Desktop** (required)
   - Download: https://www.docker.com/products/docker-desktop
   - Ensure Docker is running before proceeding

2. **API Keys** (required)
   - **Anthropic API Key**: Get from https://console.anthropic.com/
   - **Google Gemini API Key**: Get from https://makersuite.google.com/app/apikey

## Step 1: Configure API Keys

1. Open the `.env` file in the project root:
   ```bash
   nano .env
   # or use any text editor
   ```

2. Replace placeholder values with your actual API keys:
   ```env
   ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
   GEMINI_API_KEY=AIzaSyB-your-actual-key-here
   ```

3. Save the file

## Step 2: Start Services

From the project root directory, run:

```bash
docker compose up -d --build
```

This will:
- Build all Docker images (first time takes 5-10 minutes)
- Start 5 services: PostgreSQL, Redis, Backend, AI Engine, Playwright
- Create necessary volumes and networks

## Step 3: Run Database Migrations

Wait 30 seconds for PostgreSQL to fully initialize, then run:

```bash
docker exec ai_website_builder_backend python manage.py migrate
```

Expected output:
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, projects, sessions, users
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying users.0001_initial... OK
  ...
  (33 migrations applied)
```

## Step 4: Verify Services

Check that all services are running:

```bash
docker compose ps
```

All 5 services should show "running" status.

### Check Health Endpoints

```bash
# Backend health
curl http://localhost:8000/health/

# AI Engine health
curl http://localhost:8001/health

# Playwright health
curl http://localhost:3001/health
```

All should return `{"status": "healthy"}` or similar.

## Step 5: Open Frontend

Open the frontend in your browser:

```bash
# macOS
open simple-frontend/index.html

# Linux
xdg-open simple-frontend/index.html

# Windows
start simple-frontend/index.html
```

Or manually open `simple-frontend/index.html` in your browser.

## Step 6: Test the System

1. **Enter a Topmate username** (e.g., "phase", "yashwanth")
2. **Add custom requirements** (optional)
3. **Click "Quick Generate"**
4. **Wait 30-60 seconds** for website generation
5. **Preview the generated website** in the iframe
6. **Edit the website** using natural language (e.g., "Change header to blue")
7. **Download HTML** when satisfied

## Troubleshooting

### Issue: Services won't start

**Solution**:
```bash
# Check Docker is running
docker --version

# View logs
docker compose logs -f ai_engine

# Restart services
docker compose restart
```

### Issue: API key errors

**Error**: `ANTHROPIC_API_KEY not configured`

**Solution**:
1. Check `.env` file has correct API keys
2. Restart services:
   ```bash
   docker compose down
   docker compose up -d
   ```

### Issue: Database migrations fail

**Error**: `relation "users" does not exist`

**Solution**:
```bash
# Reset database (DESTRUCTIVE - deletes all data)
docker compose down -v
docker compose up -d postgres redis
sleep 10
docker compose up -d backend ai_engine playwright
sleep 5
docker exec ai_website_builder_backend python manage.py migrate
```

### Issue: Playwright not responding

**Error**: `Playwright service unavailable`

**Solution**:
```bash
# Rebuild Playwright service
docker compose up -d --build playwright

# Check logs
docker compose logs playwright
```

### Issue: Website generation fails

**Error**: `Failed to fetch profile for username`

**Solution**:
- Verify the Topmate username exists
- Check internet connection
- Try a known username like "phase" or "yashwanth"

### Issue: CORS errors in browser console

**Solution**:
- Ensure frontend is accessing `http://localhost:8000` and `http://localhost:8001`
- Check that services are running: `docker compose ps`
- If using a custom port, update API URLs in `simple-frontend/index.html`

## Stopping Services

To stop all services:

```bash
docker compose down
```

To stop and remove all data (volumes):

```bash
docker compose down -v
```

## Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f ai_engine
docker compose logs -f backend
docker compose logs -f playwright
```

### Check Resource Usage

```bash
docker stats
```

### Access Django Admin

1. Create superuser:
   ```bash
   docker exec -it ai_website_builder_backend python manage.py createsuperuser
   ```

2. Access admin at: http://localhost:8000/admin

## Development

### Making Code Changes

Changes to code will auto-reload in development mode (except Dockerfile changes).

### Rebuilding Services

After changing Docker configuration:

```bash
docker compose up -d --build <service-name>
```

Example:
```bash
docker compose up -d --build ai_engine
```

### Running Tests

```bash
# AI Engine tests
docker exec ai_website_builder_ai_engine pytest tests/ -v

# Backend tests
docker exec ai_website_builder_backend python manage.py test
```

## Architecture Overview

```
┌─────────────────┐
│  Simple Frontend│ (index.html, port 8080)
│   25KB, No deps │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│ Django │ │  FastAPI │
│Backend │ │AI Engine │
│  8000  │ │   8001   │
└───┬────┘ └────┬─────┘
    │           │
    ▼           ▼
┌─────────┐ ┌──────────┐
│PostgreSQL│ │Playwright│
│  Redis  │ │   3001   │
└─────────┘ └──────────┘
```

## Feature Flags

### Enable Claude Agents SDK (Phase 2)

To use the new Claude Agents SDK with autonomous iteration:

1. Edit `.env`:
   ```env
   USE_SDK_AGENTS=true
   ```

2. Restart AI Engine:
   ```bash
   docker compose restart ai_engine
   ```

**Note**: SDK agents are not yet fully implemented. Keep `USE_SDK_AGENTS=false` for now.

## Production Deployment

See `README.md` for production deployment guidelines including:
- Sentry configuration
- Rate limiting
- Health checks
- Monitoring dashboards
- Blue-green deployment strategy

## Support

For issues or questions:
1. Check logs: `docker compose logs -f`
2. Verify services are healthy
3. Review this guide's troubleshooting section
4. Check GitHub issues: https://github.com/topmate/ai-website-builder/issues

## Next Steps

Once everything is working:

1. **Customize the frontend** (`simple-frontend/index.html`)
2. **Add more features** (UX interview, guided mode)
3. **Implement Claude Agents SDK** (Phase 2 of the plan)
4. **Set up production monitoring** (Sentry, logging)
5. **Deploy to production** (AWS, GCP, Azure)

---

**Congratulations! 🎉 Your AI Website Builder is ready to use.**
