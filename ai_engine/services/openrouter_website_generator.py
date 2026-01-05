"""
Website generation service using OpenRouter API
Produces high-quality, production-ready portfolio websites.
"""
import httpx
import json
import time
from typing import Dict, Any, Optional, List
from logging_config import logger
from config import settings


class OpenRouterWebsiteGenerator:
    """Website generator using OpenRouter API"""

    GALACTUS_API_URL = "https://gcp.galactus.run/fetchByUsername/"
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize OpenRouter client"""
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        self.model = model or "anthropic/claude-3.5-sonnet"
        logger.info(f"Initialized OpenRouterWebsiteGenerator with model: {self.model}")

    async def fetch_galactus_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Fetch user profile from Galactus API."""
        try:
            logger.info(f"Fetching Galactus profile for: {username}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.GALACTUS_API_URL}?username={username}"
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully fetched Galactus profile for {username}")
                    logger.info(f"Profile has {len(data.get('services', []))} services")
                    return data
                else:
                    logger.error(f"Galactus API error: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching Galactus profile: {str(e)}")
            return None

    async def generate_website(
        self,
        username: str,
        user_prompt: str = ""
    ) -> Dict[str, Any]:
        """Generate complete website HTML from Topmate profile using OpenRouter."""
        try:
            start_time = time.time()
            logger.info(f"Generating website for username: {username} using OpenRouter")

            # Fetch profile from Galactus API
            profile_data = await self.fetch_galactus_profile(username)

            if not profile_data:
                logger.warning(f"No profile found, using mock data for {username}")
                profile_data = self._generate_mock_profile(username)

            # Build optimized prompt (not too long)
            prompt = self._build_optimized_prompt(username, profile_data, user_prompt)

            logger.info(f"Calling OpenRouter API with model: {self.model}")
            logger.info(f"Prompt length: {len(prompt)} characters")

            # Call OpenRouter API
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.OPENROUTER_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://topmate.io",
                        "X-Title": "AI Website Builder"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 8192,
                        "temperature": 0.7
                    }
                )

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"OpenRouter API error: {response.status_code} - {error_text}")
                    return {
                        "success": False,
                        "error": f"OpenRouter API error: {response.status_code}"
                    }

                result = response.json()

            # Extract HTML content
            html_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not html_content:
                return {"success": False, "error": "No content generated"}

            # Clean up HTML
            html_content = self._clean_html(html_content)

            execution_time = time.time() - start_time
            usage = result.get("usage", {})

            logger.info(f"Website generated successfully for {username} in {execution_time:.2f}s")

            return {
                "success": True,
                "html": html_content,
                "username": username,
                "model": self.model,
                "execution_time": execution_time,
                "token_usage": {
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0)
                }
            }

        except Exception as e:
            logger.error(f"Error generating website for {username}: {str(e)}")
            return {"success": False, "error": str(e)}

    def _build_optimized_prompt(
        self,
        username: str,
        profile_data: Dict[str, Any],
        user_prompt: str
    ) -> str:
        """Build an optimized prompt that's not too long but captures all key data."""

        # Ensure profile_data is a dict
        if not profile_data or not isinstance(profile_data, dict):
            profile_data = {}

        # Extract key profile information safely
        name = (profile_data.get("display_name") or
                profile_data.get("full_name") or
                profile_data.get("first_name") or
                username or "User")
        title = profile_data.get("title") or "Professional"
        bio_raw = profile_data.get("description") or ""
        bio = str(bio_raw)[:500] if bio_raw else ""
        profile_pic = profile_data.get("profile_pic") or ""

        # Stats (with safe defaults)
        rating = profile_data.get("avg_ratings") or profile_data.get("rating") or 0
        bookings = profile_data.get("bookings_count") or profile_data.get("total_bookings") or 0

        # Services (limit to 10, ensure it's a list)
        services_raw = profile_data.get("services")
        services = services_raw[:10] if isinstance(services_raw, list) else []
        services_text = self._format_services(services, username)

        # Testimonials (limit to 5, ensure it's a list)
        testimonials_raw = profile_data.get("testimonials")
        testimonials = testimonials_raw[:5] if isinstance(testimonials_raw, list) else []
        testimonials_text = self._format_testimonials(testimonials)

        # Social links (ensure it's a dict)
        social_urls = profile_data.get("social_urls")
        if not isinstance(social_urls, dict):
            social_urls = {}

        prompt = f"""Create a stunning, modern, production-ready portfolio website.

**CREATOR INFO:**
- Name: {name}
- Title: {title}
- Bio: {bio}
- Profile Picture: {profile_pic}
- Rating: {rating}/5 stars
- Total Bookings: {bookings}+
- Username: {username}

**SERVICES ({len(services)} total):**
{services_text}

**TESTIMONIALS ({len(testimonials)} reviews):**
{testimonials_text}

**SOCIAL LINKS:**
{json.dumps(social_urls) if social_urls else "None provided"}

**USER REQUEST:**
{user_prompt if user_prompt else "Create a professional, modern portfolio website"}

**REQUIREMENTS:**
1. Create a complete, single-file HTML with embedded CSS and JavaScript
2. Modern, responsive design (mobile-first)
3. Professional color scheme with gradients
4. Smooth animations and transitions
5. Include ALL sections: Hero, About, Services, Testimonials, Contact
6. Use the actual profile picture URL if provided
7. Each service must have a "Book Now" button linking to: https://topmate.io/{username}/[service_id]
8. Display rating with star icons
9. Show booking count as social proof
10. Include all social links with icons
11. Make CTAs prominent and action-oriented
12. NO external dependencies - all CSS/JS must be inline
13. Use semantic HTML5
14. Ensure excellent accessibility

**IMPORTANT:** Return ONLY the complete HTML code starting with <!DOCTYPE html>. No explanations, no markdown."""

        return prompt

    def _format_services(self, services: List[Dict], username: str) -> str:
        """Format services for the prompt."""
        if not services:
            return "No services listed"

        lines = []
        for s in services:
            if not s or not isinstance(s, dict):
                continue

            service_id = s.get("id", "")
            title = s.get("title", "Service")

            # Safely get description
            desc = ""
            if s.get("short_description"):
                desc = str(s.get("short_description", ""))[:100]
            elif s.get("description"):
                desc = str(s.get("description", ""))[:100]

            # Get price safely
            charge = s.get("charge")
            if charge and isinstance(charge, dict):
                price = charge.get("display_text") or f"₹{charge.get('amount', 'N/A')}"
            else:
                price = "Contact for price"

            duration = s.get("duration", "")
            duration_str = f" ({duration} min)" if duration else ""

            lines.append(f"- [{service_id}] {title}: {desc} | {price}{duration_str}")
            lines.append(f"  Book URL: https://topmate.io/{username}/{service_id}")

        return "\n".join(lines) if lines else "No services listed"

    def _format_testimonials(self, testimonials: List[Dict]) -> str:
        """Format testimonials for the prompt."""
        if not testimonials:
            return "No testimonials yet"

        lines = []
        for t in testimonials:
            if not t or not isinstance(t, dict):
                continue

            name = t.get("name", "Anonymous") or "Anonymous"
            quote = t.get("quote") or t.get("review") or t.get("message") or ""
            if quote:
                quote = str(quote)[:150]
            rating = t.get("rating", 5) or 5
            if isinstance(rating, (int, float)):
                stars = "⭐" * min(int(rating), 5)
            else:
                stars = "⭐⭐⭐⭐⭐"
            lines.append(f"- \"{quote}\" - {name} ({stars})")

        return "\n".join(lines) if lines else "No testimonials yet"

    def _generate_mock_profile(self, username: str) -> Dict[str, Any]:
        """Generate mock profile data when API fails"""
        return {
            "display_name": username.title(),
            "title": "Professional Consultant",
            "description": f"Welcome to {username.title()}'s profile. Expert guidance and personalized services.",
            "profile_pic": "",
            "avg_ratings": 4.9,
            "bookings_count": 100,
            "services": [
                {
                    "id": "1",
                    "title": "1:1 Consultation",
                    "short_description": "Personal guidance session",
                    "duration": 30,
                    "charge": {"display_text": "₹500", "amount": 500}
                },
                {
                    "id": "2",
                    "title": "Strategy Session",
                    "short_description": "In-depth planning discussion",
                    "duration": 60,
                    "charge": {"display_text": "₹1,000", "amount": 1000}
                }
            ],
            "testimonials": [
                {"name": "Client", "quote": "Excellent experience!", "rating": 5}
            ],
            "social_urls": {}
        }

    def _clean_html(self, html: str) -> str:
        """Clean HTML content (remove markdown code blocks)"""
        html = html.strip()
        if html.startswith("```html"):
            html = html[7:]
        elif html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]
        return html.strip()
