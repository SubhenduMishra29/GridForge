# ============================================================
# File: ui/sld/simple_wire_inspector.py
# GridForge V2 — Simple Wire Inspector Projection
# ============================================================

"""Presentation-only inspection projection for committed Simple Wires."""

from __future__ import annotations

from typing import Any, Mapping


class SimpleWireInspector:
    """Format a Simple Wire read/projection snapshot without engineering parameters."""

    @staticmethod
    def from_read_model(read_model: Any) -> Mapping[str, Any]:
        if read_model is None:
            raise ValueError("read_model is required")
        if getattr(read_model, "kind", None) != "SIMPLE_WIRE":
            raise ValueError("SimpleWireInspector accepts only SIMPLE_WIRE read models.")
        endpoint_a = dict(read_model.endpoint_a)
        endpoint_b = dict(read_model.endpoint_b)
        return {
            "type": "Simple Wired Connection",
            "id": str(read_model.connection_id),
            "endpoint_a": {
                "equipment_id": endpoint_a.get("object_id"),
                "equipment_type": endpoint_a.get("equipment_type"),
                "terminal_role": endpoint_a.get("terminal_role"),
            },
            "endpoint_b": {
                "equipment_id": endpoint_b.get("object_id"),
                "equipment_type": endpoint_b.get("equipment_type"),
                "terminal_role": endpoint_b.get("terminal_role"),
            },
            "electrical_parameters": {},
        }


__all__ = ["SimpleWireInspector"]
