#!/bin/bash

# AI Website Builder - Complete Start and Test Script

set -e

echo "🚀 AI Website Builder - Starting Services"
echo "=========================================="
echo ""

# Function to wait for Docker
wait_for_docker() {
    echo "⏳ Waiting for Docker to be ready..."
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker info >/dev/null 2>&1; then
            echo "✅ Docker is ready!"
            return 0
        fi
        echo "  Waiting for Docker... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    echo "❌ Docker failed to start. Please open Docker Desktop manually."
    exit 1
}

# Check if .env has API keys
check_api_keys() {
    echo ""
    echo "🔑 Checking API keys..."

    if ! grep -q "sk-ant-" .env 2>/dev/null; then
        echo "❌ ANTHROPIC_API_KEY not configured in .env"
        echo ""
        echo "Please add your API keys to .env file:"
        echo "  ANTHROPIC_API_KEY=sk-ant-your-key-here"
        echo "  GEMINI_API_KEY=AIzaSyB-your-key-here"
        echo ""
        echo "Get keys from:"
        echo "  - Anthropic: https://console.anthropic.com/"
        echo "  - Gemini: https://makersuite.google.com/app/apikey"
        exit 1
    fi

    if ! grep -q "AIza" .env 2>/dev/null; then
        echo "⚠️  GEMINI_API_KEY not configured (optional but recommended)"
    fi

    echo "✅ API keys configured"
}

# Start Docker Desktop if not running
echo "🐳 Starting Docker Desktop..."
open -a Docker 2>/dev/null || true

# Wait for Docker to be ready
wait_for_docker

# Check API keys
check_api_keys

echo ""
echo "📦 Building and starting services..."
echo "This will take 5-10 minutes on first run"
echo ""

# Stop any existing services
docker compose down 2>/dev/null || true

# Build and start services
docker compose up -d --build

echo ""
echo "⏳ Waiting for services to initialize (30 seconds)..."
sleep 30

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
local backend_ready=false
for i in {1..20}; do
    if docker exec ai_website_builder_backend python -c "import sys; sys.exit(0)" 2>/dev/null; then
        backend_ready=true
        break
    fi
    echo "  Waiting for backend... ($i/20)"
    sleep 3
done

if [ "$backend_ready" = false ]; then
    echo "⚠️  Backend taking longer than expected. Continuing anyway..."
fi

echo ""
echo "🗃️  Running database migrations..."
docker exec ai_website_builder_backend python manage.py migrate

echo ""
echo "🏥 Checking service health..."
echo ""

# Function to check health
check_health() {
    local service=$1
    local url=$2
    local max_attempts=10
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo "  ✅ $service is healthy"
            return 0
        fi
        if [ $attempt -eq $max_attempts ]; then
            echo "  ⚠️  $service not responding yet (may need more time)"
            return 1
        fi
        sleep 3
        ((attempt++))
    done
}

check_health "Backend" "http://localhost:8000/health/"
check_health "AI Engine" "http://localhost:8001/health"
check_health "Playwright" "http://localhost:3001/health"

echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "======================================"
echo "✅ Services are running!"
echo "======================================"
echo ""
echo "🧪 Running Quick Test..."
echo ""

# Test Backend
echo "Testing Backend API..."
backend_response=$(curl -s http://localhost:8000/health/ 2>/dev/null || echo "failed")
if echo "$backend_response" | grep -q "healthy"; then
    echo "  ✅ Backend API responding"
else
    echo "  ⚠️  Backend API may not be ready yet"
fi

# Test AI Engine
echo "Testing AI Engine API..."
ai_response=$(curl -s http://localhost:8001/health 2>/dev/null || echo "failed")
if echo "$ai_response" | grep -q "healthy"; then
    echo "  ✅ AI Engine API responding"
else
    echo "  ⚠️  AI Engine API may not be ready yet"
fi

# Test Playwright
echo "Testing Playwright service..."
playwright_response=$(curl -s http://localhost:3001/health 2>/dev/null || echo "failed")
if echo "$playwright_response" | grep -q "healthy"; then
    echo "  ✅ Playwright service responding"
else
    echo "  ⚠️  Playwright service may not be ready yet"
fi

echo ""
echo "🌐 Opening frontend in browser..."
sleep 2

# Open frontend
if [[ "$OSTYPE" == "darwin"* ]]; then
    open simple-frontend/index.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open simple-frontend/index.html
else
    echo "Please open simple-frontend/index.html in your browser"
fi

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "📝 Quick Test Steps:"
echo "  1. Frontend should have opened in your browser"
echo "  2. Enter a Topmate username: 'phase' or 'yashwanth'"
echo "  3. Click 'Quick Generate'"
echo "  4. Wait 30-60 seconds for website generation"
echo "  5. Preview, edit, and download your website!"
echo ""
echo "🔧 Useful Commands:"
echo "  View logs:        docker compose logs -f"
echo "  Stop services:    docker compose down"
echo "  Restart service:  docker compose restart <service>"
echo ""
echo "📚 Documentation:"
echo "  - SETUP_GUIDE.md - Detailed setup and troubleshooting"
echo "  - README.md - Project overview"
echo ""
echo "🎉 Happy building!"
