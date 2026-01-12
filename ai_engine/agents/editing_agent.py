"""
Editing Agent using OpenRouter API for intelligent website editing.

This agent can:
- Understand the current HTML structure
- Make targeted edits using tools
- Iterate and refine edits autonomously
- Handle complex multi-step editing tasks
- Maintain design consistency using design context
- Use Browserbase for cloud browser automation with visual verification
- Use screenshots as visual context to make accurate edits without asking questions
"""
from typing import List, Dict, Any, Optional
import json
import base64
import httpx
from logging_config import logger
from config import settings
from services.editing_system_prompt import (
    build_editing_system_prompt,
    build_user_prompt
)
from services.browserbase_service import get_browserbase_service, BrowserbaseService
from services.visual_verification import get_visual_verification_service, VisualVerificationService


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
                "description": "Replace a CSS class on a SPECIFIC element (not globally). Use the selector from the TARGET ELEMENT section to change only that element's classes. ALWAYS provide a selector to avoid changing other elements.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector to target the specific element (e.g., 'h1.hero-title', 'button.cta-primary:nth-of-type(1)'). Use the selector from TARGET ELEMENT section."
                        },
                        "old_class": {
                            "type": "string",
                            "description": "The class to replace on this element (e.g., 'bg-blue-500', 'text-white')"
                        },
                        "new_class": {
                            "type": "string",
                            "description": "The new class to use (e.g., 'bg-green-500', 'text-red-500')"
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
        },
        {
            "type": "function",
            "function": {
                "name": "capture_screenshot",
                "description": "Capture a screenshot of the current page state or a specific element. Use this to visually verify your changes or see the current state of the page. The screenshot will be shown to you.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "Optional CSS selector to capture just a specific element. Leave empty for full page."
                        },
                        "reason": {
                            "type": "string",
                            "description": "Why you're capturing this screenshot (e.g., 'verify color change', 'check layout')"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_element_visual_info",
                "description": "Get visual information about the selected element including its current colors, computed styles, and position on the page. Useful for understanding what color to change from.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector for the element. If empty, uses the currently selected element."
                        }
                    },
                    "required": []
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
        self.selected_element = None  # Store for auto-injection in tools
        self.max_iterations = 4  # Balanced: enough for complex edits, but encourages efficiency
        self.temperature = 0.15  # Low for consistency, but allows some flexibility

        # Browserbase integration (cloud browser)
        self.browserbase: BrowserbaseService = get_browserbase_service()
        self.visual_verifier: VisualVerificationService = get_visual_verification_service()
        self.use_browserbase = self.browserbase.is_available
        self.screenshots: List[bytes] = []  # Store screenshots for verification
        self.session_replay_url: Optional[str] = None

        logger.info(f"Initialized EditingAgent with model: {self.model}")
        logger.info(f"Browserbase available: {self.use_browserbase}")

    def _build_message_with_visual_context(
        self,
        user_prompt: str,
        screenshot: Optional[bytes] = None
    ) -> Any:
        """
        Build a message with visual context from screenshot.

        If a screenshot is available, creates a multi-part message with both
        text and image content. This gives the AI visual context so it can
        make accurate edits without asking questions.

        Args:
            user_prompt: The text prompt with edit instruction and HTML
            screenshot: Optional screenshot bytes from Browserbase

        Returns:
            String (text only) or list (multi-part with image)
        """
        if not screenshot:
            return user_prompt

        try:
            # Encode screenshot as base64
            screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')

            # Create multi-part message with image and text
            # Note: Claude models support vision through OpenRouter
            return [
                {
                    "type": "text",
                    "text": f"""## VISUAL CONTEXT
I've captured a screenshot of the current page. Use this to understand:
- What the page looks like visually
- Where elements are positioned
- Current colors, fonts, and styling
- The overall design aesthetic

DO NOT ask questions about the design - you can SEE it in the screenshot.
Make your best judgment based on this visual context.

{user_prompt}"""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{screenshot_b64}"
                    }
                }
            ]
        except Exception as e:
            logger.warning(f"Failed to encode screenshot: {e}")
            return user_prompt

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
            self.selected_element = selected_element  # Store for auto-injection in tools
            self.screenshots = []  # Reset screenshots for this edit session
            self.session_replay_url = None

            # Capture initial screenshot via local Playwright (fast, no cloud latency)
            initial_screenshot = await self._capture_local_screenshot(html)
            if initial_screenshot:
                self.screenshots.append(initial_screenshot)
                logger.info("EditingAgent: Captured initial screenshot via local Playwright")

            # Log what we received
            logger.info(f"EditingAgent: Instruction = '{instruction}'")
            if selected_element:
                logger.info(f"EditingAgent: Selected element selector = '{selected_element.get('selector', 'NONE')}'")
                logger.info(f"EditingAgent: Selected element tag = '{selected_element.get('tag', 'NONE')}'")
                logger.info(f"EditingAgent: Selected element classes = '{selected_element.get('classes', [])}'")
            else:
                logger.warning("EditingAgent: NO SELECTED ELEMENT - will edit globally!")

            # Build context-aware system prompt
            system_prompt = build_editing_system_prompt(
                design_context=design_context,
                selected_element=selected_element
            )

            # Build user prompt with HTML and selected element
            user_prompt = build_user_prompt(
                instruction=instruction,
                html=html,
                design_context=design_context,
                selected_element=selected_element
            )

            # Build the initial message with visual context if screenshot available
            initial_message_content = self._build_message_with_visual_context(
                user_prompt=user_prompt,
                screenshot=self.screenshots[0] if self.screenshots else None
            )

            # Run agent with tools
            messages = [{"role": "user", "content": initial_message_content}]
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
                            "iterations": iteration,
                            "screenshots_captured": len(self.screenshots)
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
                "iterations": iteration,
                "screenshots_captured": len(self.screenshots)
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
            # Helper to get selector with auto-injection from selected_element
            def get_selector():
                selector = tool_input.get("selector", "")
                if not selector and self.selected_element:
                    selector = self.selected_element.get("selector", "")
                    logger.info(f"EditingAgent: AUTO-INJECTING selector: '{selector}'")
                return selector

            if tool_name == "analyze_dom":
                return await self._analyze_dom(tool_input.get("html", self.current_html))

            elif tool_name == "edit_text":
                result = await self._edit_with_fallback(
                    html=self.current_html,  # Always use current state
                    selector=get_selector(),
                    edit_type="text",
                    edit_value=tool_input.get("new_text")
                )
                # Update current_html if successful
                if result.get("success") and result.get("html"):
                    self.current_html = result["html"]
                    logger.info(f"EditingAgent: edit_text SUCCESS - updated self.current_html")
                return result

            elif tool_name == "edit_style":
                result = await self._edit_with_fallback(
                    html=self.current_html,  # Always use current state
                    selector=get_selector(),
                    edit_type="style",
                    edit_value=tool_input.get("styles")
                )
                # Update current_html if successful
                if result.get("success") and result.get("html"):
                    self.current_html = result["html"]
                    logger.info(f"EditingAgent: edit_style SUCCESS - updated self.current_html")
                return result

            elif tool_name == "edit_attribute":
                result = await self._edit_with_fallback(
                    html=self.current_html,  # Always use current state
                    selector=get_selector(),
                    edit_type="attribute",
                    edit_value={
                        "name": tool_input.get("attribute"),
                        "value": tool_input.get("value")
                    }
                )
                # Update current_html if successful
                if result.get("success") and result.get("html"):
                    self.current_html = result["html"]
                    logger.info(f"EditingAgent: edit_attribute SUCCESS - updated self.current_html")
                return result

            elif tool_name == "replace_element":
                result = await self._edit_with_fallback(
                    html=self.current_html,  # Always use current state
                    selector=get_selector(),
                    edit_type="replace",
                    edit_value=tool_input.get("new_html")
                )
                # Update current_html if successful
                if result.get("success") and result.get("html"):
                    self.current_html = result["html"]
                    logger.info(f"EditingAgent: replace_element SUCCESS - updated self.current_html")
                return result

            elif tool_name == "modify_class":
                # Targeted class replacement using BeautifulSoup
                from bs4 import BeautifulSoup

                selector = tool_input.get("selector", "")
                old_class = tool_input.get("old_class", "")
                new_class = tool_input.get("new_class", "")

                # AUTO-INJECT: If no selector provided but we have a selected_element, use it
                if not selector and self.selected_element:
                    selector = self.selected_element.get("selector", "")
                    logger.info(f"EditingAgent: modify_class - AUTO-INJECTING selector from selected_element: '{selector}'")

                # Get outer_html for precise targeting (most reliable method)
                outer_html = self.selected_element.get("outer_html", "") if self.selected_element else ""

                logger.info(f"EditingAgent: modify_class - selector='{selector}', '{old_class}' -> '{new_class}'")
                logger.info(f"EditingAgent: modify_class - outer_html available: {bool(outer_html)}, length: {len(outer_html) if outer_html else 0}")

                if not old_class or not new_class:
                    return {"success": False, "error": "Missing old_class or new_class"}

                # STRATEGY: Try methods in order of precision
                # 1. outer_html replacement (MOST PRECISE - guaranteed to target exact element)
                # 2. BeautifulSoup selector (good but may match wrong element)
                # 3. Global replacement (LAST RESORT - affects all occurrences)

                # METHOD 1: outer_html replacement (MOST RELIABLE)
                if outer_html and old_class in outer_html:
                    logger.info(f"EditingAgent: modify_class - trying outer_html method (MOST PRECISE)")
                    new_outer_html = outer_html.replace(old_class, new_class)

                    # Check if outer_html exists in current HTML (exact match)
                    if outer_html in self.current_html:
                        modified_html = self.current_html.replace(outer_html, new_outer_html, 1)  # Replace only FIRST occurrence
                        if modified_html != self.current_html:
                            self.current_html = modified_html
                            logger.info(f"EditingAgent: modify_class SUCCESS (outer_html - PRECISE)")
                            return {
                                "success": True,
                                "html": modified_html,
                                "message": f"Changed class '{old_class}' to '{new_class}' on EXACT selected element"
                            }
                    else:
                        # Try with normalized whitespace
                        import re
                        normalized_outer = re.sub(r'\s+', ' ', outer_html.strip())
                        normalized_html = re.sub(r'\s+', ' ', self.current_html)

                        if normalized_outer in normalized_html:
                            # Find and replace in original HTML using fuzzy match
                            # Find a unique substring from outer_html that exists in current_html
                            class_pattern = re.escape(f'class="') + r'[^"]*' + re.escape(old_class) + r'[^"]*' + re.escape('"')
                            match = re.search(class_pattern, outer_html)
                            if match:
                                old_class_attr = match.group(0)
                                new_class_attr = old_class_attr.replace(old_class, new_class)
                                if old_class_attr in self.current_html:
                                    modified_html = self.current_html.replace(old_class_attr, new_class_attr, 1)
                                    if modified_html != self.current_html:
                                        self.current_html = modified_html
                                        logger.info(f"EditingAgent: modify_class SUCCESS (class attr replacement)")
                                        return {
                                            "success": True,
                                            "html": modified_html,
                                            "message": f"Changed class '{old_class}' to '{new_class}' via class attribute"
                                        }

                        logger.warning(f"EditingAgent: outer_html exact match not found, trying fingerprint method")

                # METHOD 1B: Text content fingerprint targeting
                # Use the element's text content to find the specific element
                if self.selected_element:
                    text_content = self.selected_element.get("text", "")
                    tag = self.selected_element.get("tag", "")

                    if text_content and len(text_content) > 5 and old_class in self.current_html:
                        import re
                        # Create a pattern to find the element containing this text with the old_class
                        # Escape special regex characters in text
                        escaped_text = re.escape(text_content[:50].strip())

                        # Pattern: find tag with old_class that contains our text
                        # This pattern finds: <tag ... class="...old_class..." ...>...text...</tag>
                        pattern = rf'(<{tag}[^>]*class="[^"]*){old_class}([^"]*"[^>]*>(?:[^<]*{escaped_text}|{escaped_text}[^<]*))'

                        match = re.search(pattern, self.current_html, re.IGNORECASE | re.DOTALL)
                        if match:
                            logger.info(f"EditingAgent: modify_class - found element via text fingerprint")
                            # Replace only in this specific match
                            start, end = match.span()
                            matched_text = match.group(0)
                            new_matched_text = matched_text.replace(old_class, new_class, 1)
                            modified_html = self.current_html[:start] + new_matched_text + self.current_html[end:]

                            if modified_html != self.current_html:
                                self.current_html = modified_html
                                logger.info(f"EditingAgent: modify_class SUCCESS (text fingerprint)")
                                return {
                                    "success": True,
                                    "html": modified_html,
                                    "message": f"Changed class '{old_class}' to '{new_class}' on element containing '{text_content[:30]}...'"
                                }

                        logger.warning(f"EditingAgent: fingerprint pattern didn't match, trying selector")

                # METHOD 2: BeautifulSoup selector
                if selector:
                    try:
                        soup = BeautifulSoup(self.current_html, 'html.parser')
                        element = soup.select_one(selector)

                        if element:
                            logger.info(f"EditingAgent: modify_class - found element with selector '{selector}'")
                            current_classes = element.get('class', [])
                            if isinstance(current_classes, str):
                                current_classes = current_classes.split()

                            if old_class in current_classes:
                                new_classes = [new_class if c == old_class else c for c in current_classes]
                                element['class'] = new_classes
                                modified_html = str(soup)
                                self.current_html = modified_html
                                logger.info(f"EditingAgent: modify_class SUCCESS (BeautifulSoup selector)")
                                return {
                                    "success": True,
                                    "html": modified_html,
                                    "message": f"Changed class '{old_class}' to '{new_class}' on element '{selector}'"
                                }
                            else:
                                # Class not on element, try adding new class
                                current_classes.append(new_class)
                                element['class'] = current_classes
                                modified_html = str(soup)
                                self.current_html = modified_html
                                logger.info(f"EditingAgent: modify_class - added {new_class} (old class not on element)")
                                return {
                                    "success": True,
                                    "html": modified_html,
                                    "message": f"Added class '{new_class}' to element '{selector}' ('{old_class}' was not on this element)"
                                }
                        else:
                            logger.warning(f"EditingAgent: selector '{selector}' not found in DOM")
                    except Exception as e:
                        logger.warning(f"EditingAgent: BeautifulSoup selector failed: {e}")

                # METHOD 3: Global replacement (LAST RESORT - WARN USER)
                if old_class in self.current_html:
                    logger.warning(f"EditingAgent: modify_class - using GLOBAL replacement (all methods failed)")
                    modified_html = self.current_html.replace(old_class, new_class)
                    self.current_html = modified_html
                    return {
                        "success": True,
                        "html": modified_html,
                        "message": f"WARNING: Changed ALL '{old_class}' to '{new_class}' globally (targeted methods failed)"
                    }

                logger.info(f"EditingAgent: modify_class FAILED - class '{old_class}' not found anywhere")
                return {"success": False, "error": f"Class '{old_class}' not found in HTML"}

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

            elif tool_name == "capture_screenshot":
                # Capture a screenshot for visual verification via local Playwright
                selector = tool_input.get("selector", "")
                reason = tool_input.get("reason", "visual check")

                # Auto-inject selector from selected_element if not provided
                if not selector and self.selected_element:
                    selector = self.selected_element.get("selector", "")

                try:
                    # Capture via local Playwright (fast, no cloud latency)
                    screenshot = await self._capture_local_screenshot(
                        self.current_html,
                        selector=selector if selector else None
                    )
                    if screenshot:
                        self.screenshots.append(screenshot)
                        logger.info(f"EditingAgent: capture_screenshot SUCCESS - reason: {reason}, selector: {selector or 'full page'}")
                        return {
                            "success": True,
                            "message": f"Screenshot captured for: {reason}",
                            "screenshot_index": len(self.screenshots) - 1,
                            "has_visual": True
                        }
                    else:
                        return {"success": False, "error": "Failed to capture screenshot"}
                except Exception as e:
                    logger.warning(f"EditingAgent: capture_screenshot failed: {e}")
                    return {"success": False, "error": str(e)}

            elif tool_name == "get_element_visual_info":
                # Get computed styles and visual info about an element via local Playwright
                selector = tool_input.get("selector", "")

                # Auto-inject selector from selected_element if not provided
                if not selector and self.selected_element:
                    selector = self.selected_element.get("selector", "")

                if not selector:
                    return {"success": False, "error": "No selector provided and no element selected"}

                try:
                    # Get visual info via local Playwright service
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            f"{self.playwright_url}/get-element-visual-info",
                            json={
                                "html": self.current_html,
                                "selector": selector
                            }
                        )

                        if response.status_code == 200:
                            data = response.json()
                            if data.get("success"):
                                logger.info(f"EditingAgent: get_element_visual_info SUCCESS - {selector}")
                                return {
                                    "success": True,
                                    "element": data.get("element"),
                                    "message": f"Visual info for element: {selector}"
                                }

                    # Fallback to selected_element data
                    if self.selected_element:
                        return {
                            "success": True,
                            "element": {
                                "tag": self.selected_element.get("tag"),
                                "classes": self.selected_element.get("classes", []),
                                "color_classes": self.selected_element.get("color_classes", []),
                                "text": self.selected_element.get("text", "")[:100]
                            },
                            "message": "Visual info from selected element metadata"
                        }
                    return {"success": False, "error": f"Element not found: {selector}"}
                except Exception as e:
                    logger.warning(f"EditingAgent: get_element_visual_info failed: {e}")
                    # Fallback to selected_element data
                    if self.selected_element:
                        return {
                            "success": True,
                            "element": {
                                "tag": self.selected_element.get("tag"),
                                "classes": self.selected_element.get("classes", []),
                                "color_classes": self.selected_element.get("color_classes", []),
                                "text": self.selected_element.get("text", "")[:100]
                            },
                            "message": "Visual info from selected element (fallback)"
                        }
                    return {"success": False, "error": str(e)}

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

    async def _edit_via_browserbase(
        self,
        selector: str,
        edit_type: str,
        edit_value: Any
    ) -> Dict[str, Any]:
        """
        Execute edit via Browserbase cloud browser.

        This is an alternative to local Playwright that provides:
        - Cloud-based execution (no local resources)
        - Session replay for debugging
        - Screenshot capture for verification

        Args:
            selector: CSS selector for target element
            edit_type: Type of edit (text, style, class, attribute, replace)
            edit_value: Value to apply

        Returns:
            Dict with success, html, and message
        """
        if not self.browserbase.is_available:
            return {"success": False, "error": "Browserbase not available"}

        try:
            # Map edit types to Browserbase execute_edit types
            type_mapping = {
                "text": "text",
                "style": "style",
                "class": "class",
                "attribute": "attribute",
                "replace": "outerHtml"
            }

            bb_edit_type = type_mapping.get(edit_type, edit_type)

            # Prepare value based on type
            if edit_type == "style" and isinstance(edit_value, dict):
                edit_value = json.dumps(edit_value)
            elif edit_type == "attribute" and isinstance(edit_value, dict):
                edit_value = f"{edit_value.get('name')}={edit_value.get('value', '')}"

            # Execute the edit
            result = await self.browserbase.execute_edit(
                selector=selector,
                edit_type=bb_edit_type,
                value=str(edit_value)
            )

            if result.get("success"):
                # Get the updated HTML from browser
                html = await self.browserbase.get_html()
                if html:
                    return {
                        "success": True,
                        "html": html,
                        "message": f"Successfully edited {selector} via Browserbase"
                    }
                return {"success": False, "error": "Failed to get updated HTML"}
            else:
                return {"success": False, "error": result.get("error", "Edit failed")}

        except Exception as e:
            logger.error(f"Browserbase edit error: {e}")
            return {"success": False, "error": str(e)}

    async def _edit_with_fallback(
        self,
        html: str,
        selector: str,
        edit_type: str,
        edit_value: Any
    ) -> Dict[str, Any]:
        """
        Execute edit with Browserbase first, fallback to local Playwright.

        Args:
            html: Current HTML
            selector: CSS selector
            edit_type: Type of edit
            edit_value: Value to apply

        Returns:
            Edit result dict
        """
        # Use local Playwright for edits (fast, no cloud latency)
        return await self._edit_via_playwright(html, selector, edit_type, edit_value)

    async def _capture_local_screenshot(
        self,
        html: str,
        selector: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Capture screenshot via local Playwright service.

        This provides visual context without Browserbase cloud latency.
        Typical latency: ~300-500ms (vs ~2-3s with Browserbase)

        Args:
            html: HTML content to render
            selector: Optional CSS selector for element screenshot

        Returns:
            Screenshot as bytes, or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.playwright_url}/screenshot",
                    json={
                        "html": html,
                        "selector": selector,
                        "full_page": False  # Viewport only for speed
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("screenshot"):
                        # Decode base64 to bytes
                        screenshot_bytes = base64.b64decode(data["screenshot"])
                        logger.debug(f"Local screenshot captured: {len(screenshot_bytes)} bytes")
                        return screenshot_bytes

                logger.warning(f"Local screenshot failed: {response.status_code}")
                return None

        except Exception as e:
            logger.warning(f"Local screenshot error: {e}")
            return None


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
