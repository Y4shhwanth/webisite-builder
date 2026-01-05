"""
Website generation API router
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import time

from logging_config import logger
from config import settings
from services.openrouter_website_generator import OpenRouterWebsiteGenerator
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class BuildWebsiteRequest(BaseModel):
    """Request model for building a website"""
    username: str
    user_prompt: Optional[str] = ""


class BuildWebsiteResponse(BaseModel):
    """Response model for building a website"""
    success: bool
    html: Optional[str] = None
    error: Optional[str] = None
    username: Optional[str] = None
    model: Optional[str] = None
    execution_time: Optional[float] = None
    token_usage: Optional[dict] = None


@router.post("/build/website", response_model=BuildWebsiteResponse)
@limiter.limit("5/minute")  # Rate limit: 5 requests per minute
async def build_website(request: Request, data: BuildWebsiteRequest):
    """
    Generate a complete website from Topmate username.

    This endpoint:
    1. Fetches user profile from Topmate API
    2. Generates a professional portfolio website using AI
    3. Returns complete HTML with embedded CSS/JS

    Rate limit: 5 requests per minute
    """
    try:
        start_time = time.time()

        logger.info(
            "Website build request received",
            username=data.username,
            has_user_prompt=bool(data.user_prompt)
        )

        # Check if SDK agents enabled (feature flag)
        if settings.USE_SDK_AGENTS:
            # TODO: Use Claude Agents SDK orchestrator (Phase 2)
            return BuildWebsiteResponse(
                success=False,
                error="SDK agents not yet implemented. Set USE_SDK_AGENTS=false"
            )

        # Use OpenRouter generator (default)
        generator = OpenRouterWebsiteGenerator()
        result = await generator.generate_website(
            username=data.username,
            user_prompt=data.user_prompt
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
            execution_time=execution_time
        )

        return BuildWebsiteResponse(
            success=True,
            html=result.get("html"),
            username=data.username,
            model=result.get("model"),
            execution_time=execution_time,
            token_usage=result.get("token_usage")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building website: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
