"""
Website generation service using Anthropic Claude
Based on the website-builder-intern reference implementation
"""
from anthropic import Anthropic
import httpx
import json
import time
from typing import Dict, Any, Optional
from logging_config import logger
from config import settings


class ClaudeWebsiteGenerator:
    """Website generator using Claude - matches website-builder-intern implementation"""

    GALACTUS_API_URL = "https://gcp.galactus.run/fetchByUsername/"

    def __init__(self):
        """Initialize Anthropic client"""
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.DEFAULT_CLAUDE_MODEL

        logger.info(f"Initialized ClaudeWebsiteGenerator with model: {self.model}")

    async def fetch_galactus_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user profile from Galactus API (like reference implementation).

        Args:
            username: Topmate username

        Returns:
            Complete profile data or None if not found
        """
        try:
            logger.info(f"Fetching Galactus profile for: {username}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.GALACTUS_API_URL}?username={username}"
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully fetched Galactus profile for {username}")
                    logger.info(f"Profile has {len(data.get('services', []))} services")
                    logger.info(f"Profile has {len(data.get('testimonials', []))} testimonials")
                    return data
                elif response.status_code == 404:
                    logger.warning(f"User not found in Galactus: {username}")
                    return None
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
        """
        Generate complete website HTML from Topmate profile using Claude.
        Matches the website-builder-intern reference implementation.

        Args:
            username: Topmate username
            user_prompt: Additional user requirements

        Returns:
            Generated HTML and metadata
        """
        try:
            start_time = time.time()
            logger.info(f"Generating website for username: {username} using Claude")

            # Step 1: Fetch profile from Galactus API (like reference)
            profile_data = await self.fetch_galactus_profile(username)

            if not profile_data:
                logger.warning(f"No profile found, using mock data for {username}")
                profile_data = self._generate_mock_profile(username)

            # Step 2: Build enhanced prompt with complete JSON (like reference)
            prompt = self._build_enhanced_prompt(username, profile_data, user_prompt)

            # Step 3: Generate with Claude
            logger.info(f"Calling Claude API with model: {self.model}")
            logger.info(f"Prompt length: {len(prompt)} characters")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract HTML content
            html_content = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    html_content += block.text

            # Clean up HTML
            html_content = self._clean_html(html_content)

            execution_time = time.time() - start_time

            logger.info(
                f"Website generated successfully for {username}",
                execution_time=execution_time
            )

            return {
                "success": True,
                "html": html_content,
                "username": username,
                "model": self.model,
                "execution_time": execution_time,
                "token_usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"Error generating website for {username}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _build_enhanced_prompt(
        self,
        username: str,
        profile_data: Dict[str, Any],
        user_prompt: str
    ) -> str:
        """
        Build enhanced prompt with complete profile JSON.
        Matches the website-builder-intern reference implementation.
        Includes ALL profile data: services, testimonials, badges, highlights, achievements, etc.
        """
        prompt = f"""You are an expert web developer specializing in creating beautiful, modern portfolio websites.

Create a stunning, production-ready single-page portfolio website using the following COMPLETE profile data.
You MUST include ALL information provided - services, testimonials, badges, highlights, achievements, and stats.

USER REQUEST:
{user_prompt if user_prompt else "Create a professional portfolio website"}

TOPMATE PROFILE DATA (Complete JSON - USE ALL OF THIS DATA):
```json
{json.dumps(profile_data, indent=2)}
```

CRITICAL INSTRUCTIONS - INCLUDE ALL DATA:

1. PROFILE IMAGES:
   - Use `profile_pic` for the creator's avatar (MANDATORY if available)
   - Use `meta_image` or `cover_image_url` for hero section background if available
   - Use `testimonial_image` if available for testimonials section header
   - Never use placeholder images when real URLs are provided

2. ALL SERVICES (MANDATORY - Include every single service):
   For EACH service in the `services` array (include ALL of them):
   - Display exact `title` as service name
   - Use `short_description` or `description` for details
   - Show price: `charge.display_text` or format from `charge.amount` and `charge.currency`
   - Display `duration` if available (e.g., "60 minutes")
   - Use `cover_image_url` or `document_thumbnail_url` for service images
   - Show service type/category if available
   - **CTA LINKS (MANDATORY):** Use format `https://topmate.io/{username}/{{service.id}}`
     Example: `<a href="https://topmate.io/{username}/123" target="_blank" class="btn">Book Now</a>`

3. PROFILE CREDIBILITY & STATS:
   - Display `display_name` or `first_name` + `last_name` or `full_name`
   - Show `title` as professional headline
   - Include `description` as bio
   - Show `expertise` or `expertise_string` as areas of expertise
   - **RATING (MANDATORY):** Display `avg_ratings` with stars (e.g., "4.9 ⭐")
   - **BOOKINGS (MANDATORY):** Show `bookings_count` as social proof (e.g., "500+ sessions")
   - Show `reviews_count` or `ratings_count` (e.g., "100+ reviews")
   - Display `total_ratings` if available
   - Show `is_verified` with a verified badge if true
   - Show `premium_user` or `ultra_premium_user` status if true

