# ============================================================
# File: ui/tools/tool_validator.py
# GridForge V2 — Tool Validator
# ============================================================
"""
Validation utilities for the GridForge V2 tool system.

ToolValidator validates tool-level UI contracts before dispatch.
It is intentionally separate from:

    - Core domain validation;
    - electrical topology validation;
    - command validation;
    - renderer validation;
    - Qt event handling.

The validator answers questions such as:

    - Is the requested tool available?
    - Does the tool expose the required interface?
    - Does its declared capability set satisfy a requirement?
    - Is the current interaction state compatible with an action?
    - Is a ToolInput structurally valid for dispatch?

It must never become a second domain-validation layer.

Architectural boundary
----------------------

    UI input
       |
       v
    ToolValidator
       |
       v
    ToolDispatcher
       |
       v
    Concrete Tool
       |
       v
    Command / Core

Core remains authoritative for all domain and electrical
validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Optional, Protocol

from ui.tools.tool_capabilities import (
    ToolCapability,
    ToolCapabilities,
)
from ui.tools.tool_input import ToolInput
from ui.tools.tool_interaction import (
    ToolInteraction,
    ToolInteractionState,
)
from ui.tools.tool_lifecycle import (
    ToolLifecycleState,
)
from ui.tools.tool_policy import (
    ToolPolicyContext,
)


# ============================================================
# VALIDATION STATUS
# ============================================================


class ToolValidationStatus(str, Enum):
    """Overall outcome of tool validation."""

    VALID = "valid"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"


# ============================================================
# VALIDATION CODE
# ============================================================


class ToolValidationCode(str, Enum):
    """Machine-readable validation result codes."""

    VALID = "valid"

    MISSING_TOOL = "missing_tool"
    INVALID_TOOL_ID = "invalid_tool_id"

    TOOL_NOT_ACTIVE = "tool_not_active"
    TOOL_ALREADY_ACTIVE = "tool_already_active"

    TOOL_INTERFACE_INVALID = "tool_interface_invalid"

    MISSING_CAPABILITY = "missing_capability"
    CAPABILITY_CONFLICT = "capability_conflict"

    INPUT_INVALID = "input_invalid"
    INPUT_REQUIRED = "input_required"

    INTERACTION_MISSING = "interaction_missing"
    INTERACTION_NOT_ACTIVE = "interaction_not_active"
    INTERACTION_ALREADY_ACTIVE = "interaction_already_active"
    INTERACTION_TERMINAL = "interaction_terminal"

    SESSION_MISMATCH = "session_mismatch"

    CANVAS_REQUIRED = "canvas_required"
    SELECTION_REQUIRED = "selection_required"

    POLICY_CONTEXT_INVALID = "policy_context_invalid"


# ============================================================
# VALIDATION ISSUE
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolValidationIssue:
    """
    One validation issue.

    Validation issues are descriptive only. They do not execute
    corrective actions.
    """

    code: ToolValidationCode

    message: str

    field: Optional[str] = None

    value: Any = None

    expected: Any = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "code": self.code.value,
            "message": self.message,
            "field": self.field,
            "value": self.value,
            "expected": self.expected,
            "metadata": dict(self.metadata),
        }


# ============================================================
# VALIDATION RESULT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolValidationResult:
    """
    Immutable aggregate validation result.
    """

    status: ToolValidationStatus

    issues: tuple[
        ToolValidationIssue,
        ...,
    ] = ()

    tool_id: Optional[str] = None

    capability: Optional[ToolCapability] = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    @property
    def valid(self) -> bool:
        """Return whether validation succeeded."""

        return self.status == ToolValidationStatus.VALID

    @property
    def invalid(self) -> bool:
        """Return whether validation failed."""

        return not self.valid

    @property
    def first_issue(
        self,
    ) -> Optional[ToolValidationIssue]:
        """Return the first validation issue, if any."""

        if not self.issues:
            return None

        return self.issues[0]

    def require_valid(self) -> None:
        """
        Raise ValueError when validation failed.

        This helper is intended for UI infrastructure boundaries,
        not for domain validation.
        """

        if self.valid:
            return

        issue = self.first_issue

        if issue is None:
            raise ValueError(
                "Tool validation failed."
            )

        raise ValueError(
            issue.message
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "status": self.status.value,
            "tool_id": self.tool_id,
            "capability": (
                self.capability.value
                if self.capability is not None
                else None
            ),
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
            "metadata": dict(self.metadata),
        }


# ============================================================
# TOOL PROTOCOL
# ============================================================


class ToolValidationTarget(Protocol):
    """
    Minimal protocol expected from a concrete tool.

    The validator intentionally uses structural typing so that it
    does not force concrete tools to inherit a particular class.
    """

    tool_id: str

    def handle_input(
        self,
        tool_input: ToolInput,
    ) -> Any:
        """Process normalized tool input."""
        ...


# ============================================================
# VALIDATOR
# ============================================================


class ToolValidator:
    """
    Stateless validation service for UI tool contracts.

    A validator instance may be reused throughout the lifetime of
    the UI.

    It does not maintain authoritative application state.
    """

    # ========================================================
    # TOOL ID
    # ========================================================

    @staticmethod
    def validate_tool_id(
        tool_id: Any,
    ) -> ToolValidationResult:
        """Validate a tool identifier."""

        if not isinstance(
            tool_id,
            str,
        ):
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                tool_id=None,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.INVALID_TOOL_ID,
                        message=(
                            "tool_id must be a non-empty string."
                        ),
                        field="tool_id",
                        value=tool_id,
                    ),
                ),
            )

        normalized = tool_id.strip()

        if not normalized:
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                tool_id=normalized,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.INVALID_TOOL_ID,
                        message=(
                            "tool_id must not be empty."
                        ),
                        field="tool_id",
                        value=tool_id,
                    ),
                ),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID,
            tool_id=normalized,
        )

    # ========================================================
    # TOOL OBJECT
    # ========================================================

    @classmethod
    def validate_tool(
        cls,
        tool: Any,
        *,
        expected_tool_id: Optional[str] = None,
        capabilities: Optional[
            ToolCapabilities
        ] = None,
    ) -> ToolValidationResult:
        """
        Validate the structural contract of a tool.

        This does not inspect implementation internals.
        """

        if tool is None:
            return ToolValidationResult(
                status=ToolValidationStatus.UNAVAILABLE,
                tool_id=expected_tool_id,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.MISSING_TOOL,
                        message=(
                            "No tool instance was provided."
                        ),
                    ),
                ),
            )

        tool_id = getattr(
            tool,
            "tool_id",
            None,
        )

        id_result = cls.validate_tool_id(
            tool_id
        )

        if not id_result.valid:
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                tool_id=expected_tool_id,
                issues=(
                    *id_result.issues,
                    ToolValidationIssue(
                        code=ToolValidationCode.TOOL_INTERFACE_INVALID,
                        message=(
                            "Tool must expose a valid "
                            "non-empty tool_id."
                        ),
                        field="tool_id",
                    ),
                ),
            )

        issues: list[
            ToolValidationIssue
        ] = []

        if expected_tool_id is not None:
            expected_result = cls.validate_tool_id(
                expected_tool_id
            )

            if not expected_result.valid:
                issues.extend(
                    expected_result.issues
                )
            elif tool_id != expected_result.tool_id:
                issues.append(
                    ToolValidationIssue(
                        code=ToolValidationCode.TOOL_INTERFACE_INVALID,
                        message=(
                            f"Tool ID mismatch: expected "
                            f"{expected_result.tool_id!r}, "
                            f"received {tool_id!r}."
                        ),
                        field="tool_id",
                        value=tool_id,
                        expected=expected_result.tool_id,
                    )
                )

        handler = getattr(
            tool,
            "handle_input",
            None,
        )

        if not callable(handler):
            issues.append(
                ToolValidationIssue(
                    code=ToolValidationCode.TOOL_INTERFACE_INVALID,
                    message=(
                        f"Tool {tool_id!r} must expose a "
                        "callable handle_input() method."
                    ),
                    field="handle_input",
                )
            )

        if capabilities is not None:
            capability_result = cls.validate_capabilities(
                capabilities
            )

            if not capability_result.valid:
                issues.extend(
                    capability_result.issues
                )

        if issues:
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                tool_id=tool_id,
                issues=tuple(issues),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID,
            tool_id=tool_id,
        )

    # ========================================================
    # CAPABILITIES
    # ========================================================

    @staticmethod
    def validate_capabilities(
        capabilities: Any,
    ) -> ToolValidationResult:
        """
        Validate a ToolCapabilities object.

        This validates metadata integrity, not tool behavior.
        """

        if not isinstance(
            capabilities,
            ToolCapabilities,
        ):
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.TOOL_INTERFACE_INVALID,
                        message=(
                            "capabilities must be a "
                            "ToolCapabilities instance."
                        ),
                        field="capabilities",
                        value=capabilities,
                    ),
                ),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID
        )

    # --------------------------------------------------------

    @classmethod
    def require_capability(
        cls,
        capabilities: ToolCapabilities,
        required: ToolCapability | str,
        *,
        tool_id: Optional[str] = None,
    ) -> ToolValidationResult:
        """
        Validate that a tool declares one required capability.
        """

        capability_result = cls.validate_capabilities(
            capabilities
        )

        if not capability_result.valid:
            return capability_result

        try:
            normalized = (
                ToolCapabilities._normalize_capability(
                    required
                )
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                tool_id=tool_id,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.MISSING_CAPABILITY,
                        message=str(exc),
                        field="capability",
                        value=required,
                    ),
                ),
            )

        if not capabilities.has(
            normalized
        ):
            return ToolValidationResult(
                status=ToolValidationStatus.UNSUPPORTED,
                tool_id=tool_id,
                capability=normalized,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.MISSING_CAPABILITY,
                        message=(
                            f"Tool {tool_id!r} does not declare "
                            f"required capability "
                            f"{normalized.value!r}."
                        ),
                        field="capability",
                        value=normalized.value,
                        expected=normalized.value,
                    ),
                ),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID,
            tool_id=tool_id,
            capability=normalized,
        )

    # --------------------------------------------------------

    @classmethod
    def require_capabilities(
        cls,
        capabilities: ToolCapabilities,
        required: Iterable[
            ToolCapability | str
        ],
        *,
        tool_id: Optional[str] = None,
    ) -> ToolValidationResult:
        """
        Validate that all required capabilities are declared.
        """

        capability_result = cls.validate_capabilities(
            capabilities
        )

        if not capability_result.valid:
            return capability_result

        issues: list[
            ToolValidationIssue
        ] = []

        normalized_capabilities: list[
            ToolCapability
        ] = []

        for capability in required:
            try:
                normalized = (
                    ToolCapabilities._normalize_capability(
                        capability
                    )
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                issues.append(
                    ToolValidationIssue(
                        code=ToolValidationCode.MISSING_CAPABILITY,
                        message=str(exc),
                        field="capability",
                        value=capability,
                    )
                )
                continue

            normalized_capabilities.append(
                normalized
            )

            if not capabilities.has(
                normalized
            ):
                issues.append(
                    ToolValidationIssue(
                        code=ToolValidationCode.MISSING_CAPABILITY,
                        message=(
                            f"Tool {tool_id!r} does not "
                            f"declare required capability "
                            f"{normalized.value!r}."
                        ),
                        field="capability",
                        value=normalized.value,
                    )
                )

        if issues:
            return ToolValidationResult(
                status=ToolValidationStatus.UNSUPPORTED,
                tool_id=tool_id,
                issues=tuple(issues),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID,
            tool_id=tool_id,
        )

    # ========================================================
    # INPUT
    # ========================================================

    @staticmethod
    def validate_input(
        tool_input: Any,
        *,
        required: bool = True,
    ) -> ToolValidationResult:
        """
        Validate normalized ToolInput.

        The validator deliberately does not inspect electrical
        meaning contained inside the input.
        """

        if tool_input is None:
            if required:
                return ToolValidationResult(
                    status=ToolValidationStatus.INVALID,
                    issues=(
                        ToolValidationIssue(
                            code=ToolValidationCode.INPUT_REQUIRED,
                            message=(
                                "A ToolInput is required."
                            ),
                            field="tool_input",
                        ),
                    ),
                )

            return ToolValidationResult(
                status=ToolValidationStatus.VALID
            )

        if not isinstance(
            tool_input,
            ToolInput,
        ):
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.INPUT_INVALID,
                        message=(
                            "tool_input must be a ToolInput "
                            "instance."
                        ),
                        field="tool_input",
                        value=tool_input,
                    ),
                ),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    @staticmethod
    def validate_lifecycle_state(
        lifecycle_state: Any,
        *,
        require_active: bool = False,
        require_inactive: bool = False,
    ) -> ToolValidationResult:
        """
        Validate a tool lifecycle state.
        """

        if not isinstance(
            lifecycle_state,
            ToolLifecycleState,
        ):
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.TOOL_INTERFACE_INVALID,
                        message=(
                            "lifecycle_state must be a "
                            "ToolLifecycleState."
                        ),
                        field="lifecycle_state",
                        value=lifecycle_state,
                    ),
                ),
            )

        issues: list[
            ToolValidationIssue
        ] = []

        if (
            require_active
            and lifecycle_state
            != ToolLifecycleState.ACTIVE
        ):
            issues.append(
                ToolValidationIssue(
                    code=ToolValidationCode.TOOL_NOT_ACTIVE,
                    message=(
                        "Tool must be active for this operation."
                    ),
                    field="lifecycle_state",
                    value=lifecycle_state.value,
                    expected=ToolLifecycleState.ACTIVE.value,
                )
            )

        if (
            require_inactive
            and lifecycle_state
            != ToolLifecycleState.INACTIVE
        ):
            issues.append(
                ToolValidationIssue(
                    code=ToolValidationCode.TOOL_ALREADY_ACTIVE,
                    message=(
                        "Tool must be inactive for this operation."
                    ),
                    field="lifecycle_state",
                    value=lifecycle_state.value,
                    expected=ToolLifecycleState.INACTIVE.value,
                )
            )

        if issues:
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                issues=tuple(issues),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID
        )

    # ========================================================
    # INTERACTION
    # ========================================================

    @staticmethod
    def validate_interaction(
        interaction: Optional[ToolInteraction],
        *,
        require_active: bool = False,
        require_preview: bool = False,
        require_terminal: bool = False,
        require_idle: bool = False,
    ) -> ToolValidationResult:
        """
        Validate an interaction state against operation requirements.
        """

        if interaction is None:
            return ToolValidationResult(
                status=ToolValidationStatus.UNAVAILABLE,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.INTERACTION_MISSING,
                        message=(
                            "No ToolInteraction is available."
                        ),
                        field="interaction",
                    ),
                ),
            )

        if not isinstance(
            interaction,
            ToolInteraction,
        ):
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.TOOL_INTERFACE_INVALID,
                        message=(
                            "interaction must be a "
                            "ToolInteraction instance."
                        ),
                        field="interaction",
                        value=interaction,
                    ),
                ),
            )

        state = interaction.state

        issues: list[
            ToolValidationIssue
        ] = []

        if require_active and state not in {
            ToolInteractionState.ACTIVE,
            ToolInteractionState.PREVIEW,
        }:
            issues.append(
                ToolValidationIssue(
                    code=ToolValidationCode.INTERACTION_NOT_ACTIVE,
                    message=(
                        "Interaction must be active."
                    ),
                    field="interaction.state",
                    value=state.value,
                )
            )

        if (
            require_preview
            and state
            != ToolInteractionState.PREVIEW
        ):
            issues.append(
                ToolValidationIssue(
                    code=ToolValidationCode.INTERACTION_NOT_ACTIVE,
                    message=(
                        "Interaction must be in preview state."
                    ),
                    field="interaction.state",
                    value=state.value,
                    expected=ToolInteractionState.PREVIEW.value,
                )
            )

        if require_terminal and state not in {
            ToolInteractionState.COMMITTED,
            ToolInteractionState.CANCELLED,
        }:
            issues.append(
                ToolValidationIssue(
                    code=ToolValidationCode.INTERACTION_TERMINAL,
                    message=(
                        "Interaction must be terminal."
                    ),
                    field="interaction.state",
                    value=state.value,
                )
            )

        if (
            require_idle
            and state
            != ToolInteractionState.IDLE
        ):
            issues.append(
                ToolValidationIssue(
                    code=ToolValidationCode.INTERACTION_ALREADY_ACTIVE,
                    message=(
                        "Interaction must be idle."
                    ),
                    field="interaction.state",
                    value=state.value,
                    expected=ToolInteractionState.IDLE.value,
                )
            )

        if issues:
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                issues=tuple(issues),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID
        )

    # ========================================================
    # SESSION
    # ========================================================

    @staticmethod
    def validate_session_id(
        expected_session_id: Optional[str],
        supplied_session_id: Optional[str],
    ) -> ToolValidationResult:
        """
        Validate that an optional supplied session ID matches the
        current session.

        If no expected session exists, a supplied ID is invalid.
        """

        if expected_session_id is None:
            if supplied_session_id is None:
                return ToolValidationResult(
                    status=ToolValidationStatus.VALID
                )

            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.SESSION_MISMATCH,
                        message=(
                            "A session ID was supplied but no "
                            "active session exists."
                        ),
                        field="session_id",
                        value=supplied_session_id,
                    ),
                ),
            )

        if supplied_session_id is None:
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.SESSION_MISMATCH,
                        message=(
                            "A session ID is required."
                        ),
                        field="session_id",
                        expected=expected_session_id,
                    ),
                ),
            )

        if (
            expected_session_id
            != supplied_session_id
        ):
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.SESSION_MISMATCH,
                        message=(
                            f"Session ID mismatch: expected "
                            f"{expected_session_id!r}, received "
                            f"{supplied_session_id!r}."
                        ),
                        field="session_id",
                        value=supplied_session_id,
                        expected=expected_session_id,
                    ),
                ),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID
        )

    # ========================================================
    # POLICY CONTEXT
    # ========================================================

    @staticmethod
    def validate_policy_context(
        context: Optional[ToolPolicyContext],
    ) -> ToolValidationResult:
        """
        Validate an optional ToolPolicyContext.
        """

        if context is None:
            return ToolValidationResult(
                status=ToolValidationStatus.VALID
            )

        if not isinstance(
            context,
            ToolPolicyContext,
        ):
            return ToolValidationResult(
                status=ToolValidationStatus.INVALID,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.POLICY_CONTEXT_INVALID,
                        message=(
                            "context must be a ToolPolicyContext "
                            "instance or None."
                        ),
                        field="context",
                        value=context,
                    ),
                ),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID
        )

    # ========================================================
    # COMPOSITE DISPATCH VALIDATION
    # ========================================================

    @classmethod
    def validate_dispatch(
        cls,
        *,
        tool: Any,
        tool_input: Any,
        capabilities: Optional[
            ToolCapabilities
        ] = None,
        required_capabilities: Iterable[
            ToolCapability | str
        ] = (),
        require_active: bool = True,
        interaction: Optional[ToolInteraction] = None,
        require_interaction: bool = False,
        policy_context: Optional[
            ToolPolicyContext
        ] = None,
    ) -> ToolValidationResult:
        """
        Validate the UI preconditions for a tool dispatch.

        This is the primary convenience method for ToolDispatcher
        and ToolController.

        It performs structural/UI validation only.
        """

        issues: list[
            ToolValidationIssue
        ] = []

        tool_result = cls.validate_tool(
            tool,
            capabilities=capabilities,
        )

        if not tool_result.valid:
            issues.extend(
                tool_result.issues
            )

        if capabilities is not None:
            capability_result = cls.require_capabilities(
                capabilities,
                required_capabilities,
                tool_id=tool_result.tool_id,
            )

            if not capability_result.valid:
                issues.extend(
                    capability_result.issues
                )

        input_result = cls.validate_input(
            tool_input
        )

        if not input_result.valid:
            issues.extend(
                input_result.issues
            )

        if require_active:
            lifecycle_state = getattr(
                tool,
                "lifecycle_state",
                None,
            )

            if lifecycle_state is None:
                active_attribute = getattr(
                    tool,
                    "active",
                    None,
                )

                if active_attribute is not True:
                    issues.append(
                        ToolValidationIssue(
                            code=ToolValidationCode.TOOL_NOT_ACTIVE,
                            message=(
                                "Tool must be active before "
                                "dispatch."
                            ),
                            field="active",
                            value=active_attribute,
                            expected=True,
                        )
                    )
            else:
                lifecycle_result = cls.validate_lifecycle_state(
                    lifecycle_state,
                    require_active=True,
                )

                if not lifecycle_result.valid:
                    issues.extend(
                        lifecycle_result.issues
                    )

        if require_interaction:
            interaction_result = cls.validate_interaction(
                interaction,
                require_active=True,
            )

            if not interaction_result.valid:
                issues.extend(
                    interaction_result.issues
                )

        context_result = cls.validate_policy_context(
            policy_context
        )

        if not context_result.valid:
            issues.extend(
                context_result.issues
            )

        if issues:
            status = (
                ToolValidationStatus.UNSUPPORTED
                if any(
                    issue.code
                    == ToolValidationCode.MISSING_CAPABILITY
                    for issue in issues
                )
                else ToolValidationStatus.INVALID
            )

            return ToolValidationResult(
                status=status,
                tool_id=tool_result.tool_id,
                issues=tuple(issues),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID,
            tool_id=tool_result.tool_id,
        )

    # ========================================================
    # TOOL CAPABILITY / ENVIRONMENT CHECKS
    # ========================================================

    @classmethod
    def validate_canvas_requirement(
        cls,
        capabilities: ToolCapabilities,
        *,
        canvas_available: bool,
        tool_id: Optional[str] = None,
    ) -> ToolValidationResult:
        """
        Validate a tool's canvas requirement.

        This checks only UI availability. It does not inspect or
        mutate the canvas.
        """

        capability_result = cls.require_capability(
            capabilities,
            ToolCapability.REQUIRES_CANVAS,
            tool_id=tool_id,
        )

        if not capability_result.valid:
            return capability_result

        if not canvas_available:
            return ToolValidationResult(
                status=ToolValidationStatus.UNAVAILABLE,
                tool_id=tool_id,
                capability=ToolCapability.REQUIRES_CANVAS,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.CANVAS_REQUIRED,
                        message=(
                            f"Tool {tool_id!r} requires an "
                            "active canvas."
                        ),
                        field="canvas_available",
                        value=False,
                        expected=True,
                    ),
                ),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID,
            tool_id=tool_id,
            capability=ToolCapability.REQUIRES_CANVAS,
        )

    # --------------------------------------------------------

    @classmethod
    def validate_selection_requirement(
        cls,
        capabilities: ToolCapabilities,
        *,
        has_selection: bool,
        tool_id: Optional[str] = None,
    ) -> ToolValidationResult:
        """
        Validate a tool's selection requirement.
        """

        capability_result = cls.require_capability(
            capabilities,
            ToolCapability.REQUIRES_SELECTION,
            tool_id=tool_id,
        )

        if not capability_result.valid:
            return capability_result

        if not has_selection:
            return ToolValidationResult(
                status=ToolValidationStatus.UNAVAILABLE,
                tool_id=tool_id,
                capability=ToolCapability.REQUIRES_SELECTION,
                issues=(
                    ToolValidationIssue(
                        code=ToolValidationCode.SELECTION_REQUIRED,
                        message=(
                            f"Tool {tool_id!r} requires an "
                            "active selection."
                        ),
                        field="has_selection",
                        value=False,
                        expected=True,
                    ),
                ),
            )

        return ToolValidationResult(
            status=ToolValidationStatus.VALID,
            tool_id=tool_id,
            capability=ToolCapability.REQUIRES_SELECTION,
        )


# ============================================================
# MODULE-LEVEL CONVENIENCE
# ============================================================


def validate_tool(
    tool: Any,
    *,
    expected_tool_id: Optional[str] = None,
) -> ToolValidationResult:
    """
    Validate a tool using the default stateless validator.
    """

    return ToolValidator.validate_tool(
        tool,
        expected_tool_id=expected_tool_id,
    )


def validate_tool_input(
    tool_input: Any,
) -> ToolValidationResult:
    """
    Validate ToolInput using the default validator.
    """

    return ToolValidator.validate_input(
        tool_input
    )


def validate_tool_capability(
    capabilities: ToolCapabilities,
    capability: ToolCapability | str,
    *,
    tool_id: Optional[str] = None,
) -> ToolValidationResult:
    """
    Validate one required capability.
    """

    return ToolValidator.require_capability(
        capabilities,
        capability,
        tool_id=tool_id,
    )


__all__ = [
    "ToolValidationStatus",
    "ToolValidationCode",
    "ToolValidationIssue",
    "ToolValidationResult",
    "ToolValidationTarget",
    "ToolValidator",
    "validate_tool",
    "validate_tool_input",
    "validate_tool_capability",
]
