# AI Website Builder

AI-powered website builder that generates portfolio websites from Topmate profiles using Claude/Gemini with real-time editing capabilities.

## Features

- **One-Click Generation**: Generate professional portfolio websites from Topmate username
- **5 Template Styles**: Modern Minimal, Bold Creative, Professional Corporate, Dark Elegant, Vibrant Gradient
- **Smart Model Fallback**: Claude Sonnet 4 → Claude 3.5 Sonnet → Gemini 2.0 Flash (via OpenRouter)
- **Intelligent Editing Agent**: Tool-use based editing with visual context
- **Smart Image Replacement**: Just paste a URL when image is selected
- **Real-Time Preview**: Live preview with click-to-select editing
- **Tailwind CSS v4 + Alpine.js**: Modern, responsive output

## Architecture

```
┌─────────────────┐
│  Simple Frontend│ (Single HTML)
│   Port: 3000    │
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

## Tech Stack

- **AI Models** (via OpenRouter):
  - Primary: Claude Sonnet 4
  - Fallback: Claude 3.5 Sonnet, Gemini 2.0 Flash
- **Backend**: Django 5.0 + FastAPI
- **Database**: PostgreSQL 15 + Redis 7
- **Frontend**: Vanilla JS
- **Generated Sites**: Tailwind CSS v4, Alpine.js, Google Fonts
- **Containerization**: Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenRouter API Key (get one at [openrouter.ai](https://openrouter.ai))

### 1. Clone and configure

```bash
git clone https://github.com/Y4shhwanth/webisite-builder.git
cd webisite-builder
cp .env.example .env
```

Edit `.env` and add your API key:
```env
OPENROUTER_API_KEY=your_openrouter_key
```

### 2. Start services

```bash
docker compose up -d --build
docker exec ai_website_builder_backend python manage.py migrate
```

### 3. Start frontend

```bash
cd simple-frontend
python3 -m http.server 3000
```

### 4. Open browser

Navigate to http://localhost:3000

## Usage

1. Enter a Topmate username (e.g., "yashwanth")
2. Select a template style
3. Click "Generate Website"
4. Use Edit Mode to make changes:
   - Click any element to select it
   - Type instructions like "make it blue" or "change text to Hello"
   - For images: just paste a URL to replace
5. Download the HTML file

## API Endpoints

### AI Engine (Port 8001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/build/website` | POST | Generate website |
| `/api/build/templates` | GET | List templates |
| `/api/edit/optimized` | POST | Edit website (smart routing) |
| `/api/edit/agent` | POST | Edit with AI agent |
| `/api/chat/init` | POST | Initialize chat session |
| `/api/chat/send` | POST | Send chat message (SSE) |

### Backend (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health/` | GET | Health check |
| `/api/projects/` | GET/POST | List/create projects |
| `/api/projects/{id}/` | GET/PUT/DELETE | Project CRUD |

## Project Structure

```
ai-website-builder/
├── ai_engine/           # FastAPI AI service
│   ├── agents/          # Editing agent with tool-use
│   ├── routers/         # API endpoints
│   ├── services/        # Generation & prompts
│   └── mcp_tools/       # Galactus API integration
├── backend/             # Django backend
│   └── projects/        # Project management
├── playwright/          # DOM manipulation service
│   └── server.js        # Express + Playwright
├── simple-frontend/     # Single HTML frontend
│   └── index.html
└── docker-compose.yml
```

## Editing System

The editing system uses a smart routing approach:

1. **Fast Path** (instant): Image URL replacement when image is selected
2. **AI Agent** (3-5s): Complex edits using Claude with tool-use

### Editing Agent Tools

- `edit_text` - Change text content
- `edit_style` - Modify CSS styles
- `edit_attribute` - Change attributes (src, href, etc.)
- `modify_class` - Replace Tailwind classes
- `find_and_replace` - Direct HTML replacement
- `capture_screenshot` - Visual verification

## Development

### View logs

```bash
docker compose logs -f ai_engine
```

### Restart services

```bash
docker compose restart ai_engine playwright
```

### Health checks

```bash
curl http://localhost:8001/health
curl http://localhost:8000/health/
curl http://localhost:3001/health
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key |
| `GEMINI_API_KEY` | No | Direct Gemini API (fallback) |
| `ANTHROPIC_API_KEY` | No | Direct Anthropic API |

## License

MIT License
