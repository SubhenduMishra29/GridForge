```python id="w6r4p2"
# plugins/transformer/vector_group.py

"""
GridForge Transformer Vector Group Plugin
=========================================

GridForge Plugin Layer

Defines transformer vector-group representation for the GridForge
transformer plugin architecture.

Architecture
------------
A transformer vector group describes the relative phase relationship
and winding connection between transformer windings.

Examples include:

    Dyn11
    YNd1
    Yyn0
    YNd11
    Dd0

The vector-group model stores engineering configuration and provides
basic descriptive information.

It does NOT:

    - Build sequence networks.
    - Calculate zero-sequence paths.
    - Calculate fault currents.
    - Build Y-bus matrices.
    - Perform load-flow calculations.
    - Calculate transformer losses.
    - Perform protection calculations.
    - Execute transformer controls.
    - Own network topology.
    - Store GUI state.

Those responsibilities belong to the appropriate network, solver,
analysis, protection, dynamics, simulation, or control layers.

Relationship to Core Model
--------------------------
The authoritative transformer equipment object remains:

    core.model.transformer.Transformer

This module extends that equipment through the plugin architecture:

    plugins/transformer/

Dependency direction:

    plugins/transformer
            │
            ▼
    core/model/transformer

The core model must remain independent of this plugin.

Vector Group Representation
----------------------------
IEC-style vector-group notation is represented as:

    <HV connection><LV connection><clock number>

For example:

    Dyn11

means:

    D
        HV winding connected in delta.

    y
        LV winding connected in star.

    n
        LV neutral is available.

    11
        Relative phase displacement represented by clock position 11.

The plugin stores the engineering notation and exposes the clock
position and basic connection information.

Phase displacement is expressed using the conventional clock
notation. Numerical sequence-network interpretation remains outside
this plugin.

GridForge V2 Status
-------------------
Initial transformer vector-group capability.

The interface is intentionally limited to engineering configuration
and descriptive information.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import re

from .base import TransformerPlugin


# =====================================================================
# TRANSFORMER VECTOR GROUP
# =====================================================================

class VectorGroup(TransformerPlugin):
    """
    Transformer vector-group capability.

    Parameters
    ----------
    transformer :
        Core GridForge Transformer instance.

    group : str
        IEC-style transformer vector-group notation.

        Examples:

            "Dyn11"
            "YNd1"
            "Yyn0"
            "Dd0"

    name : str, optional
        Human-readable plugin name.

    Notes
    -----
    The parser intentionally supports the common two-winding
    vector-group representation.

    Numerical phase-shift interpretation belongs to the appropriate
    network/solver layer.
    """

    plugin_type = "transformer_vector_group"

    # -----------------------------------------------------------------
    # IEC CONNECTION SYMBOLS
    # -----------------------------------------------------------------

    _VALID_CONNECTIONS = {
        "D",
        "Y",
        "Z",
    }

    # -----------------------------------------------------------------
    # VECTOR-GROUP PATTERN
    # -----------------------------------------------------------------

    _PATTERN = re.compile(
        r"^([DZY])([dzy])([nN]?)([0-9]|1[0-1])$"
    )

    def __init__(
        self,
        transformer,
        group: str,
        name: str = "",
    ):
        super().__init__(
            transformer=transformer,
            name=name,
        )

        self.group = str(group).strip()

        # Parsed engineering representation.
        self.hv_connection = ""
        self.lv_connection = ""
        self.lv_neutral = False
        self.clock_position = 0

        self._parse_group()
        self.validate()

    # =================================================================
    # PARSING
    # =================================================================

    def _parse_group(self) -> None:
        """
        Parse the IEC-style two-winding vector-group notation.
        """

        if not self.group:
            raise ValueError(
                "Transformer vector group cannot be empty."
            )

        match = self._PATTERN.fullmatch(self.group)

        if match is None:
            raise ValueError(
                f"Unsupported transformer vector group '{self.group}'. "
                "Expected a two-winding IEC-style group such as "
                "'Dyn11', 'YNd1', 'Yyn0', or 'Dd0'."
            )

        hv, lv, neutral, clock = match.groups()

        self.hv_connection = hv.upper()
        self.lv_connection = lv.upper()
        self.lv_neutral = bool(neutral)

        self.clock_position = int(clock)

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate(self) -> None:
        """
        Validate vector-group configuration.
        """

        if not self.group:
            raise ValueError(
                "Transformer vector group cannot be empty."
            )

        if self.hv_connection not in self._VALID_CONNECTIONS:
            raise ValueError(
                f"Unsupported HV connection "
                f"'{self.hv_connection}'."
            )

        if self.lv_connection not in self._VALID_CONNECTIONS:
            raise ValueError(
                f"Unsupported LV connection "
                f"'{self.lv_connection}'."
            )

        if not 0 <= self.clock_position <= 11:
            raise ValueError(
                "Transformer vector-group clock position must be "
                "between 0 and 11."
            )

        # A neutral designation is meaningful only for star/zigzag
        # type connections.
        if self.lv_neutral and self.lv_connection not in {"Y", "Z"}:
            raise ValueError(
                f"Vector group '{self.group}' specifies a neutral "
                f"for unsupported LV connection '{self.lv_connection}'."
            )

    # =================================================================
    # CONNECTION STATUS
    # =================================================================

    @property
    def has_lv_neutral(self) -> bool:
        """
        Return True when the LV winding has a neutral designation.
        """

        return self.lv_neutral

    @property
    def is_delta_delta(self) -> bool:
        """
        Return True for delta-delta connection.
        """

        return (
            self.hv_connection == "D"
            and self.lv_connection == "D"
        )

    @property
    def is_star_star(self) -> bool:
        """
        Return True for star-star connection.
        """

        return (
            self.hv_connection == "Y"
            and self.lv_connection == "Y"
        )

    @property
    def is_delta_star(self) -> bool:
        """
        Return True for delta-star connection.
        """

        return (
            self.hv_connection == "D"
            and self.lv_connection == "Y"
        )

    @property
    def is_star_delta(self) -> bool:
        """
        Return True for star-delta connection.
        """

        return (
            self.hv_connection == "Y"
            and self.lv_connection == "D"
        )

    # =================================================================
    # PHASE DISPLACEMENT
    # =================================================================

    @property
    def phase_shift_deg(self) -> float:
        """
        Return the conventional vector-group phase displacement.

        Clock position is converted using:

            phase displacement = clock × 30°

        The returned value is a descriptive engineering quantity.

        The network/solver layer remains responsible for applying its
        established transformer phase-shift sign convention.
        """

        return self.clock_position * 30.0

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured vector-group information.
        """

        data = super().summary()

        data.update(
            {
                "group": self.group,
                "hv_connection": self.hv_connection,
                "lv_connection": self.lv_connection,
                "lv_neutral": self.lv_neutral,
                "clock_position": self.clock_position,
                "phase_shift_deg": self.phase_shift_deg,
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
            f"<VectorGroup "
            f"transformer={self.transformer.id}, "
            f"group={self.group}, "
            f"clock={self.clock_position}>"
        )
```
