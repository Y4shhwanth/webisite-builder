"""
Website generation API router
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
import time

from logging_config import logger
from config import settings
from services.openrouter_website_generator import (
    OpenRouterWebsiteGenerator,
    get_available_templates,
    WEBSITE_TEMPLATES
)
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class BuildWebsiteRequest(BaseModel):
    """Request model for building a website"""
    username: str
    user_prompt: Optional[str] = ""
    template_id: Optional[str] = "modern-minimal"


class BuildWebsiteResponse(BaseModel):
    """Response model for building a website"""
    success: bool
    html: Optional[str] = None
    error: Optional[str] = None
    username: Optional[str] = None
    model: Optional[str] = None
    template_id: Optional[str] = None
    execution_time: Optional[float] = None
    token_usage: Optional[dict] = None


class TemplateInfo(BaseModel):
    """Template information model"""
    id: str
    name: str
    description: str
    preview: str


class TemplatesResponse(BaseModel):
    """Response model for templates list"""
    success: bool
    templates: List[TemplateInfo]


@router.get("/build/templates", response_model=TemplatesResponse)
async def get_templates():
    """
    Get list of available website templates.

    Returns all templates with their names, descriptions, and preview images.
    """
    templates = get_available_templates()
    return TemplatesResponse(
        success=True,
        templates=[TemplateInfo(**t) for t in templates]
    )


@router.post("/build/website", response_model=BuildWebsiteResponse)
@limiter.limit("5/minute")  # Rate limit: 5 requests per minute
async def build_website(request: Request, data: BuildWebsiteRequest):
    """
    Generate a complete website from Topmate username.

    This endpoint:
    1. Fetches user profile from Topmate API (includes services, badges, testimonials)
    2. Generates a professional portfolio website using AI (Gemini via OpenRouter)
    3. Returns complete HTML with embedded CSS/JS

    Parameters:
    - username: Topmate username to fetch profile data
    - user_prompt: Optional custom instructions for the website
    - template_id: Template style to use (default: modern-minimal)

    Available templates:
    - modern-minimal: Clean, minimalist design
    - bold-creative: Vibrant colors and dynamic layouts
    - professional-corporate: Trust-building business design
    - dark-elegant: Sophisticated dark theme
    - vibrant-gradient: Eye-catching gradients with glass effects

    Rate limit: 5 requests per minute
    """
    try:
        start_time = time.time()

        # Validate template_id
        template_id = data.template_id or "modern-minimal"
        if template_id not in WEBSITE_TEMPLATES:
            template_id = "modern-minimal"

        logger.info(
            "Website build request received",
            username=data.username,
            template_id=template_id,
            has_user_prompt=bool(data.user_prompt)
        )

        # Check if SDK agents enabled (feature flag)
        if settings.USE_SDK_AGENTS:
            # TODO: Use Claude Agents SDK orchestrator (Phase 2)
            return BuildWebsiteResponse(
                success=False,
                error="SDK agents not yet implemented. Set USE_SDK_AGENTS=false"
            )

        # Use OpenRouter generator with Gemini (default)
        generator = OpenRouterWebsiteGenerator()
        result = await generator.generate_website(
            username=data.username,
            user_prompt=data.user_prompt,
            template_id=template_id
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Unknown error during generation")
            )

        execution_time = time.time() - start_time

        logger.info(
            "Website built successfully",
            username=data.username,
            template_id=template_id,
            execution_time=execution_time
        )

        return BuildWebsiteResponse(
            success=True,
            html=result.get("html"),
            username=data.username,
            model=result.get("model"),
            template_id=template_id,
            execution_time=execution_time,
            token_usage=result.get("token_usage")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building website: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
