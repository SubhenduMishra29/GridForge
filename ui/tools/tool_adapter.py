# ============================================================
# File: ui/tools/tool_adapter.py
# GridForge V2 — Tool Adapter
# ============================================================
"""
Adapter between normalized ToolEvent objects and ToolBase tools.

ToolAdapter provides the boundary between the normalized,
UI-independent tool event model and the concrete tool interface.

Architecture
------------

    GraphicsView / InteractionController
                 │
                 ▼
              ToolEvent
                 │
                 ▼
            ToolAdapter
                 │
                 ▼
              ToolBase
                 │
                 ▼
            ToolResult
                 │
                 ▼
        InteractionController

Responsibilities
----------------
ToolAdapter:

    - normalize interaction dispatch;
    - route ToolEvent instances to the appropriate ToolBase
      handler;
    - normalize legacy/simple boolean handler responses into
      ToolResult;
    - keep ToolManager independent from raw event adaptation;
    - provide a single dispatch entry point.

ToolAdapter does NOT:

    - create or execute commands;
    - mutate Core;
    - perform snapping;
    - perform electrical validation;
    - manage tool registration;
    - activate arbitrary tools;
    - own Qt events.

The adapter is intentionally small. Qt-specific event conversion
belongs above this layer, normally in InteractionController or
GraphicsView.

No Qt dependency is permitted in this module.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from ui.tools.tool_base import ToolBase
from ui.tools.tool_event import ToolEvent, ToolEventType
from ui.tools.tool_result import ToolResult


class ToolAdapter:
    """
    Dispatch normalized ToolEvent objects to a ToolBase instance.

    ToolAdapter is stateless with respect to application state.
    The wrapped tool remains the owner of its transient
    interaction state.
    """

    def __init__(
        self,
        tool: ToolBase,
    ) -> None:
        """
        Initialize the adapter.

        Parameters
        ----------
        tool:
            ToolBase instance to which events are dispatched.
        """

        if not isinstance(
            tool,
            ToolBase,
        ):
            raise TypeError(
                "tool must be an instance of ToolBase."
            )

        self._tool = tool

    # ========================================================
    # TOOL ACCESS
    # ========================================================

    @property
    def tool(
        self,
    ) -> ToolBase:
        """
        Return the wrapped tool.
        """

        return self._tool

    # --------------------------------------------------------

    @property
    def tool_id(
        self,
    ) -> str:
        """
        Return the wrapped tool's stable identifier.
        """

        return self._tool.tool_id

    # ========================================================
    # DISPATCH
    # ========================================================

    def dispatch(
        self,
        event: ToolEvent,
    ) -> ToolResult:
        """
        Dispatch a normalized ToolEvent to the wrapped tool.

        The adapter maps normalized event types to the
        corresponding ToolBase operation.

        Raises
        ------
        TypeError
            If event is not a ToolEvent.

        ValueError
            If the event type has no supported dispatch mapping.
        """

        if not isinstance(
            event,
            ToolEvent,
        ):
            raise TypeError(
                "event must be a ToolEvent."
            )

        handler = self._handler_for(
            event.event_type
        )

        if handler is None:
            raise ValueError(
                "Unsupported ToolEventType: "
                f"{event.event_type!r}."
            )

        try:
            result = handler(
                event
            )
        except TypeError as exc:
            # ToolBase implementations created before the
            # normalized ToolEvent contract may expose handlers
            # without an event parameter. Do not silently retry
            # those handlers because doing so could hide genuine
            # TypeErrors raised inside the handler.
            raise TypeError(
                f"Tool {self.tool_id!r} does not implement the "
                f"expected handler contract for "
                f"{event.event_type.value!r}."
            ) from exc

        return self._normalize_result(
            result
        )

    # ========================================================
    # SPECIAL DISPATCH
    # ========================================================

    def cancel(
        self,
    ) -> ToolResult:
        """
        Cancel the wrapped tool's current interaction.

        This bypasses ToolEvent creation because cancellation is
        a direct lifecycle operation exposed by ToolBase.
        """

        result = self._tool.cancel()

        return self._normalize_result(
            result,
            default=ToolResult.cancelled(),
        )

    # --------------------------------------------------------

    def reset(
        self,
    ) -> ToolResult:
        """
        Reset the wrapped tool's transient state.
        """

        result = self._tool.reset()

        if result is None:
            return ToolResult.changed(
                message="Tool state reset."
            )

        return self._normalize_result(
            result,
            default=ToolResult.changed(
                message="Tool state reset."
            ),
        )

    # --------------------------------------------------------

    def activate(
        self,
    ) -> ToolResult:
        """
        Activate the wrapped tool.

        Lifecycle activation is delegated to ToolBase.
        """

        result = self._tool.activate()

        if result is None:
            return ToolResult.changed(
                message="Tool activated."
            )

        return self._normalize_result(
            result,
            default=ToolResult.changed(
                message="Tool activated."
            ),
        )

    # --------------------------------------------------------

    def deactivate(
        self,
    ) -> ToolResult:
        """
        Deactivate the wrapped tool.
        """

        result = self._tool.deactivate()

        if result is None:
            return ToolResult.changed(
                message="Tool deactivated."
            )

        return self._normalize_result(
            result,
            default=ToolResult.changed(
                message="Tool deactivated."
            ),
        )

    # ========================================================
    # EVENT HANDLER RESOLUTION
    # ========================================================

    def _handler_for(
        self,
        event_type: ToolEventType,
    ) -> Optional[Callable[[ToolEvent], Any]]:
        """
        Resolve a ToolBase handler for an event type.
        """

        handlers: dict[
            ToolEventType,
            str,
        ] = {
            ToolEventType.MOUSE_PRESS: "mouse_press",
            ToolEventType.MOUSE_MOVE: "mouse_move",
            ToolEventType.MOUSE_RELEASE: "mouse_release",
            ToolEventType.MOUSE_DOUBLE_CLICK: (
                "mouse_double_click"
            ),
            ToolEventType.KEY_PRESS: "key_press",
            ToolEventType.KEY_RELEASE: "key_release",
        }

        method_name = handlers.get(
            event_type
        )

        if method_name is None:
            return None

        handler = getattr(
            self._tool,
            method_name,
            None,
        )

        if handler is None:
            return None

        if not callable(handler):
            raise TypeError(
                f"Tool {self.tool_id!r} attribute "
                f"{method_name!r} is not callable."
            )

        return handler

    # ========================================================
    # RESULT NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_result(
        result: Any,
        *,
        default: Optional[ToolResult] = None,
    ) -> ToolResult:
        """
        Normalize a ToolBase handler response into ToolResult.

        Supported native responses:

            ToolResult
            bool
            None

        ``ToolResult`` is the preferred contract.

        Boolean compatibility exists only to keep the adapter
        tolerant of simple ToolBase implementations.
        """

        if isinstance(
            result,
            ToolResult,
        ):
            return result

        if isinstance(
            result,
            bool,
        ):
            if result:
                return ToolResult.handled(
                    consumed=True
                )

            return ToolResult.ignored()

        if result is None:
            if default is not None:
                return default

            return ToolResult.ignored()

        raise TypeError(
            "Tool handler returned an unsupported result type: "
            f"{type(result).__name__}. "
            "Expected ToolResult, bool, or None."
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return adapter/tool diagnostic state.
        """

        tool_state = None

        getter = getattr(
            self._tool,
            "get_state",
            None,
        )

        if callable(getter):
            tool_state = getter()

        return {
            "tool_id": self.tool_id,
            "tool_type": type(
                self._tool
            ).__name__,
            "tool_state": tool_state,
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            f"{type(self).__name__}("
            f"tool_id={self.tool_id!r}, "
            f"tool={type(self._tool).__name__!r}"
            ")"
        )


__all__ = [
    "ToolAdapter",
]
