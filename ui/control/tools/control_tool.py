"""Transient Control tool abstraction over the existing Application command path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.application.command import Command


@dataclass(frozen=True, slots=True)
class ControlTool:
    tool_id: str
    display_name: str
    application: Any

    def execute(self, command: Command) -> Any:
        if not isinstance(command, Command):
            raise TypeError("command must be an Application Command.")
        return self.application.execute(command)


__all__ = ["ControlTool"]
