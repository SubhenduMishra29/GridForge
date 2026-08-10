# ============================================================

# File: ui/canvas/interaction_manager.py

# GridForge Canvas Interaction Manager

# ============================================================

"""
Central input-routing layer for the GridForge canvas.

## Architecture

QGraphicsView
│
│ raw Qt events
▼
InteractionManager
│
├── PreviewLayer
├── SnapSystem
│
▼
ToolManager
│
▼
Active Tool

## Responsibilities

InteractionManager:

* receives canvas mouse events
* converts viewport coordinates to scene coordinates
* forwards events to the active tool
* owns transient interaction state
* owns PreviewLayer
* exposes SnapSystem
* delegates tool lifecycle to ToolManager
* handles generic keyboard routing
* handles ESC cancellation

InteractionManager does NOT:

* implement tool logic
* create individual tools
* destroy individual tools
* modify the electrical model directly
* render permanent model graphics
* import individual tools
* calculate electrical quantities

## Tool ownership

ToolManager is the single owner of tool lifecycle.

InteractionManager only obtains the currently active tool
from ToolManager.

## Qt rule

All Qt classes must be imported through:

```
ui.core.qt
```

No direct PySide6 / PyQt6 / PyQt5 imports are permitted.
"""

from **future** import annotations

from typing import Any, Optional

from ui.core.qt import QObject, Qt

from ui.canvas.preview_layer import PreviewLayer
from ui.core.snap_system import SnapSystem
from ui.core.tool_manager import ToolManager

class InteractionManager(QObject):
"""
Central input-routing system for the GridForge canvas.

```
InteractionManager is deliberately thin.

It receives raw canvas events and delegates them to the
active tool managed by ToolManager.
"""

# ========================================================
# INITIALIZATION
# ========================================================

def __init__(
    self,
    view: Any,
    controller: Any,
) -> None:
    """
    Initialize the InteractionManager.

    Parameters
    ----------
    view:
        GridForge GraphicsView instance.

    controller:
        GridForge Controller.
    """

    super().__init__()

    # ----------------------------------------------------
    # Core references
    # ----------------------------------------------------

    self.view = view
    self.controller = controller

    # ----------------------------------------------------
    # Active tool reference
    # ----------------------------------------------------
    #
    # This is ONLY a cached reference.
    #
    # ToolManager remains the owner of the actual tool
    # lifecycle.
    # ----------------------------------------------------

    self.current_tool: Optional[Any] = None

    # ----------------------------------------------------
    # Generic transient interaction state
    # ----------------------------------------------------

    self.dragging: bool = False

    self.last_scene_pos = None

    # ----------------------------------------------------
    # Preview layer
    # ----------------------------------------------------
    #
    # Preview graphics are transient and therefore belong
    # to the interaction layer rather than the model.
    # ----------------------------------------------------

    self.preview = PreviewLayer(
        self.view.scene()
    )

    # ----------------------------------------------------
    # Central snapping service
    # ----------------------------------------------------
    #
    # Tools access this through:
    #
    #     self.im.snap_system
    #
    # They must not implement independent snap algorithms.
    # ----------------------------------------------------

    self.snap_system = SnapSystem(
        controller=controller
    )

    # ----------------------------------------------------
    # Tool manager
    # ----------------------------------------------------
    #
    # ToolManager owns tool creation and lifecycle.
    # ----------------------------------------------------

    self.tool_manager = ToolManager(
        controller=controller,
        interaction_manager=self,
        preview=self.preview,
    )

    # ----------------------------------------------------
    # Subscribe to controller tool changes.
    #
    # Controller owns the requested tool ID.
    # ToolManager owns the actual tool instance.
    # ----------------------------------------------------

    self.controller.subscribe(
        "tool_changed",
        self._on_tool_changed,
    )

    # ----------------------------------------------------
    # Synchronize with an already-selected tool.
    #
    # IMPORTANT:
    #
    # Controller exposes current_tool_id through:
    #
    #     get_current_tool_id()
    #
    # It does NOT expose "current_tool".
    # ----------------------------------------------------

    initial_tool_id = (
        self.controller.get_current_tool_id()
    )

    if initial_tool_id is not None:
        self._on_tool_changed(
            initial_tool_id
        )

