```python
# GridForge
#
# Copyright © 2026 Subhendu Mishra
#
# All Rights Reserved.
#
# Proprietary and confidential.

"""
GridForge Contingency Analysis
==============================

File:
    core/analysis/contingency.py

Purpose
-------
Perform steady-state N-1 contingency analysis.

Supported contingencies:

    - Line outage
    - Transformer outage
    - Generator outage

For each contingency GridForge evaluates:

    - Power-flow convergence
    - Network islanding
    - Bus-voltage violations
    - Line thermal violations
    - Transformer thermal violations

Architecture
------------

                    Network
                       │
                       ▼
              ContingencyAnalyzer
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Network      Power Flow    Flow Analysis
       outage       facade       line/transformer
          │            │            │
          └────────────┼────────────┘
                       ▼
                  N-1 Result

This module is an ANALYSIS orchestrator.

It does NOT:

    - Implement Newton-Raphson
    - Build Ybus mathematics
    - Calculate line-flow equations
    - Calculate transformer-flow equations
    - Implement topology algorithms
    - Implement protection logic

Those responsibilities remain in their respective layers.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

import numpy as np


class ContingencyAnalyzer:
    """
    Perform steady-state N-1 contingency analysis.

    Parameters
    ----------
    network:
        GridForge Network instance.

    power_flow_solver:
        Optional power-flow analysis class.

        If omitted, GridForge uses:

            core.analysis.power_flow.PowerFlowSolver
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        network: Any,
        power_flow_solver: Optional[Any] = None,
    ) -> None:

        if network is None:
            raise ValueError(
                "ContingencyAnalyzer requires a valid Network."
            )

        self.base_network = network

        if power_flow_solver is None:

            from core.analysis.power_flow import (
                PowerFlowSolver
            )

            power_flow_solver = PowerFlowSolver

        self.power_flow_solver = power_flow_solver

    # =========================================================
    # PUBLIC API
    # =========================================================

    def run_n_minus_1(self) -> List[Dict[str, Any]]:
        """
        Execute all supported single-element contingencies.

        Returns
        -------
        list of dict

            Each result contains:

                contingency
                converged
                islanded
                violations

            Failed studies additionally contain:

                error
        """

        contingencies = (
            self._generate_contingencies()
        )

        results: List[Dict[str, Any]] = []

        for contingency in contingencies:

            result = self._run_single(
                contingency
            )

            results.append(result)

        return results

    # =========================================================
    # SINGLE CONTINGENCY
    # =========================================================

    def _run_single(
        self,
        contingency: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute one contingency study.
        """

        try:

            network = self._apply_contingency(
                contingency
            )

            # -------------------------------------------------
            # Rebuild topology first.
            # -------------------------------------------------

            network.rebuild_topology()

            islands = network.find_islands()

            islanded = len(islands) > 1

            # -------------------------------------------------
            # An islanded network cannot be treated as a
            # normal single-system power-flow case.
            #
            # We still attempt the power flow because an
            # individual island may have a valid solution,
            # but islanding is explicitly reported.
            # -------------------------------------------------

            solver = self.power_flow_solver(
                network
            )

            power_flow_result = solver.solve()

            converged = bool(
                power_flow_result.get(
                    "success",
                    False
                )
            )

            # -------------------------------------------------
            # If the numerical solver reports failure, return
            # the failure without attempting flow calculations.
            # -------------------------------------------------

            if not converged:

                return {
                    "contingency": contingency,
                    "converged": False,
                    "islanded": islanded,
                    "islands": islands,
                    "violations": {
                        "voltage": [],
                        "thermal": [],
                    },
                    "error": power_flow_result.get(
                        "message",
                        "Power flow did not converge."
                    ),
                }

            # -------------------------------------------------
            # Extract solved state.
            # -------------------------------------------------

            Vm = np.asarray(
                power_flow_result["Vm"],
                dtype=float,
            )

            Va = np.asarray(
                power_flow_result["Va"],
                dtype=float,
            )

            # -------------------------------------------------
            # Line flows.
            # -------------------------------------------------

            line_flows = []

            if network.lines:

                line_flows = (
                    network.compute_line_flows()
                )

            # -------------------------------------------------
            # Transformer flows.
            # -------------------------------------------------

            transformer_flows = []

            if network.transformers:

                transformer_flows = (
                    network.compute_transformer_flows()
                )

            # -------------------------------------------------
            # Violations.
            # -------------------------------------------------

            violations = self._check_violations(
                network,
                Vm,
                line_flows,
                transformer_flows,
            )

            return {
                "contingency": contingency,
                "converged": True,
                "islanded": islanded,
                "islands": islands,
                "violations": violations,
            }

        except Exception as exc:

            return {
                "contingency": contingency,
                "converged": False,
                "islanded": False,
                "islands": [],
                "violations": {
                    "voltage": [],
                    "thermal": [],
                },
                "error": str(exc),
            }

    # =========================================================
    # CONTINGENCY GENERATION
    # =========================================================

    def _generate_contingencies(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Generate supported N-1 outage cases.

        Only in-service elements are considered.
        """

        contingencies: List[
            Dict[str, Any]
        ] = []

        # -----------------------------------------------------
        # Lines
        # -----------------------------------------------------

        for line in self.base_network.lines:

            if not getattr(
                line,
                "in_service",
                True,
            ):
                continue

            contingencies.append(
                {
                    "type": "line",
                    "id": getattr(
                        line,
                        "id",
                        None,
                    ),
                }
            )

        # -----------------------------------------------------
        # Transformers
        # -----------------------------------------------------

        for trafo in self.base_network.transformers:

            if not getattr(
                trafo,
                "in_service",
                True,
            ):
                continue

            contingencies.append(
                {
                    "type": "transformer",
                    "id": getattr(
                        trafo,
                        "id",
                        None,
                    ),
                }
            )

        # -----------------------------------------------------
        # Generators
        # -----------------------------------------------------

        for generator in self.base_network.generators:

            if not getattr(
                generator,
                "in_service",
                True,
            ):
                continue

            contingencies.append(
                {
                    "type": "generator",
                    "id": getattr(
                        generator,
                        "id",
                        None,
                    ),
                }
            )

        return contingencies

    # =========================================================
    # APPLY CONTINGENCY
    # =========================================================

    def _apply_contingency(
        self,
        contingency: Dict[str, Any],
    ) -> Any:
        """
        Create an independent Network state and apply
        a single-element outage.

        The base Network is never modified.
        """

        network = copy.deepcopy(
            self.base_network
        )

        element_type = contingency[
            "type"
        ]

        element_id = contingency[
            "id"
        ]

        if element_type == "line":

            element = self._find_element(
                network.lines,
                element_id,
            )

        elif element_type == "transformer":

            element = self._find_element(
                network.transformers,
                element_id,
            )

        elif element_type == "generator":

            element = self._find_element(
                network.generators,
                element_id,
            )

        else:

            raise ValueError(
                f"Unsupported contingency type: "
                f"{element_type}"
            )

        if element is None:

            raise KeyError(
                f"Contingency element not found: "
                f"{element_type} '{element_id}'"
            )

        # -----------------------------------------------------
        # Use service-state semantics rather than deleting
        # the physical model.
        # -----------------------------------------------------

        element.in_service = False

        # -----------------------------------------------------
        # Mark network state dirty.
        # -----------------------------------------------------

        network._topology_dirty = True
        network._ybus_dirty = True

        return network

    # =========================================================
    # ELEMENT LOOKUP
    # =========================================================

    @staticmethod
    def _find_element(
        elements,
        element_id,
    ):
        """
        Find an element by its canonical ID.
        """

        for element in elements:

            if getattr(
                element,
                "id",
                None,
            ) == element_id:

                return element

        return None

    # =========================================================
    # VIOLATION ANALYSIS
    # =========================================================

    def _check_violations(
        self,
        network: Any,
        Vm: np.ndarray,
        line_flows: List[Dict[str, Any]],
        transformer_flows: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Evaluate steady-state operating-limit violations.
        """

        violations = {
            "voltage": [],
            "thermal": [],
        }

        # =====================================================
        # VOLTAGE LIMITS
        # =====================================================

        for index, bus in enumerate(
            network.buses
        ):

            voltage = float(
                Vm[index]
            )

            v_min = getattr(
                bus,
                "v_min",
                None,
            )

            v_max = getattr(
                bus,
                "v_max",
                None,
            )

            # If the frozen model does not define voltage
            # limits, no voltage violation is evaluated.
            if (
                v_min is None
                or v_max is None
            ):
                continue

            if (
                voltage < v_min
                or voltage > v_max
            ):

                violations[
                    "voltage"
                ].append(
                    {
                        "bus": bus.id,
                        "Vm": voltage,
                        "limit_min": v_min,
                        "limit_max": v_max,
                    }
                )

        # =====================================================
        # LINE THERMAL LIMITS
        # =====================================================

        line_lookup = {
            getattr(line, "id", None): line
            for line in network.lines
        }

        for flow in line_flows:

            line_id = flow.get(
                "line"
            )

            line = line_lookup.get(
                line_id
            )

            if line is None:
                continue

            rating = getattr(
                line,
                "rating",
                None,
            )

            if rating is None:
                continue

            loading_from = self._apparent_power(
                flow["P_from_to"],
                flow["Q_from_to"],
            )

            loading_to = self._apparent_power(
                flow["P_to_from"],
                flow["Q_to_from"],
            )

            loading = max(
                loading_from,
                loading_to,
            )

            if loading > rating:

                violations[
                    "thermal"
                ].append(
                    {
                        "element": line_id,
                        "type": "line",
                        "loading": loading,
                        "limit": rating,
                        "loading_percent": (
                            100.0
                            * loading
                            / rating
                        ),
                    }
                )

        # =====================================================
        # TRANSFORMER THERMAL LIMITS
        # =====================================================

        transformer_lookup = {
            getattr(
                trafo,
                "id",
                None
            ): trafo
            for trafo in network.transformers
        }

        for flow in transformer_flows:

            transformer_id = flow.get(
                "transformer"
            )

            trafo = transformer_lookup.get(
                transformer_id
            )

            if trafo is None:
                continue

            rating = getattr(
                trafo,
                "rating",
                None,
            )

            if rating is None:
                continue

            loading_from = self._apparent_power(
                flow["P_from_to"],
                flow["Q_from_to"],
            )

            loading_to = self._apparent_power(
                flow["P_to_from"],
                flow["Q_to_from"],
            )

            loading = max(
                loading_from,
                loading_to,
            )

            if loading > rating:

                violations[
                    "thermal"
                ].append(
                    {
                        "element": transformer_id,
                        "type": "transformer",
                        "loading": loading,
                        "limit": rating,
                        "loading_percent": (
                            100.0
                            * loading
                            / rating
                        ),
                    }
                )

        return violations

    # =========================================================
    # APPARENT POWER
    # =========================================================

    @staticmethod
    def _apparent_power(
        p: float,
        q: float,
    ) -> float:
        """
        Calculate apparent power magnitude in pu.
        """

        return float(
            np.hypot(
                p,
                q,
            )
        )


__all__ = [
    "ContingencyAnalyzer",
]
```
