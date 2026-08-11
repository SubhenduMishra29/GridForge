"""
GridForge Power Flow Analysis
=============================

File:
    core/analysis/power_flow.py

Purpose:
    Public analysis-level facade for AC power-flow studies.

Architecture:

    Network
        |
        v
    PowerFlowAnalysis
        |
        v
    Numerical Power-Flow Solver
        |
        v
    core/solver/power_flow/

Current numerical solver package:

    core/solver/power_flow/
        __init__.py
        nr_solver.py
        q_limit_handler.py
        solver_options.py
        sparse_solver.py

Responsibilities
----------------
This module is responsible for:

    - validating minimum structural requirements
    - maintaining the Network as the authoritative bus-index owner
    - ensuring the Network Ybus is available and current
    - creating and invoking the numerical power-flow solver
    - passing solver options to the numerical engine
    - storing the latest power-flow result on the Network
    - exposing the latest result through the public analysis API

This module does NOT:

    - build Ybus directly
    - calculate power mismatches
    - assemble Jacobians
    - solve linear systems
    - perform Newton-Raphson iterations
    - perform PV/PQ switching
    - implement numerical power-flow mathematics

Numerical responsibilities remain exclusively in:

    core/solver/power_flow/

Canonical GridForge terminology:

    "Power Flow"
"""

from __future__ import annotations

from typing import Any, Optional


