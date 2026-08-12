```python
# core/model/transformer.py

"""
GridForge Transformer Model
===========================

GridForge Model Layer V2

Defines the core two-terminal transformer equipment model.

Architecture
------------
Transformer is a specialized Branch.

The core Transformer model represents the stable physical/electrical
identity required by the GridForge network and study architecture.

Common Branch responsibilities:
    - Two-terminal connectivity
    - Series impedance
    - Equipment rating
    - In-service state
    - Common branch electrical interface
    - Transformer-compatible tap ratio
    - Transformer-compatible phase shift

Transformer-specific detailed behavior belongs to the GridForge
plugin architecture under:

    core/plugins/transformer/

Examples of transformer-specific capabilities that may be provided
by plugins include:

    - Winding definitions
    - Vector groups
    - Grounding and neutral configuration
    - Tap-changer models
    - OLTC control
    - Magnetizing/core-loss models
    - Detailed transformer equivalents
    - Sequence models
    - Thermal models
    - Specialized transformer controls

The core Transformer model does NOT:

    - Build Y-bus matrices.
    - Perform load-flow calculations.
    - Calculate transformer loading.
    - Calculate transformer losses.
    - Perform short-circuit calculations.
    - Perform voltage regulation.
    - Execute tap-changer control.
    - Perform protection calculations.
    - Perform dynamic simulation.
    - Store GUI geometry.
    - Own global network topology.

Those responsibilities belong to the appropriate network,
solver, analysis, protection, simulation, UI, or plugin layers.

Core Transformer Representation
-------------------------------
The core transformer uses the common Branch electrical representation:

    Z_series = R + jX

and the common transformer-compatible parameters:

    tap
        Magnitude tap ratio.

        Normal transformer value: 1.0

    shift
        Phase-shifting angle in radians.

        Normal transformer value: 0.0

The exact numerical interpretation of tap and phase shift,
including Y-bus stamping conventions and sign conventions, belongs
to the network/solver contract.

Plugin Architecture
--------------------
The core Transformer intentionally remains small and stable.

Detailed transformer engineering behavior should be implemented
through plugins rather than by continuously expanding this class.

The plugin layer may associate specialized capabilities with a
Transformer instance without moving numerical study logic into the
core model.

This preserves:

    core/model
        stable physical equipment contract

    core/plugins
        specialized equipment behavior and engineering models

    core/network
        network representation and topology

    core/solver
        numerical computation

    core/analysis
        public study interfaces

    core/protection
        protection engineering

State Ownership
---------------
The Transformer stores authoritative equipment parameters only.

Calculated quantities such as:

    - loading
    - losses
    - terminal power
    - terminal current
    - voltage regulation
    - fault current
    - thermal state
    - control results

must not become persistent authoritative Transformer state.

They belong to study/result objects or the appropriate higher layer.

GridForge V2 Status
-------------------
This module is part of the frozen GridForge Model Layer V2 baseline.

Changes require evidence of a genuinely fundamental transformer
equipment requirement that cannot be satisfied through the existing
Branch contract or the transformer plugin architecture.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from .branch import Branch


# =====================================================================
# TRANSFORMER
# =====================================================================

class Transformer(Branch):
    """
    Core GridForge two-terminal transformer model.

    Transformer is intentionally a thin specialization of ``Branch``.

    Parameters
    ----------
    id : str
        Unique GridForge transformer identifier.

    bus_from :
        From-side GridForge Bus.

    bus_to :
        To-side GridForge Bus.

    r : float
        Transformer series resistance in per-unit.

    x : float
        Transformer series reactance in per-unit.

    tap : float, optional
        Transformer off-nominal magnitude tap ratio.

        Default: 1.0

    shift : float, optional
        Transformer phase-shifting angle in radians.

        Default: 0.0

    name : str, optional
        Human-readable transformer name.

    rate_mva : float, optional
        Transformer equipment rating in MVA.

    Notes
    -----
    The Transformer does not independently implement tap-changer,
    vector-group, grounding, winding, magnetizing, or control logic.

    Such capabilities belong to transformer plugins.

    The inherited Branch fields ``tap`` and ``shift`` form the common
    numerical interface consumed by the network/solver layers.
    """

    def __init__(
        self,
        id: str,
        bus_from,
        bus_to,
        r: float,
        x: float,
        tap: float = 1.0,
        shift: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
    ):
        """
        Initialize a GridForge transformer.
        """

        super().__init__(
            id=id,
            bus_from=bus_from,
            bus_to=bus_to,
            r=r,
            x=x,
            b=0.0,
            name=name,
            rate_mva=rate_mva,
            tap=tap,
            shift=shift,
        )

    # =================================================================
    # TRANSFORMER IDENTIFICATION
    # =================================================================

    @property
    def is_transformer(self) -> bool:
        """
        Return True because this equipment is a transformer.
        """

        return True

    # =================================================================
    # TRANSFORMER STATUS
    # =================================================================

    @property
    def is_off_nominal(self) -> bool:
        """
        Return True when the transformer tap differs from unity.
        """

        return self.tap != 1.0

    @property
    def has_phase_shift(self) -> bool:
        """
        Return True when the transformer has a non-zero phase shift.

        The Branch ``shift`` value is expressed in radians.
        """

        return self.shift != 0.0

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured transformer information.
        """

        data = super().summary()

        data.update(
            {
                "type": "transformer",
                "tap": self.tap,
                "shift": self.shift,
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
            f"<Transformer "
            f"id={self.id}, "
            f"{self.from_bus.id} -> {self.to_bus.id}, "
            f"r={self.r:.6f}, "
            f"x={self.x:.6f}, "
            f"tap={self.tap:.6f}, "
            f"shift={self.shift:.6f} rad, "
            f"rate={self.rate_mva:.2f} MVA, "
            f"in_service={self.in_service}>"
        )
```
