"""
GridForge Sequence Network Model V2
===================================

File:
    core/solver/short_circuit/sequence_network.py

Purpose
-------
Represent positive-, negative-, and zero-sequence network data
used by GridForge unsymmetrical short-circuit studies.

Sequence networks
-----------------
    Positive sequence : Z1
    Negative sequence : Z2
    Zero sequence     : Z0

The sequence impedance convention is:

    Z = R + jX

Responsibilities
----------------
- Store sequence impedance data.
- Validate sequence impedance values.
- Register element sequence impedances.
- Provide sequence impedance lookup.
- Store optional network-level sequence impedance matrices.
- Provide sequence driving-point and transfer impedances.
- Provide deterministic diagnostics.

This module does NOT:
- Build the physical network Ybus.
- Build sequence Ybus automatically.
- Perform fault calculations.
- Calculate fault currents.
- Perform symmetrical-component transformations.
- Modify network topology.
- Perform relay/protection calculations.

Architecture
------------
                    Network
                       │
                       ▼
              SequenceNetwork
                 │    │    │
                 ▼    ▼    ▼
                Z1   Z2   Z0
                 │    │    │
                 └────┴────┘
                       │
                       ▼
             UnsymmetricalFault

V2 design principles
--------------------
1. Sequence data is explicit.
2. Sequence impedances are complex quantities.
3. Element data and network-level matrices are distinct.
4. No artificial series-path assumption is made.
5. Zero-sequence data is never silently invented.
6. Missing Z0 remains explicit.
7. Matrix access is available for future network-level
   sequence analysis.
8. No fault-calculation logic belongs in this class.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from typing import Any

import numpy as np


class SequenceNetwork:
    """
    Container and numerical interface for positive-, negative-,
    and zero-sequence network data.

    The class supports two levels of representation:

    1. Element sequence impedances.

       Example:

           add_element(
               "GEN1",
               Z1=...,
               Z2=...,
               Z0=...,
           )

    2. Network-level sequence impedance matrices.

       Example:

           set_matrix("positive", Z1bus)
           set_matrix("negative", Z2bus)
           set_matrix("zero", Z0bus)

    The second representation is the preferred V2 interface
    for network-level unsymmetrical fault calculations.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
    ) -> None:

        # -----------------------------------------------------
        # Element sequence impedances
        # -----------------------------------------------------

        self.positive: dict[Any, complex] = {}
        self.negative: dict[Any, complex] = {}
        self.zero: dict[Any, complex] = {}

        # -----------------------------------------------------
        # Network-level sequence impedance matrices
        #
        # These are optional because construction may be
        # performed by a higher-level sequence-network builder.
        # -----------------------------------------------------

        self._matrices: dict[
            str,
            np.ndarray | None,
        ] = {
            "positive": None,
            "negative": None,
            "zero": None,
        }

    # =========================================================
    # VALIDATION
    # =========================================================

    @staticmethod
    def _validate_sequence(
        sequence: str,
    ) -> str:
        """
        Validate and normalize a sequence name.
        """

        if not isinstance(
            sequence,
            str,
        ):
            raise TypeError(
                "sequence must be a string."
            )

        sequence = sequence.strip().lower()

        aliases = {
            "positive": "positive",
            "z1": "positive",
            "1": "positive",
            "negative": "negative",
            "z2": "negative",
            "2": "negative",
            "zero": "zero",
            "z0": "zero",
            "0": "zero",
        }

        if sequence not in aliases:
            raise ValueError(
                "Invalid sequence. Expected "
                "'positive', 'negative', or 'zero'."
            )

        return aliases[sequence]

    @staticmethod
    def _validate_impedance(
        value: Any,
        name: str,
    ) -> complex:
        """
        Validate a complex impedance value.
        """

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be a complex-valued numerical quantity."
            )

        try:

            impedance = complex(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise TypeError(
                f"{name} must be a valid complex number."
            ) from exc

        if not (
            np.isfinite(
                impedance.real
            )
            and
            np.isfinite(
                impedance.imag
            )
        ):

            raise ValueError(
                f"{name} must contain finite values."
            )

        return impedance

    # =========================================================
    # ELEMENT REGISTRATION
    # =========================================================

    def add_element(
        self,
        element_id: Any,
        Z1: Any,
        Z2: Any | None = None,
        Z0: Any | None = None,
    ) -> None:
        """
        Register sequence impedances for an element.

        Parameters
        ----------
        element_id:
            Unique identifier for the equipment or network
            element.

        Z1:
            Positive-sequence impedance.

        Z2:
            Negative-sequence impedance.

            If omitted, Z1 is used as an explicit engineering
            default because many conventional static models use
            Z2 approximately equal to Z1.

        Z0:
            Zero-sequence impedance.

            If omitted, the zero-sequence value is NOT inferred
            from Z1. It remains unavailable for that element.

        Notes
        -----
        Zero-sequence impedance is strongly dependent on
        equipment construction, grounding, transformer winding
        connections, line geometry, and grounding transformers.
        Therefore V2 does not silently replace a missing Z0 with
        zero impedance.
        """

        if element_id is None:
            raise ValueError(
                "element_id cannot be None."
            )

        z1 = self._validate_impedance(
            Z1,
            "Z1",
        )

        if Z2 is None:

            z2 = z1

        else:

            z2 = self._validate_impedance(
                Z2,
                "Z2",
            )

        if Z0 is not None:

            z0 = self._validate_impedance(
                Z0,
                "Z0",
            )

        else:

            z0 = None

        self.positive[element_id] = z1
        self.negative[element_id] = z2
        self.zero[element_id] = z0

    # =========================================================
    # ELEMENT EXISTENCE
    # =========================================================

    def has_element(
        self,
        element_id: Any,
    ) -> bool:
        """
        Return whether sequence data exists for an element.
        """

        return (
            element_id in self.positive
        )

    # =========================================================
    # ELEMENT LOOKUP
    # =========================================================

    def _get_element_impedance(
        self,
        element_id: Any,
        sequence: str,
    ) -> complex:
        """
        Return an element's sequence impedance.
        """

        sequence = self._validate_sequence(
            sequence
        )

        data = getattr(
            self,
            sequence,
        )

        if element_id not in data:

            raise KeyError(
                f"No {sequence}-sequence impedance "
                f"registered for element {element_id!r}."
            )

        value = data[
            element_id
        ]

        if value is None:

            raise ValueError(
                f"Zero-sequence impedance is unavailable "
                f"for element {element_id!r}."
            )

        return complex(
            value
        )

    # =========================================================
    # PUBLIC ELEMENT ACCESS
    # =========================================================

    def get_positive(
        self,
        element_id: Any,
    ) -> complex:
        """
        Return positive-sequence impedance Z1.
        """

        return self._get_element_impedance(
            element_id,
            "positive",
        )

    def get_negative(
        self,
        element_id: Any,
    ) -> complex:
        """
        Return negative-sequence impedance Z2.
        """

        return self._get_element_impedance(
            element_id,
            "negative",
        )

    def get_zero(
        self,
        element_id: Any,
    ) -> complex:
        """
        Return zero-sequence impedance Z0.
        """

        return self._get_element_impedance(
            element_id,
            "zero",
        )

    # =========================================================
    # NETWORK MATRIX VALIDATION
    # =========================================================

    @staticmethod
    def _validate_matrix(
        matrix: Any,
        name: str,
    ) -> np.ndarray:
        """
        Validate a sequence impedance matrix.
        """

        if matrix is None:
            raise ValueError(
                f"{name} cannot be None."
            )

        try:

            matrix = np.asarray(
                matrix,
                dtype=complex,
            )

        except Exception as exc:

            raise ValueError(
                f"{name} could not be converted to "
                "a complex matrix."
            ) from exc

        if matrix.ndim != 2:

            raise ValueError(
                f"{name} must be two-dimensional."
            )

        rows, cols = matrix.shape

        if rows != cols:

            raise ValueError(
                f"{name} must be square: "
                f"received shape {matrix.shape}."
            )

        if rows == 0:

            raise ValueError(
                f"{name} cannot be empty."
            )

        if not np.all(
            np.isfinite(
                matrix.real
            )
        ) or not np.all(
            np.isfinite(
                matrix.imag
            )
        ):

            raise ValueError(
                f"{name} contains NaN or infinite values."
            )

        return matrix.copy()

    # =========================================================
    # NETWORK MATRIX STORAGE
    # =========================================================

    def set_matrix(
        self,
        sequence: str,
        matrix: Any,
    ) -> None:
        """
        Store a network-level sequence impedance matrix.

        Parameters
        ----------
        sequence:
            ``positive``, ``negative``, or ``zero``.

        matrix:
            Square complex sequence impedance matrix.

        Notes
        -----
        Matrix ownership remains with this SequenceNetwork
        instance. A defensive copy is stored.
        """

        sequence = self._validate_sequence(
            sequence
        )

        validated = self._validate_matrix(
            matrix,
            f"{sequence}-sequence impedance matrix",
        )

        self._matrices[
            sequence
        ] = validated

    # =========================================================
    # NETWORK MATRIX ACCESS
    # =========================================================

    def get_matrix(
        self,
        sequence: str,
    ) -> np.ndarray:
        """
        Return a copy of the requested sequence impedance matrix.
        """

        sequence = self._validate_sequence(
            sequence
        )

        matrix = self._matrices[
            sequence
        ]

        if matrix is None:

            raise ValueError(
                f"{sequence.capitalize()}-sequence impedance "
                "matrix has not been configured."
            )

        return matrix.copy()

    def has_matrix(
        self,
        sequence: str,
    ) -> bool:
        """
        Return whether a sequence impedance matrix exists.
        """

        sequence = self._validate_sequence(
            sequence
        )

        return (
            self._matrices[
                sequence
            ]
            is not None
        )

    # =========================================================
    # MATRIX INDEX VALIDATION
    # =========================================================

    def _validate_matrix_index(
        self,
        sequence: str,
        index: int,
    ) -> int:
        """
        Validate an index against a sequence matrix.
        """

        sequence = self._validate_sequence(
            sequence
        )

        matrix = self._matrices[
            sequence
        ]

        if matrix is None:

            raise ValueError(
                f"{sequence.capitalize()}-sequence impedance "
                "matrix has not been configured."
            )

        if isinstance(
            index,
            bool,
        ) or not isinstance(
            index,
            (int, np.integer),
        ):

            raise TypeError(
                "Bus index must be an integer."
            )

        index = int(
            index
        )

        if not (
            0 <= index < matrix.shape[0]
        ):

            raise IndexError(
                f"Bus index {index} is outside the "
                f"valid range 0 to {matrix.shape[0] - 1}."
            )

        return index

    # =========================================================
    # DRIVING-POINT IMPEDANCE
    # =========================================================

    def get_driving_point_impedance(
        self,
        sequence: str,
        bus_index: int,
    ) -> complex:
        """
        Return Zii for the requested sequence network.
        """

        sequence = self._validate_sequence(
            sequence
        )

        bus_index = self._validate_matrix_index(
            sequence,
            bus_index,
        )

        matrix = self._matrices[
            sequence
        ]

        assert matrix is not None

        return complex(
            matrix[
                bus_index,
                bus_index,
            ]
        )

    # =========================================================
    # TRANSFER IMPEDANCE
    # =========================================================

    def get_transfer_impedance(
        self,
        sequence: str,
        from_bus: int,
        to_bus: int,
    ) -> complex:
        """
        Return Zij from the requested sequence network.
        """

        sequence = self._validate_sequence(
            sequence
        )

        from_bus = self._validate_matrix_index(
            sequence,
            from_bus,
        )

        to_bus = self._validate_matrix_index(
            sequence,
            to_bus,
        )

        matrix = self._matrices[
            sequence
        ]

        assert matrix is not None

        return complex(
            matrix[
                from_bus,
                to_bus,
            ]
        )

    # =========================================================
    # LEGACY SERIES EQUIVALENT
    # =========================================================

    def total_impedance(
        self,
        elements,
        sequence: str = "positive",
    ) -> complex:
        """
        Calculate the series sum of explicitly supplied element
        impedances.

        This method is retained as a compatibility utility for
        simplified fault-path models.

        It must NOT be interpreted as a general network
        equivalent impedance.

        Parameters
        ----------
        elements:
            Iterable of registered element IDs.

        sequence:
            Requested sequence.

        Returns
        -------
        complex
            Series sum.

        Notes
        -----
        V2 fault solvers should prefer network-level sequence
        impedance matrices whenever available.
        """

        sequence = self._validate_sequence(
            sequence
        )

        total = complex(
            0.0,
            0.0,
        )

        for element_id in elements:

            total += self._get_element_impedance(
                element_id,
                sequence,
            )

        return total

    # =========================================================
    # CLEAR
    # =========================================================

    def clear(
        self,
    ) -> None:
        """
        Clear all element and network sequence data.
        """

        self.positive.clear()
        self.negative.clear()
        self.zero.clear()

        for sequence in self._matrices:

            self._matrices[
                sequence
            ] = None

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(
        self,
    ) -> dict:
        """
        Return sequence-network diagnostics.
        """

        return {
            "component": "SequenceNetwork",
            "version": "2.0",
            "positive_elements": len(
                self.positive
            ),
            "negative_elements": len(
                self.negative
            ),
            "zero_elements": len(
                self.zero
            ),
            "positive_matrix": self.has_matrix(
                "positive"
            ),
            "negative_matrix": self.has_matrix(
                "negative"
            ),
            "zero_matrix": self.has_matrix(
                "zero"
            ),
            "positive_matrix_shape": (
                tuple(
                    self._matrices["positive"].shape
                )
                if self._matrices["positive"] is not None
                else None
            ),
            "negative_matrix_shape": (
                tuple(
                    self._matrices["negative"].shape
                )
                if self._matrices["negative"] is not None
                else None
            ),
            "zero_matrix_shape": (
                tuple(
                    self._matrices["zero"].shape
                )
                if self._matrices["zero"] is not None
                else None
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
            "SequenceNetwork("
            f"positive_elements={len(self.positive)}, "
            f"negative_elements={len(self.negative)}, "
            f"zero_elements={len(self.zero)}, "
            f"positive_matrix="
            f"{self.has_matrix('positive')}, "
            f"negative_matrix="
            f"{self.has_matrix('negative')}, "
            f"zero_matrix="
            f"{self.has_matrix('zero')}"
            ")"
        )


__all__ = [
    "SequenceNetwork",
]
