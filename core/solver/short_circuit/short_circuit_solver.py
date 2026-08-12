```python
"""
GridForge Short-Circuit Solver
==============================

File:
    core/solver/short_circuit/short_circuit_solver.py

GridForge Short-Circuit Solver V2

Purpose
-------
Public numerical orchestration engine for short-circuit studies.

This module coordinates:

    - FaultType validation
    - Prefault voltage acquisition
    - Zbus / Thevenin impedance extraction
    - Symmetrical fault calculation
    - Unsymmetrical fault calculation
    - Result normalization
    - Solver diagnostics

Supported fault types
---------------------
    3PH - Three-phase fault
    LG  - Single line-to-ground fault
    LL  - Line-to-line fault
    LLG - Double line-to-ground fault

Architecture
------------
The solver deliberately separates orchestration from
electrical calculation.

    ShortCircuitSolver
            |
            +--> ImpedanceMatrix
            |
            +--> FaultCalculator
            |
            +--> SymmetricalFault
            |
            +--> UnsymmetricalFault
            |
            +--> SequenceNetwork

This module does NOT:

    - Build Ybus.
    - Build sequence networks.
    - Assemble Zbus directly.
    - Perform Newton-Raphson power flow.
    - Perform contingency analysis.
    - Perform protection decisions.
    - Perform relay coordination.
    - Modify network topology.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np

from .fault_types import FaultType
from .fault_calculator import FaultCalculator
from .impedance_matrix import ImpedanceMatrix
from .sequence_network import SequenceNetwork
from .symmetrical_fault import SymmetricalFault
from .unsymmetrical_fault import UnsymmetricalFault


class ShortCircuitSolver:
    """
    Orchestrate GridForge short-circuit calculations.

    Parameters
    ----------
    network:
        GridForge Network object.

    sequence_network:
        Optional SequenceNetwork instance.

        It is required for LG, LL and LLG calculations.

    Notes
    -----
    The solver operates on the existing Network and does not
    modify network topology.

    Zbus is built lazily by ImpedanceMatrix.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        network: Any,
        sequence_network: SequenceNetwork | None = None,
    ) -> None:
        """
        Initialize the short-circuit solver.
        """

        if network is None:
            raise ValueError(
                "Network cannot be None."
            )

        if not hasattr(
            network,
            "buses",
        ):
            raise ValueError(
                "Network must provide a 'buses' collection."
            )

        self.network = network

        # -----------------------------------------------------
        # Core calculation services.
        # -----------------------------------------------------

        self.impedance_matrix = ImpedanceMatrix(
            network
        )

        self.fault_calculator = FaultCalculator(
            network
        )

        self.symmetrical_fault = SymmetricalFault(
            self.impedance_matrix
        )

        # -----------------------------------------------------
        # Sequence network.
        #
        # It is intentionally injectable so that construction
        # of sequence networks remains outside this orchestration
        # layer.
        # -----------------------------------------------------

        self.sequence_network = sequence_network

        self.unsymmetrical_fault = None

        if sequence_network is not None:

            self.unsymmetrical_fault = (
                UnsymmetricalFault(
                    sequence_network
                )
            )

        # -----------------------------------------------------
        # Runtime diagnostics.
        # -----------------------------------------------------

        self.last_result: dict | None = None

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_bus_index(
        self,
        bus_index: int,
    ) -> int:
        """
        Validate a zero-based network bus index.
        """

        if isinstance(
            bus_index,
            bool,
        ) or not isinstance(
            bus_index,
            int,
        ):
            raise TypeError(
                "bus_index must be an integer."
            )

        bus_count = len(
            self.network.buses
        )

        if bus_index < 0 or bus_index >= bus_count:

            raise IndexError(
                "bus_index is outside the network bus range: "
                f"{bus_index}."
            )

        return bus_index

    @staticmethod
    def _normalize_fault_type(
        fault_type: FaultType | str,
    ) -> FaultType:
        """
        Normalize a FaultType or string into FaultType.
        """

        if isinstance(
            fault_type,
            FaultType,
        ):
            return fault_type

        if isinstance(
            fault_type,
            str,
        ):

            value = fault_type.strip().upper()

            for candidate in FaultType:

                if value in (
                    candidate.value,
                    candidate.name,
                ):
                    return candidate

        raise ValueError(
            "Unsupported fault type: "
            f"{fault_type}"
        )

    @staticmethod
    def _validate_complex(
        value: Any,
        name: str,
    ) -> complex:
        """
        Validate a finite real or complex numerical value.
        """

        try:

            value = complex(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise TypeError(
                f"{name} must be a real or complex number."
            ) from exc

        if not (
            np.isfinite(value.real)
            and np.isfinite(value.imag)
        ):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    # =========================================================
    # SEQUENCE NETWORK REQUIREMENT
    # =========================================================

    def _require_sequence_network(
        self,
    ) -> UnsymmetricalFault:
        """
        Return the unsymmetrical-fault calculator.

        Raises
        ------
        RuntimeError
            If no sequence network has been supplied.
        """

        if self.unsymmetrical_fault is None:

            raise RuntimeError(
                "A SequenceNetwork is required for "
                "LG, LL and LLG fault calculations."
            )

        return self.unsymmetrical_fault

    # =========================================================
    # PREFAULT VOLTAGE
    # =========================================================

    def _get_prefault_voltage(
        self,
        bus_index: int,
        Vprefault: Any | None,
    ) -> complex:
        """
        Obtain the prefault voltage.

        If Vprefault is explicitly supplied, it is used.

        Otherwise the current Network bus voltage state is used.
        """

        if Vprefault is not None:

            return self._validate_complex(
                Vprefault,
                "Vprefault",
            )

        bus = self.network.buses[
            bus_index
        ]

        try:

            voltage = float(
                bus.V
            )

            angle = float(
                bus.theta
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "Bus prefault voltage state must contain "
                "finite numerical V and theta values."
            ) from exc

        if not (
            np.isfinite(voltage)
            and np.isfinite(angle)
        ):

            raise ValueError(
                "Bus prefault voltage state contains "
                "NaN or infinite values."
            )

        if voltage < 0.0:

            raise ValueError(
                "Bus prefault voltage magnitude cannot "
                "be negative."
            )

        return (
            voltage
            *
            np.exp(
                1j * angle
            )
        )

    # =========================================================
    # ELEMENT VALIDATION
    # =========================================================

    @staticmethod
    def _validate_elements(
        elements: Iterable[Any] | None,
    ) -> list:
        """
        Normalize sequence-network element identifiers.
        """

        if elements is None:
            raise ValueError(
                "elements are required for unsymmetrical "
                "fault calculations."
            )

        try:

            result = list(
                elements
            )

        except TypeError as exc:

            raise TypeError(
                "elements must be an iterable."
            ) from exc

        if not result:

            raise ValueError(
                "At least one sequence-network element "
                "is required."
            )

        return result

    # =========================================================
    # THREE-PHASE FAULT
    # =========================================================

    def calculate_three_phase(
        self,
        bus_index: int,
        Vprefault: Any | None = None,
        Zf: Any = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate a three-phase fault.

        Parameters
        ----------
        bus_index:
            Zero-based fault-bus index.

        Vprefault:
            Optional prefault voltage in per-unit.

            If omitted, the Network bus voltage state is used.

        Zf:
            Fault impedance in per-unit.
        """

        bus_index = self._validate_bus_index(
            bus_index
        )

        V = self._get_prefault_voltage(
            bus_index,
            Vprefault,
        )

        Zf = self._validate_complex(
            Zf,
            "Zf",
        )

        result = (
            self.symmetrical_fault
            .calculate_three_phase_fault(
                bus_index=bus_index,
                Vprefault=V,
                Zf=Zf,
            )
        )

        return self._finalize_result(
            result=result,
            bus_index=bus_index,
            fault_type=FaultType.THREE_PHASE,
        )

    # =========================================================
    # UNSYMMETRICAL FAULT
    # =========================================================

    def calculate_unsymmetrical(
        self,
        fault_type: FaultType | str,
        bus_index: int,
        elements: Iterable[Any],
        Vprefault: Any | None = None,
        Zf: Any = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate LG, LL or LLG fault.

        Parameters
        ----------
        fault_type:
            FaultType.LG, FaultType.LL or FaultType.LLG,
            or the corresponding string.

        bus_index:
            Fault-bus index.

        elements:
            Sequence-network elements forming the equivalent
            sequence path.

        Vprefault:
            Optional prefault voltage in per-unit.

        Zf:
            Fault impedance in per-unit.
        """

        normalized_type = self._normalize_fault_type(
            fault_type
        )

        if normalized_type == FaultType.THREE_PHASE:

            raise ValueError(
                "Use calculate_three_phase() for "
                "three-phase faults."
            )

        if not FaultType.is_unbalanced(
            normalized_type
        ):
            raise ValueError(
                "Fault type is not an unsymmetrical fault: "
                f"{normalized_type.value}"
            )

        bus_index = self._validate_bus_index(
            bus_index
        )

        elements = self._validate_elements(
            elements
        )

        V = self._get_prefault_voltage(
            bus_index,
            Vprefault,
        )

        Zf = self._validate_complex(
            Zf,
            "Zf",
        )

        calculator = (
            self._require_sequence_network()
        )

        result = calculator.calculate(
            fault_type=normalized_type,
            elements=elements,
            Vprefault=V,
            Zf=Zf,
        )

        return self._finalize_result(
            result=result,
            bus_index=bus_index,
            fault_type=normalized_type,
        )

    # =========================================================
    # GENERIC FAULT DISPATCH
    # =========================================================

    def calculate(
        self,
        fault_type: FaultType | str,
        bus_index: int,
        elements: Iterable[Any] | None = None,
        Vprefault: Any | None = None,
        Zf: Any = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate any supported short-circuit fault.

        Parameters
        ----------
        fault_type:
            FaultType member or supported string.

        bus_index:
            Zero-based fault-bus index.

        elements:
            Sequence-network elements required for
            unsymmetrical faults.

        Vprefault:
            Optional prefault voltage in per-unit.

        Zf:
            Fault impedance in per-unit.

        Returns
        -------
        dict
            Standardized GridForge short-circuit result.
        """

        normalized_type = self._normalize_fault_type(
            fault_type
        )

        if normalized_type == FaultType.THREE_PHASE:

            return self.calculate_three_phase(
                bus_index=bus_index,
                Vprefault=Vprefault,
                Zf=Zf,
            )

        return self.calculate_unsymmetrical(
            fault_type=normalized_type,
            bus_index=bus_index,
            elements=elements,
            Vprefault=Vprefault,
            Zf=Zf,
        )

    # =========================================================
    # RESULT NORMALIZATION
    # =========================================================

    def _finalize_result(
        self,
        result: dict,
        bus_index: int,
        fault_type: FaultType,
    ) -> dict:
        """
        Add common GridForge result metadata.
        """

        if not isinstance(
            result,
            dict,
        ):
            raise RuntimeError(
                "Fault calculator returned an invalid result."
            )

        final = dict(
            result
        )

        final["fault_type"] = (
            fault_type.value
        )

        final["bus_index"] = int(
            bus_index
        )

        # -----------------------------------------------------
        # Preserve a stable bus identifier when available.
        # -----------------------------------------------------

        bus = self.network.buses[
            bus_index
        ]

        if hasattr(
            bus,
            "id",
        ):

            final["bus_id"] = bus.id

        self.last_result = final

        return final

    # =========================================================
    # ZBUS / THEVENIN ACCESS
    # =========================================================

    def build_impedance_matrix(
        self,
    ):
        """
        Build and return the network Zbus matrix.

        This is a convenience method only. Zbus construction
        remains owned by ImpedanceMatrix.
        """

        return self.impedance_matrix.build()

    def get_thevenin_impedance(
        self,
        bus_index: int,
    ):
        """
        Return the Thevenin impedance at a fault bus.
        """

        bus_index = self._validate_bus_index(
            bus_index
        )

        return (
            self.impedance_matrix
            .get_thevenin_impedance(
                bus_index
            )
        )

    # =========================================================
    # BATCH STUDY
    # =========================================================

    def calculate_all_faults(
        self,
        bus_index: int,
        elements: Iterable[Any] | None = None,
        Vprefault: Any | None = None,
        Zf: Any = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate all supported fault types for one bus.

        Returns
        -------
        dict
            Mapping fault-type values to result dictionaries.

        Notes
        -----
        Three-phase calculation is always attempted.

        LG, LL and LLG require a SequenceNetwork and sequence
        element definition.
        """

        results = {}

        results[
            FaultType.THREE_PHASE.value
        ] = self.calculate_three_phase(
            bus_index=bus_index,
            Vprefault=Vprefault,
            Zf=Zf,
        )

        if (
            self.unsymmetrical_fault is not None
            and elements is not None
        ):

            for fault_type in (
                FaultType.SINGLE_LINE_GROUND,
                FaultType.LINE_LINE,
                FaultType.DOUBLE_LINE_GROUND,
            ):

                results[
                    fault_type.value
                ] = self.calculate_unsymmetrical(
                    fault_type=fault_type,
                    bus_index=bus_index,
                    elements=elements,
                    Vprefault=Vprefault,
                    Zf=Zf,
                )

        return results

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset runtime diagnostics.

        Network state is not modified.
        """

        self.last_result = None

        # -----------------------------------------------------
        # Zbus is a calculated numerical artifact and can be
        # rebuilt on demand.
        # -----------------------------------------------------

        self.impedance_matrix.Zbus = None

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return solver diagnostics and configuration.
        """

        return {
            "solver": "ShortCircuitSolver",
            "version": "2.0",
            "buses": len(
                self.network.buses
            ),
            "supported_faults": [
                fault.value
                for fault in FaultType
            ],
            "zbus_built": (
                self.impedance_matrix.Zbus
                is not None
            ),
            "sequence_network_available": (
                self.sequence_network
                is not None
            ),
            "last_result_available": (
                self.last_result
                is not None
            ),
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Developer-friendly representation.
        """

        return (
            "ShortCircuitSolver("
            f"buses={len(self.network.buses)}, "
            f"sequence_network="
            f"{self.sequence_network is not None}"
            ")"
        )


__all__ = [
    "ShortCircuitSolver",
]
```
