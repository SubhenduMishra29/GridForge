"""
File: ui/modes.py
Location: gridforge/ui/modes.py

Purpose:
    Defines interaction modes for the editor.

Why this file exists:
    The editor must behave differently based on user intent:
        - Selecting objects
        - Placing buses
        - Drawing lines

    Hardcoding behavior leads to chaos.
    Modes enforce clean, predictable interaction logic.

Responsibilities:
    - Provide a central definition of modes
    - Prevent magic strings across the codebase

Architecture Role:
    Shared UI State Definition
"""

from enum import Enum, auto


class EditorMode(Enum):
    """Defines all supported editor interaction modes."""

    SELECT = auto()
    ADD_BUS = auto()
    ADD_LINE = auto()
