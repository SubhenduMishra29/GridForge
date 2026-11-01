"""Physical conductor inventory and coupled branch-impedance contracts.

These Core value objects describe physical conductors independently of SLD
symbols, protection devices, and solver implementation. A conductor inventory
is explicit: no phase, neutral, protective-earth, or screen conductor is
synthesized from a conductor count or from aggregate phase-current values.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ConductorRole(str, Enum):
    """Physical role of one conductor in a branch conductor system."""

    PHASE_A = "A"
    PHASE_B = "B"
    PHASE_C = "C"
    NEUTRAL = "N"
    PROTECTIVE_EARTH = "PE"
    SCREEN = "SHIELD"
    PILOT = "PILOT"
    OTHER = "OTHER"


class ConductorMaterial(str, Enum):
    """Declared conductor material; no material is inferred from resistance."""

    COPPER = "COPPER"
    ALUMINIUM = "ALUMINIUM"
    ALUMINIUM_ALLOY = "ALUMINIUM_ALLOY"
    STEEL = "STEEL"
    OTHER = "OTHER"


def _finite_positive(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a finite positive number.")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite positive number.") from exc
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be a finite positive number.")
    return result


def _finite_complex(value: Any, name: str) -> complex:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a finite complex value.")
    try:
        result = complex(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite complex value.") from exc
    if not math.isfinite(result.real) or not math.isfinite(result.imag):
        raise ValueError(f"{name} must be a finite complex value.")
    return result


def _validate_positive_definite_resistance(matrix: tuple[tuple[complex, ...], ...]) -> None:
    """Require a positive-definite real resistance matrix without NumPy."""
    size = len(matrix)
    diagonal_scale = max((abs(matrix[i][i].real) for i in range(size)), default=1.0)
    tolerance = max(1.0, diagonal_scale) * 1.0e-12
    lower = [[0.0 for _ in range(size)] for _ in range(size)]
    for row in range(size):
        for column in range(row + 1):
            value = matrix[row][column].real - sum(
                lower[row][k] * lower[column][k] for k in range(column)
            )
            if row == column:
                if value <= tolerance:
                    raise ValueError("Series resistance matrix must be positive definite.")
                lower[row][column] = math.sqrt(value)
            else:
                lower[row][column] = value / lower[column][column]


@dataclass(frozen=True, slots=True)
class PhysicalConductor:
    """Stable identity and declared construction of one physical conductor.

    conductor_id is unique within its owning BranchConductorSystem. The
    canonical identity in a project is therefore (equipment_id, conductor_id).
    Protective earth, cable screen, and neutral are distinct roles.
    """

    conductor_id: str
    role: ConductorRole | str
    designation: str = ""
    material: ConductorMaterial | str | None = None
    cross_section_mm2: float | None = None
    rated_current_a: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.conductor_id, str) or not self.conductor_id.strip():
            raise ValueError("Physical conductor requires a non-empty conductor_id.")
        object.__setattr__(self, "conductor_id", self.conductor_id.strip())
        try:
            role = self.role if isinstance(self.role, ConductorRole) else ConductorRole(str(self.role).strip().upper())
        except (TypeError, ValueError) as exc:
            raise ValueError("Unsupported physical conductor role.") from exc
        object.__setattr__(self, "role", role)
        if not isinstance(self.designation, str):
            raise TypeError("Conductor designation must be a string.")
        object.__setattr__(self, "designation", self.designation.strip())
        if self.material is not None:
            try:
                material = self.material if isinstance(self.material, ConductorMaterial) else ConductorMaterial(str(self.material).strip().upper())
            except (TypeError, ValueError) as exc:
                raise ValueError("Unsupported conductor material.") from exc
            object.__setattr__(self, "material", material)
        for name in ("cross_section_mm2", "rated_current_a"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _finite_positive(value, name))

    @property
    def phase_or_sequence(self) -> str:
        """Return the explicit phase/neutral role used by protection contracts."""
        return self.role.value

    def summary(self) -> dict[str, Any]:
        return {
            "conductor_id": self.conductor_id,
            "role": self.role.value,
            "designation": self.designation,
            "material": self.material.value if self.material is not None else None,
            "cross_section_mm2": self.cross_section_mm2,
            "rated_current_a": self.rated_current_a,
        }


@dataclass(frozen=True, slots=True)
class BranchConductorSystem:
    """Explicit multi-conductor model spanning one Branch FROM/TO terminal pair.

    The series impedance matrix is expressed in ohms per kilometre and is
    ordered by matrix_conductor_ids. Diagonal entries are conductor self
    impedances; off-diagonal entries are mutual impedances. The matrix must be
    reciprocal (symmetric), and its identity ordering must exactly match the
    physical conductor inventory. Zero mutual terms are accepted only when
    explicitly supplied by the engineer/source data.

    This contract is a Core model input. It does not itself calculate currents
    or establish neutral/earth return connectivity. Missing shunt data remains
    unavailable rather than being silently interpreted as a physical zero.
    """

    conductors: tuple[PhysicalConductor, ...]
    length_km: float
    matrix_conductor_ids: tuple[str, ...]
    series_impedance_matrix_ohm_per_km: tuple[tuple[complex, ...], ...]
    shunt_admittance_matrix_siemens_per_km: tuple[tuple[complex, ...], ...] | None = None
    source_reference: str | None = None

    def __post_init__(self) -> None:
        conductors = tuple(self.conductors)
        if not conductors or any(not isinstance(item, PhysicalConductor) for item in conductors):
            raise TypeError("Branch conductor system requires one or more PhysicalConductor records.")
        ids = tuple(item.conductor_id for item in conductors)
        if len(ids) != len(set(ids)):
            raise ValueError("Physical conductor identities must be unique within a branch.")
        matrix_ids = tuple(self.matrix_conductor_ids)
        if any(not isinstance(item, str) or not item.strip() for item in matrix_ids):
            raise ValueError("Every impedance matrix conductor identity must be a non-empty string.")
        matrix_ids = tuple(item.strip() for item in matrix_ids)
        if len(matrix_ids) != len(set(matrix_ids)) or set(matrix_ids) != set(ids) or len(matrix_ids) != len(ids):
            raise ValueError("Impedance matrix conductor ordering must identify every physical conductor exactly once.")
        length = _finite_positive(self.length_km, "length_km")
        size = len(matrix_ids)

        def normalize_matrix(matrix: Any, name: str) -> tuple[tuple[complex, ...], ...]:
            rows = tuple(tuple(row) for row in matrix)
            if len(rows) != size or any(len(row) != size for row in rows):
                raise ValueError(f"{name} must be a square matrix matching matrix_conductor_ids.")
            normalized = tuple(
                tuple(_finite_complex(value, f"{name}[{i}][{j}]") for j, value in enumerate(row))
                for i, row in enumerate(rows)
            )
            for i in range(size):
                for j in range(i + 1, size):
                    if not math.isclose(normalized[i][j].real, normalized[j][i].real, rel_tol=1e-9, abs_tol=1e-12) or not math.isclose(normalized[i][j].imag, normalized[j][i].imag, rel_tol=1e-9, abs_tol=1e-12):
                        raise ValueError(f"{name} must be symmetric for reciprocal conductor coupling.")
            return normalized

        series = normalize_matrix(self.series_impedance_matrix_ohm_per_km, "series_impedance_matrix_ohm_per_km")
        _validate_positive_definite_resistance(series)
        shunt = None
        if self.shunt_admittance_matrix_siemens_per_km is not None:
            shunt = normalize_matrix(self.shunt_admittance_matrix_siemens_per_km, "shunt_admittance_matrix_siemens_per_km")
        if self.source_reference is not None:
            if not isinstance(self.source_reference, str) or not self.source_reference.strip():
                raise ValueError("source_reference must be non-empty when supplied.")
            object.__setattr__(self, "source_reference", self.source_reference.strip())
        object.__setattr__(self, "conductors", conductors)
        object.__setattr__(self, "length_km", length)
        object.__setattr__(self, "matrix_conductor_ids", matrix_ids)
        object.__setattr__(self, "series_impedance_matrix_ohm_per_km", series)
        object.__setattr__(self, "shunt_admittance_matrix_siemens_per_km", shunt)

    def conductor(self, conductor_id: str) -> PhysicalConductor:
        for item in self.conductors:
            if item.conductor_id == conductor_id:
                return item
        raise KeyError(f"Unknown physical conductor {conductor_id!r}.")

    def series_impedance_ohm(self, row_conductor_id: str, column_conductor_id: str) -> complex:
        """Return the declared total mutual/self impedance in ohms."""
        try:
            row = self.matrix_conductor_ids.index(row_conductor_id)
            column = self.matrix_conductor_ids.index(column_conductor_id)
        except ValueError as exc:
            raise KeyError("Conductor is not present in the impedance matrix.") from exc
        return self.series_impedance_matrix_ohm_per_km[row][column] * self.length_km

    def summary(self) -> dict[str, Any]:
        return {
            "conductor_ids": tuple(item.conductor_id for item in self.conductors),
            "conductor_roles": tuple(item.role.value for item in self.conductors),
            "length_km": self.length_km,
            "matrix_conductor_ids": self.matrix_conductor_ids,
            "series_impedance_matrix_ohm_per_km": self.series_impedance_matrix_ohm_per_km,
            "shunt_admittance_available": self.shunt_admittance_matrix_siemens_per_km is not None,
            "source_reference": self.source_reference,
        }


__all__ = [
    "ConductorRole",
    "ConductorMaterial",
    "PhysicalConductor",
    "BranchConductorSystem",
]
