"""
GridForge Short Circuit Impedance Matrix
========================================

File:
    core/solver/short_circuit/impedance_matrix.py

GridForge Short Circuit Solver V1.0
-----------------------------------

Provides impedance-matrix services required by the short-circuit
solver.

Responsibilities
----------------
- Validate the network Ybus.
- Construct Zbus from Ybus.
- Provide Thevenin driving-point impedance.
- Provide transfer impedance.
- Provide diagnostic information.

The module does NOT:
- Build Ybus.
- Modify network topology.
- Perform load-flow calculations.
- Perform fault classification.
- Calculate fault currents directly.
- Perform sequence-network assembly.
- Perform protection decisions.

Ybus ownership remains with the GridForge network/numerical
infrastructure.

Reference relationship:

    Zbus = inv(Ybus)

For a fault at bus k:

    Zth = Zbus[k, k]

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

import numpy as np


class ImpedanceMatrix:
    """
    Build and query the bus impedance matrix Zbus.

    Parameters
    ----------
    network:
        GridForge Network object containing an already-built
        Ybus matrix.

    Notes
    -----
    This V1.0 implementation uses dense NumPy inversion as the
    numerical reference implementation.

    The public interface intentionally does not expose the
    inversion backend, allowing a future sparse or specialized
    implementation without changing the short-circuit API.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self, network: Any):
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

        self.Zbus: np.ndarray | None = None

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_network(self) -> np.ndarray:
        """
        Validate and return the network Ybus.

        Returns
        -------
        np.ndarray
            Valid complex Ybus matrix.

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
                "Network Ybus has not been built."
            )

        if not hasattr(
            Ybus,
            "shape",
        ):
            raise ValueError(
                "Network Ybus must provide a matrix shape."
            )

        n = len(
            self.network.buses
        )

        expected_shape = (
            n,
            n,
        )

        if Ybus.shape != expected_shape:
            raise ValueError(
                "Ybus dimension does not match network bus "
                f"count: expected {expected_shape}, "
                f"received {Ybus.shape}."
            )

        if len(Ybus.shape) != 2:
            raise ValueError(
                "Ybus must be a two-dimensional matrix."
            )

        if n == 0:
            raise ValueError(
                "Cannot construct Zbus for an empty network."
            )

        # -----------------------------------------------------
        # Normalize dense/sparse input.
        # -----------------------------------------------------

        if hasattr(
            Ybus,
            "toarray",
        ):
            matrix = np.asarray(
                Ybus.toarray(),
                dtype=complex,
            )
        else:
            matrix = np.asarray(
                Ybus,
                dtype=complex,
            )

        if matrix.shape != expected_shape:
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
                "Ybus contains NaN or infinite values."
            )

        return matrix

    # =========================================================
    # BUILD ZBUS
    # =========================================================

    def build(self) -> np.ndarray:
        """
        Construct the bus impedance matrix.

        Returns
        -------
        np.ndarray
            Complex Zbus matrix.

        Raises
        ------
        ValueError
            If Ybus is unavailable or invalid.

        RuntimeError
            If Ybus is singular or inversion fails.
        """

        Ybus = self._validate_network()

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

    def _ensure_built(self) -> np.ndarray:
        """
        Return Zbus, building it when necessary.
        """

        if self.Zbus is None:
            return self.build()

        return self.Zbus

    # =========================================================
    # BUS INDEX VALIDATION
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
    # THÉVENIN IMPEDANCE
    # =========================================================

    def get_thevenin_impedance(
        self,
        bus_index: int,
    ) -> complex:
        """
        Return the driving-point/Thevenin impedance at a bus.

        Parameters
        ----------
        bus_index:
            Zero-based index into network.buses.

        Returns
        -------
        complex
            Zbus[bus_index, bus_index].
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
        Return transfer impedance between two buses.

        Parameters
        ----------
        from_bus:
            Zero-based source bus index.

        to_bus:
            Zero-based receiving bus index.

        Returns
        -------
        complex
            Zbus[from_bus, to_bus].
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

    def get_zbus(self) -> np.ndarray:
        """
        Return the complete Zbus matrix.

        A copy is returned so callers cannot accidentally
        modify the internal impedance matrix.
        """

        Zbus = self._ensure_built()

        return np.array(
            Zbus,
            dtype=complex,
            copy=True,
        )

    # =========================================================
    # RESET
    # =========================================================

    def reset(self) -> None:
        """
        Clear the cached Zbus matrix.

        This does not modify the network.
        """

        self.Zbus = None

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return impedance-matrix diagnostic information.
        """

        if self.Zbus is None:
            return {
                "solver": "ImpedanceMatrix",
                "status": "NOT_BUILT",
                "buses": len(
                    self.network.buses
                ),
            }

        return {
            "solver": "ImpedanceMatrix",
            "status": "BUILT",
            "buses": len(
                self.network.buses
            ),
            "size": tuple(
                self.Zbus.shape
            ),
            "dtype": str(
                self.Zbus.dtype
            ),
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        status = (
            "built"
            if self.Zbus is not None
            else "not_built"
        )

        return (
            "ImpedanceMatrix("
            f"buses={len(self.network.buses)}, "
            f"status={status}"
            ")"
        )


__all__ = [
    "ImpedanceMatrix",
]
