```python
# ============================================================
# File: ui/tools/bus_tool.py
# GridForge V2 — Bus Tool
# ============================================================
"""
Interactive bus-placement tool for GridForge.

Responsibilities
----------------
BusTool is responsible for:

    - handling bus-placement interaction;
    - resolving the cursor position through InteractionManager;
    - using centralized snapping infrastructure;
    - requesting creation of a Bus through Controller;
    - maintaining only temporary interaction state.

BusTool does NOT:

    - own a QGraphicsScene;
    - create QGraphicsItems;
    - render buses;
    - modify Core model objects directly;
    - calculate electrical quantities;
    - implement its own snapping algorithm;
    - manage RenderSystem;
    - own its lifecycle globally.

Architecture
------------

    InteractionManager
        │
        ├── event routing
        ├── coordinate mapping
        └── SnapSystem
                │
                ▼
             BusTool
                │
                ▼
            Controller
                │
                ▼
          Command / Core
                │
                ▼
          RenderSystem

ToolManager owns activation/deactivation.

The Core model remains authoritative for persistent bus data.

Qt Architecture
---------------

All Qt classes must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QPointF
from ui.core.tool_registry import register_tool


@register_tool("bus")
class BusTool:
    """
    Interactive tool for placing electrical buses.

    A bus is created on a valid placement click.

    Spatial resolution is delegated to the centralized
    InteractionManager/SnapSystem infrastructure.
    """

    tool_id = "bus"

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        interaction_manager: Any,
    ) -> None:
        """
        Initialize the BusTool.

        Parameters
        ----------
        controller:
            GridForge Controller.

        interaction_manager:
            GridForge InteractionManager responsible for
            coordinate conversion, snapping and interaction
            infrastructure.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        if interaction_manager is None:
            raise ValueError(
                "interaction_manager must not be None."
            )

        self.controller = controller
        self.im = interaction_manager

        # Shared snapping infrastructure.
        self.snap_system = getattr(
            interaction_manager,
            "snap_system",
            None,
        )

        if self.snap_system is None:
            raise AttributeError(
                "InteractionManager must provide "
                "snap_system."
            )

        # ----------------------------------------------------
        # Temporary interaction state.
        #
        # BusTool is otherwise stateless.
        # ----------------------------------------------------

        self.last_position: Optional[QPointF] = None

    # ========================================================
    # TOOL LIFECYCLE
    # ========================================================

    def activate(self) -> None:
        """
        Activate the BusTool.

        Activation starts with clean transient state.
        """

        self.reset()

    # --------------------------------------------------------

    def deactivate(self) -> None:
        """
        Deactivate the BusTool.

        No persistent model state is changed here.
        """

        self.reset()

    # --------------------------------------------------------

    def reset(self) -> None:
        """
        Reset temporary interaction state.
        """

        self.last_position = None

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def mouse_press(
        self,
        event: Any,
    ) -> None:
        """
        Handle a bus-placement mouse press.

        The cursor is resolved through the centralized
        SnapSystem. Persistent creation is delegated to the
        Controller.
        """

        position = self._resolve_position(
            event
        )

        if position is None:
            return

        self.last_position = QPointF(
            position.x(),
            position.y(),
        )

        # ----------------------------------------------------
        # Prevent duplicate placement on an existing bus.
        #
        # This query is delegated to InteractionManager rather
        # than inspecting QGraphicsScene directly.
        # ----------------------------------------------------

        existing_bus = self._resolve_bus(
            position
        )

        if existing_bus is not None:
            return

        # ----------------------------------------------------
        # Persistent model mutation.
        #
        # BusTool does not call model.add_bus() directly.
        # Controller owns the application mutation boundary.
        # ----------------------------------------------------

        self._create_bus(
            position
        )

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def mouse_move(
        self,
        event: Any,
    ) -> None:
        """
        Track the current resolved cursor position.

        BusTool does not create permanent graphics during hover.

        Preview behavior, if introduced later, belongs to the
        InteractionManager/PreviewLayer infrastructure.
        """

        position = self._resolve_position(
            event
        )

        if position is None:
            return

        self.last_position = QPointF(
            position.x(),
            position.y(),
        )

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def mouse_release(
        self,
        event: Any,
    ) -> None:
        """
        Handle mouse release.

        Bus creation occurs on mouse press, so release requires
        no persistent action.
        """

        return

    # ========================================================
    # KEY PRESS
    # ========================================================

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Handle optional keyboard interaction.

        Escape resets transient state.

        Returns
        -------
        bool
            True when the event was consumed.
        """

        key = event.key()

        if self._is_escape_key(
            key
        ):
            self.reset()
            return True

        return False

    # ========================================================
    # POSITION RESOLUTION
    # ========================================================

    def _resolve_position(
        self,
        event: Any,
    ) -> Optional[QPointF]:
        """
        Resolve an event position through InteractionManager
        and SnapSystem.

        InteractionManager owns coordinate conversion.

        SnapSystem owns the application's snapping rules.
        """

        position = self.im.map_to_scene(
            event
        )

        if position is None:
            return None

        # ----------------------------------------------------
        # Preferred centralized SnapSystem contract.
        # ----------------------------------------------------

        resolve = getattr(
            self.snap_system,
            "resolve",
            None,
        )

        if callable(resolve):

            result = resolve(
                position
            )

            resolved_position = getattr(
                result,
                "position",
                None,
            )

            if resolved_position is not None:
                return resolved_position

        # ----------------------------------------------------
        # Fallback for a SnapSystem exposing only grid
        # resolution.
        #
        # This keeps the tool dependent on the centralized
        # snapping service rather than implementing snapping
        # itself.
        # ----------------------------------------------------

        snap = getattr(
            self.snap_system,
            "snap",
            None,
        )

        if callable(snap):

            resolved = snap(
                position
            )

            if resolved is not None:
                return resolved

        # ----------------------------------------------------
        # If SnapSystem has no position resolver, retain the
        # authoritative scene position.
        # ----------------------------------------------------

        return QPointF(
            position.x(),
            position.y(),
        )

    # ========================================================
    # BUS RESOLUTION
    # ========================================================

    def _resolve_bus(
        self,
        position: QPointF,
    ) -> Optional[Any]:
        """
        Resolve an existing Bus at the supplied position.

        The query is delegated to SnapSystem.

        No QGraphicsScene inspection is performed here.
        """

        resolve_bus = getattr(
            self.snap_system,
            "resolve_bus",
            None,
        )

        if callable(resolve_bus):
            return resolve_bus(
                position
            )

        # ----------------------------------------------------
        # If the current SnapSystem does not expose bus
        # resolution, ask InteractionManager.
        # ----------------------------------------------------

        get_bus_at = getattr(
            self.im,
            "get_bus_at",
            None,
        )

        if callable(get_bus_at):
            return get_bus_at(
                position
            )

        return None

    # ========================================================
    # MODEL CREATION
    # ========================================================

    def _create_bus(
        self,
        position: QPointF,
    ) -> Any:
        """
        Request creation of a Bus through Controller.

        Preferred Controller contract:

            create_bus(x, y)

        A model-level fallback is intentionally not provided.

        This prevents the tool from bypassing the application's
        authoritative mutation/command boundary.
        """

        create_bus = getattr(
            self.controller,
            "create_bus",
            None,
        )

        if not callable(create_bus):
            raise AttributeError(
                "Controller must provide "
                "create_bus(x, y) for BusTool."
            )

        return create_bus(
            position.x(),
            position.y(),
        )

    # ========================================================
    # KEY HELPERS
    # ========================================================

    @staticmethod
    def _is_escape_key(
        key: Any,
    ) -> bool:
        """
        Detect the Qt Escape key without importing a Qt binding
        directly into the tool.
        """

        key_type = type(
            key
        )

        escape = getattr(
            key_type,
            "Key_Escape",
            None,
        )

        if escape is None:
            return False

        return key == escape

    # ========================================================
    # STATE / DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return read-only diagnostic state.
        """

        return {
            "tool_id": self.tool_id,
            "has_last_position": (
                self.last_position is not None
            ),
            "last_position": self.last_position,
        }

    # --------------------------------------------------------

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "BusTool("
            f"last_position={self.last_position!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "BusTool",
]
```
