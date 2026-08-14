# ============================================================
# File: ui/tools/tool_capabilities.py
# GridForge V2 — Tool Capabilities
# ============================================================
"""
Capability declarations for the GridForge V2 tool system.

ToolCapabilities describes what a tool is capable of doing from
the perspective of the UI interaction layer.

It is declarative metadata.

It does NOT:

    - implement tool behavior;
    - perform Core mutations;
    - execute commands;
    - validate topology;
    - perform rendering;
    - perform hit testing;
    - perform snapping;
    - depend on Qt.

The concrete tool list remains intentionally small:

    SelectTool
    BusTool
    LineTool

Capabilities allow controllers, toolbars, menus, shortcuts, and
interaction infrastructure to reason about tools without inspecting
their concrete implementations.

Example:

    LineTool
        selectable=False
        creates_entities=True
        supports_preview=True
        supports_cancel=True
        requires_canvas=True

The capability declaration must describe UI behavior only.
Authoritative domain semantics remain in Core.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, FrozenSet, Iterable, Mapping, Optional


# ============================================================
# CAPABILITY ENUM
# ============================================================


class ToolCapability(str, Enum):
    """
    Individual capabilities supported by a tool.
    """

    SELECT = "select"
    CREATE = "create"
    DELETE = "delete"
    MOVE = "move"
    EDIT = "edit"

    PREVIEW = "preview"
    CANCEL = "cancel"
    COMMIT = "commit"

    MULTI_SELECT = "multi_select"
    MARQUEE_SELECT = "marquee_select"

    CANVAS_INPUT = "canvas_input"
    POINTER_INPUT = "pointer_input"
    KEYBOARD_INPUT = "keyboard_input"

    REQUIRES_CANVAS = "requires_canvas"
    REQUIRES_SELECTION = "requires_selection"

    USES_SNAP = "uses_snap"
    USES_GRID = "uses_grid"

    CREATES_ENTITIES = "creates_entities"
    MODIFIES_ENTITIES = "modifies_entities"
    REMOVES_ENTITIES = "removes_entities"

    COMMAND_DRIVEN = "command_driven"
    PRODUCES_EVENTS = "produces_events"


# ============================================================
# CAPABILITY CATEGORY
# ============================================================


class ToolCapabilityCategory(str, Enum):
    """
    Logical grouping of tool capabilities.
    """

    SELECTION = "selection"
    EDITING = "editing"
    INTERACTION = "interaction"
    ENVIRONMENT = "environment"
    DOMAIN = "domain"
    EXECUTION = "execution"


_CAPABILITY_CATEGORIES: dict[
    ToolCapability,
    ToolCapabilityCategory,
] = {
    ToolCapability.SELECT:
        ToolCapabilityCategory.SELECTION,
    ToolCapability.MULTI_SELECT:
        ToolCapabilityCategory.SELECTION,
    ToolCapability.MARQUEE_SELECT:
        ToolCapabilityCategory.SELECTION,
    ToolCapability.REQUIRES_SELECTION:
        ToolCapabilityCategory.SELECTION,

    ToolCapability.CREATE:
        ToolCapabilityCategory.EDITING,
    ToolCapability.DELETE:
        ToolCapabilityCategory.EDITING,
    ToolCapability.MOVE:
        ToolCapabilityCategory.EDITING,
    ToolCapability.EDIT:
        ToolCapabilityCategory.EDITING,

    ToolCapability.PREVIEW:
        ToolCapabilityCategory.INTERACTION,
    ToolCapability.CANCEL:
        ToolCapabilityCategory.INTERACTION,
    ToolCapability.COMMIT:
        ToolCapabilityCategory.INTERACTION,
    ToolCapability.CANVAS_INPUT:
        ToolCapabilityCategory.INTERACTION,
    ToolCapability.POINTER_INPUT:
        ToolCapabilityCategory.INTERACTION,
    ToolCapability.KEYBOARD_INPUT:
        ToolCapabilityCategory.INTERACTION,

    ToolCapability.REQUIRES_CANVAS:
        ToolCapabilityCategory.ENVIRONMENT,
    ToolCapability.USES_SNAP:
        ToolCapabilityCategory.ENVIRONMENT,
    ToolCapability.USES_GRID:
        ToolCapabilityCategory.ENVIRONMENT,

    ToolCapability.CREATES_ENTITIES:
        ToolCapabilityCategory.DOMAIN,
    ToolCapability.MODIFIES_ENTITIES:
        ToolCapabilityCategory.DOMAIN,
    ToolCapability.REMOVES_ENTITIES:
        ToolCapabilityCategory.DOMAIN,

    ToolCapability.COMMAND_DRIVEN:
        ToolCapabilityCategory.EXECUTION,
    ToolCapability.PRODUCES_EVENTS:
        ToolCapabilityCategory.EXECUTION,
}


# ============================================================
# CAPABILITY PROFILE
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolCapabilities:
    """
    Immutable capability profile for one tool.

    ``capabilities`` contains the canonical capability set.

    ``description`` is informational metadata and must not be used
    as a source of executable behavior.
    """

    capabilities: FrozenSet[ToolCapability] = frozenset()

    description: str = ""

    metadata: Mapping[str, Any] = ()

    # --------------------------------------------------------
    # CONSTRUCTION
    # --------------------------------------------------------

    @classmethod
    def from_iterable(
        cls,
        capabilities: Iterable[
            ToolCapability | str
        ],
        *,
        description: str = "",
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> ToolCapabilities:
        """
        Construct a capability profile from an iterable.
        """

        normalized = frozenset(
            cls._normalize_capability(
                capability
            )
            for capability in capabilities
        )

        return cls(
            capabilities=normalized,
            description=cls._normalize_description(
                description
            ),
            metadata=dict(
                metadata or {}
            ),
        )

    # --------------------------------------------------------
    # MEMBERSHIP
    # --------------------------------------------------------

    def has(
        self,
        capability: ToolCapability | str,
    ) -> bool:
        """
        Return whether the profile contains a capability.
        """

        return (
            self._normalize_capability(
                capability
            )
            in self.capabilities
        )

    def has_any(
        self,
        capabilities: Iterable[
            ToolCapability | str
        ],
    ) -> bool:
        """Return whether at least one capability is present."""

        return any(
            self.has(capability)
            for capability in capabilities
        )

    def has_all(
        self,
        capabilities: Iterable[
            ToolCapability | str
        ],
    ) -> bool:
        """Return whether all supplied capabilities are present."""

        return all(
            self.has(capability)
            for capability in capabilities
        )

    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    def by_category(
        self,
        category: ToolCapabilityCategory | str,
    ) -> FrozenSet[ToolCapability]:
        """
        Return capabilities belonging to a category.
        """

        category = self._normalize_category(
            category
        )

        return frozenset(
            capability
            for capability in self.capabilities
            if _CAPABILITY_CATEGORIES.get(
                capability
            ) == category
        )

    # --------------------------------------------------------
    # SET OPERATIONS
    # --------------------------------------------------------

    def with_capability(
        self,
        capability: ToolCapability | str,
    ) -> ToolCapabilities:
        """Return a new profile with one capability added."""

        normalized = self._normalize_capability(
            capability
        )

        return ToolCapabilities(
            capabilities=self.capabilities | {
                normalized
            },
            description=self.description,
            metadata=dict(
                self.metadata
            ),
        )

    def without_capability(
        self,
        capability: ToolCapability | str,
    ) -> ToolCapabilities:
        """Return a new profile without one capability."""

        normalized = self._normalize_capability(
            capability
        )

        return ToolCapabilities(
            capabilities=self.capabilities - {
                normalized
            },
            description=self.description,
            metadata=dict(
                self.metadata
            ),
        )

    # --------------------------------------------------------
    # SERIALIZATION
    # --------------------------------------------------------

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """Return a deterministic diagnostic representation."""

        return {
            "capabilities": sorted(
                capability.value
                for capability in self.capabilities
            ),
            "description": self.description,
            "metadata": dict(
                self.metadata
            ),
        }

    def to_values(
        self,
    ) -> tuple[str, ...]:
        """Return capability values in deterministic order."""

        return tuple(
            sorted(
                capability.value
                for capability in self.capabilities
            )
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    @staticmethod
    def _normalize_capability(
        capability: ToolCapability | str,
    ) -> ToolCapability:
        """Normalize a capability value."""

        if isinstance(
            capability,
            ToolCapability,
        ):
            return capability

        if not isinstance(
            capability,
            str,
        ):
            raise TypeError(
                (
                    "capability must be a ToolCapability "
                    "or string."
                )
            )

        value = capability.strip()

        if not value:
            raise ValueError(
                "capability must not be empty."
            )

        try:
            return ToolCapability(
                value
            )
        except ValueError as exc:
            raise ValueError(
                f"Unknown tool capability: {capability!r}."
            ) from exc

    @staticmethod
    def _normalize_category(
        category: ToolCapabilityCategory | str,
    ) -> ToolCapabilityCategory:
        """Normalize a capability category."""

        if isinstance(
            category,
            ToolCapabilityCategory,
        ):
            return category

        if not isinstance(
            category,
            str,
        ):
            raise TypeError(
                (
                    "category must be a ToolCapabilityCategory "
                    "or string."
                )
            )

        value = category.strip()

        if not value:
            raise ValueError(
                "category must not be empty."
            )

        try:
            return ToolCapabilityCategory(
                value
            )
        except ValueError as exc:
            raise ValueError(
                f"Unknown tool capability category: {category!r}."
            ) from exc

    @staticmethod
    def _normalize_description(
        description: str,
    ) -> str:
        """Normalize a capability description."""

        if not isinstance(
            description,
            str,
        ):
            raise TypeError(
                "description must be a string."
            )

        return description.strip()


# ============================================================
# STANDARD PROFILES
# ============================================================


def select_tool_capabilities() -> ToolCapabilities:
    """
    Return the canonical capability profile for SelectTool.

    This helper contains metadata only; it does not instantiate
    SelectTool.
    """

    return ToolCapabilities.from_iterable(
        (
            ToolCapability.SELECT,
            ToolCapability.MULTI_SELECT,
            ToolCapability.MARQUEE_SELECT,
            ToolCapability.CANVAS_INPUT,
            ToolCapability.POINTER_INPUT,
            ToolCapability.KEYBOARD_INPUT,
            ToolCapability.REQUIRES_CANVAS,
            ToolCapability.PRODUCES_EVENTS,
        ),
        description=(
            "Select and inspect objects on the active canvas."
        ),
    )


def bus_tool_capabilities() -> ToolCapabilities:
    """
    Return the canonical capability profile for BusTool.
    """

    return ToolCapabilities.from_iterable(
        (
            ToolCapability.CREATE,
            ToolCapability.CANVAS_INPUT,
            ToolCapability.POINTER_INPUT,
            ToolCapability.KEYBOARD_INPUT,
            ToolCapability.PREVIEW,
            ToolCapability.CANCEL,
            ToolCapability.COMMIT,
            ToolCapability.REQUIRES_CANVAS,
            ToolCapability.USES_GRID,
            ToolCapability.USES_SNAP,
            ToolCapability.CREATES_ENTITIES,
            ToolCapability.COMMAND_DRIVEN,
            ToolCapability.PRODUCES_EVENTS,
        ),
        description=(
            "Create bus elements through the canvas interaction "
            "workflow."
        ),
    )


def line_tool_capabilities() -> ToolCapabilities:
    """
    Return the canonical capability profile for LineTool.
    """

    return ToolCapabilities.from_iterable(
        (
            ToolCapability.CREATE,
            ToolCapability.CANVAS_INPUT,
            ToolCapability.POINTER_INPUT,
            ToolCapability.KEYBOARD_INPUT,
            ToolCapability.PREVIEW,
            ToolCapability.CANCEL,
            ToolCapability.COMMIT,
            ToolCapability.REQUIRES_CANVAS,
            ToolCapability.USES_GRID,
            ToolCapability.USES_SNAP,
            ToolCapability.CREATES_ENTITIES,
            ToolCapability.COMMAND_DRIVEN,
            ToolCapability.PRODUCES_EVENTS,
        ),
        description=(
            "Create electrical line connections using grid and "
            "topology-aware snapping."
        ),
    )


# ============================================================
# PROFILE REGISTRY
# ============================================================


_STANDARD_CAPABILITIES: dict[
    str,
    ToolCapabilities,
] = {
    "select": select_tool_capabilities(),
    "bus": bus_tool_capabilities(),
    "line": line_tool_capabilities(),
}


def capabilities_for_tool(
    tool_id: str,
) -> ToolCapabilities:
    """
    Return the standard capability profile for a tool ID.

    This registry describes only the three frozen concrete tools.
    It does not instantiate tools.
    """

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

    try:
        return _STANDARD_CAPABILITIES[
            normalized
        ]
    except KeyError as exc:
        raise KeyError(
            (
                f"No standard capability profile exists for "
                f"tool {tool_id!r}."
            )
        ) from exc


# ============================================================
# EXPORTS
# ============================================================


__all__ = [
    "ToolCapability",
    "ToolCapabilityCategory",
    "ToolCapabilities",
    "select_tool_capabilities",
    "bus_tool_capabilities",
    "line_tool_capabilities",
    "capabilities_for_tool",
]
