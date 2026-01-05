"""
MCP Tools for DOM manipulation via Playwright service
"""
import httpx
from typing import Dict, Any
from logging_config import logger
from config import settings


async def get_dom_structure(html: str) -> Dict[str, Any]:
    """
    Parse HTML and return DOM structure.

    Args:
        html: HTML content to parse

    Returns:
        DOM structure information
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.PLAYWRIGHT_SERVICE_URL}/get-dom",
                json={"html": html}
            )
            response.raise_for_status()
            data = response.json()

            logger.info("Retrieved DOM structure")
            return {
                "success": True,
                "dom": data
            }

    except Exception as e:
        logger.error(f"Error getting DOM structure: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_css_selectors(html: str, element_description: str) -> Dict[str, Any]:
    """
    Find CSS selectors for elements matching description.

    Args:
        html: HTML content
        element_description: Description of element to find (e.g., "header", "main navigation")

    Returns:
        List of matching CSS selectors
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.PLAYWRIGHT_SERVICE_URL}/get-selectors",
                json={
                    "html": html,
                    "description": element_description
                }
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"Found selectors for: {element_description}")
            return {
                "success": True,
                "selectors": data.get("selectors", [])
            }

    except Exception as e:
        logger.error(f"Error getting CSS selectors: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def apply_dom_edit(
    html: str,
    selector: str,
    action: str,
    value: str = ""
) -> Dict[str, Any]:
    """
    Apply a DOM edit using Playwright.

    Args:
        html: Original HTML content
        selector: CSS selector for target element
        action: Action to perform (e.g., "setText", "setAttribute", "setStyle")
        value: Value for the action

    Returns:
        Modified HTML
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.PLAYWRIGHT_SERVICE_URL}/edit",
                json={
                    "html": html,
                    "selector": selector,
                    "action": action,
                    "value": value
                }
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"Applied DOM edit: {action} on {selector}")
            return {
                "success": True,
                "html": data.get("html", html)
            }

    except Exception as e:
        logger.error(f"Error applying DOM edit: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# Tool definitions for Claude Agents SDK
DOM_TOOLS = {
    "get_dom": {
        "name": "get_dom",
        "description": "Parse HTML and return DOM structure",
        "input_schema": {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "HTML content to parse"
                }
            },
            "required": ["html"]
        },
        "function": get_dom_structure
    },
    "get_css": {
        "name": "get_css",
        "description": "Find CSS selectors for elements matching description",
        "input_schema": {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "HTML content"
                },
                "element_description": {
                    "type": "string",
                    "description": "Description of element to find"
                }
            },
            "required": ["html", "element_description"]
        },
        "function": get_css_selectors
    },
    "apply_dom_edit": {
        "name": "apply_dom_edit",
        "description": "Apply a DOM edit using Playwright",
        "input_schema": {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "Original HTML content"
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector for target element"
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform (setText, setAttribute, setStyle)"
                },
                "value": {
                    "type": "string",
                    "description": "Value for the action"
                }
            },
            "required": ["html", "selector", "action"]
        },
        "function": apply_dom_edit
    }
}
