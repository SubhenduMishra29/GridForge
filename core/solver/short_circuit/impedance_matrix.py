"""
GridForge Short-Circuit Impedance Matrix
========================================

File:
    core/solver/short_circuit/impedance_matrix.py

GridForge Short-Circuit Solver V1.0
-----------------------------------

Provides the bus impedance matrix:

    Zbus = inv(Ybus)

The Zbus matrix is used for:

- Three-phase fault calculations.
- Thevenin equivalent extraction.
- Transfer impedance extraction.
- Short-circuit numerical studies.

Responsibilities
----------------
- Validate the network Ybus.
- Construct Zbus from an existing Ybus.
- Provide diagonal Thevenin impedances.
- Provide transfer impedances.
- Provide numerical diagnostics.

This module does NOT:
- Build Ybus.
- Modify network topology.
- Modify Bus objects.
- Perform fault calculations.
- Perform sequence-network calculations.
- Perform protection decisions.

Architecture
------------

    core/network/
          |
          | existing Ybus
          v
    ImpedanceMatrix
          |
          | Zbus
          v
    Fault Calculators

Design Rule
-----------
Ybus ownership remains outside this module.

The network must already contain a valid Ybus before
``build()`` is called.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

import numpy as np


class ImpedanceMatrix:
    """
    Construct and provide access to the bus impedance matrix.

    Parameters
    ----------
    network:
        GridForge Network object containing an already-built
        Ybus matrix.

    Notes
    -----
    The implementation uses NumPy inversion as the V1.0
    numerical reference implementation.

    Future sparse or factorization-based implementations may
    replace the internal backend without changing the public
    interface.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        network: Any,
    ) -> None:
        """
        Initialize the impedance-matrix service.
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
        # Zbus remains None until explicitly built.
        # -----------------------------------------------------

        self.Zbus: np.ndarray | None = None

    # =========================================================
    # YBUS VALIDATION
    # =========================================================

    def _get_ybus(self) -> np.ndarray:
        """
        Return and validate the existing network Ybus.

        Returns
        -------
        np.ndarray
            Valid square complex Ybus matrix.

        Raises
        ------
        ValueError
            If Ybus is unavailable or invalid.
        """

        Ybus = getattr(
            self.network,
            "Ybus",
            None,
        )

        if Ybus is None:
            raise ValueError(
                "Network Ybus has not been built. "
                "Build Ybus before constructing Zbus."
            )

        if not hasattr(
            Ybus,
            "shape",
        ):
            raise ValueError(
                "Network Ybus must provide a matrix shape."
            )

        if len(
            Ybus.shape
        ) != 2:
            raise ValueError(
                "Network Ybus must be two-dimensional."
            )

        rows, cols = Ybus.shape

        if rows != cols:
            raise ValueError(
                "Network Ybus must be square: "
                f"received shape {Ybus.shape}."
            )

        expected_size = len(
            self.network.buses
        )

        if rows != expected_size:
            raise ValueError(
                "Ybus dimension does not match network bus "
                f"count: expected {(expected_size, expected_size)}, "
                f"received {Ybus.shape}."
            )

        try:
            matrix = np.asarray(
                Ybus,
                dtype=complex,
            )

        except Exception as exc:
            raise ValueError(
                "Network Ybus could not be converted to "
                "a complex numerical matrix."
            ) from exc

        if matrix.shape != (
            rows,
            cols,
        ):
            raise ValueError(
                "Ybus shape changed during normalization."
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
                "Network Ybus contains NaN or infinite values."
            )

        return matrix

    # =========================================================
    # BUILD ZBUS
    # =========================================================

    def build(
        self,
    ) -> np.ndarray:
        """
        Construct the bus impedance matrix.

        The calculation is:

            Zbus = Ybus^-1

        Returns
        -------
        np.ndarray
            Complex bus impedance matrix.

        Raises
        ------
        ValueError
            If Ybus is invalid.

        RuntimeError
            If Ybus is singular or cannot be inverted.
        """

        Ybus = self._get_ybus()

        # -----------------------------------------------------
        # Empty network.
        # -----------------------------------------------------

        if Ybus.shape[0] == 0:
            self.Zbus = np.empty(
                (0, 0),
                dtype=complex,
            )

            return self.Zbus

        # -----------------------------------------------------
        # Matrix inversion.
        # -----------------------------------------------------

        try:
            Zbus = np.linalg.inv(
                Ybus
            )

        except np.linalg.LinAlgError as exc:
            raise RuntimeError(
                "Ybus is singular. "
                "Cannot calculate Zbus."
            ) from exc

        except Exception as exc:
            raise RuntimeError(
                "Unexpected failure while calculating Zbus: "
                f"{exc}"
            ) from exc

        Zbus = np.asarray(
            Zbus,
            dtype=complex,
        )

        # -----------------------------------------------------
        # Validate result.
        # -----------------------------------------------------

        if Zbus.shape != Ybus.shape:
            raise RuntimeError(
                "Calculated Zbus has an invalid dimension: "
                f"expected {Ybus.shape}, "
                f"received {Zbus.shape}."
            )

        if not np.all(
            np.isfinite(
                Zbus.real
            )
        ) or not np.all(
            np.isfinite(
                Zbus.imag
            )
        ):
            raise RuntimeError(
                "Calculated Zbus contains NaN or "
                "infinite values."
            )

        self.Zbus = Zbus

        return self.Zbus

    # =========================================================
    # ENSURE BUILT
    # =========================================================

    def _ensure_built(
        self,
    ) -> np.ndarray:
        """
        Return Zbus, constructing it if necessary.
        """

        if self.Zbus is None:
            return self.build()

        return self.Zbus

    # =========================================================
    # INDEX VALIDATION
    # =========================================================

    def _validate_bus_index(
        self,
        bus_index: int,
    ) -> int:
        """
        Validate a numerical bus index.
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

        n = len(
            self.network.buses
        )

        if not (
            0 <= bus_index < n
        ):
            raise IndexError(
                "Bus index out of range: "
                f"{bus_index}. Valid range is "
                f"0 to {n - 1}."
            )

        return bus_index

    # =========================================================
    # THEVENIN IMPEDANCE
    # =========================================================

    def get_thevenin_impedance(
        self,
        bus_index: int,
    ) -> complex:
        """
        Return the Thevenin impedance seen at a bus.

        For the Zbus formulation:

            Zth = Zbus[i, i]

        Parameters
        ----------
        bus_index:
            Zero-based index in ``network.buses``.

        Returns
        -------
        complex
            Thevenin impedance in the network's impedance
            base.
        """

        bus_index = self._validate_bus_index(
            bus_index
        )

        Zbus = self._ensure_built()

        return complex(
            Zbus[
                bus_index,
                bus_index,
            ]
        )

    # =========================================================
    # TRANSFER IMPEDANCE
    # =========================================================

    def get_transfer_impedance(
        self,
        from_bus: int,
        to_bus: int,
    ) -> complex:
        """
        Return the transfer impedance between two buses.

        Parameters
        ----------
        from_bus:
            Zero-based source bus index.

        to_bus:
            Zero-based destination bus index.

        Returns
        -------
        complex
            Transfer impedance Zbus[from_bus, to_bus].
        """

        from_bus = self._validate_bus_index(
            from_bus
        )

        to_bus = self._validate_bus_index(
            to_bus
        )

        Zbus = self._ensure_built()

        return complex(
            Zbus[
                from_bus,
                to_bus,
            ]
        )

    # =========================================================
    # MATRIX ACCESS
    # =========================================================

    def get_matrix(
        self,
    ) -> np.ndarray:
        """
        Return the complete Zbus matrix.

        Returns
        -------
        np.ndarray
            Complex Zbus matrix.

        Notes
        -----
        A copy is returned so callers cannot accidentally
        modify the internally stored impedance matrix.
        """

        Zbus = self._ensure_built()

        return Zbus.copy()

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
    ) -> None:
        """
        Discard the currently stored Zbus matrix.

        This does not modify the network or its Ybus.
        """

        self.Zbus = None

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(
        self,
    ) -> dict:
        """
        Return impedance-matrix diagnostics.
        """

        if self.Zbus is None:
            return {
                "component": "ImpedanceMatrix",
                "status": "NOT_BUILT",
                "buses": len(
                    self.network.buses
                ),
            }

        return {
            "component": "ImpedanceMatrix",
            "status": "BUILT",
            "buses": len(
                self.network.buses
            ),
            "size": self.Zbus.shape,
            "backend": "numpy",
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
            "ImpedanceMatrix("
            f"buses={len(self.network.buses)}, "
            f"built={self.Zbus is not None}"
            ")"
        )


__all__ = [
    "ImpedanceMatrix",
]
