# AI Website Builder - Project Summary

## Overview

AI-powered website builder that generates stunning portfolio websites from Topmate profiles. Uses Claude/Gemini via OpenRouter API with a production-grade system prompt that enforces anti-slop design principles. Built with a microservices architecture featuring Django backend, FastAPI AI engine, and Playwright for fast DOM manipulation.

**Repository**: https://github.com/Y4shhwanth/webisite-builder

## Current Status: Working

- Website generation from Topmate profiles
- 5 template styles available
- Model fallback chain (Claude → Gemini)
- Proper section ordering (Nav → Hero → About → Services → Testimonials → CTA → Footer)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI Website Builder                    │
└─────────────────────────────────────────────────────────┘

  Simple Frontend (Port 3000)
           │
    ┌──────┴──────┐
    ▼             ▼
Django Backend   FastAPI AI Engine
(Port 8000)     (Port 8001)
    │                 │
    ▼                 ▼
PostgreSQL        Playwright Service
  Redis          (Port 3001)
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Single HTML file, served via Python HTTP server |
| Backend | 8000 | Django REST API for projects and users |
| AI Engine | 8001 | FastAPI service for AI generation/editing |
| Playwright | 3001 | Node.js service for fast DOM manipulation |
| PostgreSQL | 5433 | Database |
| Redis | 6379 | Caching |

---

## Tech Stack

- **AI Models**:
  - Primary: `anthropic/claude-sonnet-4` (via OpenRouter)
  - Fallback 1: `anthropic/claude-3.5-sonnet`
  - Fallback 2: `google/gemini-2.0-flash-001`
  - Final Fallback: Direct Gemini API
- **Backend**: Django 5.0 with Django REST Framework
- **AI Engine**: FastAPI with async support
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **DOM Editor**: Playwright (Chromium)
- **Frontend**: Vanilla JavaScript (no framework)
- **Generated Sites**:
  - Tailwind CSS v4 (via CDN with @theme config)
  - Alpine.js for interactivity
  - Google Fonts (custom typography)
  - Phosphor/Remix Icons
- **Containerization**: Docker Compose

---

## Features

### Website Generation
- One-click portfolio generation from Topmate profile via Galactus API
- 5 template styles:
  - Modern Minimal (clean, whitespace-focused)
  - Bold & Creative (vibrant, dynamic)
  - Professional Corporate (trust-building)
  - Dark & Elegant (sophisticated dark theme)
  - Vibrant Gradient (glass effects)
- Production-grade system prompt with anti-slop protocol
- Structured section ordering: Nav → Hero → About → Services → Testimonials → CTA → Footer
- All services rendered with proper CTAs and booking links
- Responsive HTML output with Tailwind CSS v4

### Website Editing
- Natural language edit commands
- Fast simple edits via Playwright (<1s)
- Complex edits via AI regeneration (5-10s)
- Edit history tracking

### Production Features
- Structured JSON logging
- Sentry integration (optional)
- Rate limiting (5/min generation, 10/min edits)
- Health checks for all services
- Docker resource limits
- Auto-restart policies

