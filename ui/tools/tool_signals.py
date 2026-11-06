# ============================================================
# File: ui/tools/tool_signals.py
# GridForge V2 — Tool Signals
# ============================================================
"""
Signal definitions for GridForge V2 UI tools.

Tool signals provide the notification boundary between the tool
layer and the surrounding UI composition/controller layer.

Signals communicate interaction state; they do not become an
alternate application-state mechanism.

Architecture
------------

    Concrete Tool
         │
         ▼
      ToolSignals
       ┌──┼──────────────┐
       │  │              │
       ▼  ▼              ▼
    activated  state_changed  result
       │          │            │
       └──────────┴────────────┘
                    │
                    ▼
          InteractionController /
          ToolController / UI

Rules
-----
    - Core remains authoritative for domain state.
    - Commands remain authoritative for mutation intent.
    - Tool signals are notifications only.
    - Signals must not contain business logic.
    - No direct Core mutation is performed here.
    - Qt access is routed through ui.core.qt.

The module uses the project's central Qt abstraction rather than
importing PySide6 directly.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QObject, Signal

from ui.tools.tool_event import ToolEvent
from ui.tools.tool_result import ToolResult
from ui.tools.tool_state import ToolState


class ToolSignals(QObject):
    """
    QObject containing the signal surface shared by UI tools.

    A separate signal object keeps concrete tools focused on
    interaction behavior while providing a consistent notification
    contract to ToolController and InteractionController.

    Signals
    -------
    activated:
        Emitted when a tool becomes active.

    deactivated:
        Emitted when a tool becomes inactive.

    state_changed:
        Emitted when transient tool state changes.

    event_received:
        Emitted when a normalized ToolEvent reaches the tool.

    result:
        Emitted after a tool processes an interaction.

    cancelled:
        Emitted when an active interaction is cancelled.

    reset:
        Emitted when transient tool state is reset.

    error:
        Emitted when a tool reports an interaction error.
    """

    activated = Signal(str)
    deactivated = Signal(str)

    state_changed = Signal(object)

    event_received = Signal(object)
    result = Signal(object)

    cancelled = Signal(str)
    reset = Signal(str)

    error = Signal(str, object)

    def __init__(
        self,
        tool_id: str,
        parent: Optional[QObject] = None,
    ) -> None:
        """
        Initialize the signal surface.

        Parameters
        ----------
        tool_id:
            Stable GridForge tool identifier.

        parent:
            Optional Qt parent.
        """

        super().__init__(
            parent
        )

        if not isinstance(
            tool_id,
            str,
        ) or not tool_id.strip():
            raise ValueError(
                "tool_id must be a non-empty string."
            )

        self._tool_id = tool_id

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def tool_id(
        self,
    ) -> str:
        """
        Return the owning tool identifier.
        """

        return self._tool_id

    # ========================================================
    # NOTIFICATION HELPERS
    # ========================================================

    def emit_activated(
        self,
    ) -> None:
        """
        Notify listeners that the tool became active.
        """

        self.activated.emit(
            self._tool_id
        )

    # --------------------------------------------------------

    def emit_deactivated(
        self,
    ) -> None:
        """
        Notify listeners that the tool became inactive.
        """

        self.deactivated.emit(
            self._tool_id
        )

    # --------------------------------------------------------

    def emit_state_changed(
        self,
        state: ToolState,
    ) -> None:
        """
        Notify listeners that tool state changed.
        """

        if not isinstance(
            state,
            ToolState,
        ):
            raise TypeError(
                "state must be a ToolState."
            )

        self.state_changed.emit(
            state
        )

    # --------------------------------------------------------

    def emit_event(
        self,
        event: ToolEvent,
    ) -> None:
        """
        Notify listeners that a ToolEvent was received.
        """

        if not isinstance(
            event,
            ToolEvent,
        ):
            raise TypeError(
                "event must be a ToolEvent."
            )

        self.event_received.emit(
            event
        )

    # --------------------------------------------------------

    def emit_result(
        self,
        result: ToolResult,
    ) -> None:
        """
        Notify listeners of a tool-processing result.
        """

        if not isinstance(
            result,
            ToolResult,
        ):
            raise TypeError(
                "result must be a ToolResult."
            )

        self.result.emit(
            result
        )

    # --------------------------------------------------------

    def emit_cancelled(
        self,
    ) -> None:
        """
        Notify listeners that the current interaction was cancelled.
        """

        self.cancelled.emit(
            self._tool_id
        )

    # --------------------------------------------------------

    def emit_reset(
        self,
    ) -> None:
        """
        Notify listeners that transient tool state was reset.
        """

        self.reset.emit(
            self._tool_id
        )

    # --------------------------------------------------------

    def emit_error(
        self,
        error: BaseException,
        *,
        message: Optional[str] = None,
    ) -> None:
        """
        Notify listeners of a tool-level interaction error.

        The exception object is carried as an opaque notification
        payload. Error ownership remains with the caller.
        """

        if not isinstance(
            error,
            BaseException,
        ):
            raise TypeError(
                "error must be a BaseException."
            )

        self.error.emit(
            message or str(error),
            error,
        )

    # ========================================================
    # CONVENIENCE NOTIFICATION
    # ========================================================

    def emit_result_and_state(
        self,
        result: ToolResult,
        state: Optional[ToolState] = None,
    ) -> None:
        """
        Emit a result and, when supplied, the resulting state.

        This helper does not infer or construct state.
        """

        self.emit_result(
            result
        )

        if state is not None:
            self.emit_state_changed(
                state
            )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            f"{type(self).__name__}("
            f"tool_id={self._tool_id!r}"
            ")"
        )


__all__ = [
    "ToolSignals",
]
