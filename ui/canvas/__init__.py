"""
Canvas package

Purpose:
--------
Provides all scene, view, and interaction-related systems.

This layer is responsible for:
- Rendering surface (QGraphicsView / QGraphicsScene)
- User interaction routing
- Preview visuals

Design Notes:
-------------
- No business logic here
- No model mutation here
- Acts as UI infrastructure only
"""

# ------------------------------------------------------
# Expose key classes for clean imports
# ------------------------------------------------------

from .graphics_view import GraphicsView
from .interaction_manager import InteractionManager
from .render_system import RenderSystem
from .preview_layer import PreviewLayer
