# ============================================================
# File: ui/tools/endpoint_identity_adapter.py
# GridForge V2 — SLD Endpoint Identity Adapter
# Author: Subhendu Mishra
# ============================================================
"""
Translate presentation snap identity into Application endpoint intent.

Architecture
------------

    SnapResult
        |
        v
    EndpointIdentityAdapter
        |
        v
    EndpointReference
        |
        v
    Application Command

This module is a presentation/application boundary helper.
It never resolves Core objects, mutates Core, or performs topology.

BusItem and LineItem remain unchanged. The adapter uses existing
presentation identity and type information only.
"""

from __future__ import annotations

from typing import Any

from core.application.endpoint_reference import EndpointReference


class EndpointIdentityAdapter:
    """Convert a snapped presentation endpoint into an immutable reference."""

    @staticmethod
    def from_snap_result(result: Any) -> EndpointReference:
        """Return an EndpointReference for a supported object snap."""
        if result is None:
            raise ValueError("Snap result must not be None.")

        object_id = getattr(result, "object_id", None)
        source = getattr(result, "source", None)
        snap_type = getattr(result, "snap_type", None)

        if object_id is None:
            raise ValueError(
                "Line connection requires an object snap with a stable object_id."
            )

        if snap_type is not None and getattr(snap_type, "name", None) != "OBJECT":
            raise ValueError(
                "Line connection requires an object endpoint snap."
            )

        # Existing BusItem is a presentation projection of a Bus.
        # Do not inspect or mutate its model; only use its stable identity.
        if source is not None and source.__class__.__name__ == "BusItem":
            return EndpointReference.bus(str(object_id))

        # Future endpoint-aware presentation items may expose an immutable
        # EndpointReference directly. This keeps the adapter extensible without
        # making the UI responsible for Core topology resolution.
        endpoint_reference = getattr(source, "endpoint_reference", None)
        if isinstance(endpoint_reference, EndpointReference):
            return endpoint_reference

        raise ValueError(
            "The snapped presentation object does not expose a supported "
            "electrical endpoint identity."
        )


__all__ = ["EndpointIdentityAdapter"]
