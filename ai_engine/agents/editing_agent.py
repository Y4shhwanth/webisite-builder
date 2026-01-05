"""
Editing Agent using OpenRouter API for intelligent website editing.

This agent can:
- Understand the current HTML structure
- Make targeted edits using tools
- Iterate and refine edits autonomously
- Handle complex multi-step editing tasks
"""
from typing import List, Dict, Any, Optional
import json
import httpx
from logging_config import logger
from config import settings


class EditingAgent:
    """
    Intelligent editing agent with tool use for website modifications.
    Uses OpenRouter API for AI capabilities.
    """

    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

    SYSTEM_PROMPT = """You are an expert website editor agent. Your job is to make precise,
high-quality edits to HTML websites based on user instructions.

You have access to tools that let you:
1. Analyze the DOM structure
2. Edit specific elements by selector
3. Change text content
4. Modify styles
5. Add or remove sections

IMPORTANT GUIDELINES:
- Always analyze the HTML first to understand the structure
- Make minimal, targeted changes - don't rewrite entire sections unnecessarily
- Preserve the existing design and styling when making content changes
- Use CSS selectors precisely to target the right elements
- After making changes, verify the edit was successful
- If an edit fails, try an alternative approach

When you receive an editing instruction:
1. First, understand what needs to be changed
2. Identify the target element(s) using selectors
3. Apply the edit using the appropriate tool
4. Return the modified HTML

Always return valid, complete HTML."""

    # Tool definitions for the agent
    EDITING_TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "analyze_dom",
                "description": "Analyze the HTML DOM structure to understand the page layout and find elements. Use this first to understand what elements exist.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "html": {
                            "type": "string",
                            "description": "The HTML to analyze"
                        }
                    },
                    "required": ["html"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "edit_text",
                "description": "Change the text content of an element. Use a CSS selector to target the element.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "html": {
                            "type": "string",
                            "description": "The current HTML"
                        },
                        "selector": {
                            "type": "string",
                            "description": "CSS selector to target the element (e.g., 'h1', '.hero-title', '#main-heading')"
                        },
                        "new_text": {
                            "type": "string",
                            "description": "The new text content"
                        }
                    },
                    "required": ["html", "selector", "new_text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "edit_style",
                "description": "Change CSS styles of an element. Use a CSS selector to target the element.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "html": {
                            "type": "string",
                            "description": "The current HTML"
                        },
                        "selector": {
                            "type": "string",
                            "description": "CSS selector to target the element"
                        },
                        "styles": {
                            "type": "object",
                            "description": "Object of CSS properties to change (e.g., {\"backgroundColor\": \"blue\", \"color\": \"white\"})"
                        }
                    },
                    "required": ["html", "selector", "styles"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "edit_attribute",
                "description": "Change an attribute of an element (href, src, alt, etc.).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "html": {
                            "type": "string",
                            "description": "The current HTML"
                        },
                        "selector": {
                            "type": "string",
                            "description": "CSS selector to target the element"
                        },
                        "attribute": {
                            "type": "string",
                            "description": "The attribute name (e.g., 'href', 'src', 'alt')"
                        },
                        "value": {
                            "type": "string",
                            "description": "The new attribute value"
                        }
                    },
                    "required": ["html", "selector", "attribute", "value"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "replace_element",
                "description": "Replace an entire element's HTML. Use for more complex changes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "html": {
                            "type": "string",
                            "description": "The current HTML"
                        },
                        "selector": {
                            "type": "string",
                            "description": "CSS selector to target the element"
                        },
                        "new_html": {
                            "type": "string",
                            "description": "The new HTML to replace with"
                        }
                    },
                    "required": ["html", "selector", "new_html"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "finalize_edit",
                "description": "Call this when you're done editing to return the final HTML.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "html": {
                            "type": "string",
                            "description": "The final edited HTML"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Brief summary of changes made"
                        }
                    },
                    "required": ["html", "summary"]
                }
            }
        }
    ]

    def __init__(self, model: str = None):
        """Initialize the editing agent."""
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = model or "anthropic/claude-3.5-sonnet"
        self.playwright_url = settings.PLAYWRIGHT_SERVICE_URL
        self.current_html = ""
        self.max_iterations = 5
        self.temperature = 0.3

        logger.info(f"Initialized EditingAgent with model: {self.model}")

    async def edit(
        self,
        html: str,
        instruction: str,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Edit HTML based on user instruction using tool-based agent.

        Args:
            html: Current HTML content
            instruction: User's edit instruction
            max_iterations: Max tool use iterations

        Returns:
            Edited HTML and metadata
        """
        try:
            logger.info(f"EditingAgent: Starting edit - {instruction[:50]}...")
            self.current_html = html

            # Build the prompt
            prompt = f"""Please edit this website based on the following instruction:

INSTRUCTION: {instruction}

CURRENT HTML:
```html
{html[:50000]}
```

Use the tools to:
1. First analyze the DOM to understand the structure
2. Make the necessary edits
3. Call finalize_edit with the final HTML

Remember to make minimal, targeted changes."""

            # Run agent with tools
            messages = [{"role": "user", "content": prompt}]
            iteration = 0
            final_html = html
            edit_summary = ""

            while iteration < max_iterations:
                iteration += 1
                logger.info(f"EditingAgent: Iteration {iteration}")

                # Call OpenRouter API with tools
                async with httpx.AsyncClient(timeout=60.0) as client:
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
                                {"role": "system", "content": self.SYSTEM_PROMPT},
                                *messages
                            ],
                            "tools": self.EDITING_TOOLS,
                            "max_tokens": 8192,
                            "temperature": self.temperature
                        }
                    )

                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(f"OpenRouter API error: {response.status_code} - {error_text}")
                        return {
                            "success": False,
                            "error": f"API error: {response.status_code}",
                            "html": html
                        }

                    result = response.json()

                # Get the assistant's response
                choice = result.get("choices", [{}])[0]
                message = choice.get("message", {})
                finish_reason = choice.get("finish_reason", "")

                # Check if we're done (no tool calls)
                if finish_reason == "stop" or not message.get("tool_calls"):
                    content = message.get("content", "")
                    if content:
                        logger.info(f"EditingAgent: Final response - {content[:100]}")
                    break

                # Process tool calls
                tool_calls = message.get("tool_calls", [])
                tool_results = []

                for tool_call in tool_calls:
                    tool_name = tool_call.get("function", {}).get("name")
                    tool_args_str = tool_call.get("function", {}).get("arguments", "{}")
                    tool_id = tool_call.get("id")

                    try:
                        tool_input = json.loads(tool_args_str)
                    except json.JSONDecodeError:
                        tool_input = {}

                    logger.info(f"EditingAgent: Using tool '{tool_name}'")

                    # Execute the tool
                    tool_result = await self._execute_tool(tool_name, tool_input)

                    # Check if finalize was called
                    if tool_name == "finalize_edit":
                        final_html = tool_input.get("html", final_html)
                        edit_summary = tool_input.get("summary", "")
                        logger.info(f"EditingAgent: Finalized - {edit_summary}")
                        return {
                            "success": True,
                            "html": final_html,
                            "summary": edit_summary,
                            "iterations": iteration
                        }

                    # Update current HTML if edit was successful
                    if tool_result.get("success") and tool_result.get("html"):
                        self.current_html = tool_result["html"]

                    tool_results.append({
                        "tool_call_id": tool_id,
                        "role": "tool",
                        "content": json.dumps(tool_result)
                    })

                # Add assistant response and tool results to messages
                messages.append({"role": "assistant", "content": message.get("content"), "tool_calls": tool_calls})
                messages.extend(tool_results)

            # If we exhausted iterations, return current state
            return {
                "success": True,
                "html": self.current_html,
                "summary": edit_summary or "Edit completed",
                "iterations": iteration
            }

        except Exception as e:
            logger.error(f"EditingAgent: Error - {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "html": html  # Return original on error
            }

    async def _execute_tool(self, tool_name: str, tool_input: Dict) -> Dict[str, Any]:
        """Execute a tool and return the result."""
        try:
            if tool_name == "analyze_dom":
                return await self._analyze_dom(tool_input.get("html", self.current_html))

            elif tool_name == "edit_text":
                return await self._edit_via_playwright(
                    html=tool_input.get("html", self.current_html),
                    selector=tool_input.get("selector"),
                    edit_type="text",
                    edit_value=tool_input.get("new_text")
                )

            elif tool_name == "edit_style":
                return await self._edit_via_playwright(
                    html=tool_input.get("html", self.current_html),
                    selector=tool_input.get("selector"),
                    edit_type="style",
                    edit_value=tool_input.get("styles")
                )

            elif tool_name == "edit_attribute":
                return await self._edit_via_playwright(
                    html=tool_input.get("html", self.current_html),
                    selector=tool_input.get("selector"),
                    edit_type="attribute",
                    edit_value={
                        "name": tool_input.get("attribute"),
                        "value": tool_input.get("value")
                    }
                )

            elif tool_name == "replace_element":
                return await self._edit_via_playwright(
                    html=tool_input.get("html", self.current_html),
                    selector=tool_input.get("selector"),
                    edit_type="replace",
                    edit_value=tool_input.get("new_html")
                )

            elif tool_name == "finalize_edit":
                # This is handled in the main loop
                return {"success": True, "message": "Finalized"}

            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {str(e)}")
            return {"success": False, "error": str(e)}

    async def _analyze_dom(self, html: str) -> Dict[str, Any]:
        """Analyze DOM structure via Playwright service."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.playwright_url}/get-dom-detailed",
                    json={"html": html, "include_bounds": False}
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "dom": data.get("dom"),
                        "message": "DOM analyzed successfully"
                    }
                else:
                    return {"success": False, "error": "Failed to analyze DOM"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _edit_via_playwright(
        self,
        html: str,
        selector: str,
        edit_type: str,
        edit_value: Any
    ) -> Dict[str, Any]:
        """Execute edit via Playwright service."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.playwright_url}/edit-component",
                    json={
                        "html": html,
                        "selector": selector,
                        "edit_type": edit_type,
                        "edit_value": edit_value
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        return {
                            "success": True,
                            "html": data.get("html"),
                            "message": f"Successfully edited {selector}"
                        }
                    else:
                        return {"success": False, "error": data.get("error")}
                else:
                    return {"success": False, "error": f"Playwright error: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
editing_agent = EditingAgent()


async def edit_with_agent(html: str, instruction: str) -> Dict[str, Any]:
    """
    Convenience function to edit HTML using the editing agent.

    Args:
        html: Current HTML
        instruction: Edit instruction

    Returns:
        Edited HTML and metadata
    """
    return await editing_agent.edit(html, instruction)
