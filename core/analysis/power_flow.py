```python
"""
GridForge Power Flow Analysis
=============================

File:
    core/analysis/power_flow.py

Purpose:
    Public analysis-level interface for AC power-flow studies.

Architecture:
    Network
        │
        ▼
    PowerFlowSolver
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
    - Validate the minimum structural requirements for power flow.
    - Ensure the Network bus index is current.
    - Ensure Ybus is available and current.
    - Create the numerical power-flow solver.
    - Pass solver options to the numerical engine.
    - Execute the power-flow study.
    - Store and return the numerical result.

Does NOT:
    - Build Ybus directly.
    - Calculate power mismatches.
    - Assemble the Jacobian.
    - Solve linear systems.
    - Perform Newton-Raphson iterations.
    - Implement PV/PQ switching.
    - Perform numerical calculations.

Numerical responsibilities belong exclusively to:

    core/solver/power_flow/

"Power Flow" is the canonical GridForge terminology.
"""

from __future__ import annotations

from typing import Any, Optional


class PowerFlowSolver:
    """
    Public analysis facade for AC power-flow studies.

    Parameters
    ----------
    network:
        GridForge Network instance.

    options:
        Optional SolverOptions instance.

    Notes
    -----
    This class contains no numerical power-flow mathematics.

    It provides the analysis-level boundary between the
    Network model and the numerical solver stack.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        network: Any,
        options: Optional[Any] = None,
    ) -> None:

        self.network = network

        # -----------------------------------------------------
        # Validate network structure.
        # -----------------------------------------------------

        self._validate_network()

        # -----------------------------------------------------
        # Solver configuration.
        #
        # Solver options belong to the numerical solver
        # package, not to the analysis layer.
        # -----------------------------------------------------

        if options is None:

            from core.solver.power_flow.solver_options import (
                SolverOptions
            )

            options = SolverOptions()

        self.options = options

        # -----------------------------------------------------
        # Numerical engine.
        #
        # Lazy import prevents unnecessary solver initialization
        # when only the analysis package is imported.
        # -----------------------------------------------------

        from core.solver.power_flow.newton_raphson import (
            NewtonRaphsonSolver
        )

        self.solver = NewtonRaphsonSolver(
            network=self.network,
            options=self.options,
        )

    # =========================================================
    # PUBLIC API
    # =========================================================

    def solve(self) -> dict:
        """
        Execute the AC power-flow study.

        Returns
        -------
        dict
            Structured result returned by the numerical solver.

        Notes
        -----
        Network owns:

            - bus indexing
            - Ybus construction
            - network state

        Solver owns:

            - mismatch calculation
            - Jacobian assembly
            - numerical solution
            - convergence logic
            - PV/PQ handling
        """

        # -----------------------------------------------------
        # Ensure the authoritative Network bus index exists
        # and corresponds to the current bus collection.
        # -----------------------------------------------------

        self.network.rebuild_bus_index()

        # -----------------------------------------------------
        # Ensure Ybus exists and is current.
        #
        # Ybus construction remains exclusively owned by
        # Network/YBusBuilder.
        # -----------------------------------------------------

        if (
            getattr(self.network, "Ybus", None) is None
            or getattr(self.network, "_ybus_dirty", True)
        ):
            self.network.build_ybus()

        # -----------------------------------------------------
        # Execute numerical solution.
        # -----------------------------------------------------

        result = self.solver.solve()

        # -----------------------------------------------------
        # Store the authoritative latest result on Network.
        # -----------------------------------------------------

        self.network.power_flow_result = result

        return result

    # =========================================================
    # NETWORK VALIDATION
    # =========================================================

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

        # -----------------------------------------------------
        # Required Network interfaces.
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # At least one bus is required.
        # -----------------------------------------------------

        if not self.network.buses:
            raise ValueError(
                "Power Flow requires at least one bus."
            )

        # -----------------------------------------------------
        # Validate bus identifiers and required state fields.
        #
        # The frozen GridForge Bus model is the authoritative
        # electrical bus representation.
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Bus IDs must be unique.
        # -----------------------------------------------------

        if len(bus_ids) != len(set(bus_ids)):
            raise ValueError(
                "Network contains duplicate bus IDs."
            )

        # -----------------------------------------------------
        # Rebuild the authoritative Network index.
        #
        # Network owns bus indexing, therefore the analysis
        # facade delegates this operation rather than
        # implementing its own indexing logic.
        # -----------------------------------------------------

        self.network.rebuild_bus_index()

        # -----------------------------------------------------
        # Verify that every bus is represented in the index.
        # -----------------------------------------------------

        if len(self.network.bus_index) != len(
            self.network.buses
        ):
            raise ValueError(
                "Network bus index is inconsistent with "
                "the current bus collection."
            )

        for index, bus in enumerate(self.network.buses):

            if self.network.bus_index.get(bus.id) != index:
                raise ValueError(
                    f"Invalid bus index mapping for bus "
                    f"'{bus.id}'."
                )

    # =========================================================
    # RESULT ACCESS
    # =========================================================

    @property
    def result(self) -> Optional[dict]:
        """
        Return the latest power-flow result stored on Network.

        Returns
        -------
        dict or None
            Latest power-flow result.
        """

        return getattr(
            self.network,
            "power_flow_result",
            None,
        )


__all__ = [
    "PowerFlowSolver",
]
```
