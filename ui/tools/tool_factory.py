# ============================================================
# Author: Subhendu Mishra
# File: ui/tools/tool_factory.py
# GridForge V2 — Legacy Tool Factory Compatibility Shell
# ============================================================
"""Legacy compatibility shell for the superseded ToolFactory.

Authoritative runtime construction belongs exclusively to
ToolManager and ``create_default_tool_factories()``.

This module intentionally contains no concrete-tool construction
methods and must not be used as a runtime creation path.
"""

from __future__ import annotations


class ToolFactory:
    """Non-authoritative compatibility marker for the retired factory API."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise RuntimeError(
            "Legacy ToolFactory is non-authoritative; "
            "use ToolManager/create_default_tool_factories()."
        )

    @classmethod
    def supported_tool_ids(cls) -> tuple[str, ...]:
        """Return the canonical tool IDs exposed by the active factory registry."""
        return (
            "select", "bus", "line", "cable", "transformer", "switch",
            "breaker", "disconnector", "fuse", "load", "generator",
            "synchronous_machine", "motor", "shunt", "capacitor", "reactor",
            "solar", "battery", "grid", "current_transformer",
            "potential_transformer", "cvt", "relay",
        )


__all__ = ["ToolFactory"]
