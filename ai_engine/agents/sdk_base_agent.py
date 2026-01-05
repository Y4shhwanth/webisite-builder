"""
Base Agent class for Claude Agents SDK with autonomous iteration
"""
from typing import List, Dict, Any, Optional, AsyncIterator
from anthropic import Anthropic
from logging_config import logger
from config import settings


class SDKBaseAgent:
    """
    Base class for Claude Agents SDK agents with autonomous iteration.

    This provides a foundation for agents that can:
    - Execute tasks autonomously
    - Iterate until quality threshold met
    - Self-review and refine outputs
    - Use MCP tools for specialized operations
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        model: str = None,
        max_iterations: int = 5,
        temperature: float = 0.7
    ):
        """
        Initialize base agent.

        Args:
            name: Agent name
            system_prompt: System prompt defining agent behavior
            model: Claude model to use (defaults to settings)
            max_iterations: Maximum refinement iterations
            temperature: Sampling temperature
        """
        self.name = name
        self.system_prompt = system_prompt
        self.model = model or settings.CLAUDE_MODEL_SONNET
        self.max_iterations = max_iterations
        self.temperature = temperature

        # Initialize Anthropic client
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        logger.info(
            f"Initialized agent: {name}",
            model=self.model,
            max_iterations=max_iterations
        )

    async def run(
        self,
        prompt: str,
        tools: Optional[List[Dict]] = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        Run agent with single execution (no refinement).

        Args:
            prompt: User prompt
            tools: List of tool definitions
            max_tokens: Maximum tokens to generate

        Returns:
            Agent response with content and metadata
        """
        try:
            logger.info(f"{self.name}: Starting execution")

            max_tokens = max_tokens or settings.MAX_TOKENS

            # Prepare messages
            messages = [{"role": "user", "content": prompt}]

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=messages,
                tools=tools or []
            )

            # Extract content
            content = self._extract_content(response)

            logger.info(f"{self.name}: Execution completed")

            return {
                "success": True,
                "content": content,
                "model": self.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "stop_reason": response.stop_reason
            }

        except Exception as e:
            logger.error(f"{self.name}: Execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def run_with_refinement(
        self,
        prompt: str,
        refinement_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        Run agent with automatic refinement passes.

        Workflow:
        1. Pass 1: Initial execution
        2. Pass 2: Self-review (agent reads own output)
        3. Pass 3: Refine issues found
        4. Pass N: Iterate until quality threshold or max_iterations

        Args:
            prompt: Initial user prompt
            refinement_prompt: Prompt for refinement pass
            tools: List of tool definitions
            max_tokens: Maximum tokens per pass

        Returns:
            Final refined output with metadata
        """
        try:
            logger.info(f"{self.name}: Starting refinement workflow")

            iteration_results = []
            max_tokens = max_tokens or settings.MAX_TOKENS

            # Pass 1: Initial execution
            logger.info(f"{self.name}: Pass 1 - Initial execution")
            result = await self.run(prompt, tools, max_tokens)

            if not result.get("success"):
                return result

            iteration_results.append(result)
            current_output = result.get("content", "")

            # Refinement passes (if refinement_prompt provided)
            if refinement_prompt and self.max_iterations > 1:
                for iteration in range(2, self.max_iterations + 1):
                    logger.info(f"{self.name}: Pass {iteration} - Refinement")

                    # Construct refinement prompt with previous output
                    refinement_full_prompt = f"""{refinement_prompt}

PREVIOUS OUTPUT:
{current_output}

Please review the above output and refine it if needed. If it's already high quality, confirm it's ready."""

                    refine_result = await self.run(
                        refinement_full_prompt,
                        tools,
                        max_tokens
                    )

                    if not refine_result.get("success"):
                        break

                    iteration_results.append(refine_result)
                    current_output = refine_result.get("content", "")

                    # Check if agent says output is ready
                    if self._is_output_ready(current_output):
                        logger.info(f"{self.name}: Output ready after {iteration} passes")
                        break

            logger.info(
                f"{self.name}: Refinement completed",
                total_passes=len(iteration_results)
            )

            # Calculate total usage
            total_input_tokens = sum(
                r.get("usage", {}).get("input_tokens", 0)
                for r in iteration_results
            )
            total_output_tokens = sum(
                r.get("usage", {}).get("output_tokens", 0)
                for r in iteration_results
            )

            return {
                "success": True,
                "content": current_output,
                "iterations": len(iteration_results),
                "model": self.model,
                "usage": {
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens
                },
                "iteration_details": iteration_results
            }

        except Exception as e:
            logger.error(f"{self.name}: Refinement failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_content(self, response) -> str:
        """Extract text content from Claude API response"""
        content_blocks = []

        for block in response.content:
            if hasattr(block, 'text'):
                content_blocks.append(block.text)

        return "\n".join(content_blocks)

    def _is_output_ready(self, output: str) -> bool:
        """
        Check if output indicates agent is satisfied with quality.

        This looks for keywords indicating the agent believes output is ready.
        """
        ready_keywords = [
            "output is ready",
            "looks good",
            "no further changes needed",
            "satisfied with",
            "high quality",
            "ready for use"
        ]

        output_lower = output.lower()
        return any(keyword in output_lower for keyword in ready_keywords)
