#!/bin/bash

# AI Website Builder - Quick Start Script

set -e

echo "🚀 AI Website Builder - Quick Start"
echo "===================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo "✅ Docker is running"

# Check if .env file has API keys
if ! grep -q "sk-ant-" .env 2>/dev/null || ! grep -q "AIza" .env 2>/dev/null; then
    echo ""
    echo "⚠️  Warning: API keys not configured in .env file"
    echo ""
    echo "Please add your API keys to the .env file:"
    echo "  ANTHROPIC_API_KEY=sk-ant-your-key-here"
    echo "  GEMINI_API_KEY=AIzaSyB-your-key-here"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to exit..."
fi

echo ""
echo "📦 Building and starting services..."
echo "This may take 5-10 minutes on first run"
echo ""

docker compose up -d --build

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if backend is ready
echo "Checking backend..."
until docker exec ai_website_builder_backend python -c "import sys; sys.exit(0)" 2>/dev/null
do
    echo "Waiting for backend..."
    sleep 5
done

echo "✅ Backend ready"

# Run migrations
echo ""
echo "🗃️  Running database migrations..."
docker exec ai_website_builder_backend python manage.py migrate

echo ""
echo "✅ Database migrations completed"

# Check health of all services
echo ""
echo "🏥 Checking service health..."

check_health() {
    local service=$1
    local url=$2
    local max_attempts=10
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo "  ✅ $service is healthy"
            return 0
        fi
        echo "  ⏳ Waiting for $service... (attempt $attempt/$max_attempts)"
        sleep 3
        ((attempt++))
    done

    echo "  ⚠️  $service may not be ready yet"
    return 1
}

check_health "Backend" "http://localhost:8000/health/"
check_health "AI Engine" "http://localhost:8001/health"
check_health "Playwright" "http://localhost:3001/health"

echo ""
echo "✅ All services are ready!"
echo ""
echo "📊 Service Status:"
docker compose ps
echo ""
echo "🌐 Opening frontend..."

# Open frontend based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    open simple-frontend/index.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open simple-frontend/index.html
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    start simple-frontend/index.html
else
    echo "Please open simple-frontend/index.html in your browser"
fi

echo ""
echo "======================================"
echo "✅ AI Website Builder is ready!"
echo "======================================"
echo ""
echo "📝 Quick Guide:"
echo "  1. Enter a Topmate username (e.g., 'phase')"
echo "  2. Click 'Quick Generate'"
echo "  3. Wait 30-60 seconds"
echo "  4. Edit, preview, and download!"
echo ""
echo "📚 Documentation:"
echo "  - README.md - Overview"
echo "  - SETUP_GUIDE.md - Detailed setup"
echo "  - PROJECT_SUMMARY.md - Complete project info"
echo ""
echo "🔧 Useful Commands:"
echo "  View logs:    docker compose logs -f"
echo "  Stop services: docker compose down"
echo "  Restart:      docker compose restart"
echo ""
echo "🎉 Happy building!"
