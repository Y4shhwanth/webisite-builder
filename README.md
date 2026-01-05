# AI Website Builder

Production-ready AI-powered website builder using Claude Agents SDK with autonomous iteration.

## Features

- **Quick Generate**: One-click portfolio website generation
- **Guided Interview**: Dynamic UX interview with AI-generated questions
- **Component Editing**: Granular website edits with Playwright optimization
- **Autonomous Refinement**: Multi-pass quality improvement (iterate until satisfied)
- **Production Ready**: Monitoring, logging, rate limiting, health checks

## Architecture

```
┌─────────────────┐
│  Simple Frontend│ (Single HTML, 25KB)
│   Port: 8080    │
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

- **AI Models**: Claude Opus 4.5 (primary), Gemini Flash (UX interviews)
- **Backend**: Django 5.0 + FastAPI
- **Database**: PostgreSQL 15 + Redis 7
- **Agents**: Claude Agents SDK (autonomous iteration)
- **Frontend**: Vanilla JS (no framework, 25KB)

## Quick Start

1. **Clone and setup environment**:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

2. **Start all services**:
```bash
docker-compose up -d --build
```

3. **Run database migrations**:
```bash
docker exec ai_website_builder_backend python manage.py migrate
```

4. **Open frontend**:
```bash
open simple-frontend/index.html
```

5. **Test the system**:
   - Enter Topmate username (e.g., "phase")
   - Click "Quick Generate" or "Start Guided Interview"
   - Edit generated website with natural language

## Development

### Project Structure

```
ai-website-builder/
├── backend/              # Django backend
│   ├── projects/        # Projects app
│   ├── users/           # Users app
│   └── manage.py
├── ai_engine/           # FastAPI AI service
│   ├── agents/          # Agent implementations
│   │   ├── sdk_base_agent.py
│   │   ├── orchestrator.py
│   │   └── ...
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

### Running Tests

```bash
# AI Engine tests
docker exec ai_website_builder_ai_engine pytest tests/ -v --cov=ai_engine

# Backend tests
docker exec ai_website_builder_backend python manage.py test
```

### Health Checks

```bash
# Check all services
curl http://localhost:8001/health  # AI Engine
curl http://localhost:8000/health/ # Backend
curl http://localhost:3001/health  # Playwright
```

## Claude Agents SDK Integration

### Key Features

1. **Autonomous Iteration**: Agents iterate until quality threshold met (5-8 passes)
2. **Self-Review**: Agents read their own output and refine
3. **Subagent Delegation**: Main orchestrator delegates to specialized agents
4. **MCP Tool Servers**: Topmate API, File operations, DOM manipulation

### Agent Workflow

```
Pass 1: Generate initial website
Pass 2: Self-review (read output, check quality)
Pass 3: Refine issues found
Pass 4: Verify final output
Pass N: Iterate until satisfied (max 8 iterations)
```

### Feature Flag

Toggle between old system and new SDK agents:

```bash
# In .env
USE_SDK_AGENTS=false  # Use old system (default)
USE_SDK_AGENTS=true   # Use new Claude Agents SDK
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] All tests passing (coverage ≥70%)
- [ ] API keys secured (not in .env file)
- [ ] Sentry configured for error tracking
- [ ] Rate limiting active
- [ ] Health checks verified
- [ ] Resource limits set in docker-compose.yml
- [ ] Monitoring dashboards configured

### Deployment Strategy

**Blue-Green Rollout**:
1. Deploy with `USE_SDK_AGENTS=false` (old system)
2. Monitor for 48 hours
3. Enable SDK for 10% traffic
4. Gradual rollout: 25% → 50% → 100%

### Monitoring

**Key Metrics**:
- Latency: P50, P95, P99 generation time
- Error Rate: Failed generations / total
- Quality Score: Manual review sample
- Token Usage: Cost per generation

**Alerting**:
- Error rate >5% for 5 min → Page on-call
- Avg latency >90s for 10 min → Warning
- Memory >80% for 15 min → Warning

## API Documentation

### Generate Website

```bash
POST http://localhost:8001/api/build/website
Content-Type: application/json

{
  "username": "phase",
  "user_prompt": "Create a modern portfolio with dark mode"
}
```

### Edit Website

```bash
POST http://localhost:8001/api/edit/optimized
Content-Type: application/json

{
  "project_id": 1,
  "edit_instruction": "Change the header background to blue"
}
```

### UX Interview

```bash
POST http://localhost:8001/api/interview/generate_question
Content-Type: application/json

{
  "username": "phase",
  "conversation_history": []
}
```

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs -f ai_engine

# Restart services
docker-compose restart

# Rebuild if needed
docker-compose up -d --build
```

### Database migrations fail

```bash
# Reset database (DESTRUCTIVE)
docker-compose down -v
docker-compose up -d postgres redis
docker-compose up -d backend
docker exec ai_website_builder_backend python manage.py migrate
```

### Playwright not responding

```bash
# Check if browsers installed
docker exec ai_website_builder_playwright npx playwright --version

# Reinstall if needed
docker-compose up -d --build playwright
```

## Contributing

1. Create feature branch
2. Write tests (coverage ≥70%)
3. Ensure all tests pass
4. Submit PR with description

## License

Proprietary - Topmate.io

## Support

For issues: https://github.com/topmate/ai-website-builder/issues
