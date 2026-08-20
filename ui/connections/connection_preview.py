# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/connections/connection_preview.py
#
# Purpose:
#     Stores temporary state while the user is interactively
#     creating an SLD connection.
#
# Architectural Role:
#     Keeps incomplete connection state outside LineTool and
#     outside QGraphicsScene.
#
# Responsibilities:
#     - store source terminal;
#     - store current target terminal;
#     - store pointer/cursor position;
#     - indicate validity;
#     - provide reset lifecycle.
#
# Does NOT:
#     - commit connections;
#     - render graphics;
#     - mutate the electrical network.
#
# ============================================================

"""
GridForge V2 — Connection Preview.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


Point = Tuple[float, float]


@dataclass
class ConnectionPreview:
    """
    Temporary state for an in-progress connection.
    """

    active: bool = False

    source_terminal_id: Optional[str] = None

    target_terminal_id: Optional[str] = None

    cursor_position: Optional[Point] = None

    valid: bool = False

    validation_reason: str = ""

    def begin(
        self,
        source_terminal_id: str,
    ) -> None:
        if not source_terminal_id:
            raise ValueError(
                "source_terminal_id must not be empty"
            )

        self.active = True
        self.source_terminal_id = (
            source_terminal_id
        )
        self.target_terminal_id = None
        self.cursor_position = None
        self.valid = False
        self.validation_reason = ""

    def update_target(
        self,
        target_terminal_id: Optional[str],
        *,
        valid: bool,
        reason: str = "",
    ) -> None:
        if not self.active:
            raise RuntimeError(
                "Connection preview is not active"
            )

        self.target_terminal_id = (
            target_terminal_id
        )
        self.valid = bool(valid)
        self.validation_reason = reason

    def update_cursor(
        self,
        position: Point,
    ) -> None:
        if not self.active:
            raise RuntimeError(
                "Connection preview is not active"
            )

        self.cursor_position = (
            float(position[0]),
            float(position[1]),
        )

    def cancel(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.active = False
        self.source_terminal_id = None
        self.target_terminal_id = None
        self.cursor_position = None
        self.valid = False
        self.validation_reason = ""

    @property
    def can_commit(self) -> bool:
        return (
            self.active
            and self.valid
            and self.source_terminal_id is not None
            and self.target_terminal_id is not None
        )
