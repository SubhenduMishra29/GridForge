# ============================================================
# File: core/model/cable.py
# GridForge V2 — Cable Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Cable Model
==========================

Authoritative electrical cable model.

Architecture
------------

    ElectricalObject
          |
        Branch
       /      \
 FROM Terminal  TO Terminal
          |
         Cable

Cable is a specialized two-terminal Branch.

The Cable owns only cable-domain electrical and engineering
parameters.  Physical connectivity is owned by the inherited
Branch Terminals.

Authoritative connectivity contract
------------------------------------

    cable.from_terminal
    cable.to_terminal

    cable.from_endpoint
    cable.to_endpoint

    cable.connect_from(endpoint)
    cable.connect_to(endpoint)

    cable.disconnect_from()
    cable.disconnect_to()

The Terminal object is the sole authority for endpoint state.

Cable does NOT own:

    - Network topology
    - Bus registration
    - Y-bus assembly
    - power-flow solution state
    - protection execution
    - SLD geometry
    - canvas state
    - renderer state
    - persistence

Electrical model
----------------

The positive-sequence series impedance is:

    Z1 = R1 + jX1

The zero-sequence series impedance is:

    Z0 = R0 + jX0

The positive-sequence total charging susceptance is:

    B1 = B1_total

The zero-sequence total charging susceptance is:

    B0 = B0_total

For the positive-sequence pi model:

    Yseries = 1 / Z1
    Yshunt  = j B1
    Yhalf   = j B1 / 2

The zero-sequence quantities are exposed separately for
unbalanced and fault-analysis layers.

