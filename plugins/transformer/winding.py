```python
# plugins/transformer/winding.py

"""
GridForge Transformer Winding Plugin
====================================

GridForge Plugin Layer

Defines the transformer winding representation used by the
transformer plugin architecture.

Architecture
------------
A transformer winding represents one physical winding of a
GridForge transformer.

Typical transformer configurations include:

    - HV winding
    - LV winding
    - Tertiary winding

The winding model stores physical/engineering configuration only.

It does NOT:

    - Calculate currents.
    - Calculate winding losses.
    - Build Y-bus matrices.
    - Perform load-flow calculations.
    - Perform short-circuit calculations.
    - Execute tap-changer control.
    - Perform protection calculations.
    - Own network topology.
    - Store GUI state.

Numerical interpretation belongs to the appropriate network,
solver, analysis, protection, dynamics, or simulation layer.

Relationship to Core Model
--------------------------
The authoritative transformer equipment object remains:

    core.model.transformer.Transformer

This module provides additional transformer-specific capability
through the plugin layer:

    plugins/transformer/

Dependency direction:

    plugins/transformer
            │
            ▼
    core/model/transformer

The core model must remain independent of this module.

Winding Representation
----------------------
A winding contains:

    id
        Unique winding identifier within the transformer.

    name
        Human-readable winding name.

    side
        Engineering designation such as:

            "HV"
            "LV"
            "tertiary"

    nominal_voltage_kv
        Nominal winding voltage in kV.

    rated_mva
        Winding/equipment rating in MVA.

    connection
        Winding connection designation such as:

            "Y"
            "YN"
            "D"
            "Z"
            "ZN"

    neutral
        Whether the winding provides a neutral point.

The model intentionally does not interpret vector groups. Vector
group and phase-displacement behavior belong to the dedicated
vector-group plugin.

GridForge V2 Status
-------------------
Initial transformer winding capability.

The interface is intentionally small and may be extended only when
a genuine transformer-model requirement is identified.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

from .base import TransformerPlugin


# =====================================================================
# TRANSFORMER WINDING
# =====================================================================

class Winding(TransformerPlugin):
    """
    Transformer winding capability.

    Parameters
    ----------
    transformer :
        Core GridForge Transformer instance.

    id : str
        Unique winding identifier within the transformer.

    side : str
        Engineering winding designation.

        Typical values:

            "HV"
            "LV"
            "tertiary"

    nominal_voltage_kv : float
        Nominal winding voltage in kV.

    rated_mva : float
        Winding/equipment rating in MVA.

    connection : str, optional
        Winding connection designation.

        Examples:

            "Y"
            "YN"
            "D"
            "Z"
            "ZN"

        Default: "Y"

    neutral : bool, optional
        Whether the winding has a neutral point.

        Default: False

    name : str, optional
        Human-readable winding name.
    """

    plugin_type = "transformer_winding"

    def __init__(
        self,
        transformer,
        id: str,
        side: str,
        nominal_voltage_kv: float,
        rated_mva: float,
        connection: str = "Y",
        neutral: bool = False,
        name: str = "",
    ):
        super().__init__(
            transformer=transformer,
            name=name,
        )

        self.id = str(id)
        self.side = str(side)
        self.nominal_voltage_kv = float(nominal_voltage_kv)
        self.rated_mva = float(rated_mva)
        self.connection = str(connection).upper()
        self.neutral = bool(neutral)

        self.validate()

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate(self) -> None:
        """
        Validate winding configuration.
        """

        if not self.id.strip():
            raise ValueError(
                "Transformer winding id cannot be empty."
            )

        if not self.side.strip():
            raise ValueError(
                f"Winding '{self.id}' side cannot be empty."
            )

        if not isfinite(self.nominal_voltage_kv):
            raise ValueError(
                f"Winding '{self.id}' nominal voltage must be finite."
            )

        if self.nominal_voltage_kv <= 0.0:
            raise ValueError(
                f"Winding '{self.id}' nominal voltage must be greater "
                "than zero."
            )

        if not isfinite(self.rated_mva):
            raise ValueError(
                f"Winding '{self.id}' rated MVA must be finite."
            )

        if self.rated_mva <= 0.0:
            raise ValueError(
                f"Winding '{self.id}' rated MVA must be greater "
                "than zero."
            )

        if not self.connection.strip():
            raise ValueError(
                f"Winding '{self.id}' connection cannot be empty."
            )

        valid_connections = {
            "Y",
            "YN",
            "D",
            "DELTA",
            "Z",
            "ZN",
        }

        if self.connection not in valid_connections:
            raise ValueError(
                f"Winding '{self.id}' has unsupported connection "
                f"'{self.connection}'."
            )

        if self.connection in {"YN", "ZN"} and not self.neutral:
            raise ValueError(
                f"Winding '{self.id}' connection '{self.connection}' "
                "requires neutral=True."
            )

    # =================================================================
    # STATUS
    # =================================================================

    @property
    def has_neutral(self) -> bool:
        """
        Return True when the winding provides a neutral point.
        """

        return self.neutral

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured winding information.
        """

        data = super().summary()

        data.update(
            {
                "winding_id": self.id,
                "side": self.side,
                "nominal_voltage_kv": self.nominal_voltage_kv,
                "rated_mva": self.rated_mva,
                "connection": self.connection,
                "neutral": self.neutral,
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
            f"<Winding "
            f"id={self.id}, "
            f"transformer={self.transformer.id}, "
            f"side={self.side}, "
            f"voltage={self.nominal_voltage_kv:.3f} kV, "
            f"rated={self.rated_mva:.3f} MVA, "
            f"connection={self.connection}, "
            f"neutral={self.neutral}>"
        )
```
