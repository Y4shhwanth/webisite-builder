"""
Build Website API Endpoint
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import re
import urllib.request

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GALACTUS_API_URL = "https://gcp.galactus.run/fetchByUsername/"


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        self._send_json({"error": "Use POST method", "endpoint": "/api/build/website"})

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'

        try:
            data = json.loads(body)
        except:
            data = {}

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
            # Fetch profile
            profile_url = f"{GALACTUS_API_URL}{username}"
            req = urllib.request.Request(profile_url)
            with urllib.request.urlopen(req, timeout=30) as response:
                profile = json.loads(response.read().decode())

            # Build prompt
            prompt = self._build_prompt(profile, user_prompt, template_id)

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
            self._send_json({"success": False, "error": f"User {username} not found", "details": str(e)}, 404)
        except Exception as e:
            import traceback
            self._send_json({"success": False, "error": str(e), "traceback": traceback.format_exc()}, 500)

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _call_openrouter(self, prompt):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = json.dumps({
            "model": "anthropic/claude-sonnet-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8192,
            "temperature": 0.7,
        }).encode()

        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode())
            return result["choices"][0]["message"]["content"]

    def _build_prompt(self, profile, user_prompt, template_id):
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
5. Include sections: Header, Hero, About, Services, Testimonials, Contact, Footer
6. Use the profile data to personalize content
7. Add hover effects and animations

Return the complete HTML starting with <!DOCTYPE html>"""

    def _extract_html(self, response):
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