class PowerFlowAnalysis:
    """
    Public facade for AC power-flow studies.

    Parameters
    ----------
    network:
        GridForge Network instance.

    options:
        Optional SolverOptions instance belonging to the
        numerical power-flow solver package.

    Notes
    -----
    The analysis layer contains no numerical power-flow
    mathematics.

    The Network remains authoritative for:

        - buses
        - bus indexing
        - electrical network state
        - Ybus lifecycle
        - latest power-flow result

    The numerical solver remains authoritative for:

        - mismatch calculation
        - Jacobian construction
        - numerical solution
        - convergence logic
        - reactive-power limit handling
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        network: Any,
        options: Optional[Any] = None,
    ) -> None:

        self.network = network

        self._validate_network()

        # ---------------------------------------------------------
        # Solver options belong to the numerical solver layer.
        # ---------------------------------------------------------

        if options is None:

            from core.solver.power_flow.solver_options import (
                SolverOptions,
            )

            options = SolverOptions()

        self.options = options

        # ---------------------------------------------------------
        # Numerical solver.
        #
        # IMPORTANT:
        # Current GridForge solver module is nr_solver.py.
        # ---------------------------------------------------------

        from core.solver.power_flow.nr_solver import (
            NewtonRaphsonSolver,
        )

        self.solver = NewtonRaphsonSolver(
            network=self.network,
            options=self.options,
        )

    # =============================================================
    # PUBLIC API
    # =============================================================

    def solve(self) -> Any:
        """
        Execute the AC power-flow study.

        Returns
        -------
        Any
            Result returned by the numerical power-flow solver.

        Notes
        -----
        No numerical power-flow calculation is performed here.
        """

        # ---------------------------------------------------------
        # Revalidate current Network state.
        #
        # The Network may have changed after construction of this
        # analysis object.
        # ---------------------------------------------------------

        self._validate_network()

        # ---------------------------------------------------------
        # Network owns the authoritative bus index.
        # ---------------------------------------------------------

        self.network.rebuild_bus_index()

        # ---------------------------------------------------------
        # Ensure Ybus is available and current.
        #
        # Ybus construction remains outside this analysis layer.
        # ---------------------------------------------------------

        self._ensure_ybus()

        # ---------------------------------------------------------
        # Execute numerical solver.
        # ---------------------------------------------------------

        result = self.solver.solve()

        # ---------------------------------------------------------
        # Store latest result on authoritative Network.
        # ---------------------------------------------------------

        self.network.power_flow_result = result

        return result

    # =============================================================
    # NETWORK PREPARATION
    # =============================================================

    def _ensure_ybus(self) -> None:
        """
        Ensure that the Network has a current Ybus.

        This method only delegates Ybus construction to the
        authoritative Network interface.

        No Ybus mathematics is implemented here.
        """

        ybus = getattr(
            self.network,
            "Ybus",
            None,
        )

        ybus_dirty = getattr(
            self.network,
            "_ybus_dirty",
            True,
        )

        if ybus is None or ybus_dirty:

            self.network.build_ybus()

    # =============================================================
    # NETWORK VALIDATION
    # =============================================================

    def _validate_network(self) -> None:
        """
        Validate minimum structural requirements for Power Flow.

        This is structural validation only.

        Numerical and electrical validation belongs to the
        solver layer.
        """

        if self.network is None:
            raise ValueError(
                "Power Flow requires a valid Network object."
            )

        # ---------------------------------------------------------
        # Required Network interfaces.
        # ---------------------------------------------------------

        required_attributes = (
            "buses",
            "lines",
            "transformers",
            "generators",
            "bus_index",
            "build_ybus",
            "rebuild_bus_index",
        )

        for attribute in required_attributes:

            if not hasattr(
                self.network,
                attribute,
            ):
                raise ValueError(
                    "Network is missing required "
                    f"attribute or method '{attribute}'."
                )

        # ---------------------------------------------------------
        # At least one bus is required.
        # ---------------------------------------------------------

        if not self.network.buses:
            raise ValueError(
                "Power Flow requires at least one bus."
            )

        # ---------------------------------------------------------
        # Validate bus structure.
        # ---------------------------------------------------------

        bus_ids = []

        for bus in self.network.buses:

            if not hasattr(bus, "id"):
                raise ValueError(
                    "Bus is missing required attribute 'id'."
                )

            if bus.id is None:
                raise ValueError(
                    "Bus ID cannot be None."
                )

            bus_ids.append(bus.id)

            if not hasattr(bus, "type"):
                raise ValueError(
                    f"Bus '{bus.id}' is missing required "
                    "attribute 'type'."
                )

            if not hasattr(bus, "V"):
                raise ValueError(
                    f"Bus '{bus.id}' is missing required "
                    "voltage magnitude 'V'."
                )

            if not hasattr(bus, "theta"):
                raise ValueError(
                    f"Bus '{bus.id}' is missing required "
                    "voltage angle 'theta'."
                )

            if not hasattr(bus, "P_spec"):
                raise ValueError(
                    f"Bus '{bus.id}' is missing required "
                    "specified active power 'P_spec'."
                )

            if not hasattr(bus, "Q_spec"):
                raise ValueError(
                    f"Bus '{bus.id}' is missing required "
                    "specified reactive power 'Q_spec'."
                )

        # ---------------------------------------------------------
        # Bus IDs must be unique.
        # ---------------------------------------------------------

        if len(bus_ids) != len(set(bus_ids)):
            raise ValueError(
                "Network contains duplicate bus IDs."
            )

        # ---------------------------------------------------------
        # Rebuild authoritative bus index.
        # ---------------------------------------------------------

        self.network.rebuild_bus_index()

        # ---------------------------------------------------------
        # Verify index consistency.
        # ---------------------------------------------------------

        if len(self.network.bus_index) != len(
            self.network.buses
        ):
            raise ValueError(
                "Network bus index is inconsistent with "
                "the current bus collection."
            )

        for index, bus in enumerate(
            self.network.buses
        ):

            mapped_index = self.network.bus_index.get(
                bus.id
            )

            if mapped_index != index:
                raise ValueError(
                    f"Invalid bus index mapping for bus "
                    f"'{bus.id}'."
                )

    # =============================================================
    # RESULT ACCESS
    # =============================================================

    @property
    def result(self) -> Optional[Any]:
        """
        Return the latest power-flow result.

        Returns
        -------
        Any or None
            Latest numerical solver result, or None when no
            result has been produced.
        """

        return getattr(
            self.network,
            "power_flow_result",
            None,
        )


__all__ = [
    "PowerFlowAnalysis",
]
