# ============================================================
# File: core/network/ybus.py
# GridForge V2 — Y-Bus Builder
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Y-Bus Builder.

The YBusBuilder constructs the network nodal-admittance matrix from
the canonical electrical model objects registered on a Network.

Architecture
------------

    core.model
        canonical electrical models
              |
              v
        Network
              |
              +---- NetworkRegistry
              |
              +---- BusIndex
              |
              +---- YBusBuilder
                         |
                         v
                       Ybus

Responsibilities
----------------
YBusBuilder:

- Builds the nodal admittance matrix.
- Uses Network's canonical BusIndex.
- Resolves Line and Transformer terminals through the shared
  endpoint resolver.
- Stamps supported branch and shunt models.
- Produces a scipy sparse CSR matrix.
- Performs structural checks required to construct the matrix.

Does NOT
--------
YBusBuilder does not:

- Register network elements.
- Remove network elements.
- Build topology.
- Detect islands.
- Assign bus indices.
- Modify canonical model objects.
- Perform power-flow calculations.
- Perform short-circuit calculations.
- Perform engineering validation.
- Manage Network dirty/revision state.
- Implement command/application behavior.
- Perform GUI operations.

Ownership
---------

    NetworkRegistry
        owns membership

    BusIndex
        owns bus.id -> matrix index

    TopologyManager
        owns connectivity

    YBusBuilder
        owns Y-bus construction

    NetworkState
        owns derived-state validity

Terminal Architecture
---------------------

For branch elements:

    Line
        from_terminal -> endpoint -> Bus
        to_terminal   -> endpoint -> Bus

    Transformer
        from_terminal -> endpoint -> Bus
        to_terminal   -> endpoint -> Bus

For shunts:

    Shunt
        terminal -> endpoint -> Bus

The shared endpoint resolver is used instead of duplicating
terminal-resolution logic.

Electrical Sign Convention
---------------------------

For a branch with series admittance y:

                 y
        i ------------------ j

the standard nodal contribution is:

        Yii += y
        Yjj += y
        Yij -= y
        Yji -= y

Transformer stamping supports the conventional complex off-nominal
tap formulation when the model exposes a tap ratio and phase shift.

GridForge V2
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix

from .endpoint import resolve_terminal_bus


