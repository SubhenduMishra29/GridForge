"""Standard-dispatched time-current characteristic (TCC) read model.

The model contains engineering data only. Plotting, logarithmic axes,
annotations and coordination policy remain outside Core.
"""
from __future__ import annotations

from dataclasses import dataclass

from .ieee_curves import generate_ieee_tcc_points, normalize_ieee_curve
from .relay_functions import generate_tcc_points, normalize_iec_curve


@dataclass(frozen=True, slots=True)
class ProtectionTCCPoint:
    """One immutable current/time sample for a TCC characteristic."""

    multiple: float
    current: float
    time: float


@dataclass(frozen=True, slots=True)
class ProtectionTCCReadModel:
    """Immutable, standard-labelled TCC data for one protection element."""

    curve_standard: str
    curve: str
    pickup: float
    time_dial: float
    points: tuple[ProtectionTCCPoint, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a detached serialization-friendly representation."""
        return {
            "curve_standard": self.curve_standard,
            "curve": self.curve,
            "pickup": self.pickup,
            "time_dial": self.time_dial,
            "points": [
                {"multiple": point.multiple, "current": point.current, "time": point.time}
                for point in self.points
            ],
        }


def build_protection_tcc_read_model(
    pickup: float,
    *,
    curve_standard: str = "IEC",
    curve: str = "SI",
    time_dial: float = 1.0,
    minimum_multiple: float = 1.01,
    maximum_multiple: float = 20.0,
    points: int = 200,
) -> ProtectionTCCReadModel:
    """Build IEC 60255 or IEEE C37.112 TCC samples from typed settings.

    IEC is the backward-compatible default. The supplied time dial maps
    to IEC TMS or IEEE TD according to the selected standard.
    """
    if not isinstance(curve_standard, str):
        raise TypeError("curve_standard must be a string.")
    standard = curve_standard.strip().upper()
    if standard == "IEC":
        canonical = normalize_iec_curve(curve)
        samples = generate_tcc_points(
            pickup, curve=canonical, TMS=time_dial,
            minimum_multiple=minimum_multiple,
            maximum_multiple=maximum_multiple, points=points,
        )
    elif standard == "IEEE":
        canonical = normalize_ieee_curve(curve)
        samples = generate_ieee_tcc_points(
            pickup, curve=canonical, time_dial=time_dial,
            minimum_multiple=minimum_multiple,
            maximum_multiple=maximum_multiple, points=points,
        )
    else:
        raise ValueError("curve_standard must be IEC or IEEE.")

    immutable_points = tuple(
        ProtectionTCCPoint(
            multiple=float(sample["multiple"]),
            current=float(sample["current"]),
            time=float(sample["time"]),
        )
        for sample in samples
    )
    return ProtectionTCCReadModel(
        curve_standard=standard,
        curve=canonical,
        pickup=float(pickup),
        time_dial=float(time_dial),
        points=immutable_points,
    )


__all__ = [
    "ProtectionTCCPoint",
    "ProtectionTCCReadModel",
    "build_protection_tcc_read_model",
]
