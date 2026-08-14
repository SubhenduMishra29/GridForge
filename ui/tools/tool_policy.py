# ============================================================
# File: ui/tools/tool_policy.py
# GridForge V2 — Tool Policy
# ============================================================
"""
Interaction policies for the GridForge V2 tool system.

ToolPolicy defines what an active tool is permitted to do at the
UI interaction boundary.

It is deliberately separate from:

    ToolMode
        Describes the current interaction mode.

    ToolState
        Describes runtime state.

    ToolAction
        Describes semantic intent produced by a tool.

    ToolManager
        Owns active-tool lifecycle and selection.

    Core / Validation
        Remain authoritative for domain validity.

Policy is therefore a UI-level gate, not an electrical or domain
validation layer.

Rules
-----
    - Never mutate Core.
    - Never execute commands.
    - Never duplicate domain validation.
    - Never own tool state.
    - Never access Qt.
    - Do not infer topology validity.
    - Keep policy decisions deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional

from ui.tools.tool_action import (
    ToolAction,
    ToolActionType,
)
from ui.tools.tool_mode import ToolMode


# ============================================================
# POLICY DECISION
# ============================================================


class ToolPolicyDecision(str, Enum):
    """
    Result of a tool-policy evaluation.
    """

    ALLOW = "allow"
    DENY = "deny"


# ============================================================
# POLICY REASON
# ============================================================


class ToolPolicyReason(str, Enum):
    """
    Stable reasons explaining a policy decision.

    These are UI interaction reasons only. They must not be
    interpreted as domain validation errors.
    """

    ALLOWED = "allowed"

    NO_ACTIVE_TOOL = "no_active_tool"
    TOOL_NOT_ALLOWED = "tool_not_allowed"
    ACTION_NOT_ALLOWED = "action_not_allowed"

    INVALID_MODE = "invalid_mode"
    INVALID_ACTION = "invalid_action"

    SELECTION_REQUIRED = "selection_required"
    TARGET_REQUIRED = "target_required"

    POSITION_REQUIRED = "position_required"
    CONNECTION_REQUIRED = "connection_required"

    INTERACTION_BUSY = "interaction_busy"
    INTERACTION_INACTIVE = "interaction_inactive"


# ============================================================
# POLICY RESULT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolPolicyResult:
    """
    Immutable result of evaluating a ToolAction against a policy.

    ``allowed`` is the authoritative boolean for the policy layer.

    A denied action is not a domain validation failure. It simply
    means the current UI interaction context does not permit the
    requested action.
    """

    decision: ToolPolicyDecision
    reason: ToolPolicyReason
    message: str

    tool_id: Optional[str] = None
    action_type: Optional[ToolActionType] = None
    mode: Optional[ToolMode] = None

    @property
    def allowed(self) -> bool:
        """Return whether the action is permitted."""

        return (
            self.decision
            == ToolPolicyDecision.ALLOW
        )

    @property
    def denied(self) -> bool:
        """Return whether the action is denied."""

        return not self.allowed

    def __bool__(self) -> bool:
        """Allow direct boolean evaluation."""

        return self.allowed

    def to_dict(
        self,
    ) -> dict[str, object]:
        """Return a diagnostic representation."""

        return {
            "decision": self.decision.value,
            "reason": self.reason.value,
            "message": self.message,
            "tool_id": self.tool_id,
            "action_type": (
                self.action_type.value
                if self.action_type is not None
                else None
            ),
            "mode": (
                self.mode.value
                if self.mode is not None
                else None
            ),
        }


# ============================================================
# POLICY CONTEXT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolPolicyContext:
    """
    Immutable UI interaction context used for policy evaluation.

    The context contains only facts already resolved by the UI
    interaction layer. It does not perform hit testing or snapping.
    """

    active_tool_id: Optional[str] = None
    mode: ToolMode = ToolMode.IDLE

    interaction_active: bool = False
    interaction_busy: bool = False

    has_selection: bool = False
    has_target: bool = False
    has_position: bool = False
    has_connection: bool = False

    selected_count: int = 0

    def __post_init__(self) -> None:
        """Validate policy-context values."""

        if self.active_tool_id is not None:
            if not isinstance(
                self.active_tool_id,
                str,
            ) or not self.active_tool_id.strip():
                raise ValueError(
                    "active_tool_id must be None or "
                    "a non-empty string."
                )

        if not isinstance(
            self.mode,
            ToolMode,
        ):
            raise TypeError(
                "mode must be a ToolMode."
            )

        for field_name in (
            "interaction_active",
            "interaction_busy",
            "has_selection",
            "has_target",
            "has_position",
            "has_connection",
        ):
            if not isinstance(
                getattr(self, field_name),
                bool,
            ):
                raise TypeError(
                    f"{field_name} must be a bool."
                )

        if not isinstance(
            self.selected_count,
            int,
        ):
            raise TypeError(
                "selected_count must be an int."
            )

        if self.selected_count < 0:
            raise ValueError(
                "selected_count cannot be negative."
            )

        if (
            self.selected_count > 0
            and not self.has_selection
        ):
            raise ValueError(
                "selected_count > 0 requires has_selection=True."
            )


# ============================================================
# TOOL POLICY
# ============================================================


class ToolPolicy:
    """
    Deterministic UI interaction policy.

    The policy contains explicit rules for the frozen concrete
    GridForge tools:

        select
        bus
        line

    Additional tool IDs may be supported through the explicit
    registration API without changing the policy evaluator.
    """

    SELECT_TOOL_ID = "select"
    BUS_TOOL_ID = "bus"
    LINE_TOOL_ID = "line"

    def __init__(
        self,
        *,
        allowed_tools: Optional[set[str]] = None,
    ) -> None:
        """
        Initialize the policy.

        By default the frozen concrete tool set is used.
        """

        if allowed_tools is None:
            allowed_tools = {
                self.SELECT_TOOL_ID,
                self.BUS_TOOL_ID,
                self.LINE_TOOL_ID,
            }

        normalized = {
            self._normalize_tool_id(
                tool_id
            )
            for tool_id in allowed_tools
        }

        self._allowed_tools: FrozenSet[str] = frozenset(
            normalized
        )

    # ========================================================
    # PUBLIC EVALUATION
    # ========================================================

    def evaluate(
        self,
        action: ToolAction,
        context: ToolPolicyContext,
    ) -> ToolPolicyResult:
        """
        Evaluate whether an action is permitted.

        This method performs UI interaction-policy checks only.
        """

        if not isinstance(
            action,
            ToolAction,
        ):
            raise TypeError(
                "action must be a ToolAction."
            )

        if not isinstance(
            context,
            ToolPolicyContext,
        ):
            raise TypeError(
                "context must be a ToolPolicyContext."
            )

        if action.action_type == ToolActionType.NONE:
            return self._allow(
                action,
                context,
                "No-op action.",
            )

        if action.tool_id is None:
            return self._deny(
                action,
                context,
                ToolPolicyReason.NO_ACTIVE_TOOL,
                "Action does not identify an active tool.",
            )

        if action.tool_id not in self._allowed_tools:
            return self._deny(
                action,
                context,
                ToolPolicyReason.TOOL_NOT_ALLOWED,
                (
                    f"Tool {action.tool_id!r} is not permitted "
                    "by the current tool policy."
                ),
            )

        if context.active_tool_id is None:
            return self._deny(
                action,
                context,
                ToolPolicyReason.NO_ACTIVE_TOOL,
                "No active tool is available.",
            )

        if (
            context.active_tool_id
            != action.tool_id
        ):
            return self._deny(
                action,
                context,
                ToolPolicyReason.TOOL_NOT_ALLOWED,
                (
                    f"Action belongs to tool "
                    f"{action.tool_id!r}, but active tool is "
                    f"{context.active_tool_id!r}."
                ),
            )

        return self._evaluate_action(
            action,
            context,
        )

    # ========================================================
    # ACTION EVALUATION
    # ========================================================

    def _evaluate_action(
        self,
        action: ToolAction,
        context: ToolPolicyContext,
    ) -> ToolPolicyResult:
        """
        Dispatch action-specific policy rules.
        """

        action_type = action.action_type

        if action_type in {
            ToolActionType.SELECT,
            ToolActionType.SELECT_ADD,
            ToolActionType.SELECT_REMOVE,
        }:
            return self._evaluate_selection(
                action,
                context,
            )

        if action_type == ToolActionType.SELECT_CLEAR:
            return self._allow(
                action,
                context,
                "Selection clear is permitted.",
            )

        if action_type == ToolActionType.CREATE_BUS:
            return self._evaluate_create_bus(
                action,
                context,
            )

        if action_type == ToolActionType.CREATE_LINE:
            return self._evaluate_create_line(
                action,
                context,
            )

        if action_type == ToolActionType.CANCEL:
            return self._evaluate_cancel(
                action,
                context,
            )

        if action_type == ToolActionType.RESET:
            return self._allow(
                action,
                context,
                "Tool reset is permitted.",
            )

        if action_type == ToolActionType.DELETE_SELECTION:
            return self._evaluate_selection_command(
                action,
                context,
            )

        if action_type == ToolActionType.DUPLICATE_SELECTION:
            return self._evaluate_selection_command(
                action,
                context,
            )

        if action_type == ToolActionType.START_PREVIEW:
            return self._evaluate_preview_start(
                action,
                context,
            )

        if action_type == ToolActionType.UPDATE_PREVIEW:
            return self._evaluate_preview_update(
                action,
                context,
            )

        if action_type == ToolActionType.COMMIT_PREVIEW:
            return self._evaluate_preview_commit(
                action,
                context,
            )

        if action_type in {
            ToolActionType.PAN,
            ToolActionType.ZOOM,
        }:
            return self._evaluate_view_action(
                action,
                context,
            )

        return self._deny(
            action,
            context,
            ToolPolicyReason.ACTION_NOT_ALLOWED,
            (
                f"Action {action_type.value!r} is not "
                "supported by the current tool policy."
            ),
        )

    # --------------------------------------------------------

    def _evaluate_selection(
        self,
        action: ToolAction,
        context: ToolPolicyContext,
    ) -> ToolPolicyResult:
        """
        Evaluate selection operations.
        """

        if context.interaction_busy:
            return self._deny(
                action,
                context,
                ToolPolicyReason.INTERACTION_BUSY,
                "Selection is blocked during a busy interaction.",
            )

        if action.action_type == ToolActionType.SELECT_CLEAR:
            return self._allow(
                action,
                context,
                "Selection clear is permitted.",
            )

        if action.target_id is None:
            return self._deny(
                action,
                context,
                ToolPolicyReason.TARGET_REQUIRED,
                "Selection requires a target object.",
            )

        if context.mode not in {
            ToolMode.SELECT,
            ToolMode.EDIT,
        }:
            return self._deny(
                action,
                context,
                ToolPolicyReason.INVALID_MODE,
                (
                    f"Selection is not permitted in "
                    f"{context.mode.value!r} mode."
                ),
            )

        return self._allow(
            action,
            context,
            "Selection action is permitted.",
        )

    # --------------------------------------------------------

    def _evaluate_selection_command(
        self,
        action: ToolAction,
        context: ToolPolicyContext,
    ) -> ToolPolicyResult:
        """
        Evaluate actions operating on the current selection.
        """

        if not context.has_selection:
            return self._deny(
                action,
                context,
                ToolPolicyReason.SELECTION_REQUIRED,
                "The action requires a non-empty selection.",
            )

        if context.interaction_busy:
            return self._deny(
                action,
                context,
                ToolPolicyReason.INTERACTION_BUSY,
                "The action is blocked during a busy interaction.",
            )

        return self._allow(
            action,
            context,
            "Selection operation is permitted.",
        )

    # --------------------------------------------------------

    def _evaluate_create_bus(
        self,
        action: ToolAction,
        context: ToolPolicyContext,
    ) -> ToolPolicyResult:
        """
        Evaluate a bus-creation interaction.

        This checks only the UI interaction prerequisites.
        """

        if action.tool_id != self.BUS_TOOL_ID:
            return self._deny(
                action,
                context,
                ToolPolicyReason.TOOL_NOT_ALLOWED,
                "Bus creation must be initiated by the Bus Tool.",
            )

        if not context.has_position:
            return self._deny(
                action,
                context,
                ToolPolicyReason.POSITION_REQUIRED,
                "Bus creation requires a valid scene position.",
            )

        if action.position is None:
            return self._deny(
                action,
                context,
                ToolPolicyReason.POSITION_REQUIRED,
                "Bus creation requires an action position.",
            )

        if context.interaction_busy:
            return self._deny(
                action,
                context,
                ToolPolicyReason.INTERACTION_BUSY,
                "Bus creation is blocked during a busy interaction.",
            )

        if context.mode not in {
            ToolMode.CREATE,
            ToolMode.PREVIEW,
        }:
            return self._deny(
                action,
                context,
                ToolPolicyReason.INVALID_MODE,
                (
                    "Bus creation requires Create or Preview "
                    "interaction mode."
                ),
            )

        return self._allow(
            action,
            context,
            "Bus creation interaction is permitted.",
        )

    # --------------------------------------------------------

    def _evaluate_create_line(
        self,
        action: ToolAction,
        context: ToolPolicyContext,
    ) -> ToolPolicyResult:
        """
        Evaluate a line-creation interaction.

        Topology validity is intentionally not checked here.
        """

        if action.tool_id != self.LINE_TOOL_ID:
            return self._deny(
                action,
                context,
                ToolPolicyReason.TOOL_NOT_ALLOWED,
                "Line creation must be initiated by the Line Tool.",
            )

        if action.start_position is None:
            return self._deny(
                action,
                context,
                ToolPolicyReason.POSITION_REQUIRED,
                "Line creation requires a start position.",
            )

        if action.end_position is None:
            return self._deny(
                action,
                context,
                ToolPolicyReason.POSITION_REQUIRED,
                "Line creation requires an end position.",
            )

        if context.interaction_busy:
            return self._deny(
                action,
                context,
                ToolPolicyReason.INTERACTION_BUSY,
                "Line creation is blocked during a busy interaction.",
            )

        if context.mode not in {
            ToolMode.CREATE,
            ToolMode.CONNECT,
            ToolMode.PREVIEW,
        }:
            return self._deny(
                action,
                context,
                ToolPolicyReason.INVALID_MODE,
                (
                    "Line creation requires Create, Connect, "
                    "or Preview interaction mode."
                ),
            )

        return self._allow(
            action,
            context,
            "Line creation interaction is permitted.",
        )

    # --------------------------------------------------------

    def _evaluate_cancel(
        self,
        action: ToolAction,
        context: ToolPolicyContext,
    ) -> ToolPolicyResult:
        """
        Evaluate cancellation.

        Cancellation is intentionally idempotent at the policy
        boundary.
        """

        if not context.interaction_active:
            return self._allow(
                action,
                context,
                "Cancellation is harmless when no interaction is active.",
            )

        return self._allow(
            action,
            context,
            "Active interaction may be cancelled.",
        )

    # --------------------------------------------------------

    def _evaluate_preview_start(
        self,
        action: ToolAction,
        context: ToolPolicyContext,
    ) -> ToolPolicyResult:
        """
        Evaluate preview initiation.
        """

        if context.interaction_busy:
            return self._deny(
                action,
                context,
                ToolPolicyReason.INTERACTION_BUSY,
                "Preview cannot start during a busy interaction.",
            )

        if not context.has_position:
            return self._deny(
                action,
                context,
                ToolPolicyReason.POSITION_REQUIRED,
                "Preview requires a valid scene position.",
            )

        return self._allow(
            action,
            context,
            "Preview may start.",
        )

    # --------------------------------------------------------

    def _evaluate_preview_update(
        self,
        action: ToolAction,
        context: ToolPolicyContext,
    ) -> ToolPolicyResult:
        """
        Evaluate preview updates.
        """

        if not context.interaction_active:
            return self._deny(
                action,
                context,
                ToolPolicyReason.INTERACTION_INACTIVE,
                "Preview update requires an active interaction.",
            )

        if not context.has_position:
            return self._deny(
                action,
                context,
                ToolPolicyReason.POSITION_REQUIRED,
                "Preview update requires a valid scene position.",
            )

        return self._allow(
            action,
            context,
            "Preview update is permitted.",
        )

    # --------------------------------------------------------

    def _evaluate_preview_commit(
        self,
        action: ToolAction,
        context: ToolPolicyContext,
    ) -> ToolPolicyResult:
        """
        Evaluate preview commitment.
        """

        if not context.interaction_active:
            return self._deny(
                action,
                context,
                ToolPolicyReason.INTERACTION_INACTIVE,
                "Preview commit requires an active interaction.",
            )

        if context.interaction_busy:
            return self._deny(
                action,
                context,
                ToolPolicyReason.INTERACTION_BUSY,
                "Preview commit is blocked during a busy interaction.",
            )

        return self._allow(
            action,
            context,
            "Preview commit is permitted.",
        )

    # --------------------------------------------------------

    def _evaluate_view_action(
        self,
        action: ToolAction,
        context: ToolPolicyContext,
    ) -> ToolPolicyResult:
        """
        Evaluate canvas-view interaction actions.
        """

        if context.interaction_busy:
            return self._deny(
                action,
                context,
                ToolPolicyReason.INTERACTION_BUSY,
                "View navigation is blocked during a busy interaction.",
            )

        return self._allow(
            action,
            context,
            "Canvas view action is permitted.",
        )

    # ========================================================
    # RESULT FACTORIES
    # ========================================================

    @staticmethod
    def _allow(
        action: ToolAction,
        context: ToolPolicyContext,
        message: str,
    ) -> ToolPolicyResult:
        """Create an allow result."""

        return ToolPolicyResult(
            decision=ToolPolicyDecision.ALLOW,
            reason=ToolPolicyReason.ALLOWED,
            message=message,
            tool_id=action.tool_id,
            action_type=action.action_type,
            mode=context.mode,
        )

    @staticmethod
    def _deny(
        action: ToolAction,
        context: ToolPolicyContext,
        reason: ToolPolicyReason,
        message: str,
    ) -> ToolPolicyResult:
        """Create a deny result."""

        return ToolPolicyResult(
            decision=ToolPolicyDecision.DENY,
            reason=reason,
            message=message,
            tool_id=action.tool_id,
            action_type=action.action_type,
            mode=context.mode,
        )

    # ========================================================
    # TOOL QUERIES
    # ========================================================

    def is_tool_allowed(
        self,
        tool_id: str,
    ) -> bool:
        """Return whether a tool ID is permitted."""

        return (
            self._normalize_tool_id(tool_id)
            in self._allowed_tools
        )

    def allowed_tools(
        self,
    ) -> frozenset[str]:
        """Return the immutable set of permitted tool IDs."""

        return self._allowed_tools

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, object]:
        """Return a deterministic diagnostic snapshot."""

        return {
            "allowed_tools": tuple(
                sorted(
                    self._allowed_tools
                )
            ),
        }

    def __repr__(self) -> str:
        """Return a concise diagnostic representation."""

        return (
            f"{type(self).__name__}("
            f"allowed_tools={tuple(sorted(self._allowed_tools))!r}"
            ")"
        )

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    @staticmethod
    def _normalize_tool_id(
        tool_id: str,
    ) -> str:
        """Normalize and validate a tool identifier."""

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
    "ToolPolicyDecision",
    "ToolPolicyReason",
    "ToolPolicyResult",
    "ToolPolicyContext",
    "ToolPolicy",
]
