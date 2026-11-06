# ============================================================
# File: ui/connections/connection_preview.py
# GridForge V2 — Common transient connection preview state
# ============================================================
"""Transient, non-persistent logical state for SLD connection tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

Point = tuple[float, float]


@dataclass
class ConnectionPreview:
    """Common logical preview state shared by Wire/Line/Cable tools.

    Endpoint values are presentation/application intent only. They are normally
    immutable EndpointReference instances produced by EndpointIdentityAdapter.
    This class never resolves Core objects and never owns renderer objects.
    """

    active: bool = False
    source_endpoint: Any | None = None
    target_endpoint: Any | None = None
    cursor_position: Point | None = None
    valid: bool = False
    validation_reason: str = ""

    def begin(self, source_endpoint: Any) -> None:
        if source_endpoint is None:
            raise ValueError("source_endpoint must not be None.")
        self.active = True
        self.source_endpoint = source_endpoint
        self.target_endpoint = None
        self.cursor_position = None
        self.valid = False
        self.validation_reason = ""

    def update_target(
        self,
        target_endpoint: Any | None,
        *,
        valid: bool,
        reason: str = "",
    ) -> None:
        self._ensure_active()
        if not isinstance(valid, bool):
            raise TypeError("valid must be a bool.")
        if not isinstance(reason, str):
            raise TypeError("reason must be a string.")
        if valid and target_endpoint is None:
            raise ValueError("A valid preview requires target_endpoint.")
        self.target_endpoint = target_endpoint
        self.valid = valid
        self.validation_reason = reason.strip()

    def update_cursor(self, position: Point) -> None:
        self._ensure_active()
        self.cursor_position = self._validate_point(position)

    def cancel(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.active = False
        self.source_endpoint = None
        self.target_endpoint = None
        self.cursor_position = None
        self.valid = False
        self.validation_reason = ""

    @property
    def can_commit(self) -> bool:
        return (
            self.active
            and self.valid
            and self.source_endpoint is not None
            and self.target_endpoint is not None
        )

    def get_endpoint_pair(self) -> tuple[Any, Any] | None:
        if self.source_endpoint is None or self.target_endpoint is None:
            return None
        return self.source_endpoint, self.target_endpoint

    def get_state(self) -> dict[str, object]:
        return {
            "active": self.active,
            "source_endpoint": self.source_endpoint,
            "target_endpoint": self.target_endpoint,
            "cursor_position": self.cursor_position,
            "valid": self.valid,
            "validation_reason": self.validation_reason,
            "can_commit": self.can_commit,
        }

    @staticmethod
    def _validate_point(position: Point) -> Point:
        if isinstance(position, (str, bytes)) or not hasattr(position, "__len__"):
            raise TypeError("position must contain two coordinates.")
        if len(position) != 2:
            raise ValueError("position must contain exactly two coordinates.")
        x, y = position
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError("position.x must be numeric.")
        if isinstance(y, bool) or not isinstance(y, (int, float)):
            raise TypeError("position.y must be numeric.")
        return float(x), float(y)

    def _ensure_active(self) -> None:
        if not self.active:
            raise RuntimeError("Connection preview is not active.")

    def __repr__(self) -> str:
        return (
            "ConnectionPreview("
            f"active={self.active}, "
            f"source={self.source_endpoint!r}, "
            f"target={self.target_endpoint!r}, "
            f"valid={self.valid}, "
            f"can_commit={self.can_commit})"
        )


__all__ = ["ConnectionPreview", "Point"]
