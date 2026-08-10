"""
UI package

Purpose:
--------
Top-level UI module that exposes major subsystems.

This package contains:
- core      → application logic, registries, controller
- canvas    → rendering + interaction layer
- tools     → user interaction tools
- renderers → model → view adapters

Design Rule:
------------
Keep this file lightweight.
Do NOT trigger registrations here.
"""

# Optional: expose commonly used high-level classes
from .canvas import GraphicsView, RenderSystem
from .core import Controller