# ========================================================
# TOOL MANAGEMENT
# ========================================================

def _on_tool_changed(
    self,
    tool_id: str,
) -> None:
    """
    React to a Controller tool-change event.

    ToolManager performs the actual lifecycle operation.

    InteractionManager only:

    1. clears old transient state
    2. asks ToolManager to activate the tool
    3. stores the returned reference
    """

    # ----------------------------------------------------
    # Clear interaction state belonging to the previous
    # tool before activating the new one.
    # ----------------------------------------------------

    self._clear_interaction_state()

    # ----------------------------------------------------
    # ToolManager owns activation.
    # ----------------------------------------------------

    self.current_tool = (
        self.tool_manager.activate(
            tool_id
        )
    )

# ========================================================
# ACTIVE TOOL ACCESS
# ========================================================

def get_current_tool(self) -> Optional[Any]:
    """
    Return the currently active tool.

    ToolManager remains the authoritative owner.
    """

    return (
        self.tool_manager
        .get_current_tool()
    )

# --------------------------------------------------------

def get_current_tool_id(self) -> Optional[str]:
    """
    Return the ID of the currently active tool.
    """

    return (
        self.tool_manager
        .get_current_tool_id()
    )

# ========================================================
# INTERACTION STATE
# ========================================================

def _clear_interaction_state(
    self,
) -> None:
    """
    Clear transient interaction state.

    Called when switching tools.
    """

    self.dragging = False
    self.last_scene_pos = None

    self.clear_preview()

# ========================================================
# MOUSE PRESS
# ========================================================

def mouse_press(
    self,
    event: Any,
) -> None:
    """
    Route a mouse-press event to the active tool.
    """

    # ----------------------------------------------------
    # Convert event position once at the routing layer.
    # ----------------------------------------------------

    self.last_scene_pos = (
        self.map_to_scene(event)
    )

    self.dragging = True

    # ----------------------------------------------------
    # Get active tool from ToolManager.
    # ----------------------------------------------------

    tool = (
        self.tool_manager
        .get_current_tool()
    )

    if tool is None:
        return

    # ----------------------------------------------------
    # Delegate to tool.
    # ----------------------------------------------------

    handler = getattr(
        tool,
        "mouse_press",
        None,
    )

    if callable(handler):
        handler(event)

# ========================================================
# MOUSE MOVE
# ========================================================

def mouse_move(
    self,
    event: Any,
) -> None:
    """
    Route a mouse-move event to the active tool.
    """

    self.last_scene_pos = (
        self.map_to_scene(event)
    )

    tool = (
        self.tool_manager
        .get_current_tool()
    )

    if tool is None:
        return

    handler = getattr(
        tool,
        "mouse_move",
        None,
    )

    if callable(handler):
        handler(event)

# ========================================================
# MOUSE RELEASE
# ========================================================

def mouse_release(
    self,
    event: Any,
) -> None:
    """
    Route a mouse-release event to the active tool.
    """

    self.last_scene_pos = (
        self.map_to_scene(event)
    )

    tool = (
        self.tool_manager
        .get_current_tool()
    )

    if tool is None:
        self.dragging = False
        return

    handler = getattr(
        tool,
        "mouse_release",
        None,
    )

    if callable(handler):
        handler(event)

    # ----------------------------------------------------
    # Generic drag state ends after release.
    # ----------------------------------------------------

    self.dragging = False

# ========================================================
# KEY PRESS
# ========================================================

