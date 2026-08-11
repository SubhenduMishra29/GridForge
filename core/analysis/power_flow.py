"""
GridForge Power Flow Analysis
=============================

File:
    core/analysis/power_flow.py

Purpose:
    Public analysis-level facade for AC power-flow studies.

Architecture:
    Network
        │
        ▼
    PowerFlowAnalysis
        │
        ▼
    Numerical Power-Flow Solver
        │
        ▼
    core/solver/power_flow/
        ├── solver_options.py
        ├── mismatch.py
        ├── jacobian.py
        ├── sparse_solver.py
        ├── q_limit_handler.py
        └── newton_raphson.py

Responsibilities:
    - Validate minimum structural requirements for power flow.
    - Keep the Network bus index authoritative.
    - Ensure Ybus exists and is current.
    - Create and invoke the numerical solver.
    - Pass solver options to the numerical engine.
    - Store and return the latest numerical result.

Does NOT:
    - Build Ybus directly.
    - Calculate power mismatches.
    - Assemble the Jacobian.
    - Solve linear systems.
    - Perform Newton-Raphson iterations.
    - Implement PV/PQ switching.
    - Perform numerical power-flow mathematics.

Numerical responsibilities belong exclusively to:

    core/solver/power_flow/

Canonical GridForge terminology:
    "Power Flow"
"""

from __future__ import annotations

from typing import Any, Optional


class PowerFlowAnalysis:
    """
    Public analysis facade for AC power-flow studies.

    Parameters
    ----------
    network:
        GridForge Network instance.

    options:
        Optional instance of the numerical solver's SolverOptions.

    Notes
    -----
    This class contains no numerical power-flow mathematics.

    It provides the analysis-level boundary between the
    authoritative Network object and the numerical solver stack.
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

        # Validate the initial Network state before constructing
        # the numerical engine.
        self._validate_network()

        # Solver configuration belongs to the numerical solver
        # package. The analysis layer only owns the configuration
        # reference and passes it downstream.
        if options is None:
            from core.solver.power_flow.solver_options import (
                SolverOptions,
            )

            options = SolverOptions()

        self.options = options

        # Lazy import keeps the numerical backend out of the module
        # import path until a Power Flow analysis is instantiated.
        from core.solver.power_flow.newton_raphson import (
            NewtonRaphsonSolver,
        )

        self.solver = NewtonRaphsonSolver(
            network=self.network,
            options=self.options,
        )

    # =============================================================
    # PUBLIC API
    # =============================================================

    def solve(self) -> dict:
        """
        Execute the AC power-flow study.

        Returns
        -------
        dict
            Structured result returned by the numerical solver.

        Notes
        -----
        The Network remains authoritative for:

            - bus collection
            - bus indexing
            - Ybus lifecycle
            - network state
            - latest power-flow result

        The numerical solver remains authoritative for:

            - mismatch calculation
            - Jacobian assembly
            - numerical solution
            - convergence logic
            - PV/PQ handling
        """

        # The Network may have been modified after this analysis
        # object was created. Revalidate the current structure.
        self._validate_network()

        # ---------------------------------------------------------
        # Ensure authoritative Network bus index is current.
        # ---------------------------------------------------------

        self.network.rebuild_bus_index()

        # ---------------------------------------------------------
        # Ensure Ybus exists and is current.
        #
        # Ybus construction remains exclusively owned by the
        # Network layer / Ybus builder.
        # ---------------------------------------------------------

        self._ensure_ybus()

        # ---------------------------------------------------------
        # Execute the numerical solution.
        # ---------------------------------------------------------

        result = self.solver.solve()

        # ---------------------------------------------------------
        # Store the authoritative latest result on Network.
        # ---------------------------------------------------------

        self.network.power_flow_result = result

        return result

    # =============================================================
    # NETWORK PREPARATION
    # =============================================================

    def _ensure_ybus(self) -> None:
        """
        Ensure that the Network has a current Ybus.

        This method does not construct Ybus itself. It delegates
        construction to the authoritative Network interface.
        """

        ybus = getattr(self.network, "Ybus", None)
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
        Validate the minimum structural requirements for
        power-flow analysis.

        This method performs structural validation only.

        Numerical validation belongs to the solver layer.
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
            if not hasattr(self.network, attribute):
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
        # Validate bus identifiers and required electrical state.
        #
        # The frozen GridForge Bus model remains the authoritative
        # representation of bus electrical state.
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
        # Rebuild the authoritative Network bus index.
        #
        # Network owns indexing. The analysis layer never creates
        # or maintains a parallel index.
        # ---------------------------------------------------------

        self.network.rebuild_bus_index()

        # ---------------------------------------------------------
        # Verify that every bus is represented correctly.
        # ---------------------------------------------------------

        if len(self.network.bus_index) != len(
            self.network.buses
        ):
            raise ValueError(
                "Network bus index is inconsistent with "
                "the current bus collection."
            )

        for index, bus in enumerate(self.network.buses):

            mapped_index = self.network.bus_index.get(bus.id)

            if mapped_index != index:
                raise ValueError(
                    f"Invalid bus index mapping for bus "
                    f"'{bus.id}'."
                )

    # =============================================================
    # RESULT ACCESS
    # =============================================================

    @property
    def result(self) -> Optional[dict]:
        """
        Return the latest power-flow result stored on Network.

        Returns
        -------
        dict or None
            Latest power-flow result, or None if no study has
            successfully produced a result.
        """

        return getattr(
            self.network,
            "power_flow_result",
            None,
        )


# =============================================================
# BACKWARD COMPATIBILITY
# =============================================================
#
# Earlier GridForge code may use:
#
#     PowerFlowSolver(network)
#
# The analysis facade is now correctly named PowerFlowAnalysis,
# but the old public name is retained as an alias so that existing
# callers do not need to be rewritten immediately.
#
# The numerical solver remains:
#
#     core.solver.power_flow.newton_raphson.NewtonRaphsonSolver
#
# Therefore there is no ambiguity at the implementation level.
# =============================================================

PowerFlowSolver = PowerFlowAnalysis


__all__ = [
    "PowerFlowAnalysis",
    "PowerFlowSolver",
]
