# ============================================================
# File: core/model/branch.py
# GridForge V2 — Branch Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Branch
=====================

Base model for two-terminal electrical branch equipment.

Architecture
------------

    ElectricalObject
          │
          ▼
        Branch
       /      \
      ▼        ▼
   Terminal  Terminal
      │          │
      ▼          ▼
  endpoint    endpoint
      │          │
      └────┬─────┘
           ▼
        Network
           │
           ▼
       Topology

Branch owns exactly two authoritative Terminal objects.

Endpoint ownership
------------------

    Branch
      │
      ├── from_terminal ── owns endpoint
      │
      └── to_terminal ─── owns endpoint

Branch MUST NOT maintain a second copy of either endpoint.

Network responsibility
----------------------

Branch does not:

    - resolve endpoints into Network topology;
    - resolve endpoints into Bus objects;
    - maintain Network collections;
    - construct Y-bus matrices;
    - assign solver indices;
    - maintain solved numerical state;
    - execute protection logic;
    - execute control logic;
    - maintain UI/SLD state.

Terminal responsibility
-----------------------

Branch delegates endpoint mutation exclusively to:

    Terminal.attach()
    Terminal.detach()

The canonical Terminal API is:

    owner
    role
    endpoint
    attach()
    detach()
    is_connected
    validate()

Validation
----------

ElectricalObject defines the public validation entry point:

    validate()

Branch extends the common parameter-validation contract through:

    validate_parameters()

Specialized subclasses such as Line, Cable, and Transformer
may override validate_parameters() and must call:

    Branch.validate_parameters(self)

before validating their own parameters.

Construction
------------

Branch creates its authoritative terminals during construction.

Optional endpoint references may be supplied during construction
and are attached through Terminal.attach().

Branch intentionally does not invoke the polymorphic public
validate() method during construction because subclasses may not
yet have initialized their own state.

