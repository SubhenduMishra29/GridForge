"""
GridForge Short-Circuit Impedance Matrix
========================================

File:
    core/solver/short_circuit/impedance_matrix.py

GridForge Short-Circuit Solver V2.0
-----------------------------------

Provides bus impedance matrix (Zbus) services for short-circuit
studies.

Responsibilities
----------------
- Obtain the network Ybus.
- Validate Ybus dimensions and numerical values.
- Compute Zbus from Ybus.
- Provide bus Thevenin impedances.
- Provide transfer impedances.
- Preserve the network's Ybus without modification.
- Provide deterministic diagnostics.

This module does NOT:
- Build or modify network topology.
- Perform load-flow calculations.
- Calculate fault currents directly.
- Perform sequence-network calculations.
- Determine fault type.
- Perform protection decisions.

Architecture
------------
    Network
       │
       ▼
      Ybus
       │
       ▼
  ImpedanceMatrix
       │
       ├── Zbus
       ├── Zth
       └── Ztransfer

Notes
-----
The V2 reference implementation uses a dense NumPy inverse.

The public interface deliberately isolates the Zbus operation so
that a future sparse, factorization-based, or accelerated backend
can replace the numerical implementation without changing the
short-circuit solver API.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

import numpy as np


class ImpedanceMatrix:
    """
    Bus impedance matrix service for short-circuit studies.

    Parameters
    ----------
    network:
        GridForge Network object containing the ordered buses and
        an available Ybus.

    Notes
    -----
    ``build()`` computes:

        Zbus = inv(Ybus)

    The network itself is never modified by this class.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        network: Any,
    ) -> None:

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

        # Store the Ybus signature used to construct Zbus.
        #
        # This is diagnostic/cache metadata only. The network
        # remains the authoritative owner of Ybus.
        self._ybus_shape: tuple[int, int] | None = None

    # =========================================================
    # YBUS ACCESS
    # =========================================================

    def _get_ybus(self) -> Any:
        """
        Obtain and validate the network Ybus.

        Returns
        -------
        matrix-like
            Validated Ybus matrix.

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

        if len(
            Ybus.shape
        ) != 2:
            raise ValueError(
                "Network Ybus must be a two-dimensional matrix."
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

        return Ybus

    # =========================================================
    # MATRIX NORMALIZATION
    # =========================================================

    @staticmethod
    def _to_dense_matrix(
        matrix: Any,
        name: str,
    ) -> np.ndarray:
        """
        Normalize a dense or sparse matrix to a NumPy array.

        Parameters
        ----------
        matrix:
            Dense NumPy matrix or sparse matrix supporting
            ``toarray()``.

        name:
            Diagnostic matrix name.

        Returns
        -------
        np.ndarray
            Two-dimensional complex-valued matrix.
        """

        if matrix is None:
            raise ValueError(
                f"{name} cannot be None."
            )

        try:

            if hasattr(
                matrix,
                "toarray",
            ):

                result = np.asarray(
                    matrix.toarray(),
                    dtype=complex,
                )

            else:

                result = np.asarray(
                    matrix,
                    dtype=complex,
                )

        except Exception as exc:

            raise ValueError(
                f"{name} could not be converted to a "
                "numerical matrix."
            ) from exc

        if result.ndim != 2:
            raise ValueError(
                f"{name} must be two-dimensional."
            )

        if result.shape[0] != result.shape[1]:
            raise ValueError(
                f"{name} must be square: "
                f"received shape {result.shape}."
            )

        if not np.all(
            np.isfinite(result.real)
        ) or not np.all(
            np.isfinite(result.imag)
        ):

            raise ValueError(
                f"{name} contains NaN or infinite values."
            )

        return result

    # =========================================================
    # BUILD ZBUS
    # =========================================================

    def build(
        self,
    ) -> np.ndarray:
        """
        Build the bus impedance matrix.

        Returns
        -------
        np.ndarray
            Complex Zbus matrix.

        Raises
        ------
        ValueError
            If Ybus is invalid.

        RuntimeError
            If Ybus is singular or inversion fails.

        Notes
        -----
        The calculation is:

            Zbus = Ybus^-1

        The original network Ybus is never modified.
        """

        Ybus = self._get_ybus()

        matrix = self._to_dense_matrix(
            Ybus,
            "Ybus",
        )

        n = matrix.shape[0]

        if n == 0:
            self.Zbus = np.empty(
                (0, 0),
                dtype=complex,
            )

            self._ybus_shape = (
                0,
                0,
            )

            return self.Zbus

        # -----------------------------------------------------
        # Numerical inversion
        # -----------------------------------------------------

        try:

            Zbus = np.linalg.inv(
                matrix
            )

        except np.linalg.LinAlgError as exc:

            raise RuntimeError(
                "Ybus is singular. Cannot calculate Zbus."
            ) from exc

        except Exception as exc:

            raise RuntimeError(
                "Unexpected Zbus calculation failure: "
                f"{exc}"
            ) from exc

        Zbus = np.asarray(
            Zbus,
            dtype=complex,
        )

        # -----------------------------------------------------
        # Validate result
        # -----------------------------------------------------

        if Zbus.shape != (
            n,
            n,
        ):

            raise RuntimeError(
                "Zbus calculation returned an incorrect "
                f"matrix shape: expected {(n, n)}, "
                f"received {Zbus.shape}."
            )

        if not np.all(
            np.isfinite(Zbus.real)
        ) or not np.all(
            np.isfinite(Zbus.imag)
        ):

            raise RuntimeError(
                "Zbus calculation produced NaN or "
                "infinite values."
            )

        self.Zbus = Zbus

        self._ybus_shape = (
            n,
            n,
        )

        return self.Zbus

    # =========================================================
    # ENSURE ZBUS
    # =========================================================

    def _ensure_built(
        self,
    ) -> np.ndarray:
        """
        Ensure that Zbus is available for a query.

        Returns
        -------
        np.ndarray
            Current Zbus matrix.
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
        name: str = "bus_index",
    ) -> int:
        """
        Validate a zero-based bus index.
        """

        if isinstance(
            bus_index,
            bool,
        ) or not isinstance(
            bus_index,
            (int, np.integer),
        ):

            raise TypeError(
                f"{name} must be an integer."
            )

        bus_index = int(
            bus_index
        )

        n = len(
            self.network.buses
        )

        if bus_index < 0 or bus_index >= n:

            raise IndexError(
                f"{name} out of range: "
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
        Return the driving-point/Thevenin impedance at a bus.

        Parameters
        ----------
        bus_index:
            Zero-based network bus index.

        Returns
        -------
        complex
            Zth = Zbus[i, i].
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
            Zbus[from_bus, to_bus].
        """

        from_bus = self._validate_bus_index(
            from_bus,
            "from_bus",
        )

        to_bus = self._validate_bus_index(
            to_bus,
            "to_bus",
        )

        Zbus = self._ensure_built()

        return complex(
            Zbus[
                from_bus,
                to_bus,
            ]
        )

    # =========================================================
    # DIRECT MATRIX ACCESS
    # =========================================================

    def get_zbus(
        self,
        copy: bool = True,
    ) -> np.ndarray:
        """
        Return the calculated Zbus matrix.

        Parameters
        ----------
        copy:
            If True, return an independent copy.

        Returns
        -------
        np.ndarray
            Zbus matrix.

        Notes
        -----
        A copy is returned by default so callers cannot
        accidentally modify the internal matrix.
        """

        Zbus = self._ensure_built()

        if copy:
            return Zbus.copy()

        return Zbus

    # =========================================================
    # REBUILD
    # =========================================================

    def invalidate(
        self,
    ) -> None:
        """
        Discard the internally cached Zbus.

        This does not modify the network or its Ybus.

        Call this when the authoritative network Ybus has
        changed and Zbus must be rebuilt.
        """

        self.Zbus = None
        self._ybus_shape = None

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
                "version": "2.0",
                "status": "NOT_BUILT",
                "size": None,
            }

        return {
            "component": "ImpedanceMatrix",
            "version": "2.0",
            "status": "BUILT",
            "size": self.Zbus.shape,
            "dtype": str(
                self.Zbus.dtype
            ),
            "backend": "numpy",
            "network_ybus_shape": self._ybus_shape,
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
