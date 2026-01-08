"""
Vercel Serverless API - Self-contained AI Website Builder
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import json
import re
from bs4 import BeautifulSoup

app = FastAPI(title="AI Website Builder API")

# CORS - Allow all origins for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GALACTUS_API_URL = "https://gcp.galactus.run/fetchByUsername/"

# In-memory chat sessions (Note: stateless in serverless, sessions reset)
chat_sessions = {}


class BuildWebsiteRequest(BaseModel):
    username: str
    user_prompt: Optional[str] = ""
    template_id: Optional[str] = "modern-minimal"


class ChatInitRequest(BaseModel):
    html: str
    design_context: Optional[dict] = None


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    html: str
    selected_element: Optional[dict] = None


@app.get("/")
@app.get("/api")
async def root():
    return {"service": "AI Website Builder", "status": "running"}


@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status": "healthy", "openrouter_configured": bool(OPENROUTER_API_KEY)}


@app.post("/api/build/website")
@app.post("/build/website")
async def build_website(data: BuildWebsiteRequest):
    """Generate a website from Topmate username"""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    try:
        # Fetch profile from Galactus
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{GALACTUS_API_URL}{data.username}")
            if resp.status_code != 200:
                raise HTTPException(status_code=404, detail=f"User {data.username} not found")
            profile = resp.json()

        # Build prompt
        prompt = build_generation_prompt(profile, data.user_prompt, data.template_id)

        # Call OpenRouter
        html = await call_openrouter(prompt, max_tokens=8192)

        # Extract HTML from response
        html = extract_html(html)

        # Extract design context
        design_context = extract_design_context(html)

        return {
            "success": True,
            "html": html,
            "username": data.username,
            "template_id": data.template_id,
            "design_context": design_context
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/init")
@app.post("/chat/init")
async def chat_init(data: ChatInitRequest):
    """Initialize a chat session"""
    import uuid
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = {
        "html": data.html,
        "design_context": data.design_context,
        "history": []
    }
    return {"success": True, "session_id": session_id}


@app.post("/api/chat/message")
@app.post("/chat/message")
async def chat_message(data: ChatMessageRequest):
    """Process chat message and return edited HTML"""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    try:
        # Build editing prompt
        prompt = build_editing_prompt(data.message, data.html, data.selected_element)

        # Call OpenRouter
        response = await call_openrouter(prompt, max_tokens=16000)

        # Extract HTML from response
        edited_html = extract_html_from_edit(response, data.html)

        return {
            "success": True,
            "html": edited_html,
            "message": "Edit applied successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/stream/{session_id}")
async def chat_stream(session_id: str, message: str, request: Request):
    """Stream chat response (SSE)"""
    async def generate():
        yield f"data: {json.dumps({'type': 'start'})}\n\n"
        yield f"data: {json.dumps({'type': 'message', 'content': 'Processing your request...'})}\n\n"
        yield f"data: {json.dumps({'type': 'complete', 'success': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


async def call_openrouter(prompt: str, max_tokens: int = 8192) -> str:
    """Call OpenRouter API"""
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "anthropic/claude-sonnet-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            }
        )

        if response.status_code != 200:
            raise Exception(f"OpenRouter error: {response.text}")

        data = response.json()
        return data["choices"][0]["message"]["content"]


def build_generation_prompt(profile: dict, user_prompt: str, template_id: str) -> str:
    """Build website generation prompt"""
    return f"""You are an expert web developer. Create a complete, production-ready HTML website.

## USER PROFILE DATA:
{json.dumps(profile, indent=2)}

## TEMPLATE STYLE: {template_id}

## USER REQUEST: {user_prompt or "Create a professional portfolio website"}

## REQUIREMENTS:
1. Return ONLY valid HTML - no markdown, no explanations
2. Use Tailwind CSS via CDN: <script src="https://cdn.tailwindcss.com"></script>
3. Include Google Fonts
4. Make it fully responsive
5. Include all sections: Header, Hero, About, Services, Testimonials, Contact, Footer
6. Use the profile data to personalize content
7. Add smooth animations and hover effects
8. Make CTAs prominent

Return the complete HTML starting with <!DOCTYPE html>"""


def build_editing_prompt(instruction: str, html: str, selected_element: dict = None) -> str:
    """Build editing prompt"""
    element_context = ""
    if selected_element:
        element_context = f"""
## SELECTED ELEMENT:
- Tag: {selected_element.get('tag', 'unknown')}
- Classes: {selected_element.get('classes', [])}
- Text: {selected_element.get('text', '')[:100]}
"""

    return f"""You are an expert website editor. Make the requested edit to the HTML.

## EDIT INSTRUCTION:
{instruction}

{element_context}

## CURRENT HTML:
```html
{html}
```

## RULES:
1. Return ONLY the complete modified HTML
2. Make minimal changes - only what's requested
3. Preserve all existing styles and structure
4. For color changes, use Tailwind classes (bg-blue-500, text-red-500, etc.)

Return the complete edited HTML starting with <!DOCTYPE html>"""


def extract_html(response: str) -> str:
    """Extract HTML from LLM response"""
    # Try to find HTML in code blocks
    patterns = [
        r'```html\s*(<!DOCTYPE html>.*?</html>)\s*```',
        r'```\s*(<!DOCTYPE html>.*?</html>)\s*```',
        r'(<!DOCTYPE html>.*</html>)',
    ]

    for pattern in patterns:
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # If response starts with <!DOCTYPE, return as-is
    if response.strip().lower().startswith('<!doctype'):
        return response.strip()

    raise Exception("Could not extract HTML from response")


def extract_html_from_edit(response: str, original_html: str) -> str:
    """Extract edited HTML, fallback to original if failed"""
    try:
        return extract_html(response)
    except:
        return original_html


def extract_design_context(html: str) -> dict:
    """Extract design context from HTML"""
    soup = BeautifulSoup(html, 'html.parser')

    # Extract fonts
    fonts = []
    for link in soup.find_all('link', href=True):
        if 'fonts.googleapis.com' in link['href']:
            fonts.append(link['href'])

    # Extract colors from style tags
    colors = {}
    for style in soup.find_all('style'):
        text = style.string or ''
        for match in re.finditer(r'--color-(\w+):\s*([^;]+)', text):
            colors[match.group(1)] = match.group(2).strip()

    # Extract sections
    sections = []
    for section in soup.find_all(['section', 'header', 'footer']):
        sections.append({
            'tag': section.name,
            'id': section.get('id', ''),
            'classes': section.get('class', [])
        })

    return {
        'fonts': fonts,
        'colors': colors,
        'sections': sections
    }


# For Vercel
handler = app