The complete concrete object is validated through validate() after
construction.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Branch(ElectricalObject):
    """
    Base class for two-terminal electrical branch equipment.

    A Branch owns exactly two authoritative terminals:

        from_terminal
        to_terminal

    Endpoint state is stored exclusively by those terminals.
    """

    __slots__ = (
        "_from_terminal",
        "_to_terminal",
        "_r",
        "_x",
        "_b",
        "_rate_mva",
        "_in_service",
    )

    def __init__(
        self,
        *,
        id: str,
        endpoint_from: Any | None = None,
        endpoint_to: Any | None = None,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        name: str | None = None,
        rate_mva: float | None = None,
        in_service: bool = True,
    ) -> None:
        """
        Construct a two-terminal Branch.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        endpoint_from:
            Optional endpoint for the FROM terminal.

        endpoint_to:
            Optional endpoint for the TO terminal.

        r:
            Series resistance.

        x:
            Series reactance.

        b:
            Total shunt susceptance.

        name:
            Human-readable branch name.

        rate_mva:
            Optional continuous apparent-power rating in MVA.

        in_service:
            Operational state.

        Notes
        -----
        Terminal objects are always created internally and owned
        by this Branch.

        Endpoint references are attached through Terminal.attach().
        """

        super().__init__(
            id=id,
            name=name,
        )

        # --------------------------------------------------------
        # Authoritative terminals
        # --------------------------------------------------------

        self._from_terminal = Terminal(
            owner=self,
            role="FROM",
        )

        self._to_terminal = Terminal(
            owner=self,
            role="TO",
        )

        # --------------------------------------------------------
        # Generic branch electrical parameters
        # --------------------------------------------------------

        self._r = self._coerce_numeric(
            r,
            "r",
        )

        self._x = self._coerce_numeric(
            x,
            "x",
        )

        self._b = self._coerce_numeric(
            b,
            "b",
        )

        if rate_mva is not None:
            rate_mva = self._coerce_numeric(
                rate_mva,
                "rate_mva",
            )

            if rate_mva <= 0.0:
                raise ValueError(
                    "rate_mva must be positive when provided."
                )

        self._rate_mva = rate_mva
        self._in_service = bool(in_service)

        # --------------------------------------------------------
        # Optional initial endpoint references
        # --------------------------------------------------------

        if endpoint_from is not None:
            self._from_terminal.attach(
                endpoint_from
            )

        if endpoint_to is not None:
            self._to_terminal.attach(
                endpoint_to
            )

        # IMPORTANT:
        #
        # Do not call self.validate() here.
        #
        # Subclasses may override validate_parameters() and their
        # own state may not yet exist during Branch construction.
        #
        # Complete validation is performed after concrete
        # construction through the public validate() entry point.

    # ============================================================
    # TERMINALS
    # ============================================================

    @property
    def from_terminal(self) -> Terminal:
        """
        Return the authoritative FROM terminal.
        """
        return self._from_terminal

    @property
    def to_terminal(self) -> Terminal:
        """
        Return the authoritative TO terminal.
        """
        return self._to_terminal

    # ============================================================
    # ENDPOINTS
    # ============================================================

    @property
    def from_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by the FROM terminal.

        This is a convenience accessor only.
        """
        return self._from_terminal.endpoint

    @property
    def to_endpoint(self) -> Any | None:
        """
        Return the endpoint owned by the TO terminal.

        This is a convenience accessor only.
        """
        return self._to_terminal.endpoint

    # ============================================================
    # CONNECTION STATE
    # ============================================================

    @property
    def is_connected(self) -> bool:
        """
        Return True when both terminals have endpoints.
        """
        return (
            self._from_terminal.is_connected
            and self._to_terminal.is_connected
        )

    # ============================================================
    # ENDPOINT MUTATION
    # ============================================================

    def set_from_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to the FROM terminal.

        This method is a Branch-level convenience operation.
        The Terminal remains the authoritative endpoint owner.
        """
        self._from_terminal.attach(
            endpoint
        )

    def set_to_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach an endpoint to the TO terminal.

        This method is a Branch-level convenience operation.
        """
        self._to_terminal.attach(
            endpoint
        )

    def connect(
        self,
        from_endpoint: Any,
        to_endpoint: Any,
    ) -> None:
        """
        Attach both Branch endpoints.

        Only Terminal.attach() performs the actual endpoint state
        mutation.
        """
        self._from_terminal.attach(
            from_endpoint
        )

        self._to_terminal.attach(
            to_endpoint
        )

    def disconnect(self) -> None:
        """
        Detach both Branch terminals.

        Network topology is not modified by this method.
        """
        self._from_terminal.detach()
        self._to_terminal.detach()

    # ============================================================
    # ELECTRICAL PARAMETERS
    # ============================================================

    @property
    def r(self) -> float:
        """
        Return series resistance.
        """
        return self._r

    @r.setter
    def r(
        self,
        value: float,
    ) -> None:
        self._r = self._coerce_numeric(
            value,
            "r",
        )

    @property
    def x(self) -> float:
        """
        Return series reactance.
        """
        return self._x

    @x.setter
    def x(
        self,
        value: float,
    ) -> None:
        self._x = self._coerce_numeric(
            value,
            "x",
        )

    @property
    def b(self) -> float:
        """
        Return total shunt susceptance.
        """
        return self._b

    @b.setter
    def b(
        self,
        value: float,
    ) -> None:
        self._b = self._coerce_numeric(
            value,
            "b",
        )

    @property
    def rate_mva(self) -> float | None:
        """
        Return continuous MVA rating.
        """
        return self._rate_mva

    @rate_mva.setter
    def rate_mva(
        self,
        value: float | None,
    ) -> None:
        if value is None:
            self._rate_mva = None
            return

        value = self._coerce_numeric(
            value,
            "rate_mva",
        )

        if value <= 0.0:
            raise ValueError(
                "rate_mva must be positive when provided."
            )

        self._rate_mva = value

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @property
    def in_service(self) -> bool:
        """
        Return whether the Branch is in service.
        """
        return self._in_service

    @in_service.setter
    def in_service(
        self,
        value: bool,
    ) -> None:
        self._in_service = bool(value)

    # ============================================================
    # ELECTRICAL HELPERS
    # ============================================================

    @property
    def impedance(self) -> complex:
        """
        Return series impedance:

            Z = R + jX
        """
        return complex(
            self._r,
            self._x,
        )

    @property
    def admittance(self) -> complex:
        """
        Return series admittance:

            Y = 1 / Z
        """
        z = self.impedance

        if z == 0.0 + 0.0j:
            raise ZeroDivisionError(
                "Branch series impedance cannot be zero."
            )

        return 1.0 / z

    @property
    def shunt_admittance(self) -> complex:
        """
        Return total shunt admittance:

            Ysh = jB
        """
        return complex(
            0.0,
            self._b,
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Branch-owned parameters.

        This method intentionally does not call self.validate()
        and therefore does not create recursive validation.

        Subclasses should call this method before validating their
        own parameters.
        """

        # --------------------------------------------------------
        # Base ElectricalObject validation
        # --------------------------------------------------------

        super().validate_parameters()

        # --------------------------------------------------------
        # Terminal ownership
        # --------------------------------------------------------

        if self._from_terminal.owner is not self:
            raise ValueError(
                "FROM terminal must be owned by this Branch."
            )

        if self._to_terminal.owner is not self:
            raise ValueError(
                "TO terminal must be owned by this Branch."
            )

        # --------------------------------------------------------
        # Terminal roles
        # --------------------------------------------------------

        if self._from_terminal.role != "FROM":
            raise ValueError(
                "FROM terminal must have role 'FROM'."
            )

        if self._to_terminal.role != "TO":
            raise ValueError(
                "TO terminal must have role 'TO'."
            )

        # --------------------------------------------------------
        # Terminal-local validation
        # --------------------------------------------------------

        self._from_terminal.validate()
        self._to_terminal.validate()

        # --------------------------------------------------------
        # Branch rating
        # --------------------------------------------------------

        if (
            self._rate_mva is not None
            and self._rate_mva <= 0.0
        ):
            raise ValueError(
                "rate_mva must be positive when provided."
            )

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return Branch-local diagnostics.

        No Network topology or Bus resolution is included.
        """
        summary = super().summary()

        from_endpoint = self.from_endpoint
        to_endpoint = self.to_endpoint

        summary.update(
            {
                "from_endpoint": (
                    getattr(
                        from_endpoint,
                        "id",
                        None,
                    )
                    if from_endpoint is not None
                    else None
                ),
                "to_endpoint": (
                    getattr(
                        to_endpoint,
                        "id",
                        None,
                    )
                    if to_endpoint is not None
                    else None
                ),
                "connected": self.is_connected,
                "r": self._r,
                "x": self._x,
                "b": self._b,
                "rate_mva": self._rate_mva,
                "in_service": self._in_service,
            }
        )

        return summary

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """
        from_endpoint = self.from_endpoint
        to_endpoint = self.to_endpoint

        from_id = (
            getattr(
                from_endpoint,
                "id",
                None,
            )
            if from_endpoint is not None
            else None
        )

        to_id = (
            getattr(
                to_endpoint,
                "id",
                None,
            )
            if to_endpoint is not None
            else None
        )

        return (
            f"{type(self).__name__}("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"from_endpoint={from_id!r}, "
            f"to_endpoint={to_id!r}, "
            f"in_service={self.in_service!r}"
            f")"
        )

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    @staticmethod
    def _coerce_numeric(
        value: Any,
        name: str,
    ) -> float:
        """
        Convert a value to float and reject non-numeric values.
        """
        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc


__all__ = [
    "Branch",
]
