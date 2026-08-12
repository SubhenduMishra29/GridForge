```python
"""
GridForge Short-Circuit Analysis Facade
=======================================

File:
    core/solver/short_circuit/short_circuit.py

GridForge Short-Circuit Solver V2.0
-----------------------------------

Public orchestration facade for short-circuit studies.

Responsibilities
----------------
- Provide a stable public entry point for short-circuit calculations.
- Validate fault requests.
- Dispatch balanced faults to SymmetricalFault.
- Dispatch unbalanced faults to UnsymmetricalFault.
- Manage the impedance-matrix service.
- Manage the sequence-network service when required.
- Return deterministic, serializable study results.

This module does NOT:
- Build Ybus.
- Modify network topology.
- Perform Newton-Raphson power flow.
- Assemble sequence networks internally.
- Perform protection decisions.
- Perform relay coordination.
- Implement numerical fault equations directly.

Numerical responsibilities are delegated to:

    ImpedanceMatrix
    SequenceNetwork
    SymmetricalFault
    UnsymmetricalFault
    ShortCircuitSolver

Architecture
------------

    core/analysis/
            |
            v
    core/solver/short_circuit/
            |
            +-- FaultType
            +-- ImpedanceMatrix
            +-- SequenceNetwork
            +-- FaultCalculator
            +-- SymmetricalFault
            +-- UnsymmetricalFault
            +-- ShortCircuitSolver
            +-- ShortCircuit

Design principle
----------------
This class is an orchestration facade.

It must not become a second implementation of the
short-circuit mathematics.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

import numpy as np

from .fault_types import FaultType
from .impedance_matrix import ImpedanceMatrix
from .sequence_network import SequenceNetwork
from .symmetrical_fault import SymmetricalFault
from .unsymmetrical_fault import UnsymmetricalFault


class ShortCircuit:
    """
    Public short-circuit study facade.

    Parameters
    ----------
    network:
        GridForge Network object.

    impedance_matrix:
        Optional pre-existing :class:`ImpedanceMatrix`.

        If omitted, the facade creates one for the supplied
        network.

    sequence_network:
        Optional :class:`SequenceNetwork`.

        Required for unsymmetrical faults unless the caller
        supplies sequence impedances through the sequence
        network before calculation.

    Notes
    -----
    The facade does not modify network topology.

    The impedance matrix is built lazily when a three-phase
    fault or a Thevenin/transfer-impedance request requires it.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        network,
        impedance_matrix: Optional[ImpedanceMatrix] = None,
        sequence_network: Optional[SequenceNetwork] = None,
    ):
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
        # Impedance-matrix service
        # -----------------------------------------------------

        if impedance_matrix is None:

            impedance_matrix = ImpedanceMatrix(
                network
            )

        elif not isinstance(
            impedance_matrix,
            ImpedanceMatrix,
        ):
            raise TypeError(
                "impedance_matrix must be an "
                "ImpedanceMatrix instance."
            )

        self.impedance_matrix = impedance_matrix

        # -----------------------------------------------------
        # Sequence-network service
        # -----------------------------------------------------

        if sequence_network is None:

            sequence_network = SequenceNetwork()

        elif not isinstance(
            sequence_network,
            SequenceNetwork,
        ):
            raise TypeError(
                "sequence_network must be a "
                "SequenceNetwork instance."
            )

        self.sequence_network = sequence_network

        # -----------------------------------------------------
        # Fault calculators
        # -----------------------------------------------------

        self.symmetrical_fault = SymmetricalFault(
            self.impedance_matrix
        )

        self.unsymmetrical_fault = UnsymmetricalFault(
            self.sequence_network
        )

    # =========================================================
    # VALIDATION
    # =========================================================

    @staticmethod
    def _normalize_fault_type(
        fault_type: FaultType | str,
    ) -> FaultType:
        """
        Normalize a supported fault-type representation.

        Accepted values include:

            FaultType.THREE_PHASE
            FaultType.SINGLE_LINE_GROUND
            FaultType.LINE_LINE
            FaultType.DOUBLE_LINE_GROUND

        and their string values:

            "3PH"
            "LG"
            "LL"
            "LLG"
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

                if (
                    candidate.value.upper()
                    == value
                ):
                    return candidate

                if (
                    candidate.name.upper()
                    == value
                ):
                    return candidate

        raise ValueError(
            "Unsupported fault type: "
            f"{fault_type!r}. Supported types are: "
            + ", ".join(
                fault.value
                for fault in FaultType
            )
        )

    def _validate_bus_index(
        self,
        bus_index: int,
    ) -> int:
        """
        Validate and normalize a zero-based bus index.
        """

        if isinstance(
            bus_index,
            bool,
        ) or not isinstance(
            bus_index,
            (int, np.integer),
        ):
            raise TypeError(
                "bus_index must be an integer."
            )

        bus_index = int(
            bus_index
        )

        bus_count = len(
            self.network.buses
        )

        if not (
            0
            <= bus_index
            < bus_count
        ):
            raise IndexError(
                "bus_index is outside the network bus range: "
                f"{bus_index}; valid range is "
                f"0 to {bus_count - 1}."
            )

        return bus_index

    @staticmethod
    def _validate_complex_parameter(
        value: Any,
        name: str,
    ) -> complex:
        """
        Validate a complex-valued electrical parameter.
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
                f"{name} must be a numeric complex value."
            ) from exc

        if not (
            np.isfinite(
                value.real
            )
            and np.isfinite(
                value.imag
            )
        ):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @staticmethod
    def _validate_prefault_voltage(
        value: Any,
    ) -> complex:
        """
        Validate a prefault voltage phasor.
        """

        return ShortCircuit._validate_complex_parameter(
            value,
            "Vprefault",
        )

    # =========================================================
    # IMPEDANCE MATRIX
    # =========================================================

    def build_impedance_matrix(self):
        """
        Build and return the network bus impedance matrix.

        Returns
        -------
        numpy.ndarray
            Zbus matrix.
        """

        return self.impedance_matrix.build()

    def get_thevenin_impedance(
        self,
        bus_index: int,
    ):
        """
        Return the Thevenin impedance at a bus.
        """

        bus_index = self._validate_bus_index(
            bus_index
        )

        return self.impedance_matrix.get_thevenin_impedance(
            bus_index
        )

    def get_transfer_impedance(
        self,
        from_bus: int,
        to_bus: int,
    ):
        """
        Return the transfer impedance between two buses.
        """

        from_bus = self._validate_bus_index(
            from_bus
        )

        to_bus = self._validate_bus_index(
            to_bus
        )

        return self.impedance_matrix.get_transfer_impedance(
            from_bus,
            to_bus,
        )

    # =========================================================
    # THREE-PHASE FAULT
    # =========================================================

    def calculate_three_phase_fault(
        self,
        bus_index: int,
        Vprefault: complex = 1.0 + 0.0j,
        Zf: complex = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate a balanced three-phase fault.

        Parameters
        ----------
        bus_index:
            Zero-based fault-bus index.

        Vprefault:
            Prefault positive-sequence voltage in pu.

        Zf:
            Fault impedance in pu.

        Returns
        -------
        dict
            Standard three-phase fault result.
        """

        bus_index = self._validate_bus_index(
            bus_index
        )

        Vprefault = self._validate_prefault_voltage(
            Vprefault
        )

        Zf = self._validate_complex_parameter(
            Zf,
            "Zf",
        )

        return self.symmetrical_fault.calculate_three_phase_fault(
            bus_index=bus_index,
            Vprefault=Vprefault,
            Zf=Zf,
        )

    # =========================================================
    # UNSYMMETRICAL FAULTS
    # =========================================================

    def calculate_lg_fault(
        self,
        elements: Iterable,
        Vprefault: complex = 1.0 + 0.0j,
        Zf: complex = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate a single-line-to-ground fault.

        Parameters
        ----------
        elements:
            Ordered sequence-network path/elements.

        Vprefault:
            Prefault positive-sequence voltage in pu.

        Zf:
            Fault impedance in pu.
        """

        elements = self._validate_elements(
            elements
        )

        Vprefault = self._validate_prefault_voltage(
            Vprefault
        )

        Zf = self._validate_complex_parameter(
            Zf,
            "Zf",
        )

        return self.unsymmetrical_fault.calculate_lg_fault(
            elements=elements,
            Vprefault=Vprefault,
            Zf=Zf,
        )

    def calculate_ll_fault(
        self,
        elements: Iterable,
        Vprefault: complex = 1.0 + 0.0j,
        Zf: complex = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate a line-to-line fault.
        """

        elements = self._validate_elements(
            elements
        )

        Vprefault = self._validate_prefault_voltage(
            Vprefault
        )

        Zf = self._validate_complex_parameter(
            Zf,
            "Zf",
        )

        return self.unsymmetrical_fault.calculate_ll_fault(
            elements=elements,
            Vprefault=Vprefault,
            Zf=Zf,
        )

    def calculate_llg_fault(
        self,
        elements: Iterable,
        Vprefault: complex = 1.0 + 0.0j,
        Zf: complex = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate a double-line-to-ground fault.
        """

        elements = self._validate_elements(
            elements
        )

        Vprefault = self._validate_prefault_voltage(
            Vprefault
        )

        Zf = self._validate_complex_parameter(
            Zf,
            "Zf",
        )

        return self.unsymmetrical_fault.calculate_llg_fault(
            elements=elements,
            Vprefault=Vprefault,
            Zf=Zf,
        )

    # =========================================================
    # GENERIC FAULT DISPATCH
    # =========================================================

    def calculate(
        self,
        fault_type: FaultType | str,
        *,
        bus_index: Optional[int] = None,
        elements: Optional[Iterable] = None,
        Vprefault: complex = 1.0 + 0.0j,
        Zf: complex = 0.0 + 0.0j,
    ) -> dict:
        """
        Calculate a fault using the appropriate fault engine.

        Parameters
        ----------
        fault_type:
            FaultType enum member or supported string.

        bus_index:
            Required for three-phase faults.

        elements:
            Required for sequence-network faults.

        Vprefault:
            Prefault voltage in pu.

        Zf:
            Fault impedance in pu.

        Returns
        -------
        dict
            Fault-study result.

        Raises
        ------
        ValueError
            If the requested fault does not have the required
            location/path information.
        """

        fault_type = self._normalize_fault_type(
            fault_type
        )

        if fault_type is FaultType.THREE_PHASE:

            if bus_index is None:
                raise ValueError(
                    "bus_index is required for a "
                    "three-phase fault."
                )

            return self.calculate_three_phase_fault(
                bus_index=bus_index,
                Vprefault=Vprefault,
                Zf=Zf,
            )

        if elements is None:
            raise ValueError(
                "elements are required for an "
                f"{fault_type.value} fault."
            )

        if fault_type is FaultType.SINGLE_LINE_GROUND:

            return self.calculate_lg_fault(
                elements=elements,
                Vprefault=Vprefault,
                Zf=Zf,
            )

        if fault_type is FaultType.LINE_LINE:

            return self.calculate_ll_fault(
                elements=elements,
                Vprefault=Vprefault,
                Zf=Zf,
            )

        if fault_type is FaultType.DOUBLE_LINE_GROUND:

            return self.calculate_llg_fault(
                elements=elements,
                Vprefault=Vprefault,
                Zf=Zf,
            )

        raise ValueError(
            "Unsupported fault type."
        )

    # =========================================================
    # ELEMENT VALIDATION
    # =========================================================

    @staticmethod
    def _validate_elements(
        elements: Iterable,
    ) -> list:
        """
        Normalize sequence-network elements.

        Strings are treated as a single element rather than
        iterated character-by-character.
        """

        if elements is None:
            raise ValueError(
                "elements cannot be None."
            )

        if isinstance(
            elements,
            (str, bytes),
        ):
            normalized = [
                elements
            ]

        else:

            try:
                normalized = list(
                    elements
                )
            except TypeError as exc:

                raise TypeError(
                    "elements must be an iterable of "
                    "sequence-network element identifiers."
                ) from exc

        if not normalized:
            raise ValueError(
                "elements cannot be empty."
            )

        return normalized

    # =========================================================
    # CLASSIFICATION UTILITIES
    # =========================================================

    @staticmethod
    def is_balanced(
        fault_type: FaultType | str,
    ) -> bool:
        """
        Return True when the supplied fault is balanced.
        """

        fault_type = ShortCircuit._normalize_fault_type(
            fault_type
        )

        return FaultType.is_balanced(
            fault_type
        )

    @staticmethod
    def is_unbalanced(
        fault_type: FaultType | str,
    ) -> bool:
        """
        Return True when the supplied fault is unbalanced.
        """

        fault_type = ShortCircuit._normalize_fault_type(
            fault_type
        )

        return FaultType.is_unbalanced(
            fault_type
        )

    # =========================================================
    # STATUS
    # =========================================================

    def summary(self) -> dict:
        """
        Return short-circuit facade diagnostics.
        """

        Zbus = getattr(
            self.impedance_matrix,
            "Zbus",
            None,
        )

        return {
            "solver": "ShortCircuit",
            "version": "2.0",
            "buses": len(
                self.network.buses
            ),
            "impedance_matrix_built": (
                Zbus is not None
            ),
            "impedance_matrix_size": (
                tuple(
                    Zbus.shape
                )
                if Zbus is not None
                else None
            ),
            "sequence_positive_elements": len(
                self.sequence_network.positive
            ),
            "sequence_negative_elements": len(
                self.sequence_network.negative
            ),
            "sequence_zero_elements": len(
                self.sequence_network.zero
            ),
            "supported_fault_types": [
                fault_type.value
                for fault_type in FaultType
            ],
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
            "ShortCircuit("
            f"buses={len(self.network.buses)}, "
            f"impedance_matrix_built="
            f"{self.impedance_matrix.Zbus is not None}"
            ")"
        )


__all__ = [
    "ShortCircuit",
]
```
