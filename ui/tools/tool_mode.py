# ============================================================
# File: ui/tools/tool_mode.py
# GridForge V2 — Tool Mode
# ============================================================
"""
Tool-mode definitions for the GridForge V2 UI tool system.

Tool mode describes how the active tool participates in the
current interaction. It is distinct from:

    ToolState
        Runtime state of a tool.

    ToolEvent
        A discrete user-input event.

    ToolAction
        Semantic intent produced by a tool.

    ToolManager
        Owner of active-tool selection/lifecycle.

This module contains only semantic, UI-layer definitions.

No Qt dependency.
No Core mutation.
No command execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ToolMode(str, Enum):
    """
    Semantic interaction modes supported by GridForge tools.
    """

    IDLE = "idle"

    SELECT = "select"
    CREATE = "create"
    CONNECT = "connect"
    EDIT = "edit"

    PREVIEW = "preview"

    PAN = "pan"
    ZOOM = "zoom"

    CANCEL = "cancel"


@dataclass(frozen=True, slots=True)
class ToolModeDescriptor:
    """
    Immutable metadata describing a ToolMode.

    The descriptor is intentionally data-only. It does not control
    tool behavior.
    """

    mode: ToolMode
    description: str

    allows_selection: bool = False
    allows_creation: bool = False
    allows_connection: bool = False
    allows_preview: bool = False

    persistent: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ToolMode):
            raise TypeError(
                "mode must be a ToolMode."
            )

        if not isinstance(
            self.description,
            str,
        ) or not self.description.strip():
            raise ValueError(
                "description must be a non-empty string."
            )

        for value_name in (
            "allows_selection",
            "allows_creation",
            "allows_connection",
            "allows_preview",
            "persistent",
        ):
            if not isinstance(
                getattr(self, value_name),
                bool,
            ):
                raise TypeError(
                    f"{value_name} must be a bool."
                )


class ToolModeRegistry:
    """
    Explicit registry of supported GridForge tool modes.

    The registry is deliberately separate from ToolRegistry:
    tools and interaction modes are different architectural
    concepts.
    """

    def __init__(self) -> None:
        self._descriptors: dict[
            ToolMode,
            ToolModeDescriptor,
        ] = {}

        self._register_defaults()

    # ========================================================
    # DEFAULT MODES
    # ========================================================

    def _register_defaults(self) -> None:
        """Register the canonical GridForge interaction modes."""

        self.register(
            ToolModeDescriptor(
                mode=ToolMode.IDLE,
                description="No active interaction.",
                persistent=True,
            )
        )

        self.register(
            ToolModeDescriptor(
                mode=ToolMode.SELECT,
                description="Select and inspect canvas objects.",
                allows_selection=True,
                persistent=True,
            )
        )

        self.register(
            ToolModeDescriptor(
                mode=ToolMode.CREATE,
                description="Create a new canvas object.",
                allows_creation=True,
                persistent=True,
            )
        )

        self.register(
            ToolModeDescriptor(
                mode=ToolMode.CONNECT,
                description="Create or edit a topology connection.",
                allows_connection=True,
                persistent=True,
            )
        )

        self.register(
            ToolModeDescriptor(
                mode=ToolMode.EDIT,
                description="Edit an existing canvas object.",
                allows_selection=True,
                persistent=True,
            )
        )

        self.register(
            ToolModeDescriptor(
                mode=ToolMode.PREVIEW,
                description="Display a transient interaction preview.",
                allows_preview=True,
                persistent=False,
            )
        )

        self.register(
            ToolModeDescriptor(
                mode=ToolMode.PAN,
                description="Pan the active canvas.",
                persistent=False,
            )
        )

        self.register(
            ToolModeDescriptor(
                mode=ToolMode.ZOOM,
                description="Zoom the active canvas.",
                persistent=False,
            )
        )

        self.register(
            ToolModeDescriptor(
                mode=ToolMode.CANCEL,
                description="Cancel the current interaction.",
                persistent=False,
            )
        )

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        descriptor: ToolModeDescriptor,
    ) -> None:
        """Register a mode descriptor."""

        if not isinstance(
            descriptor,
            ToolModeDescriptor,
        ):
            raise TypeError(
                "descriptor must be a ToolModeDescriptor."
            )

        if descriptor.mode in self._descriptors:
            raise ValueError(
                f"Tool mode {descriptor.mode.value!r} "
                "is already registered."
            )

        self._descriptors[
            descriptor.mode
        ] = descriptor

    # --------------------------------------------------------

    def unregister(
        self,
        mode: ToolMode,
    ) -> ToolModeDescriptor:
        """Remove and return a mode descriptor."""

        self._validate_mode(
            mode
        )

        try:
            return self._descriptors.pop(
                mode
            )
        except KeyError as exc:
            raise KeyError(
                f"Tool mode {mode.value!r} is not registered."
            ) from exc

    # ========================================================
    # LOOKUP
    # ========================================================

    def get(
        self,
        mode: ToolMode,
    ) -> ToolModeDescriptor:
        """Return the descriptor for a mode."""

        self._validate_mode(
            mode
        )

        try:
            return self._descriptors[
                mode
            ]
        except KeyError as exc:
            raise KeyError(
                f"Tool mode {mode.value!r} is not registered."
            ) from exc

    # --------------------------------------------------------

    def get_optional(
        self,
        mode: ToolMode,
    ) -> Optional[ToolModeDescriptor]:
        """Return a descriptor or None."""

        self._validate_mode(
            mode
        )

        return self._descriptors.get(
            mode
        )

    # --------------------------------------------------------

    def has(
        self,
        mode: ToolMode,
    ) -> bool:
        """Return whether a mode is registered."""

        self._validate_mode(
            mode
        )

        return mode in self._descriptors

    # ========================================================
    # MODE CLASSIFICATION
    # ========================================================

    def is_persistent(
        self,
        mode: ToolMode,
    ) -> bool:
        """Return whether a mode is persistent."""

        return self.get(
            mode
        ).persistent

    def allows_selection(
        self,
        mode: ToolMode,
    ) -> bool:
        """Return whether a mode permits selection."""

        return self.get(
            mode
        ).allows_selection

    def allows_creation(
        self,
        mode: ToolMode,
    ) -> bool:
        """Return whether a mode permits creation."""

        return self.get(
            mode
        ).allows_creation

    def allows_connection(
        self,
        mode: ToolMode,
    ) -> bool:
        """Return whether a mode permits connection."""

        return self.get(
            mode
        ).allows_connection

    def allows_preview(
        self,
        mode: ToolMode,
    ) -> bool:
        """Return whether a mode permits preview."""

        return self.get(
            mode
        ).allows_preview

    # ========================================================
    # ITERATION
    # ========================================================

    def modes(
        self,
    ) -> tuple[ToolMode, ...]:
        """Return registered modes in deterministic order."""

        return tuple(
            self._descriptors.keys()
        )

    def descriptors(
        self,
    ) -> tuple[ToolModeDescriptor, ...]:
        """Return registered descriptors in deterministic order."""

        return tuple(
            self._descriptors.values()
        )

    def __iter__(self):
        return iter(
            self.descriptors()
        )

    def __len__(self) -> int:
        return len(
            self._descriptors
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, object]:
        """Return a deterministic diagnostic snapshot."""

        return {
            "count": len(
                self._descriptors
            ),
            "modes": tuple(
                mode.value
                for mode in self.modes()
            ),
        }

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"modes={tuple(mode.value for mode in self.modes())!r}"
            ")"
        )

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    @staticmethod
    def _validate_mode(
        mode: ToolMode,
    ) -> None:
        """Validate a ToolMode value."""

        if not isinstance(
            mode,
            ToolMode,
        ):
            raise TypeError(
                "mode must be a ToolMode."
            )


__all__ = [
    "ToolMode",
    "ToolModeDescriptor",
    "ToolModeRegistry",
]
