"""
Model provider abstraction — decouples the harness from any specific LLM SDK.

The harness NEVER imports or calls a specific model SDK directly.
To swap models: implement ModelProvider with your provider's SDK.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict  # JSON Schema — NOT model-specific format


@dataclass
class ToolCall:
    tool_name: str
    tool_input: dict
    tool_use_id: str


@dataclass
class CompletionResult:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"  # 'end_turn' | 'tool_use' | 'max_tokens'
    input_tokens: int = 0
    output_tokens: int = 0


class ModelProvider(ABC):
    """
    Abstract interface between the harness and any LLM.
    The harness NEVER imports or calls a specific model SDK directly.
    To swap models: implement ModelProvider with your provider's SDK.
    GPT-4o -> OpenAIProvider, Gemini -> GeminiProvider. Zero harness changes required.
    """

    @abstractmethod
    def complete_with_tools(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[ToolDefinition],
        max_tokens: int = 4096,
    ) -> CompletionResult: ...

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 4096,
    ) -> CompletionResult: ...


class ClaudeProvider(ModelProvider):
    """Default implementation using Anthropic SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package required for ClaudeProvider. "
                "Install with: pip install anthropic"
            )
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)

    def _to_anthropic_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in tools
        ]

    def _parse_response(self, response) -> CompletionResult:
        content_text = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        tool_name=block.name,
                        tool_input=block.input,
                        tool_use_id=block.id,
                    )
                )

        return CompletionResult(
            content=content_text,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason or "end_turn",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def complete_with_tools(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[ToolDefinition],
        max_tokens: int = 4096,
    ) -> CompletionResult:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
            tools=self._to_anthropic_tools(tools),
        )
        return self._parse_response(response)

    def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 4096,
    ) -> CompletionResult:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        return self._parse_response(response)


class MockProvider(ModelProvider):
    """For testing without API calls. Returns canned responses."""

    def __init__(self, responses: Optional[list[CompletionResult]] = None):
        self._responses = responses or [
            CompletionResult(
                content="I need more information to make a determination.",
                stop_reason="end_turn",
            )
        ]
        self._call_index = 0

    def _next_response(self) -> CompletionResult:
        response = self._responses[self._call_index % len(self._responses)]
        self._call_index += 1
        return response

    def complete_with_tools(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[ToolDefinition],
        max_tokens: int = 4096,
    ) -> CompletionResult:
        return self._next_response()

    def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 4096,
    ) -> CompletionResult:
        return self._next_response()
