# ============================================================
# File: ui/tools/tool_environment.py
# GridForge V2 — Tool Environment
# ============================================================
"""
Runtime environment exposed to GridForge V2 tools.

ToolEnvironment is the UI-side runtime context through which tools
access the services they need during interaction.

It is deliberately a composition object, not a service locator.

Responsibilities
----------------
    - hold references to injected UI/application services;
    - expose the active canvas and related infrastructure;
    - expose project/core/command services;
    - expose current interaction mode;
    - provide capability-oriented availability queries;
    - provide a detached diagnostic snapshot.

Non-responsibilities
--------------------
    - creating services;
    - owning Core domain state;
    - performing domain validation;
    - executing commands;
    - handling Qt events;
    - implementing snapping;
    - implementing rendering;
    - deciding which tool is active.

The composition/plugin layer constructs ToolEnvironment and injects
it into the tool system.

Core remains authoritative for project/domain state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


# ============================================================
# ENVIRONMENT MODE
# ============================================================


class ToolEnvironmentMode(str, Enum):
    """
    High-level interaction environment available to tools.
    """

    CANVAS = "canvas"
    CONTROL = "control"


# ============================================================
# CANVAS AVAILABILITY
# ============================================================


class CanvasAvailability(str, Enum):
    """
    Availability state of the active canvas.
    """

    UNAVAILABLE = "unavailable"
    AVAILABLE = "available"
    DISABLED = "disabled"


# ============================================================
# PROJECT AVAILABILITY
# ============================================================


class ProjectAvailability(str, Enum):
    """
    Availability state of the active project.
    """

    UNAVAILABLE = "unavailable"
    AVAILABLE = "available"
    READ_ONLY = "read_only"


# ============================================================
# ENVIRONMENT STATUS
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolEnvironmentStatus:
    """
    Immutable summary of environment availability.
    """

    mode: ToolEnvironmentMode

    canvas: CanvasAvailability

    project: ProjectAvailability

    core_available: bool

    command_manager_available: bool

    selection_available: bool

    navigation_available: bool

    coordinate_system_available: bool

    grid_system_available: bool

    snap_system_available: bool

    renderer_available: bool

    interaction_available: bool

    @property
    def canvas_available(self) -> bool:
        """Return whether an active canvas is available."""

        return self.canvas == CanvasAvailability.AVAILABLE

    @property
    def project_available(self) -> bool:
        """Return whether a project is available."""

        return self.project != ProjectAvailability.UNAVAILABLE

    @property
    def writable(self) -> bool:
        """
        Return whether project mutation is permitted by environment
        availability.

        This is only an environment-level check. Core and command
        validation remain authoritative.
        """

        return self.project == ProjectAvailability.AVAILABLE

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "mode": self.mode.value,
            "canvas": self.canvas.value,
            "project": self.project.value,
            "core_available": self.core_available,
            "command_manager_available": (
                self.command_manager_available
            ),
            "selection_available": (
                self.selection_available
            ),
            "navigation_available": (
                self.navigation_available
            ),
            "coordinate_system_available": (
                self.coordinate_system_available
            ),
            "grid_system_available": (
                self.grid_system_available
            ),
            "snap_system_available": (
                self.snap_system_available
            ),
            "renderer_available": self.renderer_available,
            "interaction_available": (
                self.interaction_available
            ),
        }


# ============================================================
# TOOL ENVIRONMENT
# ============================================================


@dataclass(slots=True)
class ToolEnvironment:
    """
    Runtime dependency environment for GridForge tools.

    All service references are injected.

    ToolEnvironment does not instantiate missing services and does
    not silently substitute global objects.
    """

    # --------------------------------------------------------
    # PRIMARY APPLICATION SERVICES
    # --------------------------------------------------------

    core: Any = None

    command_manager: Any = None

    project: Any = None

    # --------------------------------------------------------
    # CANVAS SERVICES
    # --------------------------------------------------------

    canvas: Any = None

    scene: Any = None

    coordinate_system: Any = None

    grid_system: Any = None

    snap_system: Any = None

    renderer: Any = None

    # --------------------------------------------------------
    # INTERACTION SERVICES
    # --------------------------------------------------------

    selection: Any = None

    navigation: Any = None

    interaction: Any = None

    # --------------------------------------------------------
    # ENVIRONMENT METADATA
    # --------------------------------------------------------

    mode: ToolEnvironmentMode = (
        ToolEnvironmentMode.CANVAS
    )

    read_only: bool = False

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __post_init__(self) -> None:
        """Validate the environment configuration."""

        if not isinstance(
            self.mode,
            ToolEnvironmentMode,
        ):
            self.mode = self._normalize_mode(
                self.mode
            )

        if not isinstance(
            self.read_only,
            bool,
        ):
            raise TypeError(
                "read_only must be a bool."
            )

    # ========================================================
    # AVAILABILITY
    # ========================================================

    @property
    def canvas_available(self) -> bool:
        """Return whether an active canvas is available."""

        return self.canvas is not None

    @property
    def project_available(self) -> bool:
        """Return whether a project object is available."""

        return self.project is not None

    @property
    def core_available(self) -> bool:
        """Return whether Core is available."""

        return self.core is not None

    @property
    def command_manager_available(self) -> bool:
        """Return whether CommandManager is available."""

        return self.command_manager is not None

    @property
    def selection_available(self) -> bool:
        """Return whether selection infrastructure is available."""

        return self.selection is not None

    @property
    def navigation_available(self) -> bool:
        """Return whether navigation infrastructure is available."""

        return self.navigation is not None

    @property
    def coordinate_system_available(self) -> bool:
        """Return whether coordinate conversion is available."""

        return self.coordinate_system is not None

    @property
    def grid_system_available(self) -> bool:
        """Return whether grid infrastructure is available."""

        return self.grid_system is not None

    @property
    def snap_system_available(self) -> bool:
        """Return whether snapping infrastructure is available."""

        return self.snap_system is not None

    @property
    def renderer_available(self) -> bool:
        """Return whether renderer infrastructure is available."""

        return self.renderer is not None

    @property
    def interaction_available(self) -> bool:
        """Return whether interaction infrastructure is available."""

        return self.interaction is not None

    @property
    def writable(self) -> bool:
        """
        Return whether the environment is configured for mutation.

        This does not bypass Core validation or command policy.
        """

        return (
            not self.read_only
            and self.project_available
        )

    # ========================================================
    # STATUS
    # ========================================================

    def status(self) -> ToolEnvironmentStatus:
        """Return the current environment status."""

        if self.canvas is None:
            canvas_state = (
                CanvasAvailability.UNAVAILABLE
            )
        elif self.mode != ToolEnvironmentMode.CANVAS:
            canvas_state = (
                CanvasAvailability.DISABLED
            )
        else:
            canvas_state = (
                CanvasAvailability.AVAILABLE
            )

        if self.project is None:
            project_state = (
                ProjectAvailability.UNAVAILABLE
            )
        elif self.read_only:
            project_state = (
                ProjectAvailability.READ_ONLY
            )
        else:
            project_state = (
                ProjectAvailability.AVAILABLE
            )

        return ToolEnvironmentStatus(
            mode=self.mode,
            canvas=canvas_state,
            project=project_state,
            core_available=self.core_available,
            command_manager_available=(
                self.command_manager_available
            ),
            selection_available=(
                self.selection_available
            ),
            navigation_available=(
                self.navigation_available
            ),
            coordinate_system_available=(
                self.coordinate_system_available
            ),
            grid_system_available=(
                self.grid_system_available
            ),
            snap_system_available=(
                self.snap_system_available
            ),
            renderer_available=self.renderer_available,
            interaction_available=(
                self.interaction_available
            ),
        )

    # ========================================================
    # MODE
    # ========================================================

    def set_mode(
        self,
        mode: ToolEnvironmentMode | str,
    ) -> None:
        """
        Set the active environment mode.

        Mode changes do not automatically change the active tool.
        ToolController / ToolManager remains responsible for tool
        selection and lifecycle.
        """

        self.mode = self._normalize_mode(
            mode
        )

    def is_canvas_mode(self) -> bool:
        """Return whether Canvas mode is active."""

        return self.mode == ToolEnvironmentMode.CANVAS

    def is_control_mode(self) -> bool:
        """Return whether Control mode is active."""

        return self.mode == ToolEnvironmentMode.CONTROL

    # ========================================================
    # DEPENDENCY ACCESS
    # ========================================================

    def get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return a named environment service.

        This method is intentionally limited to the explicit fields
        of ToolEnvironment. It is not a global service locator.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Environment service name must be a string."
            )

        normalized = name.strip()

        if not normalized:
            raise ValueError(
                "Environment service name must not be empty."
            )

        if not hasattr(
            self,
            normalized,
        ):
            return default

        return getattr(
            self,
            normalized,
        )

    def require(
        self,
        name: str,
    ) -> Any:
        """
        Return a named environment service.

        Raises RuntimeError when the service is unavailable.
        """

        value = self.get(
            name,
            None,
        )

        if value is None:
            raise RuntimeError(
                (
                    f"Required tool environment service "
                    f"{name!r} is unavailable."
                )
            )

        return value

    # ========================================================
    # CANVAS
    # ========================================================

    def require_canvas(self) -> Any:
        """Return the active canvas or raise RuntimeError."""

        if not self.canvas_available:
            raise RuntimeError(
                "No active canvas is available."
            )

        if not self.is_canvas_mode():
            raise RuntimeError(
                "Canvas access requires Canvas mode."
            )

        return self.canvas

    def require_coordinate_system(self) -> Any:
        """Return the coordinate system or raise RuntimeError."""

        if not self.coordinate_system_available:
            raise RuntimeError(
                "CoordinateSystem is unavailable."
            )

        return self.coordinate_system

    def require_grid_system(self) -> Any:
        """Return the grid system or raise RuntimeError."""

        if not self.grid_system_available:
            raise RuntimeError(
                "GridSystem is unavailable."
            )

        return self.grid_system

    def require_snap_system(self) -> Any:
        """Return the snap system or raise RuntimeError."""

        if not self.snap_system_available:
            raise RuntimeError(
                "SnapSystem is unavailable."
            )

        return self.snap_system

    # ========================================================
    # APPLICATION
    # ========================================================

    def require_core(self) -> Any:
        """Return Core or raise RuntimeError."""

        if not self.core_available:
            raise RuntimeError(
                "Core service is unavailable."
            )

        return self.core

    def require_command_manager(self) -> Any:
        """Return CommandManager or raise RuntimeError."""

        if not self.command_manager_available:
            raise RuntimeError(
                "CommandManager is unavailable."
            )

        return self.command_manager

    def require_project(self) -> Any:
        """Return the active project or raise RuntimeError."""

        if not self.project_available:
            raise RuntimeError(
                "No active project is available."
            )

        return self.project

    # ========================================================
    # INTERACTION
    # ========================================================

    def require_selection(self) -> Any:
        """Return selection infrastructure or raise RuntimeError."""

        if not self.selection_available:
            raise RuntimeError(
                "Selection service is unavailable."
            )

        return self.selection

    def require_navigation(self) -> Any:
        """Return navigation infrastructure or raise RuntimeError."""

        if not self.navigation_available:
            raise RuntimeError(
                "Navigation service is unavailable."
            )

        return self.navigation

    def require_interaction(self) -> Any:
        """Return interaction infrastructure or raise RuntimeError."""

        if not self.interaction_available:
            raise RuntimeError(
                "Interaction service is unavailable."
            )

        return self.interaction

    # ========================================================
    # REQUIREMENT CHECKS
    # ========================================================

    def has_services(
        self,
        *names: str,
    ) -> bool:
        """
        Return whether all named services are available.
        """

        return all(
            self.get(
                name,
                None,
            )
            is not None
            for name in names
        )

    def missing_services(
        self,
        *names: str,
    ) -> tuple[str, ...]:
        """
        Return unavailable services in declaration order.
        """

        return tuple(
            name
            for name in names
            if self.get(
                name,
                None,
            ) is None
        )

    def require_services(
        self,
        *names: str,
    ) -> None:
        """
        Require all named services to be available.
        """

        missing = self.missing_services(
            *names
        )

        if missing:
            raise RuntimeError(
                (
                    "Required tool environment services are "
                    f"unavailable: {', '.join(missing)}."
                )
            )

    # ========================================================
    # MUTABILITY
    # ========================================================

    def require_writable(self) -> None:
        """
        Require a writable project environment.

        This is a UI precondition only. Core remains authoritative
        for whether a particular mutation is valid.
        """

        if self.project is None:
            raise RuntimeError(
                "A project is required for mutation."
            )

        if self.read_only:
            raise RuntimeError(
                "The active project is read-only."
            )

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def snapshot(
        self,
    ) -> dict[str, Any]:
        """
        Return a detached diagnostic environment snapshot.

        Service instances are represented by availability rather
        than serialized into the snapshot.
        """

        status = self.status()

        return {
            "mode": self.mode.value,
            "read_only": self.read_only,
            "status": status.to_dict(),
            "services": {
                "core": self.core_available,
                "command_manager": (
                    self.command_manager_available
                ),
                "project": self.project_available,
                "canvas": self.canvas_available,
                "scene": self.scene is not None,
                "coordinate_system": (
                    self.coordinate_system_available
                ),
                "grid_system": (
                    self.grid_system_available
                ),
                "snap_system": (
                    self.snap_system_available
                ),
                "renderer": self.renderer_available,
                "selection": self.selection_available,
                "navigation": self.navigation_available,
                "interaction": self.interaction_available,
            },
            "metadata": dict(
                self.metadata
            ),
        }

    # ========================================================
    # CLONING / DERIVATION
    # ========================================================

    def with_mode(
        self,
        mode: ToolEnvironmentMode | str,
    ) -> ToolEnvironment:
        """
        Return a shallow environment copy with another mode.

        Service ownership remains unchanged.
        """

        return ToolEnvironment(
            core=self.core,
            command_manager=self.command_manager,
            project=self.project,
            canvas=self.canvas,
            scene=self.scene,
            coordinate_system=self.coordinate_system,
            grid_system=self.grid_system,
            snap_system=self.snap_system,
            renderer=self.renderer,
            selection=self.selection,
            navigation=self.navigation,
            interaction=self.interaction,
            mode=self._normalize_mode(
                mode
            ),
            read_only=self.read_only,
            metadata=dict(
                self.metadata
            ),
        )

    def with_canvas(
        self,
        canvas: Any,
        *,
        scene: Any = None,
    ) -> ToolEnvironment:
        """
        Return a shallow environment copy with another canvas.

        This does not register the canvas globally and does not
        alter application state.
        """

        return ToolEnvironment(
            core=self.core,
            command_manager=self.command_manager,
            project=self.project,
            canvas=canvas,
            scene=scene,
            coordinate_system=self.coordinate_system,
            grid_system=self.grid_system,
            snap_system=self.snap_system,
            renderer=self.renderer,
            selection=self.selection,
            navigation=self.navigation,
            interaction=self.interaction,
            mode=self.mode,
            read_only=self.read_only,
            metadata=dict(
                self.metadata
            ),
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate_canvas_environment(
        self,
    ) -> tuple[str, ...]:
        """
        Return missing services required for normal canvas tools.
        """

        required = (
            "canvas",
            "coordinate_system",
            "grid_system",
        )

        return self.missing_services(
            *required
        )

    def validate_command_environment(
        self,
    ) -> tuple[str, ...]:
        """
        Return missing services required for command-driven tools.
        """

        required = (
            "core",
            "command_manager",
        )

        return self.missing_services(
            *required
        )

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    @staticmethod
    def _normalize_mode(
        mode: ToolEnvironmentMode | str,
    ) -> ToolEnvironmentMode:
        """Normalize an environment mode."""

        if isinstance(
            mode,
            ToolEnvironmentMode,
        ):
            return mode

        if not isinstance(
            mode,
            str,
        ):
            raise TypeError(
                (
                    "mode must be a ToolEnvironmentMode "
                    "or string."
                )
            )

        value = mode.strip()

        if not value:
            raise ValueError(
                "mode must not be empty."
            )

        try:
            return ToolEnvironmentMode(
                value
            )
        except ValueError as exc:
            raise ValueError(
                f"Unknown tool environment mode: {mode!r}."
            ) from exc


# ============================================================
# ENVIRONMENT FACTORIES
# ============================================================


def create_canvas_environment(
    *,
    core: Any = None,
    command_manager: Any = None,
    project: Any = None,
    canvas: Any = None,
    scene: Any = None,
    coordinate_system: Any = None,
    grid_system: Any = None,
    snap_system: Any = None,
    renderer: Any = None,
    selection: Any = None,
    navigation: Any = None,
    interaction: Any = None,
    read_only: bool = False,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> ToolEnvironment:
    """
    Construct a Canvas-mode ToolEnvironment.

    This is a composition helper only.
    """

    return ToolEnvironment(
        core=core,
        command_manager=command_manager,
        project=project,
        canvas=canvas,
        scene=scene,
        coordinate_system=coordinate_system,
        grid_system=grid_system,
        snap_system=snap_system,
        renderer=renderer,
        selection=selection,
        navigation=navigation,
        interaction=interaction,
        mode=ToolEnvironmentMode.CANVAS,
        read_only=read_only,
        metadata=dict(
            metadata or {}
        ),
    )


def create_control_environment(
    *,
    core: Any = None,
    command_manager: Any = None,
    project: Any = None,
    selection: Any = None,
    navigation: Any = None,
    interaction: Any = None,
    read_only: bool = False,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> ToolEnvironment:
    """
    Construct a Control-mode ToolEnvironment.

    Canvas services are intentionally optional in Control mode.
    """

    return ToolEnvironment(
        core=core,
        command_manager=command_manager,
        project=project,
        selection=selection,
        navigation=navigation,
        interaction=interaction,
        mode=ToolEnvironmentMode.CONTROL,
        read_only=read_only,
        metadata=dict(
            metadata or {}
        ),
    )


__all__ = [
    "ToolEnvironmentMode",
    "CanvasAvailability",
    "ProjectAvailability",
    "ToolEnvironmentStatus",
    "ToolEnvironment",
    "create_canvas_environment",
    "create_control_environment",
]
