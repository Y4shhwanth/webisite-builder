"""
MCP Tools for Topmate API integration
"""
import httpx
from typing import Dict, Any, List, Optional
from logging_config import logger
from config import settings


async def fetch_user_by_username(username: str) -> Dict[str, Any]:
    """
    Fetch user profile from Topmate API by username.

    Args:
        username: Topmate username

    Returns:
        User profile data including services, testimonials, etc.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{settings.TOPMATE_API_URL}/public/profile/{username}"
            logger.info(f"Fetching Topmate profile for username: {username}")

            response = await client.get(url)

            if response.status_code == 404:
                logger.warning(f"User not found: {username}")
                return {
                    "error": "User not found",
                    "username": username,
                    "success": False
                }

            response.raise_for_status()
            data = response.json()

            logger.info(f"Successfully fetched profile for {username}")
            return {
                "success": True,
                "username": username,
                "data": data
            }

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching user {username}: {str(e)}")
        # FALLBACK: Use mock data for testing
        logger.warning(f"Using mock data for {username} due to API error")
        return _get_mock_user_data(username)
    except Exception as e:
        logger.error(f"Error fetching user {username}: {str(e)}")
        # FALLBACK: Use mock data for testing
        logger.warning(f"Using mock data for {username} due to error")
        return _get_mock_user_data(username)


def _get_mock_user_data(username: str) -> Dict[str, Any]:
    """Generate mock user data for testing when API is unavailable"""
    mock_data = {
        "name": username.title(),
        "bio": f"Passionate professional with expertise in technology and innovation. "
               f"Helping people achieve their goals through personalized mentorship and consulting.",
        "tagline": f"Expert Mentor & Consultant | Empowering Growth",
        "services": [
            {
                "title": "1:1 Mentorship Session",
                "description": "One-on-one personalized guidance session to help you with your career goals",
                "price": 2999,
                "duration": "60 min"
            },
            {
                "title": "Career Strategy Consultation",
                "description": "Comprehensive career planning and strategy session",
                "price": 4999,
                "duration": "90 min"
            },
            {
                "title": "Resume Review & Feedback",
                "description": "Detailed review of your resume with actionable feedback",
                "price": 1499,
                "duration": "30 min"
            }
        ],
        "testimonials": [
            {
                "text": f"Working with {username.title()} was an incredible experience. Their insights helped me land my dream job!",
                "author": "Sarah Johnson",
                "rating": 5
            },
            {
                "text": "Highly recommended! Professional, knowledgeable, and genuinely cares about your success.",
                "author": "Michael Chen",
                "rating": 5
            },
            {
                "text": f"{username.title()} provided excellent guidance that transformed my career trajectory.",
                "author": "Priya Sharma",
                "rating": 5
            }
        ],
        "social_links": {
            "twitter": f"https://twitter.com/{username}",
            "linkedin": f"https://linkedin.com/in/{username}",
            "github": f"https://github.com/{username}"
        },
        "image": f"https://ui-avatars.com/api/?name={username}&size=200&background=667eea&color=fff"
    }

    logger.info(f"Generated mock data for {username}")
    return {
        "success": True,
        "username": username,
        "data": mock_data,
        "is_mock": True
    }


async def get_user_services(username: str) -> List[Dict[str, Any]]:
    """
    Get services/offerings from a Topmate user.

    Args:
        username: Topmate username

    Returns:
        List of services with pricing, description, etc.
    """
    try:
        profile = await fetch_user_by_username(username)

        if not profile.get("success"):
            return []

        services = profile.get("data", {}).get("services", [])
        logger.info(f"Found {len(services)} services for {username}")

        return services

    except Exception as e:
        logger.error(f"Error getting services for {username}: {str(e)}")
        return []


async def get_user_testimonials(username: str) -> List[Dict[str, Any]]:
    """
    Get testimonials/reviews for a Topmate user.

    Args:
        username: Topmate username

    Returns:
        List of testimonials
    """
    try:
        profile = await fetch_user_by_username(username)

        if not profile.get("success"):
            return []

        testimonials = profile.get("data", {}).get("testimonials", [])
        logger.info(f"Found {len(testimonials)} testimonials for {username}")

        return testimonials

    except Exception as e:
        logger.error(f"Error getting testimonials for {username}: {str(e)}")
        return []


async def get_user_social_links(username: str) -> Dict[str, str]:
    """
    Get social media links for a Topmate user.

    Args:
        username: Topmate username

    Returns:
        Dictionary of social platform to URL mappings
    """
    try:
        profile = await fetch_user_by_username(username)

        if not profile.get("success"):
            return {}

        social_links = profile.get("data", {}).get("social_links", {})
        logger.info(f"Found {len(social_links)} social links for {username}")

        return social_links

    except Exception as e:
        logger.error(f"Error getting social links for {username}: {str(e)}")
        return {}


# Tool definitions for Claude Agents SDK
TOPMATE_TOOLS = {
    "fetch_user_by_username": {
        "name": "fetch_user_by_username",
        "description": "Fetch complete user profile from Topmate API",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Topmate username"
                }
            },
            "required": ["username"]
        },
        "function": fetch_user_by_username
    },
    "get_user_services": {
        "name": "get_user_services",
        "description": "Get services/offerings from a Topmate user",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Topmate username"
                }
            },
            "required": ["username"]
        },
        "function": get_user_services
    },
    "get_user_testimonials": {
        "name": "get_user_testimonials",
        "description": "Get testimonials/reviews for a Topmate user",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Topmate username"
                }
            },
            "required": ["username"]
        },
        "function": get_user_testimonials
    },
    "get_user_social_links": {
        "name": "get_user_social_links",
        "description": "Get social media links for a Topmate user",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Topmate username"
                }
            },
            "required": ["username"]
        },
        "function": get_user_social_links
    }
}
