```python id="5v0q8m"
# plugins/transformer/grounding.py

"""
GridForge Transformer Grounding Plugin
======================================

GridForge Plugin Layer

Defines transformer neutral and grounding configuration for the
GridForge transformer plugin architecture.

Architecture
------------
Transformer grounding is a physical equipment capability.

It describes how a transformer winding neutral is connected to earth
and, where applicable, the impedance associated with that connection.

Typical configurations include:

    - Ungrounded
    - Solidly grounded
    - Resistance grounded
    - Reactance grounded
    - Impedance grounded

The grounding model stores physical/equipment configuration only.

It does NOT:

    - Calculate zero-sequence currents.
    - Build zero-sequence networks.
    - Build Y-bus matrices.
    - Calculate earth-fault currents.
    - Perform short-circuit studies.
    - Perform load-flow calculations.
    - Execute protection logic.
    - Execute grounding controls.
    - Own global network topology.
    - Store GUI state.

Numerical interpretation belongs to the appropriate network, solver,
analysis, and protection layers.

Relationship to Core Model
--------------------------
The authoritative transformer equipment object remains:

    core.model.transformer.Transformer

This module extends that equipment through:

    plugins/transformer/

Dependency direction:

    plugins/transformer
            │
            ▼
    core/model/transformer

The core model must remain independent of this plugin.

Grounding Representation
-------------------------
A grounding configuration contains:

    winding
        Winding/circuit designation to which the grounding connection
        applies.

    method
        Grounding method.

    resistance_ohm
        Grounding resistance in ohms.

    reactance_ohm
        Grounding reactance in ohms.

    neutral_available
        Whether the associated winding has an accessible neutral.

The grounding impedance is represented as physical ohmic data.

Conversion to per-unit and numerical sequence-network representation
belongs to the appropriate network/solver layer.

GridForge V2 Status
-------------------
Initial transformer grounding capability.

The interface is intentionally limited to physical grounding
configuration.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

from .base import TransformerPlugin


# =====================================================================
# TRANSFORMER GROUNDING
# =====================================================================

class Grounding(TransformerPlugin):
    """
    Transformer grounding capability.

    Parameters
    ----------
    transformer :
        Core GridForge Transformer instance.

    winding :
        Winding designation to which the grounding connection applies.

        Examples:

            "HV"
            "LV"
            "tertiary"

    method : str
        Grounding method.

        Supported values:

            "ungrounded"
            "solid"
            "resistance"
            "reactance"
            "impedance"

    resistance_ohm : float, optional
        Grounding resistance in ohms.

        Default: 0.0

    reactance_ohm : float, optional
        Grounding reactance in ohms.

        Default: 0.0

    neutral_available : bool, optional
        Whether the associated winding provides an accessible neutral.

        Default: True

    name : str, optional
        Human-readable plugin name.

    Notes
    -----
    For a solidly grounded neutral:

        resistance_ohm = 0
        reactance_ohm = 0

    For an ungrounded winding:

        neutral_available may still describe whether a physical
        neutral exists, but no intentional grounding impedance is
        applied.

    The class does not calculate zero-sequence impedance.
    """

    plugin_type = "transformer_grounding"

    _VALID_METHODS = {
        "ungrounded",
        "solid",
        "resistance",
        "reactance",
        "impedance",
    }

    def __init__(
        self,
        transformer,
        winding: str,
        method: str = "ungrounded",
        resistance_ohm: float = 0.0,
        reactance_ohm: float = 0.0,
        neutral_available: bool = True,
        name: str = "",
    ):
        super().__init__(
            transformer=transformer,
            name=name,
        )

        self.winding = str(winding).strip()
        self.method = str(method).strip().lower()

        self.resistance_ohm = float(resistance_ohm)
        self.reactance_ohm = float(reactance_ohm)

        self.neutral_available = bool(neutral_available)

        self.validate()

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate(self) -> None:
        """
        Validate grounding configuration.
        """

        if not self.winding:
            raise ValueError(
                "Transformer grounding winding cannot be empty."
            )

        if self.method not in self._VALID_METHODS:
            raise ValueError(
                f"Unsupported transformer grounding method "
                f"'{self.method}'."
            )

        if not isfinite(self.resistance_ohm):
            raise ValueError(
                "Transformer grounding resistance must be finite."
            )

        if not isfinite(self.reactance_ohm):
            raise ValueError(
                "Transformer grounding reactance must be finite."
            )

        if self.resistance_ohm < 0.0:
            raise ValueError(
                "Transformer grounding resistance cannot be negative."
            )

        if self.reactance_ohm < 0.0:
            raise ValueError(
                "Transformer grounding reactance cannot be negative."
            )

        if self.method == "ungrounded":
            if self.resistance_ohm != 0.0:
                raise ValueError(
                    "Ungrounded transformer neutral cannot have a "
                    "grounding resistance."
                )

            if self.reactance_ohm != 0.0:
                raise ValueError(
                    "Ungrounded transformer neutral cannot have a "
                    "grounding reactance."
                )

        if self.method == "solid":
            if self.resistance_ohm != 0.0:
                raise ValueError(
                    "Solidly grounded transformer neutral must have "
                    "zero grounding resistance."
                )

            if self.reactance_ohm != 0.0:
                raise ValueError(
                    "Solidly grounded transformer neutral must have "
                    "zero grounding reactance."
                )

        if self.method == "resistance":
            if self.resistance_ohm <= 0.0:
                raise ValueError(
                    "Resistance-grounded transformer neutral must "
                    "have positive grounding resistance."
                )

            if self.reactance_ohm != 0.0:
                raise ValueError(
                    "Resistance-grounded transformer neutral must "
                    "have zero grounding reactance."
                )

        if self.method == "reactance":
            if self.reactance_ohm <= 0.0:
                raise ValueError(
                    "Reactance-grounded transformer neutral must "
                    "have positive grounding reactance."
                )

            if self.resistance_ohm != 0.0:
                raise ValueError(
                    "Reactance-grounded transformer neutral must "
                    "have zero grounding resistance."
                )

        if self.method == "impedance":
            if (
                self.resistance_ohm == 0.0
                and self.reactance_ohm == 0.0
            ):
                raise ValueError(
                    "Impedance-grounded transformer neutral must "
                    "have a non-zero grounding impedance."
                )

    # =================================================================
    # GROUNDING STATUS
    # =================================================================

    @property
    def is_grounded(self) -> bool:
        """
        Return True when an intentional grounding connection exists.
        """

        return self.method != "ungrounded"

    @property
    def is_solidly_grounded(self) -> bool:
        """
        Return True when the neutral is solidly grounded.
        """

        return self.method == "solid"

    @property
    def is_impedance_grounded(self) -> bool:
        """
        Return True when grounding uses an impedance.
        """

        return self.method in {
            "resistance",
            "reactance",
            "impedance",
        }

    @property
    def grounding_impedance_ohm(self) -> complex:
        """
        Return the physical grounding impedance in ohms.

        Zg = R + jX

        This is a physical parameter representation only.

        The value is not converted to per-unit and is not used to
        calculate fault current inside this plugin.
        """

        return complex(
            self.resistance_ohm,
            self.reactance_ohm,
        )

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured grounding information.
        """

        data = super().summary()

        data.update(
            {
                "winding": self.winding,
                "method": self.method,
                "resistance_ohm": self.resistance_ohm,
                "reactance_ohm": self.reactance_ohm,
                "neutral_available": self.neutral_available,
                "grounding_impedance_ohm": (
                    self.grounding_impedance_ohm
                ),
            }
        )

        return data

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<Grounding "
            f"transformer={self.transformer.id}, "
            f"winding={self.winding}, "
            f"method={self.method}, "
            f"R={self.resistance_ohm:.6f} Ω, "
            f"X={self.reactance_ohm:.6f} Ω>"
        )
```
