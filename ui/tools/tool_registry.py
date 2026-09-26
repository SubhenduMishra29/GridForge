# ============================================================
# Author: Subhendu Mishra
# File: ui/tools/tool_registry.py
# GridForge V2 — Legacy ToolRegistry Compatibility Shell
# ============================================================
"""Non-authoritative compatibility shell for the retired ToolRegistry.

The frozen V2 runtime authority is ``ui.core.tool_manager.ToolManager``.
Factories are supplied by ``create_default_tool_factories()`` and runtime
tool lifecycle is owned exclusively by ToolManager.

This module intentionally contains no tool catalogue, no registration
implementation, and no runtime tool state. It remains import-compatible
only so legacy callers fail explicitly instead of silently creating a
competing tool authority.
"""

from __future__ import annotations

from typing import Any


class ToolRegistry:
    """Retired compatibility type; never instantiate in the V2 runtime."""

    def __init__(self, *_: Any, **__: Any) -> None:
        raise RuntimeError(
            "ToolRegistry is retired and non-authoritative. "
            "Use ui.core.tool_manager.ToolManager with "
            "create_default_tool_factories()."
        )

    def __getattr__(self, name: str) -> Any:
        raise RuntimeError(
            f"ToolRegistry is retired; attribute {name!r} is unavailable. "
            "Use ToolManager."
        )


__all__ = ["ToolRegistry"]