def key_press(
    self,
    event: Any,
) -> bool:
    """
    Route keyboard events.

    ESC is handled centrally as a tool cancellation.

    Other keys are optionally forwarded to the active
    tool.
    """

    # ----------------------------------------------------
    # ESC → cancel current tool operation
    # ----------------------------------------------------

    if event.key() == Qt.Key_Escape:
        return self.cancel_tool()

    # ----------------------------------------------------
    # Forward other keys to active tool.
    # ----------------------------------------------------

    tool = (
        self.tool_manager
        .get_current_tool()
    )

    if tool is None:
        return False

    handler = getattr(
        tool,
        "key_press",
        None,
    )

    if not callable(handler):
        return False

    result = handler(event)

    # None means the tool accepted the event without
    # explicitly returning a boolean.
    if result is None:
        return True

    return bool(result)

# ========================================================
# KEY RELEASE
# ========================================================

def key_release(
    self,
    event: Any,
) -> bool:
    """
    Route keyboard-release events to the active tool.
    """

    tool = (
        self.tool_manager
        .get_current_tool()
    )

    if tool is None:
        return False

    handler = getattr(
        tool,
        "key_release",
        None,
    )

    if not callable(handler):
        return False

    result = handler(event)

    if result is None:
        return True

    return bool(result)

# ========================================================
# CANCEL TOOL
# ========================================================

def cancel_tool(self) -> bool:
    """
    Cancel the current tool operation.

    ToolManager performs the actual cancellation.
    """

    result = (
        self.tool_manager.cancel()
    )

    # ----------------------------------------------------
    # Generic interaction state is always reset.
    # ----------------------------------------------------

    self.dragging = False
    self.last_scene_pos = None

    self.clear_preview()

    return bool(result)

# ========================================================
# COORDINATE CONVERSION
# ========================================================

def map_to_scene(
    self,
    event: Any,
):
    """
    Convert viewport coordinates to scene coordinates.

    Tools should use this method rather than accessing
    QGraphicsView directly.
    """

    return self.view.mapToScene(
        event.pos()
    )

# ========================================================
# CURRENT SCENE POSITION
# ========================================================

def get_scene_position(self):
    """
    Return the most recently known scene position.
    """

    return self.last_scene_pos

# ========================================================
# PREVIEW CONTROL
# ========================================================

def clear_preview(
    self,
) -> None:
    """
    Clear all temporary preview graphics.
    """

    if self.preview is not None:
        self.preview.clear()

# ========================================================
# DEACTIVATE TOOL
# ========================================================

def deactivate_tool(
    self,
) -> None:
    """
    Deactivate the current tool through ToolManager.

    InteractionManager does not directly call the tool's
    lifecycle methods.
    """

    self.tool_manager.deactivate()

    self.current_tool = (
        self.tool_manager
        .get_current_tool()
    )

    self._clear_interaction_state()

# ========================================================
# RESET
# ========================================================

def reset(
    self,
) -> None:
    """
    Completely reset interaction state.

    Intended for:

    - loading a new model
    - resetting a canvas
    - closing a workspace
    - recovering from invalid interaction
    """

    self.tool_manager.reset()

    self.current_tool = (
        self.tool_manager
        .get_current_tool()
    )

    self.dragging = False
    self.last_scene_pos = None

    self.clear_preview()

# ========================================================
# DEBUG STATE
# ========================================================

def get_state(
    self,
) -> dict:
    """
    Return diagnostic interaction state.
    """

    active_tool = (
        self.tool_manager
        .get_current_tool()
    )

    return {
        "active_tool": (
            self.tool_manager
            .get_current_tool_id()
        ),
        "has_active_tool": (
            active_tool is not None
        ),
        "dragging": self.dragging,
        "last_scene_pos": (
            self.last_scene_pos
        ),
        "preview_active": (
            self.preview is not None
        ),
        "snap_system": (
            self.snap_system is not None
        ),
    }

# ========================================================
# DEBUG REPRESENTATION
# ========================================================

def __repr__(
    self,
) -> str:
    """
    Return a concise diagnostic representation.
    """

    tool = (
        self.tool_manager
        .get_current_tool()
    )

    tool_name = (
        type(tool).__name__
        if tool is not None
        else "None"
    )

    return (
        "InteractionManager("
        f"tool={tool_name}, "
        f"dragging={self.dragging}"
        ")"
    )
```

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"InteractionManager",
]
