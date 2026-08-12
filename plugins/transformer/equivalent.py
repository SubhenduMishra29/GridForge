```python
# plugins/transformer/equivalent.py

"""
GridForge Transformer Equivalent Plugin
=======================================

GridForge Plugin Layer

Defines the detailed electrical-equivalent capability for GridForge
transformers.

Architecture
------------
The core transformer model:

    core/model/transformer.py

contains the stable common transformer representation.

This plugin provides optional detailed transformer-equivalent data
without expanding the core model.

The equivalent may represent:

    - Series resistance.
    - Series reactance.
    - Magnetizing conductance.
    - Magnetizing susceptance.

The series impedance is represented as:

    Z_series = R + jX

The magnetizing branch is represented as:

    Y_m = G + jB

where:

    G
        Core-loss conductance.

    B
        Magnetizing susceptance.

These parameters are physical/model data only.

The plugin does NOT:

    - Build Y-bus matrices.
    - Stamp network admittance.
    - Perform load-flow calculations.
    - Calculate transformer loading.
    - Calculate transformer losses.
    - Calculate fault currents.
    - Build sequence networks.
    - Perform protection calculations.
    - Execute voltage regulation.
    - Execute tap-changer control.
    - Own global network topology.
    - Store GUI state.

Numerical interpretation belongs to the appropriate network,
solver, analysis, protection, dynamics, or simulation layer.

Relationship to Core Model
--------------------------
The authoritative transformer equipment object remains:

    core.model.transformer.Transformer

Dependency direction:

    plugins/transformer
            │
            ▼
    core/model/transformer

The core model remains independent of this plugin.

Model Representation
--------------------
The equivalent contains two optional physical branches.

Series branch:

    R_series
    X_series

Magnetizing branch:

    G_m
    B_m

The parameters are represented in per-unit, consistent with the
GridForge core branch electrical representation.

No assumptions are made about the exact network stamping convention.

Sequence-network equivalents are deliberately excluded from this
module and should be provided through a dedicated sequence-model
capability when required.

GridForge V2 Status
-------------------
Initial detailed transformer-equivalent capability.

The interface is intentionally limited to electrical-equivalent
parameters and basic diagnostics.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

from .base import TransformerPlugin


# =====================================================================
# TRANSFORMER EQUIVALENT
# =====================================================================

class TransformerEquivalent(TransformerPlugin):
    """
    Detailed transformer electrical-equivalent capability.

    Parameters
    ----------
    transformer :
        Core GridForge Transformer instance.

    r_series : float, optional
        Series resistance in per-unit.

        Default: 0.0

    x_series : float, optional
        Series reactance in per-unit.

        Default: 0.0

    g_magnetizing : float, optional
        Magnetizing/core-loss conductance in per-unit.

        Default: 0.0

    b_magnetizing : float, optional
        Magnetizing susceptance in per-unit.

        Default: 0.0

    name : str, optional
        Human-readable plugin name.

    Notes
    -----
    The equivalent may be used as an enhanced representation of the
    transformer's electrical behavior.

    It does not replace the core Transformer series parameters unless
    a higher-level integration explicitly chooses to use it.

    This separation prevents multiple model objects from silently
    becoming competing sources of truth.
    """

    plugin_type = "transformer_equivalent"

    def __init__(
        self,
        transformer,
        r_series: float = 0.0,
        x_series: float = 0.0,
        g_magnetizing: float = 0.0,
        b_magnetizing: float = 0.0,
        name: str = "",
    ):
        super().__init__(
            transformer=transformer,
            name=name,
        )

        self.r_series = float(r_series)
        self.x_series = float(x_series)

        self.g_magnetizing = float(g_magnetizing)
        self.b_magnetizing = float(b_magnetizing)

        self.validate()

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate(self) -> None:
        """
        Validate transformer-equivalent parameters.
        """

        parameters = {
            "r_series": self.r_series,
            "x_series": self.x_series,
            "g_magnetizing": self.g_magnetizing,
            "b_magnetizing": self.b_magnetizing,
        }

        for name, value in parameters.items():
            if not isfinite(value):
                raise ValueError(
                    f"Transformer equivalent parameter "
                    f"'{name}' must be finite."
                )

        if self.r_series < 0.0:
            raise ValueError(
                "Transformer equivalent series resistance cannot "
                "be negative."
            )

        if self.g_magnetizing < 0.0:
            raise ValueError(
                "Transformer magnetizing conductance cannot "
                "be negative."
            )

        # A zero series impedance is not a valid standalone
        # transformer series equivalent.
        if (
            self.r_series == 0.0
            and self.x_series == 0.0
        ):
            raise ValueError(
                "Transformer equivalent cannot have zero series "
                "impedance."
            )

    # =================================================================
    # SERIES EQUIVALENT
    # =================================================================

    @property
    def series_impedance(self) -> complex:
        """
        Return the transformer series impedance.

        Z = R + jX
        """

        return complex(
            self.r_series,
            self.x_series,
        )

    @property
    def series_admittance(self) -> complex:
        """
        Return the mathematical series admittance.

        Y = 1 / Z

        This property does not perform network stamping.
        """

        z = self.series_impedance

        if z == 0:
            raise ZeroDivisionError(
                "Transformer equivalent has zero series impedance."
            )

        return 1.0 / z

    # =================================================================
    # MAGNETIZING EQUIVALENT
    # =================================================================

    @property
    def magnetizing_admittance(self) -> complex:
        """
        Return the magnetizing-branch admittance.

        Y_m = G + jB
        """

        return complex(
            self.g_magnetizing,
            self.b_magnetizing,
        )

    @property
    def has_magnetizing_branch(self) -> bool:
        """
        Return True when the magnetizing branch is non-zero.
        """

        return (
            self.g_magnetizing != 0.0
            or self.b_magnetizing != 0.0
        )

    # =================================================================
    # CORE-LOSS STATUS
    # =================================================================

    @property
    def has_core_loss_model(self) -> bool:
        """
        Return True when a non-zero core-loss conductance is defined.
        """

        return self.g_magnetizing != 0.0

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured transformer-equivalent information.
        """

        data = super().summary()

        data.update(
            {
                "r_series": self.r_series,
                "x_series": self.x_series,
                "series_impedance": self.series_impedance,
                "g_magnetizing": self.g_magnetizing,
                "b_magnetizing": self.b_magnetizing,
                "magnetizing_admittance": (
                    self.magnetizing_admittance
                ),
                "has_magnetizing_branch": (
                    self.has_magnetizing_branch
                ),
                "has_core_loss_model": (
                    self.has_core_loss_model
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
            f"<TransformerEquivalent "
            f"transformer={self.transformer.id}, "
            f"R={self.r_series:.6f} pu, "
            f"X={self.x_series:.6f} pu, "
            f"Gm={self.g_magnetizing:.6f} pu, "
            f"Bm={self.b_magnetizing:.6f} pu>"
        )
```
