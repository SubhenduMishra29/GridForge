"""
GridForge Short-Circuit Impedance Matrix
========================================

File:
    core/solver/short_circuit/impedance_matrix.py

GridForge Short-Circuit Solver V2.0
-----------------------------------

Reference impedance-matrix service for short-circuit studies.

Responsibilities
----------------
- Obtain the network Ybus.
- Validate Ybus dimensions and numerical values.
- Construct the bus impedance matrix Zbus.
- Provide Thevenin driving-point impedances.
- Provide transfer impedances.
- Preserve deterministic bus-index semantics.
- Provide diagnostics.

This module does NOT:
- Build Ybus.
- Modify Network topology.
- Modify Bus state.
- Perform fault calculations.
- Perform sequence-network calculations.
- Perform protection calculations.
- Perform short-circuit study orchestration.

Network ownership
-----------------
The electrical network and its Ybus remain owned by:

    core.network/

The short-circuit solver consumes that state but does not construct
or mutate it.

Numerical convention
--------------------
For a nonsingular bus-admittance matrix:

    Zbus = inv(Ybus)

The driving-point Thevenin impedance at bus i is:

    Zth(i) = Zbus[i, i]

The transfer impedance between buses i and j is:

    Ztransfer(i, j) = Zbus[i, j]

This V2 implementation is intentionally a dense NumPy reference
implementation. The public interface is kept backend-independent so
that a sparse or GPU implementation can replace the numerical backend
later without changing the short-circuit API.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

import numpy as np


class ImpedanceMatrix:
    """
    Build and provide access to the network bus impedance matrix.

    Parameters
    ----------
    network:
        GridForge Network object.

    Notes
    -----
    The network must already contain a valid Ybus.

    This class never calls ``network.build_ybus()`` and never modifies
    the network.
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

        self._built = False

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_network(self) -> None:
        """
        Validate the minimum network interface.
        """

        if not hasattr(
            self.network,
            "buses",
        ):
            raise ValueError(
                "Network must provide a 'buses' collection."
            )

        n = len(
            self.network.buses
        )

        if n == 0:
            raise ValueError(
                "Network contains no buses."
            )

    # =========================================================
    # YBUS ACCESS
    # =========================================================

    def _get_ybus(self) -> np.ndarray:
        """
        Obtain and validate the network Ybus.

        Returns
        -------
        numpy.ndarray
            Complex bus-admittance matrix.

        Raises
        ------
        ValueError
            If Ybus is unavailable or invalid.
        """

        self._validate_network()

        Ybus = getattr(
            self.network,
            "Ybus",
            None,
        )

        if Ybus is None:
            raise ValueError(
                "Network Ybus has not been built. "
                "Short-circuit solver requires an existing "
                "network Ybus."
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

        if Ybus.shape != (
            n,
            n,
        ):
            raise ValueError(
                "Ybus dimension does not match network bus "
                f"count: expected {(n, n)}, "
                f"received {Ybus.shape}."
            )

        try:

            matrix = np.asarray(
                Ybus,
                dtype=complex,
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "Network Ybus cannot be converted to a "
                "complex numerical matrix."
            ) from exc

        if matrix.shape != (
            n,
            n,
        ):
            raise ValueError(
                "Ybus shape changed during numerical "
                "normalization."
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

    def build(self) -> np.ndarray:
        """
        Construct the bus impedance matrix.

        Returns
        -------
        numpy.ndarray
            Complex Zbus matrix.

        Raises
        ------
        RuntimeError
            If Ybus is singular or cannot be inverted.
        """

        Ybus = self._get_ybus()

        try:

            Zbus = np.linalg.inv(
                Ybus
            )

        except np.linalg.LinAlgError as exc:

            self.Zbus = None
            self._built = False

            raise RuntimeError(
                "Ybus is singular. "
                "Cannot construct Zbus for short-circuit analysis."
            ) from exc

        except Exception as exc:

            self.Zbus = None
            self._built = False

            raise RuntimeError(
                "Unexpected failure while constructing Zbus: "
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

            self.Zbus = None
            self._built = False

            raise RuntimeError(
                "Zbus construction produced NaN or "
                "infinite values."
            )

        self.Zbus = Zbus
        self._built = True

        return self.Zbus

    # =========================================================
    # ENSURE BUILT
    # =========================================================

    def _ensure_built(self) -> np.ndarray:
        """
        Return Zbus, constructing it if necessary.
        """

        if (
            not self._built
            or self.Zbus is None
        ):
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

        n = len(
            self.network.buses
        )

        if not (
            0 <= bus_index < n
        ):
            raise IndexError(
                "Bus index out of range: "
                f"{bus_index}. "
                f"Valid range is 0 to {n - 1}."
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
        Return the driving-point Thevenin impedance at a bus.

        Parameters
        ----------
        bus_index:
            Zero-based index into ``network.buses``.

        Returns
        -------
        complex
            Zbus[i, i].
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

    def get_zbus(
        self,
        copy: bool = True,
    ) -> np.ndarray:
        """
        Return the complete Zbus matrix.

        Parameters
        ----------
        copy:
            If True, return an independent copy.

        Returns
        -------
        numpy.ndarray
            Complex Zbus matrix.
        """

        Zbus = self._ensure_built()

        if copy:
            return Zbus.copy()

        return Zbus

    # =========================================================
    # RESET
    # =========================================================

    def reset(self) -> None:
        """
        Clear the cached Zbus matrix.

        This does not modify the network.
        """

        self.Zbus = None
        self._built = False

    # =========================================================
    # STATUS
    # =========================================================

    @property
    def is_built(self) -> bool:
        """
        Return whether a valid Zbus is currently available.
        """

        return bool(
            self._built
            and self.Zbus is not None
        )

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return impedance-matrix diagnostics.
        """

        n = len(
            self.network.buses
        )

        return {
            "component": "ImpedanceMatrix",
            "version": "2.0",
            "buses": n,
            "built": self.is_built,
            "size": (
                tuple(
                    self.Zbus.shape
                )
                if self.Zbus is not None
                else None
            ),
            "backend": "numpy",
            "network_mutation": False,
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
            f"built={self.is_built}"
            ")"
        )


__all__ = [
    "ImpedanceMatrix",
]
