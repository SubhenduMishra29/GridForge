"""
GridForge V2 — Renderers Package
================================

Purpose
-------
Contains renderer implementations responsible for translating
authoritative Core/domain objects into UI representations.

Examples
--------
- BusRenderer
- LineRenderer

Architecture
------------
Renderer implementations are registered with the renderer registry
through the renderer loading mechanism.

This package initializer intentionally performs no renderer imports
and no registration side effects.

Renderer discovery/loading is owned by the renderer registry/loader,
not by this package initializer.
"""

__all__: list[str] = []
