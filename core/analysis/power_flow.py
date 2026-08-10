# GridForge

# Copyright © 2026 Subhendu Mishra

# All Rights Reserved.

# Proprietary and confidential.

"""
GridForge Power Flow Analysis Interface
=======================================

File:
core/analysis/power_flow.py

## Purpose

Public analysis-level interface for AC power-flow studies.

## Architecture

```
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
```

## Responsibilities

* Validate the network for power-flow analysis.
* Ensure Ybus is available.
* Create the numerical power-flow solver.
* Pass solver options to the numerical engine.
* Execute the power-flow study.
* Return the numerical solver result.

## Does NOT

* Build Ybus directly.
* Calculate bus power directly.
* Assemble the Jacobian.
* Solve linear equations.
* Perform Newton-Raphson iterations.
* Manage PV/PQ switching directly.

Those responsibilities belong to the network and solver layers.

## Important

This module is an ANALYSIS FACADE.

The numerical implementation belongs exclusively to:

```
core/solver/power_flow/
```

"Power Flow" is the canonical GridForge terminology.
The previous load-flow implementation is not duplicated here.
"""

from **future** import annotations

from typing import Any, Optional

class PowerFlowSolver:
"""
Public analysis interface for AC power-flow studies.

```
Parameters
----------
network:
    GridForge Network instance.

options:
    Optional SolverOptions instance.

Notes
-----
This class intentionally contains no numerical power-flow
mathematics. It delegates all numerical work to the solver
layer.
"""

def __init__(
    self,
    network: Any,
    options: Optional[Any] = None,
):
    """
    Initialize the Power Flow analysis interface.
    """

    self.network = network

    # -----------------------------------------------------
    # Validate the network before constructing the solver.
    # -----------------------------------------------------

    self._validate_network()

    # -----------------------------------------------------
    # Solver configuration
    #
    # Numerical options belong to the solver package.
    # -----------------------------------------------------

    if options is None:

        from core.solver.power_flow.solver_options import (
            SolverOptions
        )

        options = SolverOptions()

    self.options = options

    # -----------------------------------------------------
    # Numerical engine
    #
    # Import lazily so that importing the analysis package
    # does not unnecessarily initialize the solver stack.
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

def solve(self):
    """
    Execute the AC power-flow study.

    Returns
    -------
    dict
        Structured result returned by the Newton-Raphson
        numerical engine.

    Notes
    -----
    Ybus ownership remains with the Network/YBusBuilder
    layer.

    Newton-Raphson numerical calculations remain inside:

        core/solver/power_flow/newton_raphson.py
    """

    # -----------------------------------------------------
    # Ensure Ybus exists before starting the numerical
    # solution.
    #
    # The Network object owns Ybus construction.
    # -----------------------------------------------------

    if getattr(self.network, "Ybus", None) is None:

        self.network.build_ybus()

    # -----------------------------------------------------
    # Execute the numerical solver.
    # -----------------------------------------------------

    result = self.solver.solve()

    # -----------------------------------------------------
    # Store the latest result on the network.
    #
    # This provides a single authoritative location for
    # the latest power-flow study result.
    # -----------------------------------------------------

    self.network.power_flow_result = result

    return result

# =========================================================
# NETWORK VALIDATION
# =========================================================

def _validate_network(self):
    """
    Validate the minimum structural requirements for
    power-flow analysis.

    This method performs only structural validation.

    Numerical validation belongs to the solver layer.
    """

    if self.network is None:

        raise ValueError(
            "Power Flow requires a valid Network object."
        )

    # -----------------------------------------------------
    # Required network containers
    # -----------------------------------------------------

    required_attributes = (
        "buses",
        "lines",
        "transformers",
        "generators",
        "bus_index",
    )

    for attribute in required_attributes:

        if not hasattr(self.network, attribute):

            raise ValueError(
                f"Network is missing required "
                f"attribute '{attribute}'."
            )

    # -----------------------------------------------------
    # At least one bus is required.
    # -----------------------------------------------------

    if len(self.network.buses) == 0:

        raise ValueError(
            "Power Flow requires at least one bus."
        )

    # -----------------------------------------------------
    # Validate each bus against the unified Bus model.
    #
    # The canonical state variables are:
    #
    #     V
    #     theta
    #
    # Specified injections are:
    #
    #     P_spec
    #     Q_spec
    # -----------------------------------------------------

    for bus in self.network.buses:

        if not hasattr(bus, "id"):

            raise ValueError(
                "Bus is missing 'id'."
            )

        if not hasattr(bus, "type"):

            raise ValueError(
                f"Bus '{bus.id}' is missing 'type'."
            )

        if not hasattr(bus, "V"):

            raise ValueError(
                f"Bus '{bus.id}' is missing voltage "
                "magnitude 'V'."
            )

        if not hasattr(bus, "theta"):

            raise ValueError(
                f"Bus '{bus.id}' is missing voltage "
                "angle 'theta'."
            )

        if not hasattr(bus, "P_spec"):

            raise ValueError(
                f"Bus '{bus.id}' is missing 'P_spec'."
            )

        if not hasattr(bus, "Q_spec"):

            raise ValueError(
                f"Bus '{bus.id}' is missing 'Q_spec'."
            )

    # -----------------------------------------------------
    # Validate that every bus has a unique identifier.
    # -----------------------------------------------------

    bus_ids = [
        bus.id
        for bus in self.network.buses
    ]

    if len(bus_ids) != len(set(bus_ids)):

        raise ValueError(
            "Network contains duplicate bus IDs."
        )

    # -----------------------------------------------------
    # Validate that the network bus index corresponds to
    # the actual bus collection.
    #
    # Do not silently rebuild it here. Network owns the
    # authoritative indexing operation.
    # -----------------------------------------------------

    if len(self.network.bus_index) != len(
        self.network.buses
    ):

        self.network._build_bus_index()

# =========================================================
# RESULT ACCESS
# =========================================================

@property
def result(self):
    """
    Return the latest power-flow result stored on the
    network.

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
```

**all** = [
"PowerFlowSolver",
]