class YBusBuilder:
    """
    Construct the network nodal-admittance matrix.

    The builder is intentionally stateless with respect to the
    resulting matrix. The Network owns the resulting Ybus object.
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        network: Any,
    ) -> None:

        if network is None:
            raise ValueError(
                "YBusBuilder requires a Network."
            )

        self.network = network

    # ============================================================
    # PUBLIC BUILD API
    # ============================================================

    def build(self) -> csr_matrix:
        """
        Construct and return the Network Y-bus matrix.

        Returns
        -------
        scipy.sparse.csr_matrix
            Complex nodal-admittance matrix.

        Notes
        -----
        The Network must already contain the canonical model
        objects. Bus indexing is ensured before stamping.
        """

        buses = self.network.buses

        if not buses:
            raise ValueError(
                "Cannot build Y-bus for a Network with no buses."
            )

        self.network.index.ensure(
            buses,
        )

        n = len(buses)

        Y = lil_matrix(
            (n, n),
            dtype=np.complex128,
        )

        # --------------------------------------------------------
        # LINES
        # --------------------------------------------------------

        for line in self.network.lines:

            if not self._is_in_service(line):
                continue

            self._stamp_line(
                Y,
                line,
            )

        # --------------------------------------------------------
        # TRANSFORMERS
        # --------------------------------------------------------

        for transformer in self.network.transformers:

            if not self._is_in_service(transformer):
                continue

            self._stamp_transformer(
                Y,
                transformer,
            )

        # --------------------------------------------------------
        # SHUNTS
        # --------------------------------------------------------

        for shunt in self.network.shunts:

            if not self._is_in_service(shunt):
                continue

            self._stamp_shunt(
                Y,
                shunt,
            )

        return Y.tocsr()

    # ============================================================
    # LINE STAMPING
    # ============================================================

    def _stamp_line(
        self,
        Y: lil_matrix,
        line: Any,
    ) -> None:
        """
        Stamp a Line into the Y-bus.

        The Line model must expose either:

            - series impedance ``z``, or
            - ``r`` and ``x``

        Optional shunt charging may be supplied through:

            - ``b``
            - ``b_shunt``
            - ``b_total``

        The builder intentionally does not create or modify the
        Line model.
        """

        from_bus = self._resolve_terminal_bus(
            line,
            "from_terminal",
        )

        to_bus = self._resolve_terminal_bus(
            line,
            "to_terminal",
        )

        i = self._bus_index(
            from_bus,
        )

        j = self._bus_index(
            to_bus,
        )

        z = self._line_impedance(
            line,
        )

        if z == 0:
            raise ValueError(
                f"Line '{getattr(line, 'id', line)}' "
                "has zero series impedance."
            )

        y_series = 1.0 / z

        # --------------------------------------------------------
        # Standard pi-model shunt susceptance.
        #
        # If total B is supplied, half goes to each terminal.
        # --------------------------------------------------------

        b_total = self._first_numeric_attribute(
            line,
            (
                "b_total",
                "b_shunt",
                "b",
            ),
            default=0.0,
        )

        y_shunt_half = 1j * complex(
            b_total,
        ) / 2.0

        Y[i, i] += y_series + y_shunt_half
        Y[j, j] += y_series + y_shunt_half
        Y[i, j] -= y_series
        Y[j, i] -= y_series

    # ============================================================
    # TRANSFORMER STAMPING
    # ============================================================

    def _stamp_transformer(
        self,
        Y: lil_matrix,
        transformer: Any,
    ) -> None:
        """
        Stamp a two-winding transformer.

        The transformer series impedance is obtained from:

            z

        or:

            r + j*x

        Optional complex tap information is supported.

        Accepted tap representations:

            tap
            turns_ratio
            tap_ratio

        Optional phase shift:

            phase_shift
            phase_shift_deg
            angle_deg

        If no tap is supplied, the transformer is stamped as a
        unity-ratio branch.
        """

        from_bus = self._resolve_terminal_bus(
            transformer,
            "from_terminal",
        )

        to_bus = self._resolve_terminal_bus(
            transformer,
            "to_terminal",
        )

        i = self._bus_index(
            from_bus,
        )

        j = self._bus_index(
            to_bus,
        )

        z = self._transformer_impedance(
            transformer,
        )

        if z == 0:
            raise ValueError(
                f"Transformer "
                f"'{getattr(transformer, 'id', transformer)}' "
                "has zero series impedance."
            )

        y_series = 1.0 / z

        tap = self._transformer_tap(
            transformer,
        )

        if tap == 0:
            raise ValueError(
                f"Transformer "
                f"'{getattr(transformer, 'id', transformer)}' "
                "has zero tap ratio."
            )

        # --------------------------------------------------------
        # Complex off-nominal tap:
        #
        # a = |tap| * exp(j*theta)
        #
        # Standard branch stamping:
        #
        # Yii += y / |a|²
        # Yij -= y / conj(a)
        # Yji -= y / a
        # Yjj += y
        # --------------------------------------------------------

        Y[i, i] += y_series / (
            abs(tap) ** 2
        )

        Y[i, j] -= y_series / np.conj(
            tap,
        )

        Y[j, i] -= y_series / tap

        Y[j, j] += y_series

        # --------------------------------------------------------
        # Optional transformer shunt/admittance contribution.
        # --------------------------------------------------------

        b_total = self._first_numeric_attribute(
            transformer,
            (
                "b_total",
                "b_shunt",
                "b",
            ),
            default=0.0,
        )

        if b_total != 0.0:

            y_shunt_half = 1j * complex(
                b_total,
            ) / 2.0

            Y[i, i] += y_shunt_half
            Y[j, j] += y_shunt_half

    # ============================================================
    # SHUNT STAMPING
    # ============================================================

    def _stamp_shunt(
        self,
        Y: lil_matrix,
        shunt: Any,
    ) -> None:
        """
        Stamp a single-terminal shunt.

        Supported representations include:

            y
            admittance
            b
            susceptance

        If ``y`` or ``admittance`` is supplied it is used directly.

        If only ``b`` or ``susceptance`` is supplied, the shunt is
        interpreted as:

            Y = jB
        """

        bus = self._resolve_shunt_bus(
            shunt,
        )

        index = self._bus_index(
            bus,
        )

        admittance = self._shunt_admittance(
            shunt,
        )

        Y[index, index] += admittance

    # ============================================================
    # ENDPOINT RESOLUTION
    # ============================================================

    def _resolve_terminal_bus(
        self,
        element: Any,
        terminal_name: str,
    ) -> Any:
        """
        Resolve an element terminal to its canonical Bus.

        Endpoint resolution belongs to the shared network endpoint
        contract and is not duplicated here.
        """

        terminal = getattr(
            element,
            terminal_name,
            None,
        )

        if terminal is None:
            raise ValueError(
                f"{type(element).__name__} "
                f"'{getattr(element, 'id', element)}' "
                f"does not provide '{terminal_name}'."
            )

        bus = resolve_terminal_bus(
            terminal,
        )

        if bus is None:
            raise ValueError(
                f"{type(element).__name__} "
                f"'{getattr(element, 'id', element)}' "
                f"terminal '{terminal_name}' does not resolve "
                "to a Bus."
            )

        if bus not in self.network.buses:
            raise ValueError(
                f"{type(element).__name__} "
                f"'{getattr(element, 'id', element)}' "
                f"terminal '{terminal_name}' resolves to Bus "
                f"'{getattr(bus, 'id', bus)}', which is not "
                "registered on this Network."
            )

        return bus

    # ------------------------------------------------------------

    def _resolve_shunt_bus(
        self,
        shunt: Any,
    ) -> Any:
        """
        Resolve a single-terminal shunt to its Bus.
        """

        terminal = getattr(
            shunt,
            "terminal",
            None,
        )

        if terminal is None:
            raise ValueError(
                f"Shunt "
                f"'{getattr(shunt, 'id', shunt)}' "
                "does not provide a terminal."
            )

        bus = resolve_terminal_bus(
            terminal,
        )

        if bus is None:
            raise ValueError(
                f"Shunt "
                f"'{getattr(shunt, 'id', shunt)}' "
                "terminal does not resolve to a Bus."
            )

        if bus not in self.network.buses:
            raise ValueError(
                f"Shunt "
                f"'{getattr(shunt, 'id', shunt)}' "
                f"resolves to Bus "
                f"'{getattr(bus, 'id', bus)}', which is not "
                "registered on this Network."
            )

        return bus

    # ============================================================
    # BUS INDEX
    # ============================================================

    def _bus_index(
        self,
        bus: Any,
    ) -> int:
        """
        Obtain the matrix index of a canonical Bus.

        BusIndex remains the sole owner of bus-to-matrix indexing.
        """

        try:
            return self.network.index.get(
                bus.id,
            )

        except (KeyError, AttributeError) as exc:

            raise ValueError(
                f"Bus "
                f"'{getattr(bus, 'id', bus)}' "
                "does not have a valid Y-bus index."
            ) from exc

    # ============================================================
    # LINE IMPEDANCE
    # ============================================================

    @staticmethod
    def _line_impedance(
        line: Any,
    ) -> complex:
        """
        Extract the series impedance from a Line model.
        """

        if hasattr(line, "z"):

            z = getattr(
                line,
                "z",
            )

            if z is not None:
                return complex(z)

        if hasattr(line, "impedance"):

            z = getattr(
                line,
                "impedance",
            )

            if z is not None:
                return complex(z)

        if hasattr(line, "r") and hasattr(line, "x"):

            return complex(
                getattr(line, "r"),
                getattr(line, "x"),
            )

        raise AttributeError(
            f"Line "
            f"'{getattr(line, 'id', line)}' "
            "must provide 'z'/'impedance' or 'r' and 'x'."
        )

    # ============================================================
    # TRANSFORMER IMPEDANCE
    # ============================================================

    @staticmethod
    def _transformer_impedance(
        transformer: Any,
    ) -> complex:
        """
        Extract transformer series impedance.
        """

        if hasattr(transformer, "z"):

            z = getattr(
                transformer,
                "z",
            )

            if z is not None:
                return complex(z)

        if hasattr(transformer, "impedance"):

            z = getattr(
                transformer,
                "impedance",
            )

            if z is not None:
                return complex(z)

        if (
            hasattr(transformer, "r")
            and hasattr(transformer, "x")
        ):

            return complex(
                getattr(transformer, "r"),
                getattr(transformer, "x"),
            )

        raise AttributeError(
            f"Transformer "
            f"'{getattr(transformer, 'id', transformer)}' "
            "must provide 'z'/'impedance' or 'r' and 'x'."
        )

    # ============================================================
    # TRANSFORMER TAP
    # ============================================================

    @staticmethod
    def _transformer_tap(
        transformer: Any,
    ) -> complex:
        """
        Resolve the transformer's complex off-nominal tap ratio.

        Default:

            a = 1 + j0

        Accepted magnitude attributes:

            tap
            tap_ratio
            turns_ratio

        Accepted phase-angle attributes:

            phase_shift
            phase_shift_deg
            angle_deg

        A numeric ``tap`` is treated as the magnitude unless it is
        already complex.
        """

        tap_value: Optional[Any] = None

        for name in (
            "tap",
            "tap_ratio",
            "turns_ratio",
        ):

            if hasattr(transformer, name):

                value = getattr(
                    transformer,
                    name,
                )

                if value is not None:
                    tap_value = value
                    break

        if tap_value is None:
            magnitude = 1.0

        else:
            magnitude = float(
                tap_value,
            )

        phase_deg = 0.0

        for name in (
            "phase_shift_deg",
            "angle_deg",
        ):

            if hasattr(transformer, name):

                value = getattr(
                    transformer,
                    name,
                )

                if value is not None:
                    phase_deg = float(
                        value,
                    )
                    break

        # ``phase_shift`` may be explicitly stored in degrees in
        # many model implementations. Only use it when the explicit
        # degree fields are absent.

        if phase_deg == 0.0 and hasattr(
            transformer,
            "phase_shift",
        ):

            value = getattr(
                transformer,
                "phase_shift",
            )

            if value is not None:
                phase_deg = float(
                    value,
                )

        return (
            magnitude
            * np.exp(
                1j * np.deg2rad(
                    phase_deg,
                )
            )
        )

    # ============================================================
    # SHUNT ADMITTANCE
    # ============================================================

    @staticmethod
    def _shunt_admittance(
        shunt: Any,
    ) -> complex:
        """
        Extract the shunt admittance.

        Direct admittance has priority over susceptance.
        """

        for name in (
            "y",
            "admittance",
        ):

            if hasattr(shunt, name):

                value = getattr(
                    shunt,
                    name,
                )

                if value is not None:
                    return complex(value)

        for name in (
            "b",
            "susceptance",
        ):

            if hasattr(shunt, name):

                value = getattr(
                    shunt,
                    name,
                )

                if value is not None:
                    return 1j * complex(
                        value,
                    )

        raise AttributeError(
            f"Shunt "
            f"'{getattr(shunt, 'id', shunt)}' "
            "must provide 'y'/'admittance' or "
            "'b'/'susceptance'."
        )

    # ============================================================
    # GENERIC NUMERIC ATTRIBUTE
    # ============================================================

    @staticmethod
    def _first_numeric_attribute(
        element: Any,
        names: Tuple[str, ...],
        default: float = 0.0,
    ) -> float:
        """
        Return the first available numeric attribute.
        """

        for name in names:

            if hasattr(element, name):

                value = getattr(
                    element,
                    name,
                )

                if value is not None:
                    return float(value)

        return float(default)

    # ============================================================
    # SERVICE STATE
    # ============================================================

    @staticmethod
    def _is_in_service(
        element: Any,
    ) -> bool:
        """
        Return whether an element contributes to Y-bus.

        Elements without an explicit ``in_service`` property are
        treated as active for compatibility.
        """

        return bool(
            getattr(
                element,
                "in_service",
                True,
            )
        )

    # ============================================================
    # VALIDATION OF RESULT
    # ============================================================

    @staticmethod
    def validate_matrix(
        Ybus: Any,
    ) -> None:
        """
        Perform structural checks on a generated Y-bus.

        This is not engineering validation. It only verifies that
        the produced matrix is suitable as a nodal-admittance
        matrix object.
        """

        if Ybus is None:
            raise ValueError(
                "Y-bus cannot be None."
            )

        if getattr(Ybus, "ndim", None) != 2:
            raise ValueError(
                "Y-bus must be a two-dimensional matrix."
            )

        rows, columns = Ybus.shape

        if rows != columns:
            raise ValueError(
                "Y-bus must be square."
            )

        if not np.iscomplexobj(
            Ybus.data
            if hasattr(Ybus, "data")
            else Ybus
        ):
            raise TypeError(
                "Y-bus must use a complex numerical representation."
            )

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"YBusBuilder("
            f"buses={len(self.network.buses)}, "
            f"lines={len(self.network.lines)}, "
            f"transformers={len(self.network.transformers)}, "
            f"shunts={len(self.network.shunts)}"
            f")"
        )
