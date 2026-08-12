"""
GridForge Short-Circuit Impedance Matrix V2
===========================================

File:
    core/solver/short_circuit/impedance_matrix.py

Purpose
-------
Build and provide access to the bus impedance matrix (Zbus)
used by GridForge short-circuit studies.

Primary responsibilities
------------------------
- Validate the network Ybus.
- Construct Zbus from Ybus.
- Provide Thevenin driving-point impedance.
- Provide transfer impedance.
- Provide deterministic diagnostics.
- Preserve complex numerical precision.

This module does NOT:
- Build Ybus.
- Modify network topology.
- Perform fault calculations.
- Calculate sequence components.
- Perform protection calculations.
- Perform relay coordination.
- Perform power-flow calculations.

Architecture
------------
Network
   │
   └── Ybus
        │
        ▼
ImpedanceMatrix
        │
        └── Zbus
             ├── Zii  → Thevenin impedance
             └── Zij  → Transfer impedance

Numerical convention
--------------------
All impedances are complex quantities:

    Z = R + jX

Zbus is defined as:

    V = Zbus I

where:

    V = bus-voltage vector
    I = injected-current vector

Therefore the diagonal element:

    Zbus[i, i]

is the driving-point/Thevenin impedance seen at bus i
for the network represented by Ybus.

V2 design principles
--------------------
- Explicit validation.
- No pseudo-inverse fallback.
- No silent singularity handling.
- No topology mutation.
- No hidden Ybus construction.
- Complex-valued numerical representation.
- Deterministic failure on singular or invalid Ybus.
- Stable public interface for future sparse/GPU implementations.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from typing import Any

import numpy as np


class ImpedanceMatrix:
    """
    Bus impedance matrix service for GridForge
    short-circuit studies.

    Parameters
    ----------
    network:
        GridForge Network object.

    Notes
    -----
    The network is expected to own the already-built Ybus.

    This class does not own or construct network topology.
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

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_network(self) -> None:
        """
        Validate the minimum network interface required by
        the impedance-matrix calculation.
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
        Retrieve and validate the network Ybus.

        Returns
        -------
        np.ndarray
            Complex square Ybus matrix.

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

        if Ybus.shape != (
            n,
            n,
        ):
            raise ValueError(
                "Ybus dimension does not match network "
                f"bus count: expected {(n, n)}, "
                f"received {Ybus.shape}."
            )

        try:

            matrix = np.asarray(
                Ybus,
                dtype=complex,
            )

        except Exception as exc:

            raise ValueError(
                "Network Ybus could not be converted "
                "to a complex numerical matrix."
            ) from exc

        if matrix.shape != (
            n,
            n,
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
                "Ybus contains NaN or infinite values."
            )

        return matrix

    # =========================================================
    # BUILD ZBUS
    # =========================================================

    def build(self) -> np.ndarray:
        """
        Build the bus impedance matrix.

        The mathematical relationship is:

            Zbus = Ybus^-1

        The implementation uses a linear solve rather than
        explicitly calling ``np.linalg.inv``:

            Ybus Zbus = I

        This avoids unnecessary explicit matrix inversion
        while producing the complete Zbus matrix.

        Returns
        -------
        np.ndarray
            Complex Zbus matrix.

        Raises
        ------
        RuntimeError
            If Ybus is singular or the numerical solve fails.
        """

        Ybus = self._get_ybus()

        n = Ybus.shape[0]

        identity = np.eye(
            n,
            dtype=complex,
        )

        try:

            Zbus = np.linalg.solve(
                Ybus,
                identity,
            )

        except np.linalg.LinAlgError as exc:

            raise RuntimeError(
                "Ybus is singular or numerically "
                "non-invertible. Cannot construct Zbus."
            ) from exc

        except Exception as exc:

            raise RuntimeError(
                "Unexpected failure while constructing Zbus: "
                f"{exc}"
            ) from exc

        Zbus = np.asarray(
            Zbus,
            dtype=complex,
        )

        if Zbus.shape != (
            n,
            n,
        ):
            raise RuntimeError(
                "Zbus construction returned an incorrect "
                f"matrix shape: {Zbus.shape}."
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
                "Zbus contains NaN or infinite values."
            )

        self.Zbus = Zbus

        return self.Zbus.copy()

    # =========================================================
    # ENSURE ZBUS
    # =========================================================

    def _ensure_built(self) -> None:
        """
        Ensure that Zbus is available.
        """

        if self.Zbus is None:
            self.build()

    # =========================================================
    # BUS INDEX VALIDATION
    # =========================================================

    def _validate_bus_index(
        self,
        bus_index: int,
    ) -> int:
        """
        Validate a positional bus index.

        Returns
        -------
        int
            Validated integer index.
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
        Return the driving-point/Thevenin impedance at a bus.

        Parameters
        ----------
        bus_index:
            Zero-based positional index in network.buses.

        Returns
        -------
        complex
            Zbus[bus_index, bus_index].
        """

        bus_index = self._validate_bus_index(
            bus_index
        )

        self._ensure_built()

        assert self.Zbus is not None

        return complex(
            self.Zbus[
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
            Source/injection bus index.

        to_bus:
            Observation bus index.

        Returns
        -------
        complex
            Corresponding Zbus matrix element.
        """

        from_bus = self._validate_bus_index(
            from_bus
        )

        to_bus = self._validate_bus_index(
            to_bus
        )

        self._ensure_built()

        assert self.Zbus is not None

        return complex(
            self.Zbus[
                from_bus,
                to_bus,
            ]
        )

    # =========================================================
    # FULL MATRIX ACCESS
    # =========================================================

    def get_zbus(self) -> np.ndarray:
        """
        Return a copy of the complete Zbus matrix.

        Returns
        -------
        np.ndarray
            Complex bus impedance matrix.
        """

        self._ensure_built()

        assert self.Zbus is not None

        return self.Zbus.copy()

    # =========================================================
    # RESET
    # =========================================================

    def reset(self) -> None:
        """
        Discard the currently stored Zbus matrix.

        This does not modify the network or Ybus.
        """

        self.Zbus = None

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return impedance-matrix diagnostics.
        """

        if self.Zbus is None:

            return {
                "component": "ImpedanceMatrix",
                "version": "2.0",
                "status": "NOT_BUILT",
                "buses": len(
                    self.network.buses
                ),
            }

        return {
            "component": "ImpedanceMatrix",
            "version": "2.0",
            "status": "BUILT",
            "buses": len(
                self.network.buses
            ),
            "shape": tuple(
                self.Zbus.shape
            ),
            "complex": True,
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
            f"status='{status}'"
            ")"
        )


__all__ = [
    "ImpedanceMatrix",
]
