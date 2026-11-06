"""Explicit transformer winding conductor construction metadata.

This is intentionally not a generic terminal-to-terminal conductor path:
transformer windings are magnetically coupled and require a dedicated
multi-winding phase-domain primitive before they can be stamped into a
conductor graph.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True, slots=True)
class TransformerWindingConductorConstruction:
    winding: str
    terminal_role: str
    connection: str
    phase_roles: tuple[str, ...]
    neutral_terminal_role: str | None
    neutral_grounding_impedance_ohm: complex | None
    earth_return_impedance_ohm: complex | None = None

    def __post_init__(self) -> None:
        winding = str(self.winding).strip().upper()
        if winding not in {"HV", "LV"}:
            raise ValueError("Transformer winding must be HV or LV.")
        object.__setattr__(self, "winding", winding)
        if not isinstance(self.terminal_role, str) or not self.terminal_role.strip():
            raise ValueError("Transformer winding requires an explicit SLD terminal role.")
        object.__setattr__(self, "terminal_role", self.terminal_role.strip())
        connection = str(getattr(self.connection, "value", self.connection)).strip().upper()
        if connection not in {"DELTA", "WYE_GROUNDED", "WYE_UNGROUNDED"}:
            raise ValueError("Unsupported transformer winding connection.")
        object.__setattr__(self, "connection", connection)
        roles = tuple(str(getattr(role, "value", role)).strip().upper() for role in self.phase_roles)
        if roles != ("A", "B", "C"):
            raise ValueError("Transformer winding phase_roles must explicitly identify A, B and C in order.")
        object.__setattr__(self, "phase_roles", roles)
        if connection == "WYE_GROUNDED":
            if self.neutral_terminal_role is None:
                raise ValueError("Grounded-wye winding requires an explicit physical neutral terminal mapping.")
            if not str(self.neutral_terminal_role).strip():
                raise ValueError("Neutral terminal role cannot be blank.")
            object.__setattr__(self, "neutral_terminal_role", str(self.neutral_terminal_role).strip())
            if self.neutral_grounding_impedance_ohm is None:
                raise ValueError("Grounded-wye winding requires explicit neutral grounding impedance.")
            if self.earth_return_impedance_ohm is None:
                raise ValueError("Grounded-wye winding requires an explicit earth-return impedance to the study earth reference.")
            z = complex(self.neutral_grounding_impedance_ohm)
            if not math.isfinite(z.real) or not math.isfinite(z.imag) or z.real < 0:
                raise ValueError("Neutral grounding impedance must be finite and passive.")
            if z == 0j:
                raise ValueError("Zero-ohm neutral grounding is not individually resolvable in the physical return-current model.")
            object.__setattr__(self, "neutral_grounding_impedance_ohm", z)
            earth_z = complex(self.earth_return_impedance_ohm)
            if not math.isfinite(earth_z.real) or not math.isfinite(earth_z.imag) or earth_z.real < 0 or earth_z == 0j:
                raise ValueError("Earth-return impedance must be finite, passive and non-zero.")
            object.__setattr__(self, "earth_return_impedance_ohm", earth_z)
        else:
            if self.neutral_terminal_role is not None or self.neutral_grounding_impedance_ohm is not None or self.earth_return_impedance_ohm is not None:
                raise ValueError("Only grounded-wye windings may declare a neutral terminal or grounding impedance.")


@dataclass(frozen=True, slots=True)
class TransformerPhysicalConductorConstruction:
    """Two winding descriptions; deliberately no galvanic HV-LV continuity."""

    hv: TransformerWindingConductorConstruction
    lv: TransformerWindingConductorConstruction
    vector_group: Any | None
    core_construction: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.hv, TransformerWindingConductorConstruction) or self.hv.winding != "HV":
            raise TypeError("hv must be an HV TransformerWindingConductorConstruction.")
        if not isinstance(self.lv, TransformerWindingConductorConstruction) or self.lv.winding != "LV":
            raise TypeError("lv must be an LV TransformerWindingConductorConstruction.")
        if self.hv.terminal_role.casefold() == self.lv.terminal_role.casefold():
            raise ValueError("HV and LV winding mappings must use distinct SLD terminal roles.")
        if self.core_construction is not None:
            value = str(getattr(self.core_construction, "value", self.core_construction)).strip().upper()
            if value not in {"THREE_LIMB", "FIVE_LIMB", "SHELL_FORM"}:
                raise ValueError("Unsupported transformer core construction.")
            object.__setattr__(self, "core_construction", value)


__all__ = [
    "TransformerWindingConductorConstruction",
    "TransformerPhysicalConductorConstruction",
]
