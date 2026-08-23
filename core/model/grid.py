"""
GridForge V2 Grid Model
=======================

File:
    core/model/grid.py

Author:
    Subhendu Mishra

Purpose
-------
Defines the canonical GridForge V2 electrical Grid-source model.

Architectural Role
------------------
Grid is an electrical source/equipment model representing an external
utility/grid source connected to the GridForge electrical network.

Grid is an electrical element.

Grid is NOT:
    - an electrical-network container;
    - a collection of buses;
    - a collection of loads;
    - a collection of generators;
    - a collection of branches;
    - a topology manager;
    - a Y-bus builder;
    - a power-flow solver;
    - an SLD container;
    - a GUI object.

The assembled electrical network is owned by the network layer.

    Grid
      |
      +-- Terminal(s)
              |
              v
        core.network
              |
              v
             Bus
              |
              v
        Network topology

SLD Relationship
----------------
The Grid model is the authoritative electrical/domain object.

The SLD representation of Grid is a presentation projection of this
model. The SLD symbol is not the Grid electrical object.

Engineering Model
-----------------
The Grid model represents an external utility/grid source and stores
the electrical characteristics required by GridForge studies.

The model supports:

    - nominal voltage;
    - frequency;
    - phase/system configuration;
    - operating voltage;
    - source active/reactive power information;
    - short-circuit strength;
    - positive-sequence source impedance;
    - negative-sequence source impedance;
    - zero-sequence source impedance;
    - X/R information;
    - source voltage angle;
    - grounding/reference information;
    - source operating state;
    - physical terminal connectivity.

The exact interpretation of these parameters belongs to the
corresponding engineering study/model and must remain compatible with
the applicable IEEE/industry modelling conventions.

Grid does not perform the studies itself.

Responsibilities
----------------
Grid owns:

    - identity;
    - engineering name;
    - electrical source parameters;
    - physical terminal definitions;
    - source operating state;
    - source-model configuration.

Grid does NOT own:

    - global network membership;
    - global topology;
    - buses;
    - loads;
    - generators;
    - lines;
    - transformers;
    - shunts;
    - Y-bus;
    - network indexing;
    - network validation;
    - power-flow solution;
    - short-circuit solution;
    - protection analysis;
    - dynamic simulation;
    - SLD state;
    - rendering;
    - persistence.

Those responsibilities belong to the appropriate Core layers.

Terminal Model
--------------
The Grid owns its physical electrical terminal.

The terminal is the authoritative local connection point.

Global connectivity is established by core.network.

Typical relationship:

    Grid
      |
      +-- Terminal
              |
              +-- network topology
              |
              +-- Bus

The Grid model must therefore never directly modify a Network or
TopologyManager.

No Container API
----------------
Grid intentionally provides NO methods such as:

    add_bus()
    add_load()
    add_generator()
    add_branch()
    add_line()
    add_transformer()
    add_shunt()

It is an electrical element, not a network container.

Validation
----------
Grid does not perform global network validation.

Model-level parameter validation is performed when parameters are
created or changed.

Global network validation belongs to core.validation.

Power Source Semantics
----------------------
The Grid represents an external electrical source.

Positive active and reactive power values represent source injection
into the connected electrical network.

For studies requiring a more specific source representation, the
appropriate analysis/solver layer interprets the Grid parameters.

Grid does not determine network bus classification.

Plugin Compatibility
--------------------
Grid may expose a lightweight extension registry for optional
engineering capabilities.

The core Grid model does not import concrete plugins.

Plugins must not bypass the Core command/application architecture.

Copyright
---------
Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

from .base import ElectricalObject
from .terminal import Terminal


class Grid(ElectricalObject):
    """
    Canonical GridForge V2 external-grid/source model.

    Grid is an electrical source element, not a network container.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable engineering name.

    nominal_voltage_kv:
        Nominal line-to-line system voltage in kV.

    frequency_hz:
        Nominal system frequency in Hz.

    voltage_pu:
        Present source voltage magnitude in per-unit.

    angle_deg:
        Source voltage reference angle in degrees.

    p_mw:
        Active-power injection into the network in MW.

    q_mvar:
        Reactive-power injection into the network in MVAr.

    short_circuit_mva:
        Three-phase short-circuit level at the grid connection
        point, in MVA.

    x_over_r:
        Positive-sequence source X/R ratio.

    z1_pu:
        Positive-sequence source impedance in per-unit.

    z2_pu:
        Negative-sequence source impedance in per-unit.

    z0_pu:
        Zero-sequence source impedance in per-unit.

    in_service:
        Whether the Grid source is electrically in service.

    grounded:
        Whether the source has an applicable grounding/reference
        connection.

    """

    TYPE = "GRID"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        nominal_voltage_kv: float = 0.0,
        frequency_hz: float = 50.0,
        voltage_pu: float = 1.0,
        angle_deg: float = 0.0,
        p_mw: float = 0.0,
        q_mvar: float = 0.0,
        short_circuit_mva: Optional[float] = None,
        x_over_r: Optional[float] = None,
        z1_pu: Optional[complex] = None,
        z2_pu: Optional[complex] = None,
        z0_pu: Optional[complex] = None,
        in_service: bool = True,
        grounded: bool = True,
        terminal: Optional[Terminal] = None,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # ============================================================
        # SOURCE ELECTRICAL PARAMETERS
        # ============================================================

        self.nominal_voltage_kv = self._validate_positive_or_zero(
            nominal_voltage_kv,
            "nominal_voltage_kv",
        )

        self.frequency_hz = self._validate_positive(
            frequency_hz,
            "frequency_hz",
        )

        self.voltage_pu = self._validate_positive(
            voltage_pu,
            "voltage_pu",
        )

        self.angle_deg = self._validate_finite(
            angle_deg,
            "angle_deg",
        )

        self.p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self.q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        # ============================================================
        # SHORT-CIRCUIT / SOURCE IMPEDANCE PARAMETERS
        # ============================================================

        self.short_circuit_mva = (
            self._validate_optional_positive(
                short_circuit_mva,
                "short_circuit_mva",
            )
        )

        self.x_over_r = (
            self._validate_optional_positive(
                x_over_r,
                "x_over_r",
            )
        )

        self.z1_pu = self._validate_optional_impedance(
            z1_pu,
            "z1_pu",
        )

        self.z2_pu = self._validate_optional_impedance(
            z2_pu,
            "z2_pu",
        )

        self.z0_pu = self._validate_optional_impedance(
            z0_pu,
            "z0_pu",
        )

        # ============================================================
        # OPERATING STATE
        # ============================================================

        self.in_service = bool(in_service)

        self.grounded = bool(grounded)

        # ============================================================
        # PHYSICAL CONNECTION
        # ============================================================

        self.terminal: Optional[Terminal] = None

        if terminal is not None:
            self.set_terminal(terminal)

        # ============================================================
        # OPTIONAL EXTENSIONS
        # ============================================================

        self._extensions: Dict[str, Any] = {}

    # =================================================================
    # TYPE / IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge model element type.
        """
        return self.TYPE

    # =================================================================
    # TERMINAL
    # =================================================================

    def set_terminal(
        self,
        terminal: Terminal,
    ) -> None:
        """
        Assign the physical electrical terminal owned by the Grid.

        Global topology is not modified here.
        """

        if not isinstance(
            terminal,
            Terminal,
        ):
            raise TypeError(
                "terminal must be a Terminal instance."
            )

        self.terminal = terminal

    # -----------------------------------------------------------------

    def clear_terminal(self) -> None:
        """
        Remove the local terminal reference.

        This does not modify global network topology.
        """

        self.terminal = None

    # -----------------------------------------------------------------

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """
        Return the Grid's physical terminals.

        The returned tuple prevents callers from modifying the
        terminal collection directly.
        """

        if self.terminal is None:
            return ()

        return (self.terminal,)

    # =================================================================
    # SOURCE STATE
    # =================================================================

    def connect(self) -> None:
        """
        Mark the Grid source as electrically in service.

        Topology management remains the responsibility of
        core.network.
        """

        self.in_service = True

    # -----------------------------------------------------------------

    def disconnect(self) -> None:
        """
        Mark the Grid source as electrically out of service.

        This changes the Grid's local operating state only.

        Network topology interpretation belongs to core.network.
        """

        self.in_service = False

    # -----------------------------------------------------------------

    @property
    def is_available(self) -> bool:
        """
        Return whether the Grid source is available for study use.
        """

        return self.in_service

    # =================================================================
    # POWER INJECTION
    # =================================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return source active/reactive power injection.

        Returns
        -------
        tuple[float, float]
            (P_MW, Q_MVAr)

        Positive values represent injection into the electrical
        network.
        """

        return (
            self.p_mw,
            self.q_mvar,
        )

    # -----------------------------------------------------------------

    def set_power(
        self,
        p_mw: float,
        q_mvar: float,
    ) -> None:
        """
        Set source active/reactive power injection.

        No numerical study is performed.
        """

        self.p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self.q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

    # =================================================================
    # VOLTAGE SOURCE
    # =================================================================

    def set_voltage(
        self,
        voltage_pu: float,
        angle_deg: float = 0.0,
    ) -> None:
        """
        Set the source voltage magnitude and reference angle.
        """

        self.voltage_pu = self._validate_positive(
            voltage_pu,
            "voltage_pu",
        )

        self.angle_deg = self._validate_finite(
            angle_deg,
            "angle_deg",
        )

    # =================================================================
    # SOURCE IMPEDANCE
    # =================================================================

    def set_sequence_impedances(
        self,
        *,
        z1_pu: Optional[complex] = None,
        z2_pu: Optional[complex] = None,
        z0_pu: Optional[complex] = None,
    ) -> None:
        """
        Set positive-, negative-, and zero-sequence source
        impedances.

        The Grid model stores the parameters.

        It does not calculate fault currents.
        """

        self.z1_pu = self._validate_optional_impedance(
            z1_pu,
            "z1_pu",
        )

        self.z2_pu = self._validate_optional_impedance(
            z2_pu,
            "z2_pu",
        )

        self.z0_pu = self._validate_optional_impedance(
            z0_pu,
            "z0_pu",
        )

    # -----------------------------------------------------------------

    def has_sequence_impedance_data(self) -> bool:
        """
        Return True when at least positive-sequence source impedance
        data is available.
        """

        return self.z1_pu is not None

    # =================================================================
    # PLUGIN / EXTENSION REGISTRY
    # =================================================================

    def register_extension(
        self,
        extension_id: str,
        extension: Any,
    ) -> None:
        """
        Register an optional extension object.

        Grid does not interpret or execute extension behavior.
        """

        if not isinstance(
            extension_id,
            str,
        ):
            raise TypeError(
                "extension_id must be a string."
            )

        extension_id = extension_id.strip()

        if not extension_id:
            raise ValueError(
                "extension_id cannot be empty."
            )

        if extension is None:
            raise ValueError(
                "extension cannot be None."
            )

        if extension_id in self._extensions:
            raise ValueError(
                f"Extension '{extension_id}' is already registered."
            )

        self._extensions[extension_id] = extension

    # -----------------------------------------------------------------

    def get_extension(
        self,
        extension_id: str,
    ) -> Any:
        """
        Return a registered extension.
        """

        try:
            return self._extensions[extension_id]

        except KeyError as exc:
            raise KeyError(
                f"Extension '{extension_id}' is not registered."
            ) from exc

    # -----------------------------------------------------------------

    def remove_extension(
        self,
        extension_id: str,
    ) -> None:
        """
        Remove a registered extension.
        """

        try:
            del self._extensions[extension_id]

        except KeyError as exc:
            raise KeyError(
                f"Extension '{extension_id}' is not registered."
            ) from exc

    # -----------------------------------------------------------------

    @property
    def extension_ids(self) -> tuple[str, ...]:
        """
        Return registered extension identifiers.
        """

        return tuple(
            self._extensions.keys()
        )

    # =================================================================
    # MODEL VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate the Grid's own engineering parameters.

        This method deliberately does NOT validate the global
        electrical network.

        Global validation belongs to core.validation.
        """

        self._validate_positive_or_zero(
            self.nominal_voltage_kv,
            "nominal_voltage_kv",
        )

        self._validate_positive(
            self.frequency_hz,
            "frequency_hz",
        )

        self._validate_positive(
            self.voltage_pu,
            "voltage_pu",
        )

        self._validate_finite(
            self.angle_deg,
            "angle_deg",
        )

        self._validate_finite(
            self.p_mw,
            "p_mw",
        )

        self._validate_finite(
            self.q_mvar,
            "q_mvar",
        )

        self._validate_optional_positive(
            self.short_circuit_mva,
            "short_circuit_mva",
        )

        self._validate_optional_positive(
            self.x_over_r,
            "x_over_r",
        )

        self._validate_optional_impedance(
            self.z1_pu,
            "z1_pu",
        )

        self._validate_optional_impedance(
            self.z2_pu,
            "z2_pu",
        )

        self._validate_optional_impedance(
            self.z0_pu,
            "z0_pu",
        )

        if self.terminal is not None:
            if not isinstance(
                self.terminal,
                Terminal,
            ):
                raise TypeError(
                    "Grid terminal must be a Terminal instance."
                )

        return True

    # =================================================================
    # VALIDATION HELPERS
    # =================================================================

    @staticmethod
    def _validate_finite(
        value: float,
        field_name: str,
    ) -> float:
        """
        Validate a finite numeric value.
        """

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{field_name} cannot be bool."
            )

        try:
            value = float(value)

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise TypeError(
                f"{field_name} must be numeric."
            ) from exc

        if not math.isfinite(value):
            raise ValueError(
                f"{field_name} must be finite."
            )

        return value

    # -----------------------------------------------------------------

    @classmethod
    def _validate_positive(
        cls,
        value: float,
        field_name: str,
    ) -> float:
        """
        Validate a strictly positive numeric value.
        """

        value = cls._validate_finite(
            value,
            field_name,
        )

        if value <= 0.0:
            raise ValueError(
                f"{field_name} must be greater than zero."
            )

        return value

    # -----------------------------------------------------------------

    @classmethod
    def _validate_positive_or_zero(
        cls,
        value: float,
        field_name: str,
    ) -> float:
        """
        Validate a non-negative numeric value.
        """

        value = cls._validate_finite(
            value,
            field_name,
        )

        if value < 0.0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

        return value

    # -----------------------------------------------------------------

    @classmethod
    def _validate_optional_positive(
        cls,
        value: Optional[float],
        field_name: str,
    ) -> Optional[float]:
        """
        Validate an optional strictly positive value.
        """

        if value is None:
            return None

        return cls._validate_positive(
            value,
            field_name,
        )

    # -----------------------------------------------------------------

    @staticmethod
    def _validate_optional_impedance(
        value: Optional[complex],
        field_name: str,
    ) -> Optional[complex]:
        """
        Validate an optional finite complex impedance.
        """

        if value is None:
            return None

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{field_name} cannot be bool."
            )

        try:
            impedance = complex(value)

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise TypeError(
                f"{field_name} must be a numeric complex impedance."
            ) from exc

        if (
            not math.isfinite(impedance.real)
            or not math.isfinite(impedance.imag)
        ):
            raise ValueError(
                f"{field_name} must contain finite values."
            )

        return impedance

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        return (
            f"Grid("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"nominal_voltage_kv={self.nominal_voltage_kv!r}, "
            f"frequency_hz={self.frequency_hz!r}, "
            f"voltage_pu={self.voltage_pu!r}, "
            f"p_mw={self.p_mw!r}, "
            f"q_mvar={self.q_mvar!r}, "
            f"in_service={self.in_service!r}"
            f")"
        )
