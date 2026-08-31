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

Branch owns two authoritative Terminal objects.

Branch does NOT:
    - resolve endpoints into Network topology
    - maintain duplicate endpoint state
    - maintain from_bus / to_bus state
    - mutate Network topology
    - construct Y-bus
    - perform numerical analysis
    - manage UI / SLD state
    - execute protection logic

The Terminal object is the sole owner of each endpoint
reference.

Canonical Terminal API
----------------------

    Terminal.attach(endpoint)
    Terminal.detach()
    Terminal.endpoint
    Terminal.is_connected

Branch-level convenience methods delegate exclusively
to the Terminal API.
"""

from __future__ import annotations

from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Branch(ElectricalObject):
    """
    Base class for two-terminal electrical branch equipment.

    A Branch always owns exactly two authoritative terminals:

        from_terminal
        to_terminal

    Endpoint references are stored exclusively by those
    Terminal objects.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable equipment name.

    r:
        Series resistance.

    x:
        Series reactance.

    b:
        Total shunt susceptance.

    rate_mva:
        Continuous apparent-power rating in MVA.

    in_service:
        Whether the equipment participates in service.

    Notes
    -----
    Branch contains generic branch-level electrical parameters.
    Specialized equipment models such as Line, Cable, and
    Transformer extend this class with their own physical
    parameters.
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
        name: str | None = None,
        r: float = 0.0,
        x: float = 0.0,
        b: float = 0.0,
        rate_mva: float | None = None,
        in_service: bool = True,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
        )

        self._from_terminal = Terminal(
            owner=self,
            role="FROM",
        )

        self._to_terminal = Terminal(
            owner=self,
            role="TO",
        )

        self._r = float(r)
        self._x = float(x)
        self._b = float(b)

        if rate_mva is not None and rate_mva <= 0.0:
            raise ValueError("rate_mva must be positive when provided.")

        self._rate_mva = (
            float(rate_mva)
            if rate_mva is not None
            else None
        )

        self._in_service = bool(in_service)

        self.validate()

    # --------------------------------------------------------
    # Terminal access
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Endpoint access
    # --------------------------------------------------------

    @property
    def from_endpoint(self) -> Any | None:
        """
        Return the endpoint attached to the FROM terminal.

        This is a convenience accessor only. The authoritative
        endpoint state is owned by from_terminal.
        """
        return self._from_terminal.endpoint

    @property
    def to_endpoint(self) -> Any | None:
        """
        Return the endpoint attached to the TO terminal.

        This is a convenience accessor only. The authoritative
        endpoint state is owned by to_terminal.
        """
        return self._to_terminal.endpoint

    # --------------------------------------------------------
    # Electrical parameters
    # --------------------------------------------------------

    @property
    def r(self) -> float:
        """Return series resistance."""
        return self._r

    @r.setter
    def r(self, value: float) -> None:
        self._r = float(value)

    @property
    def x(self) -> float:
        """Return series reactance."""
        return self._x

    @x.setter
    def x(self, value: float) -> None:
        self._x = float(value)

    @property
    def b(self) -> float:
        """Return total shunt susceptance."""
        return self._b

    @b.setter
    def b(self, value: float) -> None:
        self._b = float(value)

    @property
    def rate_mva(self) -> float | None:
        """Return continuous MVA rating."""
        return self._rate_mva

    @rate_mva.setter
    def rate_mva(self, value: float | None) -> None:
        if value is not None and value <= 0.0:
            raise ValueError(
                "rate_mva must be positive when provided."
            )

        self._rate_mva = (
            float(value)
            if value is not None
            else None
        )

    # --------------------------------------------------------
    # Service state
    # --------------------------------------------------------

    @property
    def in_service(self) -> bool:
        """Return whether the branch is in service."""
        return self._in_service

    @in_service.setter
    def in_service(self, value: bool) -> None:
        self._in_service = bool(value)

    # --------------------------------------------------------
    # Connection state
    # --------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """
        Return True when both branch terminals are connected.
        """
        return (
            self._from_terminal.is_connected
            and self._to_terminal.is_connected
        )

    # --------------------------------------------------------
    # Endpoint mutation
    # --------------------------------------------------------

    def set_from_endpoint(self, endpoint: Any) -> None:
        """
        Attach an endpoint to the FROM terminal.

        Network topology is not modified here.
        """
        self._from_terminal.attach(endpoint)

    def set_to_endpoint(self, endpoint: Any) -> None:
        """
        Attach an endpoint to the TO terminal.

        Network topology is not modified here.
        """
        self._to_terminal.attach(endpoint)

    def connect(
        self,
        from_endpoint: Any,
        to_endpoint: Any,
    ) -> None:
        """
        Attach both branch terminals.

        This is a Branch-level convenience method that delegates
        endpoint ownership to the canonical Terminal API.

        Parameters
        ----------
        from_endpoint:
            Endpoint for the FROM terminal.

        to_endpoint:
            Endpoint for the TO terminal.
        """
        self._from_terminal.attach(from_endpoint)
        self._to_terminal.attach(to_endpoint)

    def disconnect(self) -> None:
        """
        Detach both branch terminals.

        This operation changes only local model state.
        Network topology interpretation belongs to Network.
        """
        self._from_terminal.detach()
        self._to_terminal.detach()

    # --------------------------------------------------------
    # Electrical helper methods
    # --------------------------------------------------------

    @property
    def impedance(self) -> complex:
        """
        Return the series impedance Z = R + jX.
        """
        return complex(self._r, self._x)

    @property
    def admittance(self) -> complex:
        """
        Return the series admittance Y = 1 / Z.

        Raises
        ------
        ZeroDivisionError
            If both r and x are zero.
        """
        z = self.impedance

        if z == 0:
            raise ZeroDivisionError(
                "Branch series impedance cannot be zero."
            )

        return 1.0 / z

    @property
    def shunt_admittance(self) -> complex:
        """
        Return the total shunt admittance jB.
        """
        return complex(0.0, self._b)

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def validate(self) -> None:
        """
        Validate Branch-local invariants.

        Global topology validation remains the responsibility
        of Network.
        """
        super().validate()

        if self._from_terminal.owner is not self:
            raise ValueError(
                "FROM terminal must be owned by this Branch."
            )

        if self._to_terminal.owner is not self:
            raise ValueError(
                "TO terminal must be owned by this Branch."
            )

        if self._from_terminal.role != "FROM":
            raise ValueError(
                "FROM terminal must have role 'FROM'."
            )

        if self._to_terminal.role != "TO":
            raise ValueError(
                "TO terminal must have role 'TO'."
            )

        self._from_terminal.validate()
        self._to_terminal.validate()

        if self._rate_mva is not None and self._rate_mva <= 0.0:
            raise ValueError(
                "rate_mva must be positive when provided."
            )

    # --------------------------------------------------------
    # Representation
    # --------------------------------------------------------

    def __repr__(self) -> str:
        """
        Return a concise debugging representation.
        """
        return (
            f"{type(self).__name__}("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"from_endpoint={self.from_endpoint!r}, "
            f"to_endpoint={self.to_endpoint!r}, "
            f"in_service={self.in_service!r}"
            f")"
        )
