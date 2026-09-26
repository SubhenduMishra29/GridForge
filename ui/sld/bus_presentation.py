# ============================================================
# GridForge V2 — Canonical SLD Bus presentation definition
# ============================================================
"""Renderer-neutral Bus-bar presentation geometry shared by preview and commit."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SLDBusPresentationDefinition:
    """Canonical renderer-neutral geometry and attachment policy for an SLD Bus."""

    half_length: float = 80.0
    attachment_count: int = 9
    orientation_deg: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.half_length, bool) or not isinstance(self.half_length, (int, float)) or self.half_length <= 0:
            raise ValueError("half_length must be positive")
        if isinstance(self.attachment_count, bool) or not isinstance(self.attachment_count, int) or self.attachment_count < 2:
            raise ValueError("attachment_count must be at least two")
        if isinstance(self.orientation_deg, bool) or not isinstance(self.orientation_deg, (int, float)):
            raise TypeError("orientation_deg must be numeric")

    def _rotate(self, point: tuple[float, float]) -> tuple[float, float]:
        angle = math.radians(float(self.orientation_deg))
        cosine, sine = math.cos(angle), math.sin(angle)
        x, y = point
        return (x * cosine - y * sine, x * sine + y * cosine)

    @property
    def start(self) -> tuple[float, float]:
        return self._rotate((-self.half_length, 0.0))

    @property
    def end(self) -> tuple[float, float]:
        return self._rotate((self.half_length, 0.0))

    def attachment_fraction(self, attachment_id: str) -> float:
        if not isinstance(attachment_id, str) or not attachment_id:
            raise ValueError("attachment_id must be a non-empty string")
        try:
            index = int(attachment_id.rsplit("-", 1)[1])
        except (ValueError, IndexError) as exc:
            raise ValueError("attachment_id must use the canonical 'attachment-N' form") from exc
        if index < 0 or index >= self.attachment_count:
            raise ValueError(f"attachment index {index} is outside the canonical range")
        return index / float(self.attachment_count - 1)

    def attachment_position(self, attachment_id: str) -> tuple[float, float]:
        fraction = self.attachment_fraction(attachment_id)
        start = self.start
        end = self.end
        return (
            start[0] + (end[0] - start[0]) * fraction,
            start[1] + (end[1] - start[1]) * fraction,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": list(self.start),
            "end": list(self.end),
            "orientation": float(self.orientation_deg),
            "attachment_count": int(self.attachment_count),
            "half_length": float(self.half_length),
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> "SLDBusPresentationDefinition":
        if not data:
            return cls()
        orientation = data.get("orientation", data.get("orientation_deg", 0.0))
        half_length = data.get("half_length")
        if half_length is None:
            start = data.get("start")
            end = data.get("end")
            if isinstance(start, (tuple, list)) and isinstance(end, (tuple, list)) and len(start) == 2 and len(end) == 2:
                half_length = math.hypot(float(end[0]) - float(start[0]), float(end[1]) - float(start[1])) / 2.0
            else:
                half_length = DEFAULT_SLD_BUS_PRESENTATION.half_length
        return cls(
            half_length=float(half_length),
            attachment_count=int(data.get("attachment_count", DEFAULT_SLD_BUS_PRESENTATION.attachment_count)),
            orientation_deg=float(orientation),
        )


DEFAULT_SLD_BUS_PRESENTATION = SLDBusPresentationDefinition()


__all__ = ["SLDBusPresentationDefinition", "DEFAULT_SLD_BUS_PRESENTATION"]
