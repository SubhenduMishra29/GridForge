```python
# plugins/transformer/tap_changer.py

"""
GridForge Transformer Tap Changer Plugin
========================================

GridForge Plugin Layer

Defines the physical tap-changer capability for GridForge
transformers.

Architecture
------------
A tap changer is a physical transformer capability that modifies
the effective transformer turns ratio.

This module represents the tap-changer equipment and its current
mechanical/electrical position.

It does NOT:

    - Perform automatic voltage regulation.
    - Execute an OLTC control algorithm.
    - Measure remote bus voltage.
    - Calculate control error.
    - Execute control deadbands.
    - Coordinate multiple transformers.
    - Build Y-bus matrices.
    - Perform load-flow calculations.
    - Calculate transformer loading.
    - Perform short-circuit calculations.
    - Perform protection calculations.
    - Own global network topology.
    - Store GUI state.

Control behavior belongs to the appropriate control/dynamics layer.

Relationship to Core Model
--------------------------
The authoritative transformer equipment object remains:

    core.model.transformer.Transformer

The tap changer extends that transformer through:

    plugins/transformer/

Dependency direction:

    plugins/transformer
            │
            ▼
    core/model/transformer

The core model remains independent of this plugin.

Tap Representation
------------------
The tap changer is represented using:

    min_ratio
        Minimum permitted tap ratio.

    max_ratio
        Maximum permitted tap ratio.

    nominal_ratio
        Nominal tap ratio.

    step_ratio
        Ratio increment per tap position.

    position
        Current discrete tap position.

    neutral_position
        Position corresponding to nominal ratio.

The effective ratio is calculated as:

    tap = nominal_ratio + position * step_ratio

The tap changer does not directly modify the core Transformer.tap
value. Higher-level equipment/control integration is responsible
for applying an accepted tap position to the common Transformer
interface.

This prevents the plugin from silently changing authoritative core
model state.

GridForge V2 Status
-------------------
Initial physical tap-changer capability.

Automatic voltage regulation and OLTC control are intentionally
outside this module.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

from .base import TransformerPlugin


# =====================================================================
# TAP CHANGER
# =====================================================================

class TapChanger(TransformerPlugin):
    """
    Physical transformer tap-changer capability.

    Parameters
    ----------
    transformer :
        Core GridForge Transformer instance.

    min_ratio : float
        Minimum permitted tap ratio.

    max_ratio : float
        Maximum permitted tap ratio.

    step_ratio : float
        Tap-ratio increment between adjacent positions.

    position : int, optional
        Current tap position.

        Default: 0

    neutral_position : int, optional
        Tap position corresponding to nominal ratio.

        Default: 0

    nominal_ratio : float, optional
        Transformer ratio at the neutral position.

        Default: 1.0

    name : str, optional
        Human-readable plugin name.

    Notes
    -----
    The tap changer represents physical capability and state.

    It does not implement automatic voltage regulation.
    """

    plugin_type = "transformer_tap_changer"

    def __init__(
        self,
        transformer,
        min_ratio: float,
        max_ratio: float,
        step_ratio: float,
        position: int = 0,
        neutral_position: int = 0,
        nominal_ratio: float = 1.0,
        name: str = "",
    ):
        super().__init__(
            transformer=transformer,
            name=name,
        )

        self.min_ratio = float(min_ratio)
        self.max_ratio = float(max_ratio)
        self.step_ratio = float(step_ratio)

        self.position = int(position)
        self.neutral_position = int(neutral_position)

        self.nominal_ratio = float(nominal_ratio)

        self.validate()

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate(self) -> None:
        """
        Validate tap-changer configuration.
        """

        if not isfinite(self.min_ratio):
            raise ValueError(
                "Tap-changer minimum ratio must be finite."
            )

        if not isfinite(self.max_ratio):
            raise ValueError(
                "Tap-changer maximum ratio must be finite."
            )

        if not isfinite(self.step_ratio):
            raise ValueError(
                "Tap-changer step ratio must be finite."
            )

        if not isfinite(self.nominal_ratio):
            raise ValueError(
                "Tap-changer nominal ratio must be finite."
            )

        if self.min_ratio <= 0.0:
            raise ValueError(
                "Tap-changer minimum ratio must be greater than zero."
            )

        if self.max_ratio <= 0.0:
            raise ValueError(
                "Tap-changer maximum ratio must be greater than zero."
            )

        if self.max_ratio < self.min_ratio:
            raise ValueError(
                "Tap-changer maximum ratio cannot be less than "
                "minimum ratio."
            )

        if self.step_ratio <= 0.0:
            raise ValueError(
                "Tap-changer step ratio must be greater than zero."
            )

        if self.nominal_ratio <= 0.0:
            raise ValueError(
                "Tap-changer nominal ratio must be greater than zero."
            )

        if not (
            self.min_ratio
            <= self.nominal_ratio
            <= self.max_ratio
        ):
            raise ValueError(
                "Tap-changer nominal ratio must lie within the "
                "configured tap range."
            )

        if self.position < self.minimum_position:
            raise ValueError(
                "Tap-changer position is below the minimum position."
            )

        if self.position > self.maximum_position:
            raise ValueError(
                "Tap-changer position is above the maximum position."
            )

        if (
            self.neutral_position < self.minimum_position
            or self.neutral_position > self.maximum_position
        ):
            raise ValueError(
                "Tap-changer neutral position lies outside the "
                "permitted tap range."
            )

    # =================================================================
    # TAP POSITION RANGE
    # =================================================================

    @property
    def minimum_position(self) -> int:
        """
        Return the minimum discrete tap position.

        The range is derived from the configured physical ratio
        limits and tap step.
        """

        return int(
            round(
                (self.min_ratio - self.nominal_ratio)
                / self.step_ratio
            )
            + self.neutral_position
        )

    @property
    def maximum_position(self) -> int:
        """
        Return the maximum discrete tap position.

        The range is derived from the configured physical ratio
        limits and tap step.
        """

        return int(
            round(
                (self.max_ratio - self.nominal_ratio)
                / self.step_ratio
            )
            + self.neutral_position
        )

    # =================================================================
    # EFFECTIVE TAP
    # =================================================================

    @property
    def ratio(self) -> float:
        """
        Return the effective tap ratio at the current position.

        Formula:

            tap = nominal_ratio
                  + (position - neutral_position) * step_ratio
        """

        return (
            self.nominal_ratio
            + (
                self.position
                - self.neutral_position
            )
            * self.step_ratio
        )

    # =================================================================
    # POSITION STATUS
    # =================================================================

    @property
    def is_at_neutral(self) -> bool:
        """
        Return True when the tap changer is at neutral position.
        """

        return self.position == self.neutral_position

    @property
    def is_at_minimum(self) -> bool:
        """
        Return True when the tap changer is at its minimum position.
        """

        return self.position == self.minimum_position

    @property
    def is_at_maximum(self) -> bool:
        """
        Return True when the tap changer is at its maximum position.
        """

        return self.position == self.maximum_position

    # =================================================================
    # POSITION CONTROL
    # =================================================================

    def set_position(
        self,
        position: int,
    ) -> None:
        """
        Set the tap changer to a discrete position.

        Parameters
        ----------
        position : int
            Requested tap position.

        Notes
        -----
        This method changes only the tap-changer plugin state.

        It does not modify ``Transformer.tap``.
        """

        position = int(position)

        if position < self.minimum_position:
            raise ValueError(
                f"Tap position {position} is below the minimum "
                f"position {self.minimum_position}."
            )

        if position > self.maximum_position:
            raise ValueError(
                f"Tap position {position} is above the maximum "
                f"position {self.maximum_position}."
            )

        self.position = position

    def raise_tap(self) -> None:
        """
        Move the tap changer one position upward.
        """

        if self.is_at_maximum:
            raise ValueError(
                "Tap changer is already at maximum position."
            )

        self.position += 1

    def lower_tap(self) -> None:
        """
        Move the tap changer one position downward.
        """

        if self.is_at_minimum:
            raise ValueError(
                "Tap changer is already at minimum position."
            )

        self.position -= 1

    def move_to_neutral(self) -> None:
        """
        Move the tap changer to its neutral position.
        """

        self.position = self.neutral_position

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured tap-changer information.
        """

        data = super().summary()

        data.update(
            {
                "min_ratio": self.min_ratio,
                "max_ratio": self.max_ratio,
                "step_ratio": self.step_ratio,
                "nominal_ratio": self.nominal_ratio,
                "minimum_position": self.minimum_position,
                "maximum_position": self.maximum_position,
                "neutral_position": self.neutral_position,
                "position": self.position,
                "ratio": self.ratio,
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
            f"<TapChanger "
            f"transformer={self.transformer.id}, "
            f"position={self.position}, "
            f"ratio={self.ratio:.6f}, "
            f"range={self.min_ratio:.6f}-"
            f"{self.max_ratio:.6f}>"
        )
```
