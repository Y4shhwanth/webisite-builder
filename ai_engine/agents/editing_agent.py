"""
Editing Agent using OpenRouter API for intelligent website editing.

This agent can:
- Understand the current HTML structure
- Make targeted edits using tools
- Iterate and refine edits autonomously
- Handle complex multi-step editing tasks
- Maintain design consistency using design context
"""
from typing import List, Dict, Any, Optional
import json
import httpx
from logging_config import logger
from config import settings
from services.editing_system_prompt import (
    build_editing_system_prompt,
    build_user_prompt
)


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
                "name": "modify_class",
                "description": "Add, remove, or replace CSS classes directly in the HTML. Best for Tailwind CSS class changes. This works by string replacement and doesn't require finding elements.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "old_class": {
                            "type": "string",
                            "description": "The class to find and replace (e.g., 'bg-primary', 'text-red-500')"
                        },
                        "new_class": {
                            "type": "string",
                            "description": "The new class to use (e.g., 'bg-green-500', 'text-blue-500')"
                        }
                    },
                    "required": ["old_class", "new_class"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "find_and_replace",
                "description": "Find and replace text/HTML directly in the source. Use for targeted changes when selectors don't work.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "find": {
                            "type": "string",
                            "description": "The exact text or HTML to find"
                        },
                        "replace": {
                            "type": "string",
                            "description": "The text or HTML to replace it with"
                        }
                    },
                    "required": ["find", "replace"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "finalize_edit",
                "description": "Call this when you're done editing. The system will use the HTML from your previous edit tools automatically. Just provide a summary of what you changed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Brief summary of changes made (e.g., 'Changed header color from blue to green')"
                        }
                    },
                    "required": ["summary"]
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
        max_iterations: int = 5,
        design_context: Optional[Dict[str, Any]] = None,
        selected_element: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Edit HTML based on user instruction using tool-based agent.

        Args:
            html: Current HTML content
            instruction: User's edit instruction
            max_iterations: Max tool use iterations
            design_context: Extracted design metadata (fonts, colors, sections)
            selected_element: Currently selected element info (selector, tag, classes)

        Returns:
            Edited HTML and metadata
        """
        try:
            logger.info(f"EditingAgent: Starting edit - {instruction[:50]}...")
            if design_context:
                logger.info(f"EditingAgent: Using design context with template: {design_context.get('template_id', 'unknown')}")
            if selected_element:
                logger.info(f"EditingAgent: Target element: {selected_element.get('selector', 'none')}")

            self.current_html = html

            # Build context-aware system prompt
            system_prompt = build_editing_system_prompt(
                design_context=design_context,
                selected_element=selected_element
            )

            # Build user prompt with HTML
            user_prompt = build_user_prompt(
                instruction=instruction,
                html=html,
                design_context=design_context
            )

            # Run agent with tools
            messages = [{"role": "user", "content": user_prompt}]
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
                                {"role": "system", "content": system_prompt},
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
                        # Always use self.current_html - it has been modified by previous tools
                        # The AI should NOT pass HTML, just a summary
                        edit_summary = tool_input.get("summary", "Edit completed")
                        final_html = self.current_html

                        logger.info(f"EditingAgent: finalize_edit called - summary: {edit_summary}")
                        logger.info(f"EditingAgent: Using self.current_html with length: {len(final_html)}")

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

            elif tool_name == "modify_class":
                # Direct string replacement for CSS classes
                old_class = tool_input.get("old_class", "")
                new_class = tool_input.get("new_class", "")
                logger.info(f"EditingAgent: modify_class - '{old_class}' -> '{new_class}'")
                if old_class and new_class:
                    if old_class in self.current_html:
                        modified_html = self.current_html.replace(old_class, new_class)
                        self.current_html = modified_html
                        logger.info(f"EditingAgent: modify_class SUCCESS")
                        return {
                            "success": True,
                            "html": modified_html,
                            "message": f"Replaced class '{old_class}' with '{new_class}'"
                        }
                    else:
                        logger.info(f"EditingAgent: modify_class FAILED - class not found")
                        return {"success": False, "error": f"Class '{old_class}' not found in HTML"}
                return {"success": False, "error": "Missing old_class or new_class"}

            elif tool_name == "find_and_replace":
                # Direct string replacement
                find_str = tool_input.get("find", "")
                replace_str = tool_input.get("replace", "")
                logger.info(f"EditingAgent: find_and_replace - finding: '{find_str[:100]}...'")
                if find_str:
                    if find_str in self.current_html:
                        modified_html = self.current_html.replace(find_str, replace_str)
                        self.current_html = modified_html
                        logger.info(f"EditingAgent: find_and_replace SUCCESS")
                        return {
                            "success": True,
                            "html": modified_html,
                            "message": f"Replaced '{find_str[:50]}...' successfully"
                        }
                    else:
                        logger.info(f"EditingAgent: find_and_replace FAILED - text not found")
                        return {"success": False, "error": f"Text '{find_str[:50]}...' not found in HTML"}
                return {"success": False, "error": "Missing find parameter"}

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


async def edit_with_agent(
    html: str,
    instruction: str,
    design_context: Optional[Dict[str, Any]] = None,
    selected_element: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to edit HTML using the editing agent.

    Args:
        html: Current HTML
        instruction: Edit instruction
        design_context: Extracted design metadata (fonts, colors, sections)
        selected_element: Currently selected element info

    Returns:
        Edited HTML and metadata
    """
    return await editing_agent.edit(
        html=html,
        instruction=instruction,
        design_context=design_context,
        selected_element=selected_element
    )
