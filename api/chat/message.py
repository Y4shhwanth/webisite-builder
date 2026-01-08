"""
Chat Message API Endpoint
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import re
import urllib.request

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        self._send_json({"error": "Use POST method"})

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

        message = data.get('message', '')
        html = data.get('html', '')
        selected_element = data.get('selected_element')

        if not message or not html:
            self._send_json({"success": False, "error": "Message and HTML required"}, 400)
            return

        try:
            prompt = self._build_prompt(message, html, selected_element)
            response = self._call_openrouter(prompt)
            edited_html = self._extract_html(response)

            self._send_json({
                "success": True,
                "html": edited_html,
                "message": "Edit applied"
            })
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, 500)

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
            "model": "google/gemini-2.0-flash-001",  # Fast model for Vercel
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 16000,
            "temperature": 0.7,
        }).encode()

        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=55) as response:
            result = json.loads(response.read().decode())
            return result["choices"][0]["message"]["content"]

    def _build_prompt(self, instruction, html, selected_element=None):
        element_context = ""
        if selected_element:
            element_context = f"""
## SELECTED ELEMENT:
- Tag: {selected_element.get('tag', 'unknown')}
- Classes: {selected_element.get('classes', [])}
- Text: {str(selected_element.get('text', ''))[:100]}
"""
        return f"""You are an expert website editor. Make the requested edit.

## EDIT INSTRUCTION:
{instruction}

{element_context}

## CURRENT HTML:
```html
{html}
```

## RULES:
1. Return ONLY the complete modified HTML
2. Make minimal changes
3. Use Tailwind classes for colors (bg-blue-500, text-red-500)

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
        raise Exception("Could not extract HTML")
