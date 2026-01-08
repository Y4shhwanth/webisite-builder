"""
Vercel Serverless Function Entry Point for AI Engine
"""
import sys
import os

# Add ai_engine to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ai_engine'))

# Set environment for serverless
os.environ.setdefault('REDIS_URL', '')  # Disable Redis in serverless

# Import the FastAPI app
from main import app

# Vercel handler
handler = app
