"""
GridForge Sequence Network Model
================================

File:
    core/solver/short_circuit/sequence_network.py

GridForge Short Circuit Solver V1.0
-----------------------------------

Stores positive-, negative-, and zero-sequence impedances used
by unsymmetrical-fault calculations.

Sequence networks:

    Positive sequence: Z1
    Negative sequence: Z2
    Zero sequence:     Z0

Impedance convention:

    Z = R + jX

Responsibilities
----------------
- Store sequence impedances associated with identifiable
  electrical elements.
- Provide validated access to Z1, Z2, and Z0.
- Provide deterministic equivalent series impedance for an
  explicitly supplied element path.
- Provide diagnostic information.

This module does NOT:
- Build Ybus.
- Build Zbus.
- Determine network topology.
- Perform fault calculations.
- Calculate fault currents.
- Modify Network state.
- Perform protection decisions.

Important V1.0 limitation
-------------------------
The current implementation represents sequence impedances as
element-level data.

It does NOT yet construct full positive-, negative-, or
zero-sequence bus impedance matrices.

A future sequence-network implementation may introduce:

    Z1bus
    Z2bus
    Z0bus

or equivalent sequence-network assembly without changing the
basic element impedance API.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

import numpy as np


class SequenceNetwork:
    """
    Store sequence impedances for short-circuit calculations.

    Each element is identified by an application-level
    ``element_id``.

    Parameters
    ----------
    None
        The sequence network is initially empty.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self) -> None:
        """
        Initialize an empty sequence network.
        """

        self.positive: dict[Any, complex] = {}
        self.negative: dict[Any, complex] = {}
        self.zero: dict[Any, complex] = {}

    # =========================================================
    # IMPEDANCE VALIDATION
    # =========================================================

    @staticmethod
    def _validate_impedance(
        value: Any,
        name: str,
    ) -> complex:
        """
        Validate and normalize a sequence impedance.
        """

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be a complex-valued impedance."
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
                f"{name} must be a valid complex impedance."
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
                f"{name} must be finite."
            )

        return impedance

    # =========================================================
    # ADD ELEMENT
    # =========================================================

    def add_element(
        self,
        element_id: Any,
        Z1: Any,
        Z2: Any = None,
        Z0: Any = None,
    ) -> None:
        """
        Add or replace sequence impedances for an element.

        Parameters
        ----------
        element_id:
            Unique application-level identifier for the
            electrical element.

        Z1:
            Positive-sequence impedance.

        Z2:
            Negative-sequence impedance.

            If omitted, Z2 = Z1 is used as the default.

        Z0:
            Zero-sequence impedance.

            If omitted, zero impedance is NOT physically inferred;
            V1.0 uses 0 + j0 as an explicit default for backward
            compatibility. Equipment-specific zero-sequence data
            should therefore be supplied whenever required.

        Raises
        ------
        ValueError
            If element_id is invalid or already unsupported.

        TypeError
            If an impedance cannot be converted to complex form.
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

        if Z0 is None:

            z0 = complex(
                0.0,
                0.0,
            )

        else:

            z0 = self._validate_impedance(
                Z0,
                "Z0",
            )

        self.positive[element_id] = z1
        self.negative[element_id] = z2
        self.zero[element_id] = z0

    # =========================================================
    # GET POSITIVE SEQUENCE
    # =========================================================

    def get_positive(
        self,
        element_id: Any,
    ) -> complex:
        """
        Return positive-sequence impedance Z1.
        """

        try:

            return self.positive[
                element_id
            ]

        except KeyError as exc:

            raise KeyError(
                f"No positive-sequence impedance registered "
                f"for element {element_id!r}."
            ) from exc

    # =========================================================
    # GET NEGATIVE SEQUENCE
    # =========================================================

    def get_negative(
        self,
        element_id: Any,
    ) -> complex:
        """
        Return negative-sequence impedance Z2.
        """

        try:

            return self.negative[
                element_id
            ]

        except KeyError as exc:

            raise KeyError(
                f"No negative-sequence impedance registered "
                f"for element {element_id!r}."
            ) from exc

    # =========================================================
    # GET ZERO SEQUENCE
    # =========================================================

    def get_zero(
        self,
        element_id: Any,
    ) -> complex:
        """
        Return zero-sequence impedance Z0.
        """

        try:

            return self.zero[
                element_id
            ]

        except KeyError as exc:

            raise KeyError(
                f"No zero-sequence impedance registered "
                f"for element {element_id!r}."
            ) from exc

    # =========================================================
    # SEQUENCE DATASET
    # =========================================================

    def _get_sequence_data(
        self,
        sequence: str,
    ) -> dict[Any, complex]:
        """
        Return the impedance dictionary for a sequence.
        """

        if not isinstance(
            sequence,
            str,
        ):
            raise TypeError(
                "sequence must be a string."
            )

        normalized = sequence.lower().strip()

        if normalized in {
            "positive",
            "z1",
            "1",
        }:

            return self.positive

        if normalized in {
            "negative",
            "z2",
            "2",
        }:

            return self.negative

        if normalized in {
            "zero",
            "z0",
            "0",
        }:

            return self.zero

        raise ValueError(
            "Invalid sequence. Expected "
            "'positive', 'negative', or 'zero'."
        )

    # =========================================================
    # TOTAL PATH IMPEDANCE
    # =========================================================

    def total_impedance(
        self,
        elements,
        sequence: str = "positive",
    ) -> complex:
        """
        Calculate the series impedance of an explicitly
        supplied element path.

        Parameters
        ----------
        elements:
            Iterable of registered element identifiers.

        sequence:
            Sequence network to use:

                "positive"
                "negative"
                "zero"

        Returns
        -------
        complex
            Equivalent series impedance.

        Notes
        -----
        This is intentionally a simple series-path operation.

        It must NOT be interpreted as a general network reduction.
        Parallel paths, meshed networks, sequence bus matrices,
        grounding connections, and transformer phase shifts require
        a higher-level network assembly mechanism.
        """

        if elements is None:
            raise ValueError(
                "elements cannot be None."
            )

        data = self._get_sequence_data(
            sequence
        )

        total = complex(
            0.0,
            0.0,
        )

        for element in elements:

            if element not in data:
                raise KeyError(
                    f"Element {element!r} has no "
                    f"{sequence} sequence impedance."
                )

            total += data[
                element
            ]

        if not (
            np.isfinite(
                total.real
            )
            and
            np.isfinite(
                total.imag
            )
        ):
            raise RuntimeError(
                "Equivalent sequence impedance became "
                "non-finite."
            )

        return total

    # =========================================================
    # ELEMENT MANAGEMENT
    # =========================================================

    def contains(
        self,
        element_id: Any,
    ) -> bool:
        """
        Return whether an element has sequence data.
        """

        return (
            element_id in self.positive
        )

    def remove_element(
        self,
        element_id: Any,
    ) -> None:
        """
        Remove an element from all sequence datasets.
        """

        self.positive.pop(
            element_id,
            None,
        )

        self.negative.pop(
            element_id,
            None,
        )

        self.zero.pop(
            element_id,
            None,
        )

    def clear(self) -> None:
        """
        Remove all sequence impedance data.
        """

        self.positive.clear()
        self.negative.clear()
        self.zero.clear()

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return sequence-network diagnostic information.
        """

        return {
            "model": "SequenceNetwork",
            "positive_elements": len(
                self.positive
            ),
            "negative_elements": len(
                self.negative
            ),
            "zero_elements": len(
                self.zero
            ),
            "elements": len(
                self.positive
            ),
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            "SequenceNetwork("
            f"elements={len(self.positive)}"
            ")"
        )


__all__ = [
    "SequenceNetwork",
]
