# ============================================================
# File: ui/tools/tool_requirements.py
# GridForge V2 — Tool Requirements
# ============================================================
"""
Declarative runtime requirements for GridForge V2 tools.

Tool requirements describe what must be available before a tool can
be activated or perform a particular interaction.

This module is intentionally separate from ``tool_dependencies``:

    ToolDependencies
        -> describes injected services

    ToolRequirements
        -> describes operational preconditions

A dependency may exist while the corresponding operational
requirement is still unsatisfied. For example, a SnapSystem may be
injected but no active canvas may currently exist.

Architectural rules
-------------------
- Requirements do not create services.
- Requirements do not mutate Core.
- Requirements do not execute commands.
- Requirements do not own tool state.
- Requirements do not contain Qt-specific event handling.
- Core remains authoritative for domain validity.
- ToolController / ToolManager decide activation policy.
- Tool implementations perform interaction-specific validation.

The three concrete tools remain the canonical tool set:

    SelectTool
    BusTool
    LineTool
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Optional, Sequence

from .tool_environment import (
    ToolEnvironment,
    ToolEnvironmentMode,
)


# ============================================================
# REQUIREMENT TYPE
# ============================================================


class ToolRequirementType(str, Enum):
    """
    Categories of operational requirements.
    """

    ENVIRONMENT_MODE = "environment_mode"

    CANVAS = "canvas"
    SCENE = "scene"
    PROJECT = "project"
    WRITABLE_PROJECT = "writable_project"

    CORE = "core"
    COMMAND_MANAGER = "command_manager"

    COORDINATE_SYSTEM = "coordinate_system"
    GRID_SYSTEM = "grid_system"
    SNAP_SYSTEM = "snap_system"

    SELECTION = "selection"
    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    RENDERER = "renderer"


# ============================================================
# REQUIREMENT PHASE
# ============================================================


class ToolRequirementPhase(str, Enum):
    """
    Phase in which a requirement is evaluated.
    """

    ACTIVATION = "activation"
    INTERACTION = "interaction"


# ============================================================
# REQUIREMENT SEVERITY
# ============================================================


class ToolRequirementSeverity(str, Enum):
    """
    Severity of an unsatisfied requirement.
    """

    REQUIRED = "required"
    OPTIONAL = "optional"


# ============================================================
# REQUIREMENT RESULT
# ============================================================


class ToolRequirementStatus(str, Enum):
    """
    Evaluation result for an individual requirement.
    """

    SATISFIED = "satisfied"
    MISSING = "missing"
    INVALID = "invalid"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class ToolRequirement:
    """
    Declarative description of one operational requirement.
    """

    name: str

    requirement_type: ToolRequirementType

    phase: ToolRequirementPhase = (
        ToolRequirementPhase.ACTIVATION
    )

    severity: ToolRequirementSeverity = (
        ToolRequirementSeverity.REQUIRED
    )

    description: str = ""

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.name,
            str,
        ):
            raise TypeError(
                "Requirement name must be a string."
            )

        name = self.name.strip()

        if not name:
            raise ValueError(
                "Requirement name must not be empty."
            )

        object.__setattr__(
            self,
            "name",
            name,
        )

        if not isinstance(
            self.requirement_type,
            ToolRequirementType,
        ):
            raise TypeError(
                "requirement_type must be a ToolRequirementType."
            )

        if not isinstance(
            self.phase,
            ToolRequirementPhase,
        ):
            raise TypeError(
                "phase must be a ToolRequirementPhase."
            )

        if not isinstance(
            self.severity,
            ToolRequirementSeverity,
        ):
            raise TypeError(
                "severity must be a ToolRequirementSeverity."
            )

        if not isinstance(
            self.description,
            str,
        ):
            raise TypeError(
                "description must be a string."
            )

    @property
    def required(self) -> bool:
        """Return whether this requirement is mandatory."""

        return (
            self.severity
            == ToolRequirementSeverity.REQUIRED
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "name": self.name,
            "requirement_type": (
                self.requirement_type.value
            ),
            "phase": self.phase.value,
            "severity": self.severity.value,
            "description": self.description,
            "metadata": dict(self.metadata),
        }


# ============================================================
# REQUIREMENT CHECK
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolRequirementCheck:
    """
    Result of evaluating one requirement.
    """

    requirement: ToolRequirement

    status: ToolRequirementStatus

    message: str = ""

    value: Any = None

    @property
    def satisfied(self) -> bool:
        """Return whether the requirement is satisfied."""

        return (
            self.status
            in (
                ToolRequirementStatus.SATISFIED,
                ToolRequirementStatus.NOT_APPLICABLE,
            )
        )

    @property
    def blocking(self) -> bool:
        """
        Return whether this check blocks operation.

        Only unsatisfied required requirements are blocking.
        """

        return (
            self.requirement.required
            and self.status
            not in (
                ToolRequirementStatus.SATISFIED,
                ToolRequirementStatus.NOT_APPLICABLE,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "requirement": self.requirement.name,
            "requirement_type": (
                self.requirement.requirement_type.value
            ),
            "phase": self.requirement.phase.value,
            "severity": self.requirement.severity.value,
            "status": self.status.value,
            "message": self.message,
        }


# ============================================================
# REQUIREMENT EVALUATION
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolRequirementEvaluation:
    """
    Aggregate result of evaluating a ToolRequirements set.
    """

    checks: tuple[
        ToolRequirementCheck,
        ...
    ] = ()

    @property
    def valid(self) -> bool:
        """
        Return whether all required requirements are satisfied.
        """

        return not any(
            check.blocking
            for check in self.checks
        )

    @property
    def satisfied(self) -> tuple[
        ToolRequirementCheck,
        ...
    ]:
        """Return satisfied checks."""

        return tuple(
            check
            for check in self.checks
            if check.status
            == ToolRequirementStatus.SATISFIED
        )

    @property
    def missing(self) -> tuple[
        ToolRequirementCheck,
        ...
    ]:
        """Return missing checks."""

        return tuple(
            check
            for check in self.checks
            if check.status
            == ToolRequirementStatus.MISSING
        )

    @property
    def invalid(self) -> tuple[
        ToolRequirementCheck,
        ...
    ]:
        """Return invalid checks."""

        return tuple(
            check
            for check in self.checks
            if check.status
            == ToolRequirementStatus.INVALID
        )

    @property
    def blocking(self) -> tuple[
        ToolRequirementCheck,
        ...
    ]:
        """Return checks that block operation."""

        return tuple(
            check
            for check in self.checks
            if check.blocking
        )

    @property
    def optional_failures(self) -> tuple[
        ToolRequirementCheck,
        ...
    ]:
        """Return unsatisfied optional requirements."""

        return tuple(
            check
            for check in self.checks
            if (
                not check.requirement.required
                and not check.satisfied
            )
        )

    def first_blocking(
        self,
    ) -> Optional[ToolRequirementCheck]:
        """Return the first blocking check."""

        for check in self.checks:
            if check.blocking:
                return check

        return None

    def require_valid(
        self,
    ) -> None:
        """
        Raise RuntimeError if a required requirement is missing.
        """

        if self.valid:
            return

        messages = [
            check.message
            or check.requirement.name
            for check in self.blocking
        ]

        raise RuntimeError(
            (
                "Tool requirements are not satisfied: "
                + "; ".join(messages)
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "valid": self.valid,
            "checks": [
                check.to_dict()
                for check in self.checks
            ],
        }


# ============================================================
# TOOL REQUIREMENTS
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolRequirements:
    """
    Immutable collection of operational tool requirements.
    """

    requirements: tuple[
        ToolRequirement,
        ...
    ] = ()

    @classmethod
    def from_iterable(
        cls,
        requirements: Iterable[
            ToolRequirement
        ],
    ) -> ToolRequirements:
        """Construct requirements from an iterable."""

        normalized = tuple(
            requirements
        )

        names: set[str] = set()

        for requirement in normalized:
            if not isinstance(
                requirement,
                ToolRequirement,
            ):
                raise TypeError(
                    (
                        "All requirements must be "
                        "ToolRequirement instances."
                    )
                )

            if requirement.name in names:
                raise ValueError(
                    (
                        "Duplicate tool requirement name: "
                        f"{requirement.name!r}."
                    )
                )

            names.add(
                requirement.name
            )

        return cls(
            requirements=normalized
        )

    @property
    def empty(self) -> bool:
        """Return whether no requirements are declared."""

        return not self.requirements

    @property
    def names(self) -> tuple[str, ...]:
        """Return requirement names."""

        return tuple(
            requirement.name
            for requirement in self.requirements
        )

    @property
    def required(self) -> tuple[
        ToolRequirement,
        ...
    ]:
        """Return required requirements."""

        return tuple(
            requirement
            for requirement in self.requirements
            if requirement.required
        )

    @property
    def optional(self) -> tuple[
        ToolRequirement,
        ...
    ]:
        """Return optional requirements."""

        return tuple(
            requirement
            for requirement in self.requirements
            if not requirement.required
        )

    def contains(
        self,
        name: str,
    ) -> bool:
        """Return whether a requirement name exists."""

        return any(
            requirement.name == name
            for requirement in self.requirements
        )

    def get(
        self,
        name: str,
    ) -> Optional[ToolRequirement]:
        """Return a requirement by name."""

        for requirement in self.requirements:
            if requirement.name == name:
                return requirement

        return None

    def by_phase(
        self,
        phase: ToolRequirementPhase,
    ) -> ToolRequirements:
        """Return requirements for a specific lifecycle phase."""

        if not isinstance(
            phase,
            ToolRequirementPhase,
        ):
            raise TypeError(
                "phase must be a ToolRequirementPhase."
            )

        return ToolRequirements.from_iterable(
            requirement
            for requirement in self.requirements
            if requirement.phase == phase
        )

    def by_type(
        self,
        requirement_type: ToolRequirementType,
    ) -> ToolRequirements:
        """Return requirements of one category."""

        if not isinstance(
            requirement_type,
            ToolRequirementType,
        ):
            raise TypeError(
                (
                    "requirement_type must be a "
                    "ToolRequirementType."
                )
            )

        return ToolRequirements.from_iterable(
            requirement
            for requirement in self.requirements
            if requirement.requirement_type
            == requirement_type
        )

    def merge(
        self,
        other: ToolRequirements,
    ) -> ToolRequirements:
        """Merge two requirement declarations."""

        if not isinstance(
            other,
            ToolRequirements,
        ):
            raise TypeError(
                "other must be a ToolRequirements instance."
            )

        return ToolRequirements.from_iterable(
            (
                *self.requirements,
                *other.requirements,
            )
        )

    def evaluate(
        self,
        environment: ToolEnvironment,
        *,
        phase: ToolRequirementPhase = (
            ToolRequirementPhase.ACTIVATION
        ),
    ) -> ToolRequirementEvaluation:
        """Evaluate requirements against an environment."""

        return ToolRequirementEvaluator.evaluate(
            self,
            environment,
            phase=phase,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "requirements": [
                requirement.to_dict()
                for requirement in self.requirements
            ]
        }


# ============================================================
# REQUIREMENT EVALUATOR
# ============================================================


class ToolRequirementEvaluator:
    """
    Stateless evaluator for ToolRequirements.
    """

    @classmethod
    def evaluate(
        cls,
        requirements: ToolRequirements,
        environment: ToolEnvironment,
        *,
        phase: ToolRequirementPhase = (
            ToolRequirementPhase.ACTIVATION
        ),
    ) -> ToolRequirementEvaluation:
        """
        Evaluate all requirements applicable to the requested phase.
        """

        if not isinstance(
            requirements,
            ToolRequirements,
        ):
            raise TypeError(
                "requirements must be ToolRequirements."
            )

        if not isinstance(
            environment,
            ToolEnvironment,
        ):
            raise TypeError(
                "environment must be ToolEnvironment."
            )

        if not isinstance(
            phase,
            ToolRequirementPhase,
        ):
            raise TypeError(
                "phase must be a ToolRequirementPhase."
            )

        checks = tuple(
            cls._evaluate_requirement(
                requirement,
                environment,
            )
            for requirement in requirements.requirements
            if requirement.phase == phase
        )

        return ToolRequirementEvaluation(
            checks=checks
        )

    @classmethod
    def _evaluate_requirement(
        cls,
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        """Evaluate a single requirement."""

        evaluator = {
            ToolRequirementType.ENVIRONMENT_MODE: (
                cls._environment_mode
            ),
            ToolRequirementType.CANVAS: (
                cls._canvas
            ),
            ToolRequirementType.SCENE: (
                cls._scene
            ),
            ToolRequirementType.PROJECT: (
                cls._project
            ),
            ToolRequirementType.WRITABLE_PROJECT: (
                cls._writable_project
            ),
            ToolRequirementType.CORE: (
                cls._core
            ),
            ToolRequirementType.COMMAND_MANAGER: (
                cls._command_manager
            ),
            ToolRequirementType.COORDINATE_SYSTEM: (
                cls._coordinate_system
            ),
            ToolRequirementType.GRID_SYSTEM: (
                cls._grid_system
            ),
            ToolRequirementType.SNAP_SYSTEM: (
                cls._snap_system
            ),
            ToolRequirementType.SELECTION: (
                cls._selection
            ),
            ToolRequirementType.NAVIGATION: (
                cls._navigation
            ),
            ToolRequirementType.INTERACTION: (
                cls._interaction
            ),
            ToolRequirementType.RENDERER: (
                cls._renderer
            ),
        }.get(
            requirement.requirement_type
        )

        if evaluator is None:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.INVALID,
                message=(
                    "No evaluator exists for requirement type "
                    f"{requirement.requirement_type.value!r}."
                ),
            )

        try:
            return evaluator(
                requirement,
                environment,
            )
        except Exception as exc:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.INVALID,
                message=(
                    f"Requirement evaluation failed: {exc}"
                ),
            )

    # ========================================================
    # STANDARD EVALUATORS
    # ========================================================

    @staticmethod
    def _environment_mode(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        expected = requirement.metadata.get(
            "mode"
        )

        if expected is None:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.INVALID,
                message=(
                    "Environment-mode requirement requires "
                    "metadata['mode']."
                ),
            )

        try:
            if isinstance(
                expected,
                ToolEnvironmentMode,
            ):
                expected_mode = expected
            else:
                expected_mode = ToolEnvironmentMode(
                    str(expected)
                )
        except ValueError:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.INVALID,
                message=(
                    f"Invalid environment mode: {expected!r}."
                ),
            )

        if environment.mode == expected_mode:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message=(
                    f"Environment is in "
                    f"{expected_mode.value} mode."
                ),
                value=environment.mode,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message=(
                f"Tool requires {expected_mode.value!r} mode; "
                f"current mode is {environment.mode.value!r}."
            ),
            value=environment.mode,
        )

    @staticmethod
    def _canvas(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if environment.canvas_available:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message="Active canvas is available.",
                value=environment.canvas,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message="No active canvas is available.",
        )

    @staticmethod
    def _scene(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if environment.scene is not None:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message="Active scene is available.",
                value=environment.scene,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message="No active scene is available.",
        )

    @staticmethod
    def _project(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if environment.project_available:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message="Active project is available.",
                value=environment.project,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message="No active project is available.",
        )

    @staticmethod
    def _writable_project(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if not environment.project_available:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.MISSING,
                message="No active project is available.",
            )

        if environment.read_only:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.MISSING,
                message="Active project is read-only.",
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.SATISFIED,
            message="Active project is writable.",
            value=environment.project,
        )

    @staticmethod
    def _core(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if environment.core_available:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message="Core service is available.",
                value=environment.core,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message="Core service is unavailable.",
        )

    @staticmethod
    def _command_manager(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if environment.command_manager_available:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message="CommandManager is available.",
                value=environment.command_manager,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message="CommandManager is unavailable.",
        )

    @staticmethod
    def _coordinate_system(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if environment.coordinate_system_available:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message="CoordinateSystem is available.",
                value=environment.coordinate_system,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message="CoordinateSystem is unavailable.",
        )

    @staticmethod
    def _grid_system(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if environment.grid_system_available:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message="GridSystem is available.",
                value=environment.grid_system,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message="GridSystem is unavailable.",
        )

    @staticmethod
    def _snap_system(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if environment.snap_system_available:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message="SnapSystem is available.",
                value=environment.snap_system,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message="SnapSystem is unavailable.",
        )

    @staticmethod
    def _selection(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if environment.selection_available:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message="Selection service is available.",
                value=environment.selection,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message="Selection service is unavailable.",
        )

    @staticmethod
    def _navigation(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if environment.navigation_available:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message="Navigation service is available.",
                value=environment.navigation,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message="Navigation service is unavailable.",
        )

    @staticmethod
    def _interaction(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if environment.interaction_available:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message="Interaction service is available.",
                value=environment.interaction,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message="Interaction service is unavailable.",
        )

    @staticmethod
    def _renderer(
        requirement: ToolRequirement,
        environment: ToolEnvironment,
    ) -> ToolRequirementCheck:
        if environment.renderer_available:
            return ToolRequirementCheck(
                requirement=requirement,
                status=ToolRequirementStatus.SATISFIED,
                message="Renderer is available.",
                value=environment.renderer,
            )

        return ToolRequirementCheck(
            requirement=requirement,
            status=ToolRequirementStatus.MISSING,
            message="Renderer is unavailable.",
        )


# ============================================================
# REQUIREMENT BUILDERS
# ============================================================


def environment_mode_requirement(
    mode: ToolEnvironmentMode | str,
    *,
    required: bool = True,
    phase: ToolRequirementPhase = (
        ToolRequirementPhase.ACTIVATION
    ),
    description: str = "",
) -> ToolRequirement:
    """Create an environment-mode requirement."""

    if not isinstance(
        mode,
        ToolEnvironmentMode,
    ):
        mode = ToolEnvironmentMode(
            str(mode)
        )

    return ToolRequirement(
        name=f"environment_mode:{mode.value}",
        requirement_type=(
            ToolRequirementType.ENVIRONMENT_MODE
        ),
        phase=phase,
        severity=(
            ToolRequirementSeverity.REQUIRED
            if required
            else ToolRequirementSeverity.OPTIONAL
        ),
        description=description
        or (
            f"Environment must be in "
            f"{mode.value} mode."
        ),
        metadata={
            "mode": mode.value,
        },
    )


def service_requirement(
    name: str,
    requirement_type: ToolRequirementType,
    *,
    required: bool = True,
    phase: ToolRequirementPhase = (
        ToolRequirementPhase.ACTIVATION
    ),
    description: str = "",
) -> ToolRequirement:
    """Create a service availability requirement."""

    if requirement_type in (
        ToolRequirementType.ENVIRONMENT_MODE,
    ):
        raise ValueError(
            (
                "Use environment_mode_requirement() for "
                "environment-mode requirements."
            )
        )

    return ToolRequirement(
        name=name,
        requirement_type=requirement_type,
        phase=phase,
        severity=(
            ToolRequirementSeverity.REQUIRED
            if required
            else ToolRequirementSeverity.OPTIONAL
        ),
        description=description,
    )


# ============================================================
# STANDARD TOOL PROFILES
# ============================================================


def select_tool_requirements() -> ToolRequirements:
    """
    Canonical requirements for SelectTool.

    Selection is a canvas interaction and therefore requires the
    canvas, scene, coordinate system, and selection infrastructure.
    """

    return ToolRequirements.from_iterable(
        (
            environment_mode_requirement(
                ToolEnvironmentMode.CANVAS
            ),
            service_requirement(
                "canvas",
                ToolRequirementType.CANVAS,
            ),
            service_requirement(
                "scene",
                ToolRequirementType.SCENE,
            ),
            service_requirement(
                "coordinate_system",
                ToolRequirementType.COORDINATE_SYSTEM,
            ),
            service_requirement(
                "selection",
                ToolRequirementType.SELECTION,
            ),
        )
    )


def bus_tool_requirements() -> ToolRequirements:
    """
    Canonical requirements for BusTool.

    BusTool creates a domain object through the command layer.
    """

    return ToolRequirements.from_iterable(
        (
            environment_mode_requirement(
                ToolEnvironmentMode.CANVAS
            ),
            service_requirement(
                "canvas",
                ToolRequirementType.CANVAS,
            ),
            service_requirement(
                "scene",
                ToolRequirementType.SCENE,
            ),
            service_requirement(
                "coordinate_system",
                ToolRequirementType.COORDINATE_SYSTEM,
            ),
            service_requirement(
                "grid_system",
                ToolRequirementType.GRID_SYSTEM,
            ),
            service_requirement(
                "core",
                ToolRequirementType.CORE,
            ),
            service_requirement(
                "command_manager",
                ToolRequirementType.COMMAND_MANAGER,
            ),
            service_requirement(
                "writable_project",
                ToolRequirementType.WRITABLE_PROJECT,
            ),
        )
    )


def line_tool_requirements() -> ToolRequirements:
    """
    Canonical requirements for LineTool.

    LineTool requires topology-aware snapping and command execution.
    """

    return ToolRequirements.from_iterable(
        (
            environment_mode_requirement(
                ToolEnvironmentMode.CANVAS
            ),
            service_requirement(
                "canvas",
                ToolRequirementType.CANVAS,
            ),
            service_requirement(
                "scene",
                ToolRequirementType.SCENE,
            ),
            service_requirement(
                "coordinate_system",
                ToolRequirementType.COORDINATE_SYSTEM,
            ),
            service_requirement(
                "grid_system",
                ToolRequirementType.GRID_SYSTEM,
            ),
            service_requirement(
                "snap_system",
                ToolRequirementType.SNAP_SYSTEM,
            ),
            service_requirement(
                "core",
                ToolRequirementType.CORE,
            ),
            service_requirement(
                "command_manager",
                ToolRequirementType.COMMAND_MANAGER,
            ),
            service_requirement(
                "writable_project",
                ToolRequirementType.WRITABLE_PROJECT,
            ),
        )
    )


def requirements_for_tool(
    tool_id: str,
) -> ToolRequirements:
    """
    Return the canonical requirement profile for one of the
    three concrete GridForge V2 tools.
    """

    if not isinstance(
        tool_id,
        str,
    ):
        raise TypeError(
            "tool_id must be a string."
        )

    normalized = tool_id.strip()

    profiles = {
        "select": select_tool_requirements,
        "bus": bus_tool_requirements,
        "line": line_tool_requirements,
    }

    try:
        return profiles[
            normalized
        ]()
    except KeyError as exc:
        raise KeyError(
            (
                "No standard requirement profile exists for "
                f"tool {tool_id!r}."
            )
        ) from exc


# ============================================================
# UTILITY FUNCTIONS
# ============================================================


def evaluate_tool_requirements(
    tool_id: str,
    environment: ToolEnvironment,
    *,
    phase: ToolRequirementPhase = (
        ToolRequirementPhase.ACTIVATION
    ),
) -> ToolRequirementEvaluation:
    """
    Evaluate the canonical requirements of a concrete tool.
    """

    return requirements_for_tool(
        tool_id
    ).evaluate(
        environment,
        phase=phase,
    )


def can_activate_tool(
    tool_id: str,
    environment: ToolEnvironment,
) -> bool:
    """
    Return whether the specified concrete tool can be activated.
    """

    return evaluate_tool_requirements(
        tool_id,
        environment,
        phase=ToolRequirementPhase.ACTIVATION,
    ).valid


__all__ = [
    "ToolRequirementType",
    "ToolRequirementPhase",
    "ToolRequirementSeverity",
    "ToolRequirementStatus",
    "ToolRequirement",
    "ToolRequirementCheck",
    "ToolRequirementEvaluation",
    "ToolRequirements",
    "ToolRequirementEvaluator",
    "environment_mode_requirement",
    "service_requirement",
    "select_tool_requirements",
    "bus_tool_requirements",
    "line_tool_requirements",
    "requirements_for_tool",
    "evaluate_tool_requirements",
    "can_activate_tool",
]
