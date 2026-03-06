"""Tests for harness.model_provider — MockProvider only, no API calls."""

from harness.model_provider import (
    MockProvider,
    CompletionResult,
    ToolCall,
    ToolDefinition,
)


def test_mock_returns_default_response():
    provider = MockProvider()
    result = provider.complete("system", [{"role": "user", "content": "hello"}])
    assert isinstance(result, CompletionResult)
    assert result.content != ""
    assert result.stop_reason == "end_turn"


def test_mock_cycles_through_responses():
    responses = [
        CompletionResult(content="first", stop_reason="end_turn"),
        CompletionResult(content="second", stop_reason="end_turn"),
    ]
    provider = MockProvider(responses=responses)

    r1 = provider.complete("sys", [])
    r2 = provider.complete("sys", [])
    r3 = provider.complete("sys", [])  # wraps around

    assert r1.content == "first"
    assert r2.content == "second"
    assert r3.content == "first"


def test_mock_complete_with_tools():
    tool_response = CompletionResult(
        content="",
        tool_calls=[
            ToolCall(
                tool_name="lookup_member",
                tool_input={"member_id": "MBR-001"},
                tool_use_id="tc-1",
            )
        ],
        stop_reason="tool_use",
    )
    provider = MockProvider(responses=[tool_response])

    tools = [
        ToolDefinition(
            name="lookup_member",
            description="Look up a member",
            input_schema={"type": "object", "properties": {"member_id": {"type": "string"}}},
        )
    ]
    result = provider.complete_with_tools("system", [], tools)

    assert result.stop_reason == "tool_use"
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "lookup_member"


def test_mock_tracks_call_count():
    provider = MockProvider()
    assert provider._call_index == 0
    provider.complete("sys", [])
    provider.complete("sys", [])
    assert provider._call_index == 2


def test_completion_result_defaults():
    result = CompletionResult(content="test")
    assert result.tool_calls == []
    assert result.stop_reason == "end_turn"
    assert result.input_tokens == 0
    assert result.output_tokens == 0