### System Prompt Features (Anti-Slop Protocol)
- No default Tailwind colors - custom palettes in @theme
- No generic fonts (Arial, Roboto) - expressive Google Fonts
- No placeholder images if real URLs exist in data
- Every interactive element has hover states
- Noise & texture for depth (not flat AI look)
- Extreme typography contrast
- Generous negative space

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/Y4shhwanth/webisite-builder.git
cd webisite-builder
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` and set your API keys:
```env
OPENROUTER_API_KEY=your_key_here
```

### 3. Start Services

```bash
docker compose up -d --build
docker exec ai_website_builder_backend python manage.py migrate
```

### 4. Start Frontend

```bash
cd simple-frontend
python3 -m http.server 3000
```

### 5. Open Browser

Navigate to http://localhost:3000

---

## Project Structure

```
ai-website-builder/
├── backend/                    # Django Backend
│   ├── backend/               # Django settings
│   ├── projects/              # Projects app
│   ├── users/                 # Custom User model
│   ├── Dockerfile
│   └── requirements.txt
│
├── ai_engine/                 # FastAPI AI Engine
│   ├── agents/               # AI agent implementations
│   ├── mcp_tools/            # MCP tool integrations
│   ├── routers/              # API endpoints
│   │   └── build_website.py  # Website generation endpoint
│   ├── services/             # Business logic
│   │   ├── openrouter_website_generator.py  # Main generator with fallback
│   │   ├── builder_system_prompt.py         # Production system prompt
│   │   └── llm_response_handler.py          # Response cleaning
│   ├── config.py             # Settings & feature flags
│   ├── main.py               # FastAPI app
│   └── Dockerfile
│
├── playwright/                # Playwright Service
│   ├── server.js             # Express + Playwright
│   ├── Dockerfile
│   └── package.json
│
├── simple-frontend/           # Frontend
│   └── index.html
│
├── docker-compose.yml
├── .env.example
├── README.md
└── PROJECT_SUMMARY.md
```

---

## API Reference

### AI Engine (Port 8001)

**Get Templates**
```bash
GET /api/build/templates
```

**Generate Website**
```bash
POST /api/build/website
Content-Type: application/json

{
  "username": "yashwanth",
  "user_prompt": "Focus on consulting services",
  "template_id": "modern-minimal"  # or: bold-creative, professional-corporate, dark-elegant, vibrant-gradient
}
```

**Edit Website**
```bash
POST /api/edit/optimized
Content-Type: application/json

{
  "project_id": 1,
  "edit_instruction": "Change header to blue"
}
```

**Health Check**
```bash
GET /health
```

### Backend (Port 8000)

**List Projects**
```bash
GET /api/projects/
```

**Create Project**
```bash
POST /api/projects/
```

**Update HTML**
```bash
POST /api/projects/{id}/update_html/
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key for Claude/Gemini access |
| `GEMINI_API_KEY` | Recommended | Direct Google Gemini API key (fallback) |
| `ANTHROPIC_API_KEY` | No | Direct Anthropic API key |
| `USE_SDK_AGENTS` | No | Enable Claude Agents SDK (default: false) |
| `SENTRY_DSN` | No | Sentry error tracking |

### Model Priority Chain

The system tries models in order until one succeeds:
1. `anthropic/claude-sonnet-4` (OpenRouter)
2. `anthropic/claude-3.5-sonnet` (OpenRouter)
3. `google/gemini-2.0-flash-001` (OpenRouter)
4. Direct Gemini API (if GEMINI_API_KEY set)

### Feature Flags

```env
USE_SDK_AGENTS=false  # Use standard generation
USE_SDK_AGENTS=true   # Use Claude Agents SDK with autonomous iteration
```

---

## Performance

| Operation | Time | Service |
|-----------|------|---------|
| Website Generation | 30-60s | AI Engine |
| Simple Edit (text/color) | <1s | Playwright |
| Complex Edit (layout) | 5-10s | AI Engine |
| Health Check | <100ms | All |

---

## Monitoring

### Health Checks

```bash
curl http://localhost:8001/health  # AI Engine
curl http://localhost:8000/health/ # Backend
curl http://localhost:3001/health  # Playwright
```

### Logs

```bash
docker compose logs -f           # All services
docker compose logs -f ai_engine # Specific service
```

---

## Development

### Rebuild Services

```bash
docker compose up -d --build
```

### Reset Database

```bash
docker compose down -v
docker compose up -d --build
docker exec ai_website_builder_backend python manage.py migrate
```

### Run Tests

```bash
docker exec ai_website_builder_ai_engine pytest tests/ -v
docker exec ai_website_builder_backend python manage.py test
```

---

## Troubleshooting

### Services won't start
```bash
docker compose logs -f
docker compose restart
```

### Playwright errors
```bash
docker compose up -d --build playwright
```

### Database errors
```bash
docker compose down -v
docker compose up -d postgres redis
docker compose up -d backend
docker exec ai_website_builder_backend python manage.py migrate
```

---

## License

MIT License

## Support

Issues: https://github.com/Y4shhwanth/webisite-builder/issues
