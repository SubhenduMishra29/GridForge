# ============================================================
# File: ui/tools/tool_dispatcher.py
# GridForge V2 — Tool Dispatcher
# ============================================================
"""
Dispatch semantic tool actions to the active tool.

The dispatcher is deliberately a thin UI-layer coordination
component.

Responsibilities
----------------
    - receive normalized ToolInput / ToolAction data;
    - identify the active tool;
    - evaluate the UI interaction policy;
    - invoke the active tool;
    - publish resulting ToolEvents when requested.

Non-responsibilities
--------------------
    - Core mutation;
    - domain validation;
    - command execution;
    - topology validation;
    - rendering;
    - tool discovery;
    - Qt event handling.

The ToolController remains the orchestration boundary. The
dispatcher exists to keep action routing separate from tool
lifecycle management.

Frozen concrete tools remain:

    SelectTool
    BusTool
    LineTool

No Qt dependency is permitted in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Optional, Protocol

from ui.tools.tool_action import ToolAction
from ui.tools.tool_event import ToolEvent
from ui.tools.tool_events import ToolEventBus
from ui.tools.tool_input import ToolInput
from ui.tools.tool_policy import (
    ToolPolicy,
    ToolPolicyContext,
    ToolPolicyResult,
)
from ui.tools.tool_result import ToolResult


# ============================================================
# TOOL PROTOCOL
# ============================================================


class ToolDispatchTarget(Protocol):
    """
    Minimal protocol required by ToolDispatcher.

    Concrete tools may expose a richer interface through
    ToolBase. The dispatcher depends only on the interaction
    methods needed for dispatch.
    """

    tool_id: str

    def handle_input(
        self,
        tool_input: ToolInput,
    ) -> ToolResult:
        """
        Process normalized input.
        """
        ...


# ============================================================
# DISPATCH STATUS
# ============================================================


class ToolDispatchStatus(str, Enum):
    """
    Outcome of dispatching a tool interaction.
    """

    DISPATCHED = "dispatched"
    DENIED = "denied"
    NO_TOOL = "no_tool"
    IGNORED = "ignored"
    FAILED = "failed"


# ============================================================
# DISPATCH RESULT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolDispatchResult:
    """
    Immutable result returned by ToolDispatcher.

    ``tool_result`` contains the concrete tool's result when the
    tool was actually invoked.

    ``policy_result`` contains the UI-policy decision when policy
    evaluation occurred.
    """

    status: ToolDispatchStatus

    tool_id: Optional[str] = None

    tool_result: Optional[ToolResult] = None

    policy_result: Optional[ToolPolicyResult] = None

    event_count: int = 0

    error: Optional[BaseException] = None

    @property
    def dispatched(self) -> bool:
        """Return whether a tool was actually dispatched."""

        return (
            self.status
            == ToolDispatchStatus.DISPATCHED
        )

    @property
    def denied(self) -> bool:
        """Return whether dispatch was denied by policy."""

        return (
            self.status
            == ToolDispatchStatus.DENIED
        )

    @property
    def failed(self) -> bool:
        """Return whether dispatch failed."""

        return (
            self.status
            == ToolDispatchStatus.FAILED
        )

    @property
    def succeeded(self) -> bool:
        """
        Return whether dispatch completed without failure.

        A policy denial is not considered a dispatch failure.
        """

        return self.status in {
            ToolDispatchStatus.DISPATCHED,
            ToolDispatchStatus.IGNORED,
        }

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "status": self.status.value,
            "tool_id": self.tool_id,
            "tool_result": (
                self.tool_result.to_dict()
                if self.tool_result is not None
                and hasattr(self.tool_result, "to_dict")
                else self.tool_result
            ),
            "policy_result": (
                self.policy_result.to_dict()
                if self.policy_result is not None
                else None
            ),
            "event_count": self.event_count,
            "error": (
                repr(self.error)
                if self.error is not None
                else None
            ),
        }


# ============================================================
# DISPATCHER
# ============================================================


class ToolDispatcher:
    """
    Thin semantic action dispatcher.

    The dispatcher does not own tool registration. A tool provider
    is supplied by the ToolManager / ToolController boundary.

    Typical flow:

        InteractionController
                |
                v
           ToolDispatcher
                |
          policy evaluation
                |
                v
           active Tool
                |
                v
           ToolResult
                |
                v
          ToolEventBus

    The dispatcher may be used synchronously. No background
    execution is performed.
    """

    def __init__(
        self,
        *,
        tool_provider: Optional[
            Callable[[str], Optional[ToolDispatchTarget]]
        ] = None,
        policy: Optional[ToolPolicy] = None,
        event_bus: Optional[ToolEventBus] = None,
    ) -> None:
        """
        Initialize the dispatcher.

        Parameters
        ----------
        tool_provider:
            Callable resolving a tool ID to an active/registered
            tool instance.

        policy:
            UI interaction policy. A default ToolPolicy is created
            when omitted.

        event_bus:
            Optional ToolEventBus used to publish events returned
            by tools.
        """

        self._tool_provider = tool_provider
        self._policy = (
            policy
            if policy is not None
            else ToolPolicy()
        )
        self._event_bus = event_bus

        self._active_tool_id: Optional[str] = None

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def set_tool_provider(
        self,
        provider: Optional[
            Callable[[str], Optional[ToolDispatchTarget]]
        ],
    ) -> None:
        """Set the tool-resolution callback."""

        if provider is not None and not callable(
            provider
        ):
            raise TypeError(
                "provider must be callable or None."
            )

        self._tool_provider = provider

    # --------------------------------------------------------

    def set_policy(
        self,
        policy: ToolPolicy,
    ) -> None:
        """Replace the interaction policy."""

        if not isinstance(
            policy,
            ToolPolicy,
        ):
            raise TypeError(
                "policy must be a ToolPolicy."
            )

        self._policy = policy

    # --------------------------------------------------------

    def set_event_bus(
        self,
        event_bus: Optional[ToolEventBus],
    ) -> None:
        """Set or clear the event bus."""

        if event_bus is not None and not isinstance(
            event_bus,
            ToolEventBus,
        ):
            raise TypeError(
                "event_bus must be a ToolEventBus or None."
            )

        self._event_bus = event_bus

    # --------------------------------------------------------

    def set_active_tool(
        self,
        tool_id: Optional[str],
    ) -> None:
        """Set the tool ID used for implicit dispatch."""

        if tool_id is not None:
            tool_id = self._normalize_tool_id(
                tool_id
            )

        self._active_tool_id = tool_id

    # ========================================================
    # DISPATCH
    # ========================================================

    def dispatch(
        self,
        tool_input: ToolInput,
        *,
        context: Optional[ToolPolicyContext] = None,
        action: Optional[ToolAction] = None,
        tool_id: Optional[str] = None,
    ) -> ToolDispatchResult:
        """
        Dispatch normalized input to a tool.

        ``action`` is optional because some tools consume direct
        normalized input and produce semantic ToolActions
        internally.

        If a ToolAction is supplied, policy evaluation is performed
        before the tool is invoked.
        """

        if not isinstance(
            tool_input,
            ToolInput,
        ):
            raise TypeError(
                "tool_input must be a ToolInput."
            )

        resolved_tool_id = self._resolve_tool_id(
            action=action,
            explicit_tool_id=tool_id,
        )

        if resolved_tool_id is None:
            return ToolDispatchResult(
                status=ToolDispatchStatus.NO_TOOL,
            )

        tool = self._resolve_tool(
            resolved_tool_id
        )

        if tool is None:
            return ToolDispatchResult(
                status=ToolDispatchStatus.NO_TOOL,
                tool_id=resolved_tool_id,
            )

        if action is not None:
            policy_context = self._resolve_policy_context(
                context=context,
                tool_id=resolved_tool_id,
            )

            policy_result = self._policy.evaluate(
                action,
                policy_context,
            )

            if not policy_result.allowed:
                return ToolDispatchResult(
                    status=ToolDispatchStatus.DENIED,
                    tool_id=resolved_tool_id,
                    policy_result=policy_result,
                )

        try:
            tool_result = self._invoke_tool(
                tool,
                tool_input,
            )
        except Exception as exc:
            return ToolDispatchResult(
                status=ToolDispatchStatus.FAILED,
                tool_id=resolved_tool_id,
                error=exc,
            )

        event_count = self._publish_result_events(
            tool_result
        )

        return ToolDispatchResult(
            status=ToolDispatchStatus.DISPATCHED,
            tool_id=resolved_tool_id,
            tool_result=tool_result,
            event_count=event_count,
        )

    # --------------------------------------------------------

    def dispatch_action(
        self,
        action: ToolAction,
        *,
        tool_input: Optional[ToolInput] = None,
        context: Optional[ToolPolicyContext] = None,
    ) -> ToolDispatchResult:
        """
        Dispatch a semantic ToolAction.

        When no ToolInput is supplied, an empty ToolInput is used.
        Tools requiring position or other interaction data should
        receive an explicit ToolInput.
        """

        if not isinstance(
            action,
            ToolAction,
        ):
            raise TypeError(
                "action must be a ToolAction."
            )

        if tool_input is None:
            tool_input = ToolInput()

        return self.dispatch(
            tool_input,
            context=context,
            action=action,
        )

    # ========================================================
    # TOOL RESOLUTION
    # ========================================================

    def _resolve_tool_id(
        self,
        *,
        action: Optional[ToolAction],
        explicit_tool_id: Optional[str],
    ) -> Optional[str]:
        """Resolve the tool ID used by dispatch."""

        if explicit_tool_id is not None:
            return self._normalize_tool_id(
                explicit_tool_id
            )

        if action is not None and action.tool_id is not None:
            return self._normalize_tool_id(
                action.tool_id
            )

        return self._active_tool_id

    # --------------------------------------------------------

    def _resolve_tool(
        self,
        tool_id: str,
    ) -> Optional[ToolDispatchTarget]:
        """Resolve a tool through the configured provider."""

        if self._tool_provider is None:
            return None

        tool = self._tool_provider(
            tool_id
        )

        if tool is None:
            return None

        resolved_id = getattr(
            tool,
            "tool_id",
            None,
        )

        if resolved_id is not None:
            if resolved_id != tool_id:
                raise ValueError(
                    (
                        f"Tool provider returned tool "
                        f"{resolved_id!r} for requested tool "
                        f"{tool_id!r}."
                    )
                )

        return tool

    # ========================================================
    # TOOL INVOCATION
    # ========================================================

    @staticmethod
    def _invoke_tool(
        tool: ToolDispatchTarget,
        tool_input: ToolInput,
    ) -> ToolResult:
        """
        Invoke a tool using its normalized input interface.
        """

        handler = getattr(
            tool,
            "handle_input",
            None,
        )

        if not callable(
            handler
        ):
            raise TypeError(
                (
                    f"Tool {tool!r} does not expose "
                    "a callable handle_input() method."
                )
            )

        result = handler(
            tool_input
        )

        if not isinstance(
            result,
            ToolResult,
        ):
            raise TypeError(
                (
                    f"Tool {tool!r} returned "
                    f"{type(result).__name__}; expected ToolResult."
                )
            )

        return result

    # ========================================================
    # EVENT PUBLICATION
    # ========================================================

    def _publish_result_events(
        self,
        tool_result: ToolResult,
    ) -> int:
        """
        Publish ToolEvents contained in a ToolResult.

        The ToolResult contract may expose events through an
        ``events`` attribute. A result without events is valid.
        """

        if self._event_bus is None:
            return 0

        events = getattr(
            tool_result,
            "events",
            (),
        )

        if events is None:
            return 0

        count = 0

        for event in events:
            if not isinstance(
                event,
                ToolEvent,
            ):
                raise TypeError(
                    (
                        "ToolResult.events contains a non-"
                        "ToolEvent value."
                    )
                )

            self._event_bus.publish(
                event
            )

            count += 1

        return count

    # ========================================================
    # POLICY
    # ========================================================

    @staticmethod
    def _resolve_policy_context(
        *,
        context: Optional[ToolPolicyContext],
        tool_id: str,
    ) -> ToolPolicyContext:
        """
        Resolve a policy context for the current dispatch.

        An explicit context is authoritative. When omitted, a
        minimal context is created for the active tool.
        """

        if context is not None:
            if not isinstance(
                context,
                ToolPolicyContext,
            ):
                raise TypeError(
                    "context must be a ToolPolicyContext."
                )

            return context

        return ToolPolicyContext(
            active_tool_id=tool_id,
            interaction_active=True,
        )

    # ========================================================
    # QUERIES
    # ========================================================

    @property
    def active_tool_id(
        self,
    ) -> Optional[str]:
        """Return the current implicit tool ID."""

        return self._active_tool_id

    @property
    def policy(
        self,
    ) -> ToolPolicy:
        """Return the configured policy."""

        return self._policy

    @property
    def event_bus(
        self,
    ) -> Optional[ToolEventBus]:
        """Return the configured event bus."""

        return self._event_bus

    def has_tool_provider(
        self,
    ) -> bool:
        """Return whether a tool provider is configured."""

        return self._tool_provider is not None

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """Return a deterministic diagnostic snapshot."""

        return {
            "active_tool_id": self._active_tool_id,
            "has_tool_provider": self.has_tool_provider(),
            "has_event_bus": self._event_bus is not None,
            "policy": self._policy.get_state(),
        }

    def __repr__(self) -> str:
        """Return a concise diagnostic representation."""

        return (
            f"{type(self).__name__}("
            f"active_tool_id={self._active_tool_id!r}, "
            f"has_tool_provider={self.has_tool_provider()}, "
            f"has_event_bus={self._event_bus is not None}"
            ")"
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _normalize_tool_id(
        tool_id: str,
    ) -> str:
        """Validate and normalize a tool identifier."""

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        normalized = tool_id.strip()

        if not normalized:
            raise ValueError(
                "tool_id must not be empty."
            )

        return normalized


__all__ = [
    "ToolDispatchTarget",
    "ToolDispatchStatus",
    "ToolDispatchResult",
    "ToolDispatcher",
]
