"""Explicit migration boundary for legacy electrical representations.

Migration normalizes representation metadata; it never guesses engineering
units, system bases, or transformer impedance bases. Ambiguous legacy data is
reported for explicit user/source-system migration rather than silently
interpreted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class AmbiguousElectricalDataError(ValueError):
    """Raised when legacy electrical values cannot be interpreted safely."""


@dataclass(frozen=True, slots=True)
class MigrationResult:
    """Detached migration output containing only explicitly resolved values."""

    equipment_type: str
    values: Mapping[str, Any]
    migrated: bool


class LegacyElectricalDataMigration:
    """Validate and migrate legacy electrical payloads without guessing units."""

    def migrate(self, equipment_type: str, payload: Mapping[str, Any]) -> MigrationResult:
        if not isinstance(equipment_type, str) or not equipment_type.strip():
            raise ValueError("equipment_type must be a non-empty string.")
        if not isinstance(payload, Mapping):
            raise TypeError("payload must be a mapping.")

        normalized_type = equipment_type.strip().lower()
        values = dict(payload)

        if normalized_type == "cable":
            self._validate_cable(values)
        elif normalized_type == "transformer":
            self._validate_transformer(values)

        return MigrationResult(
            equipment_type=normalized_type,
            values=values,
            migrated=True,
        )

    @staticmethod
    def _validate_cable(values: Mapping[str, Any]) -> None:
        legacy = {key: values.get(key) for key in ("r", "x", "b") if key in values}
        if not legacy:
            return

        explicit_units = values.get("impedance_units")
        if explicit_units is None:
            raise AmbiguousElectricalDataError(
                "Legacy cable r/x/b values require explicit impedance_units; "
                "migration will not guess ohms versus per-unit."
            )

        units = str(explicit_units).strip().lower()
        if units not in {"ohm", "ohms", "pu", "per_unit"}:
            raise AmbiguousElectricalDataError(
                f"Unsupported legacy cable impedance_units={explicit_units!r}."
            )

    @staticmethod
    def _validate_transformer(values: Mapping[str, Any]) -> None:
        if "impedance_basis" not in values:
            raise AmbiguousElectricalDataError(
                "Legacy transformer impedance requires an explicit impedance_basis; "
                "migration will not infer the basis."
            )
        basis = str(values["impedance_basis"]).strip().lower()
        if basis not in {
            "ohm_hv",
            "ohm_lv",
            "percent_on_rated",
            "pu_on_rated",
            "pu_on_system",
            "pu",
            "engineering",
        }:
            raise AmbiguousElectricalDataError(
                f"Unsupported transformer impedance_basis={values['impedance_basis']!r}."
            )


__all__ = [
    "AmbiguousElectricalDataError",
    "LegacyElectricalDataMigration",
    "MigrationResult",
]
