# AI Website Builder

AI-powered website builder that generates stunning portfolio websites from Topmate profiles using Claude/Gemini with real-time editing capabilities.

## Features

- **One-Click Generation**: Generate professional portfolio websites from Topmate username
- **5 Template Styles**: Modern Minimal, Bold Creative, Professional Corporate, Dark Elegant, Vibrant Gradient
- **Smart Model Fallback**: Claude Sonnet 4 → Claude 3.5 Sonnet → Gemini 2.0 Flash
- **Anti-Slop Design**: Production-grade system prompt that avoids generic AI aesthetics
- **Real-Time Editing**: Natural language commands to modify your website
- **Tailwind CSS v4 + Alpine.js**: Modern, responsive output with interactive components
- **Production Ready**: Monitoring, logging, rate limiting, health checks

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

- **AI Models**:
  - Primary: Claude Sonnet 4 (via OpenRouter)
  - Fallback: Claude 3.5 Sonnet, Gemini 2.0 Flash
  - Direct Gemini API as final fallback
- **Backend**: Django 5.0 + FastAPI
- **Database**: PostgreSQL 15 + Redis 7
- **Frontend**: Vanilla JS (no framework)
- **Generated Sites**: Tailwind CSS v4, Alpine.js, Google Fonts
- **Containerization**: Docker Compose

## Available Templates

| Template | Description |
|----------|-------------|
| Modern Minimal | Clean, minimalist design with focus on content |
| Bold & Creative | Vibrant colors and dynamic layouts |
| Professional Corporate | Trust-building business design |
| Dark & Elegant | Sophisticated dark theme with premium feel |
| Vibrant Gradient | Eye-catching gradients with glass effects |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenRouter API Key (get one at [openrouter.ai](https://openrouter.ai))

### 1. Clone the repository

```bash
git clone https://github.com/Y4shhwanth/webisite-builder.git
cd webisite-builder
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required environment variables:
```env
OPENROUTER_API_KEY=your_openrouter_key
ANTHROPIC_API_KEY=your_anthropic_key  # Optional
GEMINI_API_KEY=your_gemini_key        # Optional
```

### 3. Start all services

```bash
docker compose up -d --build
```

### 4. Run database migrations

```bash
docker exec ai_website_builder_backend python manage.py migrate
```

### 5. Start the frontend

```bash
cd simple-frontend
python3 -m http.server 3000
```

### 6. Open in browser

Navigate to http://localhost:3000

## Usage

1. Enter a Topmate username (e.g., "yashwanth")
2. Select a template style (Modern Minimal, Bold Creative, etc.)
3. Add custom instructions (optional)
4. Click "Generate Website"
5. Wait 30-60 seconds for AI generation
6. Preview your website with proper sections:
   - Navigation → Hero → About → Services → Testimonials → CTA → Footer
7. Use Edit Mode to make changes with AI assistance
8. Download the HTML file

### Edit Commands

Use natural language to edit your website:
- "Change header to blue"
- "Make the text bigger"
- "Hide the testimonials section"
- "Change background to white"

## Project Structure

```
ai-website-builder/
├── backend/              # Django backend
│   ├── projects/        # Projects app
│   ├── users/           # Users app
│   └── manage.py
├── ai_engine/           # FastAPI AI service
│   ├── agents/          # Agent implementations
│   ├── mcp_tools/       # MCP tool servers
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   └── main.py
├── playwright/          # Fast HTML editor service
│   ├── server.js
│   └── Dockerfile
├── simple-frontend/     # Single HTML frontend
│   └── index.html
├── docker-compose.yml
└── README.md
```

## API Endpoints

### AI Engine (Port 8001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/build/website` | POST | Generate website from Topmate profile |
| `/api/build/templates` | GET | List available templates |
| `/api/edit/optimized` | POST | Edit website with AI |
| `/api/chat/init` | POST | Initialize chat session |
| `/api/chat/send` | POST | Send chat message for editing |

### Backend (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health/` | GET | Health check |
| `/api/projects/` | GET/POST | List/create projects |
| `/api/projects/{id}/` | GET/PUT/DELETE | Project CRUD |

## Health Checks

```bash
curl http://localhost:8001/health  # AI Engine
curl http://localhost:8000/health/ # Backend
curl http://localhost:3001/health  # Playwright
```

## Development

### View logs

```bash
docker compose logs -f           # All services
docker compose logs -f ai_engine # Specific service
```

### Restart services

```bash
docker compose restart
```

### Rebuild

```bash
docker compose up -d --build
```

### Reset database

```bash
docker compose down -v
docker compose up -d --build
docker exec ai_website_builder_backend python manage.py migrate
```

## Troubleshooting

### Services won't start

```bash
docker compose logs -f ai_engine
docker compose restart
```

### Playwright not responding

```bash
docker compose up -d --build playwright
```

### Database issues

```bash
docker compose down -v
docker compose up -d postgres redis
docker compose up -d backend
docker exec ai_website_builder_backend python manage.py migrate
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Support

For issues: https://github.com/Y4shhwanth/webisite-builder/issues
