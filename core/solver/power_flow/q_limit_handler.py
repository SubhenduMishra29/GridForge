"""
GridForge Generator Reactive Power Limit Handler

Handles:

- PV -> PQ switching when generator reactive power exceeds limits
- PQ -> PV restoration for originally-PV buses
- Preservation of generator voltage setpoints
- Controlled Q-limit state tracking

Responsibilities
----------------
This module manages the operating-mode transition associated
with generator reactive-power limits.

It does NOT:

- Calculate generator reactive power
- Build Ybus
- Calculate power mismatch
- Build the Jacobian
- Perform Newton-Raphson iteration
- Solve linear systems
- Modify network topology

The current generator reactive power must therefore be available
through the generator model as:

    generator.Q

Generator limits are expected as:

    generator.Qmin
    generator.Qmax

Generator voltage setpoint:

    generator.Vset

Expected Bus interface:

    bus.id
    bus.type
    bus.V
    bus.Q_spec

    bus.is_pv()
    bus.is_pq()
    bus.is_slack()

Expected Generator interface:

    generator.bus
    generator.Q
    generator.Qmin
    generator.Qmax
    generator.Vset

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


class QLimitHandler:
    """
    Manage generator reactive-power limits during AC power flow.

    The handler remembers which buses were originally PV buses so
    that a bus converted to PQ can subsequently be restored to PV
    when its generator returns inside its reactive limits.

    Notes
    -----
    The handler does not calculate generator Q.

    It assumes generator.Q represents the current reactive output
    corresponding to the present network state.
    """

    def __init__(
        self,
        network,
        tolerance: float = 1e-6
    ):
        """
        Parameters
        ----------
        network:
            GridForge Network object.

        tolerance:
            Numerical tolerance used when comparing generator Q
            against Qmin and Qmax.
        """

        if network is None:
            raise ValueError(
                "Network cannot be None"
            )

        if not hasattr(network, "buses"):
            raise ValueError(
                "Network must provide a 'buses' collection"
            )

        if not hasattr(network, "generators"):
            raise ValueError(
                "Network must provide a 'generators' collection"
            )

        if tolerance < 0:
            raise ValueError(
                "Tolerance must be >= 0"
            )

        self.network = network
        self.tol = float(tolerance)

        # ---------------------------------------------------------
        # Remember buses that were originally operating as PV.
        #
        # Only these buses are eligible for automatic PQ -> PV
        # restoration.
        # ---------------------------------------------------------

        self.original_pv = {
            bus.id
            for bus in network.buses
            if bus.is_pv()
        }

        # ---------------------------------------------------------
        # Track buses currently constrained by Q limits.
        #
        # bus_id -> "QMIN" / "QMAX"
        # ---------------------------------------------------------

        self.limited_buses = {}

    # =============================================================
    # MAIN LIMIT CHECK
    # =============================================================

    def check_limits(self):
        """
        Check generator reactive-power limits.

        Returns
        -------
        list
            Bus IDs whose operating mode changed during this call.

        Behavior
        --------
        PV bus:
            Q > Qmax -> PQ at Qmax
            Q < Qmin -> PQ at Qmin

        Originally-PV PQ bus:
            Q inside limits -> PV restoration

        Slack buses are never modified.
        """

        changed = []

        # ---------------------------------------------------------
        # Evaluate each network bus.
        # ---------------------------------------------------------

        for bus in self.network.buses:

            # -----------------------------------------------------
            # Slack buses do not participate in PV/PQ Q-limit
            # switching.
            # -----------------------------------------------------

            if bus.is_slack():
                continue

            generator = self._find_generator(
                bus.id
            )

            if generator is None:
                continue

            self._validate_generator_limits(
                generator
            )

            Q = float(
                generator.Q
            )

            Qmin = float(
                generator.Qmin
            )

            Qmax = float(
                generator.Qmax
            )

            # =====================================================
            # PV -> PQ
            # =====================================================

            if bus.is_pv():

                # -------------------------------------------------
                # Upper reactive limit
                # -------------------------------------------------

                if Q > Qmax + self.tol:

                    self._convert_to_pq(
                        bus,
                        Qmax,
                        "QMAX"
                    )

                    changed.append(
                        bus.id
                    )

                    continue

                # -------------------------------------------------
                # Lower reactive limit
                # -------------------------------------------------

                if Q < Qmin - self.tol:

                    self._convert_to_pq(
                        bus,
                        Qmin,
                        "QMIN"
                    )

                    changed.append(
                        bus.id
                    )

                    continue

            # =====================================================
            # PQ -> PV
            # =====================================================

            elif (
                bus.is_pq()
                and
                bus.id in self.original_pv
            ):

                if self._inside_limits(
                    Q,
                    Qmin,
                    Qmax
                ):

                    self._restore_pv(
                        bus,
                        generator
                    )

                    changed.append(
                        bus.id
                    )

        return changed

    # =============================================================
    # PV -> PQ
    # =============================================================

    def _convert_to_pq(
        self,
        bus,
        q_limit: float,
        limit_type: str
    ):
        """
        Convert a PV bus into a PQ bus at the violated Q limit.
        """

        bus.type = "PQ"

        # ---------------------------------------------------------
        # Once the generator reaches a reactive limit, Q becomes
        # a specified quantity for the PQ formulation.
        # ---------------------------------------------------------

        bus.Q_spec = float(
            q_limit
        )

        self.limited_buses[
            bus.id
        ] = limit_type

    # =============================================================
    # PQ -> PV
    # =============================================================

    def _restore_pv(
        self,
        bus,
        generator
    ):
        """
        Restore an originally-PV bus to PV operation.
        """

        bus.type = "PV"

        # ---------------------------------------------------------
        # Restore the generator voltage setpoint.
        # ---------------------------------------------------------

        if not hasattr(
            generator,
            "Vset"
        ):
            raise ValueError(
                f"Generator at bus {bus.id} "
                "does not provide Vset"
            )

        bus.V = float(
            generator.Vset
        )

        # ---------------------------------------------------------
        # No longer constrained by a Q limit.
        # ---------------------------------------------------------

        self.limited_buses.pop(
            bus.id,
            None
        )

    # =============================================================
    # LIMIT TEST
    # =============================================================

    def _inside_limits(
        self,
        Q: float,
        Qmin: float,
        Qmax: float
    ) -> bool:
        """
        Determine whether Q is safely inside the generator limits.
        """

        return (
            Q >= Qmin + self.tol
            and
            Q <= Qmax - self.tol
        )

    # =============================================================
    # GENERATOR LOOKUP
    # =============================================================

    def _find_generator(
        self,
        bus_id
    ):
        """
        Find the generator associated with a bus.

        The current GridForge model contract uses:

            generator.bus == bus.id
        """

        for generator in self.network.generators:

            if generator.bus == bus_id:
                return generator

        return None

    # =============================================================
    # VALIDATION
    # =============================================================

    @staticmethod
    def _validate_generator_limits(
        generator
    ):
        """
        Validate the generator Q-limit interface.
        """

        required = (
            "Q",
            "Qmin",
            "Qmax"
        )

        for attribute in required:

            if not hasattr(
                generator,
                attribute
            ):
                raise ValueError(
                    "Generator is missing required "
                    f"attribute '{attribute}'"
                )

        if generator.Qmin > generator.Qmax:

            raise ValueError(
                "Generator Qmin cannot be greater than Qmax"
            )

    # =============================================================
    # STATE RESET
    # =============================================================

    def reset(self):
        """
        Reset the handler's runtime limit-tracking state.

        The original PV bus definition is preserved.
        """

        self.limited_buses.clear()

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self):
        """
        Return Q-limit handler state.
        """

        return {
            "tolerance": self.tol,
            "original_pv_buses": sorted(
                self.original_pv,
                key=str
            ),
            "limited_buses": dict(
                self.limited_buses
            )
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self):
        """
        Developer-friendly representation.
        """

        return (
            "QLimitHandler("
            f"original_pv={len(self.original_pv)}, "
            f"limited={len(self.limited_buses)}, "
            f"tolerance={self.tol}"
            ")"
        )
