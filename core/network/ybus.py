# ============================================================
# File: core/network/ybus.py
# GridForge V2 — Network Layer
# ============================================================
"""
GridForge Network Layer V2
==========================

Y-Bus Builder
-------------

Builds the network bus-admittance matrix from canonical electrical
model objects assembled in ``core.network.Network``.

Responsibilities
----------------
- Build deterministic bus indexing.
- Assemble the network Y-bus.
- Stamp in-service transmission/distribution lines.
- Stamp in-service transformers.
- Stamp bus shunts.
- Stamp supported canonical shunt elements.
- Produce a sparse CSR admittance matrix.
- Perform structural matrix validation.
- Provide lightweight diagnostic information.

Does NOT
--------
- Define electrical equipment models.
- Modify canonical model objects.
- Perform power-flow calculations.
- Perform Newton-Raphson iterations.
- Calculate short-circuit currents.
- Perform contingency analysis.
- Perform protection calculations.
- Perform dynamic simulation.
- Decide PV/PQ/Slack classification.
- Perform engineering validation.
- Manage GUI state.

Architecture
------------

    core/model/
        Canonical electrical entities
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

Y-Bus Convention
----------------

For a conventional passive network:

    I = Ybus V

The matrix is assembled using complex nodal admittances.

Line Model
----------

Lines use the nominal-pi model:

    y = 1 / (r + jx)

with total charging susceptance ``b_pu``:

    Yii += y + j*b/2
    Yjj += y + j*b/2
    Yij -= y
    Yji -= y

Transformer Model
-----------------

Transformers use a complex off-nominal tap:

    a = tap_ratio * exp(j * phase_shift)

with:

    y = 1 / (r + jx)

The standard complex-tap formulation is:

    Yii += y / |a|²
    Yij -= y / conj(a)
    Yji -= y / a
    Yjj += y

Optional transformer shunt susceptance is divided equally between
the two sides.

A transformer with non-zero phase shift can produce a non-symmetric
Y-bus.

Shunts
------

Bus shunt quantities are added directly to the diagonal:

    Yii += g_shunt + j*b_shunt

Canonical Shunt objects may additionally contribute directly at
their associated bus.

Sparse Representation
---------------------

Assembly uses ``scipy.sparse.lil_matrix`` and converts the result
to ``scipy.sparse.csr_matrix`` for downstream numerical use.

Validation
----------

The builder validates:

- deterministic bus indexing,
- registered bus references,
- matrix dimensions,
- finite matrix values.

Y-bus symmetry is deliberately NOT enforced because phase-shifting
transformers can legitimately produce a non-symmetric matrix.

Terminal Endpoint Resolution
----------------------------

The model layer uses Terminal objects as the authoritative physical
connection representation.

For two-terminal branch equipment:

    element.from_terminal.endpoint
    element.to_terminal.endpoint

are therefore the authoritative physical references.

The Y-bus remains bus-centric because numerical admittance matrices
are assembled between electrical buses.

Accordingly, this builder resolves:

    terminal
        -> endpoint
        -> bus compatibility resolution
        -> canonical Network bus
        -> bus matrix index

The compatibility ``terminal.bus`` accessor is used only after the
authoritative terminal endpoint has been established.

The builder does not modify terminals or endpoint relationships.

GridForge V2 Status
-------------------

This module is part of the GridForge Network Layer V2 freeze
baseline.

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
    their state.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        network: Any,
    ) -> None:
        """
        Initialize the Y-bus builder.
        """

        if network is None:
            raise ValueError(
                "YBusBuilder requires a Network instance."
            )

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
            Mapping ``bus.id -> matrix index``.

        Notes
        -----
        The ordering is exactly the ordering of
        ``network.buses``.
        """

        index: dict[Any, int] = {}

        for position, bus in enumerate(
            self.network.buses
        ):
            if not hasattr(
                bus,
                "id",
            ):
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

        No network equations are solved by this method.
        """

        self.build_bus_index()

        n = len(
            self.network.buses
        )

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
        # Bus-level shunts and canonical Shunt elements.
        # -------------------------------------------------------------

        self.stamp_bus_shunts(Y)

        # -------------------------------------------------------------
        # Convert to downstream-friendly CSR representation.
        # -------------------------------------------------------------

        self.Ybus = Y.tocsr()

        # -------------------------------------------------------------
        # Structural validation.
        #
        # Do NOT enforce symmetry:
        #
        # phase-shifting transformers can legitimately produce
        #
        #     Yij != Yji
        # -------------------------------------------------------------

        self._validate_dimensions()
        self._validate_finite()

        # -------------------------------------------------------------
        # Store derived representation on Network.
        # -------------------------------------------------------------

        self.network.Ybus = self.Ybus

        return self.Ybus

    # =================================================================
    # TERMINAL / BUS RESOLUTION
    # =================================================================

    @staticmethod
    def _resolve_terminal_bus(
        terminal: Any,
        element: Any,
        terminal_name: str,
        element_type: str,
    ) -> Any:
        """
        Resolve a branch Terminal to its canonical electrical Bus.

        Parameters
        ----------
        terminal :
            Authoritative Terminal object.

        element :
            Canonical branch model.

        terminal_name : str
            Diagnostic terminal name.

        element_type : str
            Logical element type.

        Returns
        -------
        object
            Canonical Bus-like object.

        Raises
        ------
        AttributeError
            If the terminal contract is missing.

        ValueError
            If the terminal is disconnected or cannot resolve to a
            Bus.

        Notes
        -----
        ``terminal.endpoint`` is authoritative.

        ``terminal.bus`` is used only as the model-layer compatibility
        resolution after the endpoint has been established.

        The concrete Bus class is deliberately not imported here.
        """

        if terminal is None:
            raise AttributeError(
                f"{element_type.capitalize()} "
                f"'{getattr(element, 'id', element)}' "
                f"must provide a '{terminal_name}' Terminal."
            )

        if not hasattr(
            terminal,
            "endpoint",
        ):
            raise AttributeError(
                f"{element_type.capitalize()} "
                f"'{getattr(element, 'id', element)}' "
                f"has an invalid '{terminal_name}' Terminal: "
                "missing endpoint."
            )

        endpoint = getattr(
            terminal,
            "endpoint",
            None,
        )

        if endpoint is None:
            raise ValueError(
                f"{element_type.capitalize()} "
                f"'{getattr(element, 'id', element)}' "
                f"has a disconnected '{terminal_name}' Terminal."
            )

        # -------------------------------------------------------------
        # Establish that the authoritative endpoint exists before
        # using the compatibility bus accessor.
        # -------------------------------------------------------------

        bus = getattr(
            terminal,
            "bus",
            None,
        )

        if bus is None:
            raise ValueError(
                f"{element_type.capitalize()} "
                f"'{getattr(element, 'id', element)}' "
                f"'{terminal_name}' Terminal endpoint "
                "does not resolve to a Bus."
            )

        if not hasattr(
            bus,
            "id",
        ):
            raise AttributeError(
                f"{element_type.capitalize()} "
                f"'{getattr(element, 'id', element)}' "
                f"'{terminal_name}' Terminal resolved to an "
                "endpoint without an 'id' attribute."
            )

        return bus

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
        """

        if not getattr(
            line,
            "in_service",
            True,
        ):
            return

        # -------------------------------------------------------------
        # AUTHORITATIVE TERMINAL CONNECTION
        # -------------------------------------------------------------

        from_terminal = getattr(
            line,
            "from_terminal",
            None,
        )

        to_terminal = getattr(
            line,
            "to_terminal",
            None,
        )

        from_bus = self._resolve_terminal_bus(
            from_terminal,
            line,
            "from_terminal",
            "line",
        )

        to_bus = self._resolve_terminal_bus(
            to_terminal,
            line,
            "to_terminal",
            "line",
        )

        i = self._bus_index(
            from_bus,
            line,
        )

        j = self._bus_index(
            to_bus,
            line,
        )

        r = float(
            line.r_pu
        )

        x = float(
            line.x_pu
        )

        if not np.isfinite(r) or not np.isfinite(x):
            raise ValueError(
                f"Line '{getattr(line, 'id', line)}' "
                "has non-finite impedance parameters."
            )

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

        if not np.isfinite(b_total):
            raise ValueError(
                f"Line '{getattr(line, 'id', line)}' "
                "has non-finite b_pu."
            )

        y_shunt = 1j * b_total / 2.0

        # -------------------------------------------------------------
        # Nominal-pi line stamp.
        # -------------------------------------------------------------

        Y[i, i] += y + y_shunt
        Y[j, j] += y + y_shunt

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
        The transformer uses:

            a = tap * exp(j*shift)

        and:

            Yii += y / |a|²
            Yij -= y / conj(a)
            Yji -= y / a
            Yjj += y
        """

        if not getattr(
            transformer,
            "in_service",
            True,
        ):
            return

        # -------------------------------------------------------------
        # AUTHORITATIVE TERMINAL CONNECTION
        # -------------------------------------------------------------

        from_terminal = getattr(
            transformer,
            "from_terminal",
            None,
        )

        to_terminal = getattr(
            transformer,
            "to_terminal",
            None,
        )

        from_bus = self._resolve_terminal_bus(
            from_terminal,
            transformer,
            "from_terminal",
            "transformer",
        )

        to_bus = self._resolve_terminal_bus(
            to_terminal,
            transformer,
            "to_terminal",
            "transformer",
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

        if not np.isfinite(r) or not np.isfinite(x):
            raise ValueError(
                f"Transformer "
                f"'{getattr(transformer, 'id', transformer)}' "
                "has non-finite impedance parameters."
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
        # Optional transformer shunt susceptance.
        # -------------------------------------------------------------

        b_shunt = float(
            getattr(
                transformer,
                "b_shunt_pu",
                0.0,
            )
        )

        if not np.isfinite(b_shunt):
            raise ValueError(
                f"Transformer shunt susceptance must be finite: "
                f"{transformer}"
            )

        y_shunt = 1j * b_shunt / 2.0

        # -------------------------------------------------------------
        # Transformer stamp.
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
        Stamp bus-level shunt quantities and canonical Shunt objects.

        Bus attributes:

            g_shunt
            b_shunt

        contribute:

            Yii += g_shunt + j*b_shunt

        Canonical Shunt objects are supported when they expose:

            bus
            g_pu
            b_pu

        Missing bus-level shunt attributes are treated as zero.
        """

        # -------------------------------------------------------------
        # Bus-level shunts
        # -------------------------------------------------------------

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
                    f"Bus '{bus.id}' has non-finite g_shunt."
                )

            if not np.isfinite(b):
                raise ValueError(
                    f"Bus '{bus.id}' has non-finite b_shunt."
                )

            if g != 0.0 or b != 0.0:
                Y[idx, idx] += complex(
                    g,
                    b,
                )

        # -------------------------------------------------------------
        # Canonical Shunt model collection
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

            # ---------------------------------------------------------
            # Shunt is terminal-first in the model layer.
            # ---------------------------------------------------------

            terminal = getattr(
                shunt,
                "terminal",
                None,
            )

            if terminal is None:
                raise ValueError(
                    f"Shunt "
                    f"'{getattr(shunt, 'id', shunt)}' "
                    "must provide a terminal reference."
                )

            if not hasattr(
                terminal,
                "endpoint",
            ):
                raise AttributeError(
                    f"Shunt "
                    f"'{getattr(shunt, 'id', shunt)}' "
                    "terminal is missing endpoint."
                )

            endpoint = getattr(
                terminal,
                "endpoint",
                None,
            )

            if endpoint is None:
                raise ValueError(
                    f"Shunt "
                    f"'{getattr(shunt, 'id', shunt)}' "
                    "has a disconnected terminal."
                )

            bus = getattr(
                terminal,
                "bus",
                None,
            )

            if bus is None:
                raise ValueError(
                    f"Shunt "
                    f"'{getattr(shunt, 'id', shunt)}' "
                    "terminal endpoint does not resolve to a bus."
                )

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
                    f"Shunt "
                    f"'{getattr(shunt, 'id', shunt)}' "
                    "has non-finite conductance."
                )

            if not np.isfinite(b):
                raise ValueError(
                    f"Shunt "
                    f"'{getattr(shunt, 'id', shunt)}' "
                    "has non-finite susceptance."
                )

            if g != 0.0 or b != 0.0:
                Y[idx, idx] += complex(
                    g,
                    b,
                )

    # =================================================================
    # BUS INDEX RESOLUTION
    # =================================================================

    def _bus_index(
        self,
        bus: Any,
        element: Any,
    ) -> int:
        """
        Resolve a canonical bus object to its matrix index.
        """

        if not hasattr(
            bus,
            "id",
        ):
            raise TypeError(
                f"Element "
                f"'{getattr(element, 'id', element)}' "
                "references a bus without an 'id'."
            )

        bus_id = bus.id

        if bus_id not in self.bus_index:
            raise ValueError(
                f"Element "
                f"'{getattr(element, 'id', element)}' "
                f"references unregistered bus '{bus_id}'."
            )

        return self.bus_index[bus_id]

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate_dimensions(
        self,
    ) -> None:
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

    # -----------------------------------------------------------------

    def _validate_finite(
        self,
    ) -> None:
        """
        Verify that all Y-bus entries are finite.
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

    def get_ybus(
        self,
    ) -> csr_matrix:
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

    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Return concise Y-bus assembly diagnostics.
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

    def __repr__(
        self,
    ) -> str:
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
