"""
Canvas package

Purpose:
--------
Provides all scene, view, and interaction-related systems.

Design Notes:
-------------
- No business logic here
- No model mutation here
- Acts as UI infrastructure only
"""

from .graphics_view import GraphicsView
from .interaction_manager import InteractionManager
from .render_system import RenderSystem
from .preview_layer import PreviewLayer


__all__ = [
    "GraphicsView",
    "InteractionManager",
    "RenderSystem",
    "PreviewLayer",
]
