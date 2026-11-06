# ============================================================
# File: ui/tools/tool_dependencies.py
# GridForge V2 — Tool Dependencies
# ============================================================
"""
Dependency declarations for the GridForge V2 tool system.

This module describes the UI services a tool expects to interact
with. It does not create, own, or mutate those services.

Architectural boundary
----------------------

    ToolDependencies
          |
          v
    Tool / ToolAdapter
          |
          v
    UI infrastructure
          |
          v
    Core / Command layer

Dependencies are injected by the composition/root layer. Concrete
tools must not discover global application objects implicitly.

The dependency model is intentionally structural and lightweight.
It is suitable for:

    - ToolManager
    - ToolController
    - ToolFactory
    - ToolAdapter
    - controller/plugin composition

It must remain independent of Qt.

Core remains authoritative for domain state and validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, FrozenSet, Iterable, Mapping, Optional, Protocol


# ============================================================
# DEPENDENCY TYPE
# ============================================================


class ToolDependencyType(str, Enum):
    """Supported categories of UI tool dependencies."""

    CANVAS = "canvas"
    SCENE = "scene"
    COORDINATE_SYSTEM = "coordinate_system"
    GRID_SYSTEM = "grid_system"
    SNAP_SYSTEM = "snap_system"

    SELECTION = "selection"
    NAVIGATION = "navigation"

    COMMAND_MANAGER = "command_manager"
    CORE = "core"
    PROJECT = "project"

    RENDERER = "renderer"
    INTERACTION = "interaction"
    CONTEXT = "context"


# ============================================================
# DEPENDENCY SCOPE
# ============================================================


class ToolDependencyScope(str, Enum):
    """
    Lifetime/scope classification of a dependency.

    The scope is descriptive metadata. Dependency ownership is
    determined by the application composition layer.
    """

    APPLICATION = "application"
    PROJECT = "project"
    CANVAS = "canvas"
    TOOL = "tool"
    SESSION = "session"


# ============================================================
# DEPENDENCY SPECIFICATION
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolDependencySpec:
    """
    Declarative specification for one tool dependency.
    """

    name: str

    dependency_type: ToolDependencyType

    required: bool = True

    scope: ToolDependencyScope = ToolDependencyScope.APPLICATION

    description: str = ""

    interface: Optional[str] = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        name = self.name.strip()

        if not name:
            raise ValueError(
                "Dependency name must not be empty."
            )

        object.__setattr__(
            self,
            "name",
            name,
        )

        if not isinstance(
            self.dependency_type,
            ToolDependencyType,
        ):
            raise TypeError(
                "dependency_type must be a ToolDependencyType."
            )

        if not isinstance(
            self.scope,
            ToolDependencyScope,
        ):
            raise TypeError(
                "scope must be a ToolDependencyScope."
            )

        if not isinstance(
            self.required,
            bool,
        ):
            raise TypeError(
                "required must be a bool."
            )

        if not isinstance(
            self.description,
            str,
        ):
            raise TypeError(
                "description must be a string."
            )

        if self.interface is not None:
            if not isinstance(
                self.interface,
                str,
            ):
                raise TypeError(
                    "interface must be a string or None."
                )

            interface = self.interface.strip()

            object.__setattr__(
                self,
                "interface",
                interface or None,
            )

    @property
    def key(self) -> str:
        """Return the canonical dependency key."""

        return self.name

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "name": self.name,
            "dependency_type": self.dependency_type.value,
            "required": self.required,
            "scope": self.scope.value,
            "description": self.description,
            "interface": self.interface,
            "metadata": dict(self.metadata),
        }


# ============================================================
# DEPENDENCY SET
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolDependencies:
    """
    Immutable dependency declaration for a tool.

    The declaration contains names and requirements only. Actual
    dependency instances are supplied separately through
    ToolDependencyContainer.
    """

    specifications: tuple[
        ToolDependencySpec,
        ...,
    ] = ()

    # --------------------------------------------------------
    # CONSTRUCTION
    # --------------------------------------------------------

    @classmethod
    def from_iterable(
        cls,
        specifications: Iterable[
            ToolDependencySpec
        ],
    ) -> ToolDependencies:
        """Create a dependency declaration from specifications."""

        normalized = tuple(
            specifications
        )

        names: set[str] = set()

        for specification in normalized:
            if not isinstance(
                specification,
                ToolDependencySpec,
            ):
                raise TypeError(
                    (
                        "All dependency specifications must "
                        "be ToolDependencySpec instances."
                    )
                )

            if specification.name in names:
                raise ValueError(
                    (
                        "Duplicate tool dependency name: "
                        f"{specification.name!r}."
                    )
                )

            names.add(
                specification.name
            )

        return cls(
            specifications=normalized
        )

    # --------------------------------------------------------
    # QUERIES
    # --------------------------------------------------------

    @property
    def names(self) -> tuple[str, ...]:
        """Return dependency names in declaration order."""

        return tuple(
            specification.name
            for specification in self.specifications
        )

    @property
    def required(self) -> tuple[
        ToolDependencySpec,
        ...,
    ]:
        """Return required dependency specifications."""

        return tuple(
            specification
            for specification in self.specifications
            if specification.required
        )

    @property
    def optional(self) -> tuple[
        ToolDependencySpec,
        ...,
    ]:
        """Return optional dependency specifications."""

        return tuple(
            specification
            for specification in self.specifications
            if not specification.required
        )

    @property
    def empty(self) -> bool:
        """Return whether no dependencies are declared."""

        return not self.specifications

    def contains(
        self,
        name: str,
    ) -> bool:
        """Return whether a dependency name is declared."""

        return any(
            specification.name == name
            for specification in self.specifications
        )

    def get(
        self,
        name: str,
    ) -> Optional[ToolDependencySpec]:
        """Return a dependency specification by name."""

        for specification in self.specifications:
            if specification.name == name:
                return specification

        return None

    def by_type(
        self,
        dependency_type: ToolDependencyType,
    ) -> tuple[
        ToolDependencySpec,
        ...,
    ]:
        """Return dependencies belonging to one type."""

        if not isinstance(
            dependency_type,
            ToolDependencyType,
        ):
            raise TypeError(
                "dependency_type must be a ToolDependencyType."
            )

        return tuple(
            specification
            for specification in self.specifications
            if specification.dependency_type
            == dependency_type
        )

    def by_scope(
        self,
        scope: ToolDependencyScope,
    ) -> tuple[
        ToolDependencySpec,
        ...,
    ]:
        """Return dependencies belonging to one scope."""

        if not isinstance(
            scope,
            ToolDependencyScope,
        ):
            raise TypeError(
                "scope must be a ToolDependencyScope."
            )

        return tuple(
            specification
            for specification in self.specifications
            if specification.scope == scope
        )

    # --------------------------------------------------------
    # SET OPERATIONS
    # --------------------------------------------------------

    def merge(
        self,
        other: ToolDependencies,
    ) -> ToolDependencies:
        """
        Merge two dependency declarations.

        Duplicate names are rejected rather than silently replaced.
        """

        if not isinstance(
            other,
            ToolDependencies,
        ):
            raise TypeError(
                "other must be a ToolDependencies instance."
            )

        return ToolDependencies.from_iterable(
            (
                *self.specifications,
                *other.specifications,
            )
        )

    # --------------------------------------------------------
    # SERIALIZATION
    # --------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "dependencies": [
                specification.to_dict()
                for specification in self.specifications
            ]
        }


# ============================================================
# DEPENDENCY CONTAINER
# ============================================================


class ToolDependencyContainer:
    """
    Runtime container for injected tool dependencies.

    The container stores references supplied by the composition
    layer. It does not instantiate services and does not assume
    ownership of them.

    It is intentionally not a global service locator.
    """

    def __init__(
        self,
        dependencies: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> None:
        self._dependencies: dict[
            str,
            Any,
        ] = {}

        if dependencies is not None:
            for name, value in dependencies.items():
                self.set(
                    name,
                    value,
                )

    # --------------------------------------------------------
    # ACCESS
    # --------------------------------------------------------

    def set(
        self,
        name: str,
        value: Any,
    ) -> None:
        """Inject or replace a dependency."""

        normalized = self._normalize_name(
            name
        )

        if value is None:
            raise ValueError(
                (
                    f"Dependency {normalized!r} cannot be "
                    "set to None."
                )
            )

        self._dependencies[
            normalized
        ] = value

    def remove(
        self,
        name: str,
    ) -> Any:
        """Remove and return a dependency."""

        normalized = self._normalize_name(
            name
        )

        try:
            return self._dependencies.pop(
                normalized
            )
        except KeyError as exc:
            raise KeyError(
                (
                    f"Dependency {normalized!r} is not "
                    "registered."
                )
            ) from exc

    def get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """Return a dependency or default."""

        normalized = self._normalize_name(
            name
        )

        return self._dependencies.get(
            normalized,
            default,
        )

    def require(
        self,
        name: str,
    ) -> Any:
        """Return a dependency or raise KeyError."""

        normalized = self._normalize_name(
            name
        )

        try:
            return self._dependencies[
                normalized
            ]
        except KeyError as exc:
            raise KeyError(
                (
                    f"Required tool dependency "
                    f"{normalized!r} is unavailable."
                )
            ) from exc

    def contains(
        self,
        name: str,
    ) -> bool:
        """Return whether a dependency is present."""

        normalized = self._normalize_name(
            name
        )

        return normalized in self._dependencies

    @property
    def names(self) -> tuple[str, ...]:
        """Return registered dependency names."""

        return tuple(
            self._dependencies.keys()
        )

    @property
    def empty(self) -> bool:
        """Return whether the container is empty."""

        return not self._dependencies

    def snapshot(
        self,
    ) -> Mapping[str, Any]:
        """
        Return a shallow read-only-style snapshot.

        The contained objects are not copied.
        """

        return dict(
            self._dependencies
        )

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:
        """Normalize a dependency name."""

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Dependency name must be a string."
            )

        normalized = name.strip()

        if not normalized:
            raise ValueError(
                "Dependency name must not be empty."
            )

        return normalized


# ============================================================
# DEPENDENCY RESOLUTION RESULT
# ============================================================


class ToolDependencyResolutionStatus(str, Enum):
    """Outcome of dependency resolution."""

    RESOLVED = "resolved"
    MISSING_REQUIRED = "missing_required"
    MISSING_OPTIONAL = "missing_optional"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class ToolDependencyResolution:
    """
    Result of resolving a ToolDependencies declaration against
    a runtime dependency container.
    """

    status: ToolDependencyResolutionStatus

    resolved: Mapping[str, Any] = field(
        default_factory=dict
    )

    missing_required: FrozenSet[str] = frozenset()

    missing_optional: FrozenSet[str] = frozenset()

    unexpected: FrozenSet[str] = frozenset()

    def __post_init__(self) -> None:
        if self.status == (
            ToolDependencyResolutionStatus.RESOLVED
        ):
            if self.missing_required:
                raise ValueError(
                    (
                        "Resolved dependency result cannot "
                        "contain missing required dependencies."
                    )
                )

    @property
    def valid(self) -> bool:
        """Return whether all required dependencies resolved."""

        return (
            self.status
            == ToolDependencyResolutionStatus.RESOLVED
        )

    @property
    def complete(self) -> bool:
        """Return whether required and optional dependencies resolved."""

        return (
            self.valid
            and not self.missing_optional
        )

    def require_valid(self) -> None:
        """Raise RuntimeError when required dependencies are missing."""

        if self.valid:
            return

        missing = ", ".join(
            sorted(
                self.missing_required
            )
        )

        raise RuntimeError(
            (
                "Tool dependency resolution failed. "
                f"Missing required dependencies: {missing}."
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "status": self.status.value,
            "resolved": tuple(
                self.resolved.keys()
            ),
            "missing_required": tuple(
                sorted(
                    self.missing_required
                )
            ),
            "missing_optional": tuple(
                sorted(
                    self.missing_optional
                )
            ),
            "unexpected": tuple(
                sorted(
                    self.unexpected
                )
            ),
        }


# ============================================================
# DEPENDENCY RESOLVER
# ============================================================


class ToolDependencyResolver:
    """
    Resolves declarative dependencies against injected instances.

    Resolution is deterministic and side-effect free.
    """

    @staticmethod
    def resolve(
        declarations: ToolDependencies,
        container: ToolDependencyContainer,
    ) -> ToolDependencyResolution:
        """Resolve declared dependencies."""

        if not isinstance(
            declarations,
            ToolDependencies,
        ):
            return ToolDependencyResolution(
                status=ToolDependencyResolutionStatus.INVALID
            )

        if not isinstance(
            container,
            ToolDependencyContainer,
        ):
            return ToolDependencyResolution(
                status=ToolDependencyResolutionStatus.INVALID
            )

        resolved: dict[
            str,
            Any,
        ] = {}

        missing_required: set[str] = set()
        missing_optional: set[str] = set()

        for specification in declarations.specifications:
            if container.contains(
                specification.name
            ):
                resolved[
                    specification.name
                ] = container.require(
                    specification.name
                )
                continue

            if specification.required:
                missing_required.add(
                    specification.name
                )
            else:
                missing_optional.add(
                    specification.name
                )

        if missing_required:
            status = (
                ToolDependencyResolutionStatus.MISSING_REQUIRED
            )
        elif missing_optional:
            status = (
                ToolDependencyResolutionStatus.MISSING_OPTIONAL
            )
        else:
            status = (
                ToolDependencyResolutionStatus.RESOLVED
            )

        return ToolDependencyResolution(
            status=status,
            resolved=resolved,
            missing_required=frozenset(
                missing_required
            ),
            missing_optional=frozenset(
                missing_optional
            ),
        )


# ============================================================
# STRUCTURAL DEPENDENCY PROTOCOL
# ============================================================


class ToolDependencyProvider(Protocol):
    """
    Protocol for objects capable of providing dependencies.

    This protocol is intentionally minimal and does not prescribe
    ownership or implementation.
    """

    def get_dependency(
        self,
        name: str,
    ) -> Any:
        """Return a dependency by name."""
        ...


# ============================================================
# STANDARD DEPENDENCY DECLARATIONS
# ============================================================


def canvas_dependencies() -> ToolDependencies:
    """
    Dependencies commonly required by canvas-based tools.
    """

    return ToolDependencies.from_iterable(
        (
            ToolDependencySpec(
                name="canvas",
                dependency_type=ToolDependencyType.CANVAS,
                required=True,
                scope=ToolDependencyScope.CANVAS,
                description=(
                    "Active GridForge canvas interaction surface."
                ),
            ),
            ToolDependencySpec(
                name="coordinate_system",
                dependency_type=(
                    ToolDependencyType.COORDINATE_SYSTEM
                ),
                required=True,
                scope=ToolDependencyScope.CANVAS,
                description=(
                    "Canvas/world coordinate conversion service."
                ),
            ),
            ToolDependencySpec(
                name="grid_system",
                dependency_type=(
                    ToolDependencyType.GRID_SYSTEM
                ),
                required=True,
                scope=ToolDependencyScope.CANVAS,
                description=(
                    "Grid visibility and coordinate-grid service."
                ),
            ),
            ToolDependencySpec(
                name="snap_system",
                dependency_type=(
                    ToolDependencyType.SNAP_SYSTEM
                ),
                required=False,
                scope=ToolDependencyScope.CANVAS,
                description=(
                    "Optional snapping service."
                ),
            ),
        )
    )


def command_dependencies() -> ToolDependencies:
    """
    Dependencies commonly required by command-driven tools.
    """

    return ToolDependencies.from_iterable(
        (
            ToolDependencySpec(
                name="command_manager",
                dependency_type=(
                    ToolDependencyType.COMMAND_MANAGER
                ),
                required=True,
                scope=ToolDependencyScope.APPLICATION,
                description=(
                    "Authoritative command execution/history service."
                ),
            ),
            ToolDependencySpec(
                name="core",
                dependency_type=ToolDependencyType.CORE,
                required=True,
                scope=ToolDependencyScope.APPLICATION,
                description=(
                    "Authoritative GridForge domain/core service."
                ),
            ),
        )
    )


def selection_dependencies() -> ToolDependencies:
    """
    Dependencies commonly required by selection-aware tools.
    """

    return ToolDependencies.from_iterable(
        (
            ToolDependencySpec(
                name="selection",
                dependency_type=ToolDependencyType.SELECTION,
                required=True,
                scope=ToolDependencyScope.CANVAS,
                description=(
                    "Selection state/controller service."
                ),
            ),
        )
    )


# ============================================================
# STANDARD TOOL DEPENDENCY PROFILES
# ============================================================


def select_tool_dependencies() -> ToolDependencies:
    """
    Canonical dependencies for SelectTool.
    """

    return canvas_dependencies().merge(
        selection_dependencies()
    )


def bus_tool_dependencies() -> ToolDependencies:
    """
    Canonical dependencies for BusTool.

    BusTool requires the canvas, coordinate/grid infrastructure,
    command execution, and Core.
    """

    return canvas_dependencies().merge(
        command_dependencies()
    )


def line_tool_dependencies() -> ToolDependencies:
    """
    Canonical dependencies for LineTool.

    LineTool requires canvas coordinate/grid infrastructure,
    snapping, command execution, and Core.
    """

    return ToolDependencies.from_iterable(
        (
            ToolDependencySpec(
                name="canvas",
                dependency_type=ToolDependencyType.CANVAS,
                required=True,
                scope=ToolDependencyScope.CANVAS,
                description=(
                    "Active GridForge canvas interaction surface."
                ),
            ),
            ToolDependencySpec(
                name="coordinate_system",
                dependency_type=(
                    ToolDependencyType.COORDINATE_SYSTEM
                ),
                required=True,
                scope=ToolDependencyScope.CANVAS,
                description=(
                    "Canvas/world coordinate conversion service."
                ),
            ),
            ToolDependencySpec(
                name="grid_system",
                dependency_type=(
                    ToolDependencyType.GRID_SYSTEM
                ),
                required=True,
                scope=ToolDependencyScope.CANVAS,
                description=(
                    "Grid visibility and coordinate-grid service."
                ),
            ),
            ToolDependencySpec(
                name="snap_system",
                dependency_type=(
                    ToolDependencyType.SNAP_SYSTEM
                ),
                required=True,
                scope=ToolDependencyScope.CANVAS,
                description=(
                    "Topology-aware snapping service."
                ),
            ),
            ToolDependencySpec(
                name="command_manager",
                dependency_type=(
                    ToolDependencyType.COMMAND_MANAGER
                ),
                required=True,
                scope=ToolDependencyScope.APPLICATION,
                description=(
                    "Authoritative command execution/history service."
                ),
            ),
            ToolDependencySpec(
                name="core",
                dependency_type=ToolDependencyType.CORE,
                required=True,
                scope=ToolDependencyScope.APPLICATION,
                description=(
                    "Authoritative GridForge domain/core service."
                ),
            ),
        )
    )


def dependencies_for_tool(
    tool_id: str,
) -> ToolDependencies:
    """
    Return the canonical dependency declaration for one of the
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
        "select": select_tool_dependencies,
        "bus": bus_tool_dependencies,
        "line": line_tool_dependencies,
    }

    try:
        return profiles[
            normalized
        ]()
    except KeyError as exc:
        raise KeyError(
            (
                f"No standard dependency profile exists for "
                f"tool {tool_id!r}."
            )
        ) from exc


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    "ToolDependencyType",
    "ToolDependencyScope",
    "ToolDependencySpec",
    "ToolDependencies",
    "ToolDependencyContainer",
    "ToolDependencyResolutionStatus",
    "ToolDependencyResolution",
    "ToolDependencyResolver",
    "ToolDependencyProvider",
    "canvas_dependencies",
    "command_dependencies",
    "selection_dependencies",
    "select_tool_dependencies",
    "bus_tool_dependencies",
    "line_tool_dependencies",
    "dependencies_for_tool",
]
