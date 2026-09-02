# ============================================================
# File: ui/sld/sld_scene_renderer.py
# GridForge V2 — SLD Scene Renderer
# Author: Subhendu Mishra
# ============================================================
"""Render the structural SLD document model into a Qt scene.

This is a presentation boundary. It owns graphics-item reconciliation only;
it does not mutate the SLD model, Core electrical state, or viewport state.
"""

from __future__ import annotations

from typing import Dict

from ui.core.qt import QGraphicsScene

from .items import SLDConnectionItem, SLDNodeItem
from .sld_layout import SLDLayout
from .sld_model import SLDModel


class SLDSceneRenderer:
    """Synchronize an :class:`SLDModel` with a graphics scene."""

    def __init__(self, scene: QGraphicsScene, layout: SLDLayout | None = None) -> None:
        if scene is None:
            raise ValueError("scene is required")
        self._scene = scene
        self._layout = layout or SLDLayout()
        self._node_items: Dict[str, SLDNodeItem] = {}
        self._connection_items: Dict[str, SLDConnectionItem] = {}

    @property
    def scene(self) -> QGraphicsScene:
        return self._scene

    @property
    def layout(self) -> SLDLayout:
        return self._layout

    def render(self, model: SLDModel) -> None:
        """Reconcile all model nodes and connections with the scene."""
        if not isinstance(model, SLDModel):
            raise TypeError("model must be an SLDModel")

        node_ids = {node.node_id for node in model.nodes}
        connection_ids = {connection.connection_id for connection in model.connections}

        for node_id in tuple(self._node_items):
            if node_id not in node_ids:
                self._scene.removeItem(self._node_items.pop(node_id))

        for connection_id in tuple(self._connection_items):
            if connection_id not in connection_ids:
                self._scene.removeItem(self._connection_items.pop(connection_id))

        for node in model.nodes:
            item = self._node_items.get(node.node_id)
            if item is None:
                item = SLDNodeItem(node.node_id)
                self._node_items[node.node_id] = item
                self._scene.addItem(item)

            position = self._layout.position(node.node_id)
            if position is None:
                position = node.position
            item.set_visual_position(*position)

        node_positions = {
            node.node_id: (self._layout.position(node.node_id) or node.position)
            for node in model.nodes
        }

        for connection in model.connections:
            source = node_positions.get(connection.source_node_id)
            target = node_positions.get(connection.target_node_id)
            if source is None or target is None:
                continue

            item = self._connection_items.get(connection.connection_id)
            if item is None:
                item = SLDConnectionItem(
                    connection.connection_id,
                    connection.source_node_id,
                    connection.target_node_id,
                )
                self._connection_items[connection.connection_id] = item
                self._scene.addItem(item)

            item.set_visual_endpoints(*source, *target)

    def clear(self) -> None:
        """Remove all renderer-owned graphics items from the scene."""
        for item in self._node_items.values():
            self._scene.removeItem(item)
        for item in self._connection_items.values():
            self._scene.removeItem(item)
        self._node_items.clear()
        self._connection_items.clear()

    def node_item(self, node_id: str) -> SLDNodeItem | None:
        return self._node_items.get(node_id)

    def connection_item(self, connection_id: str) -> SLDConnectionItem | None:
        return self._connection_items.get(connection_id)
