"""
GridForge Y-Bus Builder
=======================

GridForge Network Layer V2

Builds the network bus-admittance matrix from the canonical electrical
model objects assembled in ``core.network.Network``.

Responsibilities
----------------
- Build deterministic bus indexing.
- Assemble the network Y-bus.
- Stamp in-service transmission/distribution lines.
- Stamp in-service transformers.
- Stamp bus shunts.
- Produce a sparse CSR admittance matrix.
- Perform structural matrix validation.
- Provide lightweight diagnostic information.

Architecture
------------

    core/model/
        Bus
        Line
        Transformer
        Shunt
              |
              v
    core/network/
        Network
        YBusBuilder
              |
              v
    core/analysis/
        Study orchestration
              |
              v
    core/solver/
        Numerical algorithms

The canonical electrical model objects remain owned by
``core.model``.

YBusBuilder only reads their electrical parameters.

The YBusBuilder does NOT:

- Define electrical equipment models.
- Modify Bus state.
- Modify Line state.
- Modify Transformer state.
- Modify Shunt state.
- Perform power-flow calculations.
- Perform Newton-Raphson iterations.
- Calculate short-circuit currents.
- Perform contingency analysis.
- Perform protection calculations.
- Perform dynamic simulation.
- Decide PV/PQ/Slack bus classification.
- Perform engineering validation.
- Manage GUI state.

Y-Bus Convention
----------------
For a conventional passive network:

    I = Ybus V

The matrix is assembled using complex nodal admittances.

Line Model
----------
A line is represented using the standard nominal-pi model:

                    y + jb/2
              +----/\\/\\/\\/----+
              |                |
              |                |
        Bus i +                + Bus j
              |                |
              +----/\\/\\/\\/----+
                    y + jb/2

where:

    y = 1 / (r + jx)

and ``b_pu`` is the total line charging susceptance.

Therefore each line contributes:

    Yii += y + j*b/2
    Yjj += y + j*b/2
    Yij -= y
    Yji -= y

Transformer Model
-----------------
The transformer uses a complex off-nominal tap:

    a = tap_ratio * exp(j * phase_shift)

For series admittance:

    y = 1 / (r + jx)

the standard complex tap formulation is:

    Yii += y / |a|²
    Yij -= y / conj(a)
    Yji -= y / a
    Yjj += y

Optional transformer shunt susceptance is divided equally between
the two sides.

Unlike a zero-phase transformer, a transformer with a non-zero phase
shift generally produces a non-symmetric Y-bus.

Shunts
------
Bus shunt conductance/susceptance is added directly to the diagonal.

If a bus provides:

    g_shunt
    b_shunt

then:

    Yii += g_shunt + j*b_shunt

The model layer remains responsible for defining the meaning and
units of these quantities.

Sparse Representation
---------------------
The assembled matrix is constructed using SciPy ``lil_matrix`` for
efficient incremental stamping and converted to ``csr_matrix`` for
normal downstream numerical use.

GridForge V2 Status
-------------------
This module is part of the Network Layer V2 audit baseline.

Changes require evidence of a genuinely fundamental network
representation requirement that cannot be satisfied by the existing
model, network, solver, or analysis layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix


# =====================================================================
# Y-BUS BUILDER
# =====================================================================

class YBusBuilder:
    """
    Assemble the sparse network bus-admittance matrix.

    Parameters
    ----------
    network :
        GridForge ``Network`` instance.

    Notes
    -----
    The builder reads canonical model objects from the Network.

    It does not take ownership of those objects and does not modify
    them.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(self, network) -> None:
        self.network = network

        self.bus_index: dict[Any, int] = {}
        self.Ybus: csr_matrix | None = None

    # =================================================================
    # BUS INDEX
    # =================================================================

    def build_bus_index(self) -> dict[Any, int]:
        """
        Build the deterministic bus-ID to matrix-index mapping.

        Returns
        -------
        dict
            Mapping:

                bus.id -> matrix index

        Notes
        -----
        The ordering is exactly the ordering of
        ``network.buses``.
        """

        index: dict[Any, int] = {}

        for position, bus in enumerate(
            self.network.buses
        ):

            if not hasattr(bus, "id"):
                raise TypeError(
                    "Every network bus must provide "
                    "an 'id' attribute."
                )

            if bus.id in index:
                raise ValueError(
                    f"Duplicate bus ID: {bus.id}"
                )

            index[bus.id] = position

        self.bus_index = index

        return self.bus_index

    # =================================================================
    # MAIN BUILD
    # =================================================================

    def build(self) -> csr_matrix:
        """
        Build and return the network Y-bus.

        Returns
        -------
        scipy.sparse.csr_matrix
            Complex sparse bus-admittance matrix.

        Notes
        -----
        The returned matrix follows:

            I = Ybus V

        The builder does not solve any network equations.
        """

        self.build_bus_index()

        n = len(self.network.buses)

        Y = lil_matrix(
            (n, n),
            dtype=complex,
        )

        # -------------------------------------------------------------
        # Lines
        # -------------------------------------------------------------

        for line in getattr(
            self.network,
            "lines",
            [],
        ):
            self.stamp_line(
                Y,
                line,
            )

        # -------------------------------------------------------------
        # Transformers
        # -------------------------------------------------------------

        for transformer in getattr(
            self.network,
            "transformers",
            [],
        ):
            self.stamp_transformer(
                Y,
                transformer,
            )

        # -------------------------------------------------------------
        # Bus shunts
        # -------------------------------------------------------------

        self.stamp_bus_shunts(Y)

        # -------------------------------------------------------------
        # Convert to downstream-friendly sparse representation.
        # -------------------------------------------------------------

        self.Ybus = Y.tocsr()

        # -------------------------------------------------------------
        # Structural validation.
        #
        # Deliberately do NOT enforce matrix symmetry.
        #
        # A transformer phase shift can legitimately produce:
        #
        #     Yij != Yji
        #
        # Therefore symmetry is not a universal Y-bus invariant.
        # -------------------------------------------------------------

        self._validate_dimensions()
        self._validate_finite()

        # -------------------------------------------------------------
        # Store the assembled representation on Network.
        # -------------------------------------------------------------

        self.network.Ybus = self.Ybus

        return self.Ybus

    # =================================================================
    # LINE STAMP
    # =================================================================

    def stamp_line(
        self,
        Y: lil_matrix,
        line: Any,
    ) -> None:
        """
        Stamp an in-service line using the nominal-pi model.

        Parameters
        ----------
        Y :
            Mutable sparse matrix being assembled.

        line :
            Canonical GridForge Line model.

        Raises
        ------
        ValueError
            If the line has effectively zero series impedance.

        Key equations
        -------------
            z = r + jx
            y = 1 / z

        For total charging susceptance ``b_pu``:

            Yii += y + j*b/2
            Yjj += y + j*b/2
            Yij -= y
            Yji -= y
        """

        if not getattr(
            line,
            "in_service",
            True,
        ):
            return

        from_bus = getattr(
            line,
            "from_bus",
            None,
        )

        to_bus = getattr(
            line,
            "to_bus",
            None,
        )

        if from_bus is None or to_bus is None:
            raise ValueError(
                f"Line '{getattr(line, 'id', line)}' "
                "must provide from_bus and to_bus."
            )

        i = self._bus_index(
            from_bus,
            line,
        )

        j = self._bus_index(
            to_bus,
            line,
        )

        r = float(line.r_pu)
        x = float(line.x_pu)

        z = complex(
            r,
            x,
        )

        if abs(z) <= 1e-12:
            raise ValueError(
                f"Zero impedance line detected: {line}"
            )

        y = 1.0 / z

        b_total = float(
            getattr(
                line,
                "b_pu",
                0.0,
            )
        )

        y_shunt = 1j * b_total / 2.0

        # Diagonal elements.
        Y[i, i] += y + y_shunt
        Y[j, j] += y + y_shunt

        # Mutual elements.
        Y[i, j] -= y
        Y[j, i] -= y

    # =================================================================
    # TRANSFORMER STAMP
    # =================================================================

    def stamp_transformer(
        self,
        Y: lil_matrix,
        transformer: Any,
    ) -> None:
        """
        Stamp an in-service transformer.

        Parameters
        ----------
        Y :
            Mutable sparse matrix being assembled.

        transformer :
            Canonical GridForge Transformer model.

        Notes
        -----
        The transformer uses a complex off-nominal tap:

            a = tap * exp(j*theta)

        The resulting matrix is generally non-symmetric when
        ``phase_shift_deg != 0``.
        """

        if not getattr(
            transformer,
            "in_service",
            True,
        ):
            return

        from_bus = getattr(
            transformer,
            "from_bus",
            None,
        )

        to_bus = getattr(
            transformer,
            "to_bus",
            None,
        )

        if from_bus is None or to_bus is None:
            raise ValueError(
                f"Transformer "
                f"'{getattr(transformer, 'id', transformer)}' "
                "must provide from_bus and to_bus."
            )

        i = self._bus_index(
            from_bus,
            transformer,
        )

        j = self._bus_index(
            to_bus,
            transformer,
        )

        r = float(
            transformer.r_pu
        )

        x = float(
            transformer.x_pu
        )

        z = complex(
            r,
            x,
        )

        if abs(z) <= 1e-12:
            raise ValueError(
                f"Zero impedance transformer detected: "
                f"{transformer}"
            )

        y = 1.0 / z

        # -------------------------------------------------------------
        # Tap ratio
        # -------------------------------------------------------------

        tap = float(
            getattr(
                transformer,
                "tap_ratio",
                1.0,
            )
        )

        if not np.isfinite(tap):
            raise ValueError(
                f"Transformer tap ratio must be finite: "
                f"{transformer}"
            )

        if abs(tap) <= 1e-12:
            raise ValueError(
                f"Transformer tap ratio cannot be zero: "
                f"{transformer}"
            )

        # -------------------------------------------------------------
        # Phase shift
        # -------------------------------------------------------------

        shift_deg = float(
            getattr(
                transformer,
                "phase_shift_deg",
                0.0,
            )
        )

        if not np.isfinite(shift_deg):
            raise ValueError(
                f"Transformer phase shift must be finite: "
                f"{transformer}"
            )

        shift = np.deg2rad(
            shift_deg
        )

        a = (
            tap
            * np.exp(1j * shift)
        )

        # -------------------------------------------------------------
        # Optional magnetizing/shunt susceptance.
        # -------------------------------------------------------------

        b_shunt = float(
            getattr(
                transformer,
                "b_shunt_pu",
                0.0,
            )
        )

        y_shunt = 1j * b_shunt / 2.0

        # -------------------------------------------------------------
        # Transformer stamp.
        #
        # For:
        #
        #     a = tap * exp(j*shift)
        #
        # the standard complex tap formulation is:
        #
        #     Yii += y / |a|²
        #     Yij -= y / conj(a)
        #     Yji -= y / a
        #     Yjj += y
        # -------------------------------------------------------------

        Y[i, i] += (
            y / (a * np.conj(a))
            + y_shunt
        )

        Y[j, j] += (
            y
            + y_shunt
        )

        Y[i, j] -= (
            y / np.conj(a)
        )

        Y[j, i] -= (
            y / a
        )

    # =================================================================
    # BUS SHUNTS
    # =================================================================

    def stamp_bus_shunts(
        self,
        Y: lil_matrix,
    ) -> None:
        """
        Stamp bus-level shunt conductance and susceptance.

        Expected optional Bus attributes:

            g_shunt
            b_shunt

        The contribution is:

            Yii += g_shunt + j*b_shunt

        Notes
        -----
        Missing shunt attributes are treated as zero.
        """

        for bus in self.network.buses:

            idx = self._bus_index(
                bus,
                bus,
            )

            g = float(
                getattr(
                    bus,
                    "g_shunt",
                    0.0,
                )
            )

            b = float(
                getattr(
                    bus,
                    "b_shunt",
                    0.0,
                )
            )

            if not np.isfinite(g):
                raise ValueError(
                    f"Bus '{bus.id}' has non-finite "
                    "g_shunt."
                )

            if not np.isfinite(b):
                raise ValueError(
                    f"Bus '{bus.id}' has non-finite "
                    "b_shunt."
                )

            if g != 0.0 or b != 0.0:
                Y[idx, idx] += complex(
                    g,
                    b,
                )

        # -------------------------------------------------------------
        # Explicit Shunt model collection.
        #
        # If the canonical Shunt model exposes a direct bus endpoint,
        # stamp it here. This keeps shunt equipment separate from the
        # Bus object while allowing Network.shunts to participate in
        # Y-bus assembly.
        # -------------------------------------------------------------

        for shunt in getattr(
            self.network,
            "shunts",
            [],
        ):

            if not getattr(
                shunt,
                "in_service",
                True,
            ):
                continue

            bus = getattr(
                shunt,
                "bus",
                None,
            )

            if bus is None:
                continue

            idx = self._bus_index(
                bus,
                shunt,
            )

            g = float(
                getattr(
                    shunt,
                    "g_pu",
                    0.0,
                )
            )

            b = float(
                getattr(
                    shunt,
                    "b_pu",
                    0.0,
                )
            )

            if not np.isfinite(g):
                raise ValueError(
                    f"Shunt '{getattr(shunt, 'id', shunt)}' "
                    "has non-finite conductance."
                )

            if not np.isfinite(b):
                raise ValueError(
                    f"Shunt '{getattr(shunt, 'id', shunt)}' "
                    "has non-finite susceptance."
                )

            if g != 0.0 or b != 0.0:
                Y[idx, idx] += complex(
                    g,
                    b,
                )

    # =================================================================
    # INDEX VALIDATION
    # =================================================================

    def _bus_index(
        self,
        bus: Any,
        element: Any,
    ) -> int:
        """
        Resolve a bus object to its Y-bus matrix index.
        """

        if not hasattr(
            bus,
            "id",
        ):
            raise TypeError(
                f"Element '{getattr(element, 'id', element)}' "
                "references a bus without an 'id'."
            )

        bus_id = bus.id

        if bus_id not in self.bus_index:
            raise ValueError(
                f"Element '{getattr(element, 'id', element)}' "
                f"references unregistered bus '{bus_id}'."
            )

        return self.bus_index[bus_id]

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate_dimensions(self) -> None:
        """
        Verify that Y-bus dimensions match the network bus count.
        """

        if self.Ybus is None:
            raise RuntimeError(
                "Ybus has not been built."
            )

        n = len(
            self.network.buses
        )

        if self.Ybus.shape != (
            n,
            n,
        ):
            raise ValueError(
                "Invalid Ybus dimensions: "
                f"expected {(n, n)}, "
                f"got {self.Ybus.shape}."
            )

    def _validate_finite(self) -> None:
        """
        Verify that all assembled Y-bus entries are finite.

        Complex entries are checked by examining their real and
        imaginary components.
        """

        if self.Ybus is None:
            raise RuntimeError(
                "Ybus has not been built."
            )

        data = self.Ybus.data

        if not (
            np.all(
                np.isfinite(
                    data.real
                )
            )
            and np.all(
                np.isfinite(
                    data.imag
                )
            )
        ):
            raise ValueError(
                "Ybus contains non-finite values."
            )

    # =================================================================
    # ACCESS
    # =================================================================

    def get_ybus(self) -> csr_matrix:
        """
        Return the most recently built Y-bus.

        Raises
        ------
        RuntimeError
            If Y-bus has not yet been built.
        """

        if self.Ybus is None:
            raise RuntimeError(
                "Ybus has not been built. "
                "Call build() first."
            )

        return self.Ybus

    # =================================================================
    # SUMMARY
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return concise Y-bus assembly information.
        """

        return {
            "buses": len(
                self.network.buses
            ),
            "lines": len(
                getattr(
                    self.network,
                    "lines",
                    [],
                )
            ),
            "transformers": len(
                getattr(
                    self.network,
                    "transformers",
                    [],
                )
            ),
            "shunts": len(
                getattr(
                    self.network,
                    "shunts",
                    [],
                )
            ),
            "matrix_size": (
                None
                if self.Ybus is None
                else self.Ybus.shape
            ),
            "nnz": (
                None
                if self.Ybus is None
                else self.Ybus.nnz
            ),
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        matrix_size = (
            None
            if self.Ybus is None
            else self.Ybus.shape
        )

        return (
            f"<YBusBuilder "
            f"buses={len(self.network.buses)}, "
            f"matrix_size={matrix_size}>"
        )
