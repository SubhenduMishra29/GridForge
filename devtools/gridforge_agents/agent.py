from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import Settings
from .ollama import OllamaClient
from .tools import ToolRunner


class AgentExecutionError(RuntimeError):
    """Raised when an agent exceeds its bounded tool execution budget."""


def run_agent(
    *,
    client: OllamaClient,
    settings: Settings,
    model: str,
    system_prompt: str,
    user_prompt: str,
    root: Path,
    writable: bool = False,
    temperature: float = 0.1,
) -> str:
    tool_runner = ToolRunner(root, writable=writable)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    tool_calls_used = 0

    for _ in range(settings.max_tool_rounds):
        response = client.chat(
            model=model,
            messages=messages,
            tools=tool_runner.schemas,
            temperature=temperature,
        )
        message = response.get("message") or {}
        calls = message.get("tool_calls") or []
        content = message.get("content") or ""
        if not calls:
            if content.strip():
                return content.strip()
            raise AgentExecutionError(
                "The model returned neither a final response nor a tool call. "
                "Check that the selected Ollama model supports tool calling."
            )

        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": content,
            "tool_calls": calls,
        }
        messages.append(assistant_message)

        for call in calls:
            tool_calls_used += 1
            if tool_calls_used > settings.max_tool_rounds * 3:
                raise AgentExecutionError("Agent exceeded the maximum number of tool calls.")
            function = call.get("function") or {}
            name = function.get("name", "")
            arguments = function.get("arguments") or {}
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            if not isinstance(arguments, dict):
                arguments = {}
            try:
                output = tool_runner.execute(name, arguments)
            except Exception as exc:
                output = "TOOL ERROR (%s): %s" % (name, exc)
            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": output[:20_000],
            })

    raise AgentExecutionError(
        "Agent reached %d tool rounds without producing a final answer."
        % settings.max_tool_rounds
    )
