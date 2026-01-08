"""
Vercel Serverless API - AI Website Builder
Using BaseHTTPRequestHandler for Vercel compatibility
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import re
import urllib.request
import urllib.parse

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GALACTUS_API_URL = "https://gcp.galactus.run/fetchByUsername/"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        path = self.path.split('?')[0]

        if path == '/api' or path == '/api/':
            self._send_json({"service": "AI Website Builder", "status": "running"})
        elif path == '/api/health':
            self._send_json({"status": "healthy", "openrouter_configured": bool(OPENROUTER_API_KEY)})
        else:
            self._send_json({"error": "Not found", "path": path}, 404)

    def do_POST(self):
        """Handle POST requests"""
        path = self.path.split('?')[0]

        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'

        try:
            data = json.loads(body)
        except:
            data = {}

        if path == '/api/build/website':
            self._handle_build_website(data)
        elif path == '/api/chat/init':
            self._handle_chat_init(data)
        elif path == '/api/chat/message':
            self._handle_chat_message(data)
        else:
            self._send_json({"error": "Not found", "path": path}, 404)

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _handle_build_website(self, data):
        """Generate website from username"""
        if not OPENROUTER_API_KEY:
            self._send_json({"success": False, "error": "OPENROUTER_API_KEY not configured"}, 500)
            return

        username = data.get('username', '')
        user_prompt = data.get('user_prompt', '')
        template_id = data.get('template_id', 'modern-minimal')

        if not username:
            self._send_json({"success": False, "error": "Username required"}, 400)
            return

        try:
            # Fetch profile from Galactus
            profile_url = f"{GALACTUS_API_URL}{username}"
            req = urllib.request.Request(profile_url)
            with urllib.request.urlopen(req, timeout=30) as response:
                profile = json.loads(response.read().decode())

            # Build prompt
            prompt = self._build_generation_prompt(profile, user_prompt, template_id)

            # Call OpenRouter
            html = self._call_openrouter(prompt)

            # Extract HTML
            html = self._extract_html(html)

            self._send_json({
                "success": True,
                "html": html,
                "username": username,
                "template_id": template_id,
                "design_context": {}
            })

        except urllib.error.HTTPError as e:
            self._send_json({"success": False, "error": f"User {username} not found"}, 404)
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, 500)

    def _handle_chat_init(self, data):
        """Initialize chat session"""
        import uuid
        session_id = str(uuid.uuid4())
        self._send_json({"success": True, "session_id": session_id})

    def _handle_chat_message(self, data):
        """Handle chat edit message"""
        if not OPENROUTER_API_KEY:
            self._send_json({"success": False, "error": "OPENROUTER_API_KEY not configured"}, 500)
            return

        message = data.get('message', '')
        html = data.get('html', '')
        selected_element = data.get('selected_element')

        if not message or not html:
            self._send_json({"success": False, "error": "Message and HTML required"}, 400)
            return

        try:
            prompt = self._build_editing_prompt(message, html, selected_element)
            response = self._call_openrouter(prompt, max_tokens=16000)
            edited_html = self._extract_html(response)

            self._send_json({
                "success": True,
                "html": edited_html,
                "message": "Edit applied"
            })
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, 500)

    def _call_openrouter(self, prompt, max_tokens=8192):
        """Call OpenRouter API"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = json.dumps({
            "model": "anthropic/claude-sonnet-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }).encode()

        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode())
            return result["choices"][0]["message"]["content"]

    def _build_generation_prompt(self, profile, user_prompt, template_id):
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

    def _build_editing_prompt(self, instruction, html, selected_element=None):
        """Build editing prompt"""
        element_context = ""
        if selected_element:
            element_context = f"""
## SELECTED ELEMENT:
- Tag: {selected_element.get('tag', 'unknown')}
- Classes: {selected_element.get('classes', [])}
- Text: {str(selected_element.get('text', ''))[:100]}
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

    def _extract_html(self, response):
        """Extract HTML from LLM response"""
        patterns = [
            r'```html\s*(<!DOCTYPE html>.*?</html>)\s*```',
            r'```\s*(<!DOCTYPE html>.*?</html>)\s*```',
            r'(<!DOCTYPE html>.*</html>)',
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        if response.strip().lower().startswith('<!doctype'):
            return response.strip()

        raise Exception("Could not extract HTML from response")