The model deliberately does not construct Network/Y-bus
objects.  Those responsibilities belong to Core Network and
solver/analysis layers.
"""

from __future__ import annotations

import math
from typing import Any

from .branch import Branch


class Cable(Branch):
    """
    Two-terminal underground/submarine/special cable model.

    The class preserves the Branch two-terminal electrical
    contract while adding cable-specific sequence, physical,
    thermal and engineering parameters.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    r:
        Positive-sequence series resistance in per-unit.

    x:
        Positive-sequence series reactance in per-unit.

    b:
        Positive-sequence total charging susceptance in per-unit.

    r0:
        Zero-sequence series resistance in per-unit.

    x0:
        Zero-sequence series reactance in per-unit.

    b0:
        Zero-sequence total charging susceptance in per-unit.

    length_km:
        Cable length in kilometres.

    rated_voltage_kv:
        Rated line-to-line voltage in kV.

    rated_current_a:
        Continuous current rating in amperes.

    thermal_limit_mva:
        Continuous apparent-power thermal limit in MVA.

    conductor_count:
        Number of parallel conductors per phase.

    name:
        Human-readable cable name.

    in_service:
        Initial operational state.
    """

    TYPE = "CABLE"

    def __init__(
        self,
        id: str,
        *,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        r0: float | None = None,
        x0: float | None = None,
        b0: float | None = None,
        length_km: float = 0.0,
        rated_voltage_kv: float = 0.0,
        rated_current_a: float = 0.0,
        thermal_limit_mva: float = 0.0,
        conductor_count: int = 1,
        name: str = "",
        in_service: bool = True,
        from_endpoint: Any = None,
        to_endpoint: Any = None,
    ) -> None:
        """
        Construct a Cable.

        ``r``, ``x`` and ``b`` are the canonical positive-sequence
        Branch parameters.

        Zero-sequence parameters default to their positive-sequence
        counterparts when omitted.

        Connectivity is delegated entirely to Branch/Terminal.
        """

        # ========================================================
        # DEFAULT ZERO-SEQUENCE PARAMETERS
        # ========================================================

        if r0 is None:
            r0 = r

        if x0 is None:
            x0 = x

        if b0 is None:
            b0 = b

        # ========================================================
        # BRANCH INITIALIZATION
        # ========================================================

        super().__init__(
            id=id,
            r=r,
            x=x,
            b=b,
            name=name,
            in_service=in_service,
            from_endpoint=from_endpoint,
            to_endpoint=to_endpoint,
        )

        # ========================================================
        # ZERO-SEQUENCE PARAMETERS
        # ========================================================

        self.r0 = self._validate_finite(
            r0,
            "r0",
        )

        self.x0 = self._validate_finite(
            x0,
            "x0",
        )

        self.b0 = self._validate_finite(
            b0,
            "b0",
        )

        # ========================================================
        # PHYSICAL PARAMETERS
        # ========================================================

        self.length_km = self._validate_non_negative(
            length_km,
            "length_km",
        )

        self.rated_voltage_kv = (
            self._validate_non_negative(
                rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        self.rated_current_a = (
            self._validate_non_negative(
                rated_current_a,
                "rated_current_a",
            )
        )

        self.thermal_limit_mva = (
            self._validate_non_negative(
                thermal_limit_mva,
                "thermal_limit_mva",
            )
        )

        if not isinstance(
            conductor_count,
            int,
        ):
            raise TypeError(
                "conductor_count must be an integer."
            )

        if conductor_count < 1:
            raise ValueError(
                "conductor_count must be at least 1."
            )

        self.conductor_count = conductor_count

        # ========================================================
        # FINAL VALIDATION
        # ========================================================

        self.validate()

    # ============================================================
    # IDENTITY
    # ============================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # ============================================================
    # POSITIVE-SEQUENCE PARAMETERS
    # ============================================================

    @property
    def resistance(self) -> float:
        """Return positive-sequence resistance."""

        return self.r

    @resistance.setter
    def resistance(
        self,
        value: float,
    ) -> None:
        self.r = self._validate_finite(
            value,
            "resistance",
        )

    @property
    def reactance(self) -> float:
        """Return positive-sequence reactance."""

        return self.x

    @reactance.setter
    def reactance(
        self,
        value: float,
    ) -> None:
        self.x = self._validate_finite(
            value,
            "reactance",
        )

    @property
    def shunt_susceptance(self) -> float:
        """Return positive-sequence total charging susceptance."""

        return self.b

    @shunt_susceptance.setter
    def shunt_susceptance(
        self,
        value: float,
    ) -> None:
        self.b = self._validate_finite(
            value,
            "shunt_susceptance",
        )

    # ============================================================
    # ZERO-SEQUENCE ALIASES
    # ============================================================

    @property
    def zero_sequence_resistance(self) -> float:
        """Return zero-sequence resistance."""

        return self.r0

    @zero_sequence_resistance.setter
    def zero_sequence_resistance(
        self,
        value: float,
    ) -> None:
        self.r0 = self._validate_finite(
            value,
            "zero_sequence_resistance",
        )

    @property
    def zero_sequence_reactance(self) -> float:
        """Return zero-sequence reactance."""

        return self.x0

    @zero_sequence_reactance.setter
    def zero_sequence_reactance(
        self,
        value: float,
    ) -> None:
        self.x0 = self._validate_finite(
            value,
            "zero_sequence_reactance",
        )

    @property
    def zero_sequence_susceptance(self) -> float:
        """Return zero-sequence total charging susceptance."""

        return self.b0

    @zero_sequence_susceptance.setter
    def zero_sequence_susceptance(
        self,
        value: float,
    ) -> None:
        self.b0 = self._validate_finite(
            value,
            "zero_sequence_susceptance",
        )

    # ============================================================
    # IMPEDANCE
    # ============================================================

    @property
    def impedance(self) -> complex:
        """
        Return positive-sequence series impedance.

            Z1 = R1 + jX1
        """

        return complex(
            self.r,
            self.x,
        )

    @property
    def zero_sequence_impedance(self) -> complex:
        """
        Return zero-sequence series impedance.

            Z0 = R0 + jX0
        """

        return complex(
            self.r0,
            self.x0,
        )

    @property
    def z1(self) -> complex:
        """Canonical positive-sequence impedance."""

        return self.impedance

    @property
    def z0(self) -> complex:
        """Canonical zero-sequence impedance."""

        return self.zero_sequence_impedance

    # ============================================================
    # SERIES ADMITTANCE
    # ============================================================

    @property
    def series_admittance(self) -> complex:
        """
        Return positive-sequence series admittance.

            Y1 = 1 / Z1
        """

        z = self.impedance

        if abs(z) == 0.0:
            raise ZeroDivisionError(
                f"Cable '{self.id}' has zero positive-sequence "
                "series impedance."
            )

        return 1.0 / z

    @property
    def y1(self) -> complex:
        """Canonical positive-sequence series admittance."""

        return self.series_admittance

    @property
    def zero_sequence_series_admittance(self) -> complex:
        """
        Return zero-sequence series admittance.

            Y0 = 1 / Z0
        """

        z = self.zero_sequence_impedance

        if abs(z) == 0.0:
            raise ZeroDivisionError(
                f"Cable '{self.id}' has zero zero-sequence "
                "series impedance."
            )

        return 1.0 / z

    @property
    def y0(self) -> complex:
        """Canonical zero-sequence series admittance."""

        return self.zero_sequence_series_admittance

    # ============================================================
    # SHUNT ADMITTANCE
    # ============================================================

    @property
    def shunt_admittance(self) -> complex:
        """
        Return total positive-sequence shunt admittance.

            Yshunt1 = jB1
        """

        return complex(
            0.0,
            self.b,
        )

    @property
    def y_shunt(self) -> complex:
        """Alias for positive-sequence total shunt admittance."""

        return self.shunt_admittance

    @property
    def half_shunt_admittance(self) -> complex:
        """
        Return half of the positive-sequence charging admittance.

            Yhalf1 = jB1 / 2
        """

        return self.shunt_admittance / 2.0

    @property
    def y_half(self) -> complex:
        """Alias for half positive-sequence shunt admittance."""

        return self.half_shunt_admittance

    @property
    def zero_sequence_shunt_admittance(self) -> complex:
        """
        Return total zero-sequence shunt admittance.

            Yshunt0 = jB0
        """

        return complex(
            0.0,
            self.b0,
        )

    @property
    def zero_sequence_half_shunt_admittance(self) -> complex:
        """
        Return half zero-sequence charging admittance.
        """

        return (
            self.zero_sequence_shunt_admittance
            / 2.0
        )

    # ============================================================
    # PI MODEL
    # ============================================================

    @property
    def pi_model(self) -> dict[str, complex]:
        """
        Return the positive-sequence nominal pi-model parameters.

        This is a value representation only.  It does not create
        or modify a Network/Y-bus object.
        """

        return {
            "z_series": self.impedance,
            "y_series": self.series_admittance,
            "y_shunt": self.shunt_admittance,
            "y_half": self.half_shunt_admittance,
        }

    @property
    def zero_sequence_pi_model(
        self,
    ) -> dict[str, complex]:
        """
        Return zero-sequence nominal pi-model parameters.
        """

        return {
            "z_series":
                self.zero_sequence_impedance,
            "y_series":
                self.zero_sequence_series_admittance,
            "y_shunt":
                self.zero_sequence_shunt_admittance,
            "y_half":
                self.zero_sequence_half_shunt_admittance,
        }

    # ============================================================
    # ENGINEERING PARAMETERS
    # ============================================================

    @property
    def length_m(self) -> float:
        """Return cable length in metres."""

        return self.length_km * 1000.0

    @length_m.setter
    def length_m(
        self,
        value: float,
    ) -> None:
        self.length_km = (
            self._validate_non_negative(
                value,
                "length_m",
            )
            / 1000.0
        )

    @property
    def rated_apparent_power_mva(self) -> float:
        """
        Return the thermal apparent-power rating.

        If an explicit thermal_limit_mva is available, it is
        authoritative.  Otherwise, when voltage and current ratings
        are available, derive:

            S = sqrt(3) V I / 1000
        """

        if self.thermal_limit_mva > 0.0:
            return self.thermal_limit_mva

        if (
            self.rated_voltage_kv > 0.0
            and self.rated_current_a > 0.0
        ):
            return (
                math.sqrt(3.0)
                * self.rated_voltage_kv
                * self.rated_current_a
                / 1000.0
            )

        return 0.0

    @property
    def ampacity_a(self) -> float:
        """Return continuous current rating."""

        return self.rated_current_a

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @property
    def is_in_service(self) -> bool:
        """Return whether the Cable is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the Cable is out of service."""

        return not self.in_service

    def put_in_service(self) -> None:
        """Place Cable in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take Cable out of service."""

        self.in_service = False

    # ============================================================
    # PARAMETER VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Cable-local parameters.

        Zero series impedance is not permitted because the Cable
        is a physical branch and its series admittance must remain
        mathematically defined.
        """

        # --------------------------------------------------------
        # Parent Branch validation
        # --------------------------------------------------------

        super().validate_parameters()

        # --------------------------------------------------------
        # Zero sequence
        # --------------------------------------------------------

        self.r0 = self._validate_finite(
            self.r0,
            "r0",
        )

        self.x0 = self._validate_finite(
            self.x0,
            "x0",
        )

        self.b0 = self._validate_finite(
            self.b0,
            "b0",
        )

        # --------------------------------------------------------
        # Physical parameters
        # --------------------------------------------------------

        self.length_km = (
            self._validate_non_negative(
                self.length_km,
                "length_km",
            )
        )

        self.rated_voltage_kv = (
            self._validate_non_negative(
                self.rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        self.rated_current_a = (
            self._validate_non_negative(
                self.rated_current_a,
                "rated_current_a",
            )
        )

        self.thermal_limit_mva = (
            self._validate_non_negative(
                self.thermal_limit_mva,
                "thermal_limit_mva",
            )
        )

        if not isinstance(
            self.conductor_count,
            int,
        ):
            raise TypeError(
                "conductor_count must be an integer."
            )

        if self.conductor_count < 1:
            raise ValueError(
                "conductor_count must be at least 1."
            )

        # --------------------------------------------------------
        # Series impedance
        # --------------------------------------------------------

        if abs(self.impedance) == 0.0:
            raise ValueError(
                f"Cable '{self.id}' must have non-zero "
                "positive-sequence series impedance."
            )

        if (
            self.r0 == 0.0
            and self.x0 == 0.0
        ):
            raise ValueError(
                f"Cable '{self.id}' must have non-zero "
                "zero-sequence series impedance."
            )

        return True

    # ============================================================
    # COMPLETE VALIDATION
    # ============================================================

    def validate(self) -> bool:
        """
        Validate the complete Cable.

        Terminal and topology validation remains delegated to
        Branch and Terminal.
        """

        self.validate_parameters()

        return super().validate()

    # ============================================================
    # ENGINEERING SUMMARY
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return a structured engineering summary.

        The summary contains only model-owned state and derived
        electrical values.
        """

        from_endpoint = self.from_endpoint
        to_endpoint = self.to_endpoint

        from_id = None
        to_id = None

        if from_endpoint is not None:
            from_id = getattr(
                from_endpoint,
                "id",
                from_endpoint,
            )

        if to_endpoint is not None:
            to_id = getattr(
                to_endpoint,
                "id",
                to_endpoint,
            )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "from_endpoint": from_id,
            "to_endpoint": to_id,

            "from_connected":
                self.from_terminal.is_connected,
            "to_connected":
                self.to_terminal.is_connected,

            "r": self.r,
            "x": self.x,
            "b": self.b,

            "r0": self.r0,
            "x0": self.x0,
            "b0": self.b0,

            "z1": self.impedance,
            "z0":
                self.zero_sequence_impedance,

            "y1":
                self.series_admittance,
            "y0":
                self.zero_sequence_series_admittance,

            "length_km":
                self.length_km,

            "rated_voltage_kv":
                self.rated_voltage_kv,

            "rated_current_a":
                self.rated_current_a,

            "thermal_limit_mva":
                self.thermal_limit_mva,

            "conductor_count":
                self.conductor_count,

            "in_service":
                self.in_service,
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        return (
            f"<Cable "
            f"id={self.id}, "
            f"Z1={self.impedance!r}, "
            f"Z0={self.zero_sequence_impedance!r}, "
            f"length={self.length_km:.6f} km, "
            f"in_service={self.in_service}>"
        )

    # ============================================================
    # VALIDATION HELPERS
    # ============================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Convert value to float and require finiteness."""

        try:
            numeric = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(
            numeric
        ):
            raise ValueError(
                f"{name} must be finite."
            )

        return numeric

    @classmethod
    def _validate_non_negative(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Convert value to float and require >= 0."""

        numeric = cls._validate_finite(
            value,
            name,
        )

        if numeric < 0.0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        return numeric


__all__ = [
    "Cable",
]