4. ALL TESTIMONIALS (MANDATORY - Include every testimonial):
   For EACH testimonial in the `testimonials` array (include ALL):
   - Use `avatar_url` for testimonial giver's image if available
   - Display exact `name` (NEVER modify or hallucinate names)
   - Show exact `quote` or `message` or `review` text (NEVER paraphrase)
   - Display `rating` with stars (e.g., "⭐⭐⭐⭐⭐")
   - Include ALL testimonials - do not skip any
   - Also use `ai_testimonial_short` or `ai_testimonial_long` if no testimonials array
   - Use `ai_testimonial_tags` to show key themes

5. BADGES (MANDATORY if available):
   For EACH badge in the `badges` array:
   - Display badge name/title
   - Show badge icon or image if available
   - Display badge description
   - Create a dedicated "Badges" or "Achievements" section

6. HIGHLIGHTS (MANDATORY if available):
   For EACH item in `highlights` array:
   - Display prominently in hero or about section
   - Use as key selling points

7. YEAR-END ACHIEVEMENTS (if available):
   Display `year_end_achievements` data in a special achievements section

8. SOCIAL LINKS (MANDATORY):
   - Include ALL social links from `social_urls` object
   - Also check `social_url` field
   - Display with appropriate icons (LinkedIn, Twitter, Instagram, etc.)

9. ADDITIONAL DATA TO INCLUDE:
   - `expertise` - Show areas of expertise
   - `timezone` - Mention availability timezone
   - `attendance_percentage` - Show reliability if high
   - `date_joined` - Show "Member since" if relevant
   - `theme_details` - Use for color scheme inspiration if available

10. DESIGN REQUIREMENTS:
    - Modern, responsive design that works on mobile and desktop
    - Professional color scheme with modern gradients
    - Smooth scrolling and subtle animations
    - Good typography and spacing
    - All CSS and JS must be embedded (no external dependencies)
    - Semantic HTML5 elements
    - Excellent accessibility

11. CTA BUTTONS:
    - All booking buttons MUST link to: https://topmate.io/{username}/{{service_id}}
    - Include the actual service ID from the data in every CTA link
    - Make CTAs prominent and action-oriented

MANDATORY SECTIONS (in order):
1. Hero section - name, profile pic, tagline, rating, bookings count, verified badge, main CTA
2. About section - full bio, expertise areas, highlights
3. Badges/Achievements section - ALL badges and achievements
4. Services section - ALL services with pricing and individual booking CTAs
5. Testimonials section - ALL testimonials with ratings and quotes
6. Social proof banner - total bookings, average rating, reviews count
7. Contact/CTA section - social links, final call to action

CRITICAL REQUIREMENTS:
- Include EVERY service from the services array (show all {len(profile_data.get('services', []))} services)
- Include EVERY testimonial from the testimonials array
- Include ALL badges
- Include ALL highlights and achievements
- Use ALL images provided (profile pic, service images, testimonial avatars)
- Include service ID in ALL CTA links
- Display ratings with stars (⭐) prominently throughout
- Return ONLY the complete HTML code, no explanations, no markdown code blocks
- Start with <!DOCTYPE html>"""

        return prompt

    def _generate_mock_profile(self, username: str) -> Dict[str, Any]:
        """Generate mock profile data when API fails"""
        return {
            "id": 1,
            "username": username,
            "first_name": username.title(),
            "last_name": "",
            "display_name": username.title(),
            "title": "Professional Consultant",
            "description": f"Welcome to {username.title()}'s profile. I help people achieve their goals through personalized guidance and expertise.",
            "profile_pic": None,
            "rating": 4.9,
            "total_bookings": 100,
            "services": [
                {
                    "id": 1,
                    "title": "1:1 Consultation",
                    "short_description": "Personal guidance session tailored to your needs",
                    "duration": 30,
                    "charge": {
                        "amount": 500,
                        "currency": "INR",
                        "display_text": "₹500"
                    }
                },
                {
                    "id": 2,
                    "title": "Strategy Session",
                    "short_description": "In-depth strategy and planning discussion",
                    "duration": 60,
                    "charge": {
                        "amount": 1000,
                        "currency": "INR",
                        "display_text": "₹1,000"
                    }
                }
            ],
            "testimonials": [
                {
                    "name": "Happy Client",
                    "quote": "Excellent experience! Highly recommended.",
                    "rating": 5
                }
            ],
            "social_links": {}
        }

    def _clean_html(self, html: str) -> str:
        """Clean HTML content (remove markdown code blocks)"""
        # Remove markdown code blocks
        if html.startswith("```html"):
            html = html[7:]
        if html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]

        return html.strip()
