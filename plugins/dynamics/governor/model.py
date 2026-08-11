"""
GridForge Governor Dynamic Plugin
=================================

Provides the Governor dynamic component as a plugin.

The plugin does not own numerical integration or simulation state.
It wraps the existing GridForge Governor model and exposes a
dynamic-component interface suitable for the dynamic solver.

Architecture
------------
Dynamic solver owns:

    - state vector
    - integration
    - time stepping
    - simulation state

Governor plugin owns:

    - governor model configuration
    - differential equation evaluation
    - output calculation
    - initialization
    - diagnostics
"""

from __future__ import annotations

from core.model.governor import Governor


class GovernorPlugin:
    """
    Plugin adapter for the GridForge Governor model.

    State
    -----
    The governor contributes one dynamic state:

        Pm

    where Pm is mechanical power in per-unit.
    """

    plugin_type = "dynamics.governor"
    model_type = "FIRST_ORDER_GOVERNOR"

    state_names = (
        "Pm",
    )

    def __init__(
        self,
        governor: Governor | None = None,
        *,
        id: str = "",
        name: str = "",
    ) -> None:

        self.id = str(id)
        self.name = str(name)

        self.model = (
            governor
            if governor is not None
            else Governor()
        )

        if not isinstance(self.model, Governor):
            raise TypeError(
                "GovernorPlugin requires a "
                "core.model.governor.Governor instance."
            )

    # =========================================================
    # STATE INTERFACE
    # =========================================================

    @property
    def state_size(self) -> int:
        """
        Number of dynamic states contributed by this plugin.
        """

        return 1

    def initial_state(
        self,
        omega: float = 0.0,
    ) -> tuple[float]:
        """
        Return the initial dynamic state vector.
        """

        Pm = self.model.initial_state(
            omega=omega,
        )

        return (Pm,)

    # =========================================================
    # DIFFERENTIAL EQUATION
    # =========================================================

    def derivatives(
        self,
        state: tuple[float] | list[float],
        *,
        omega: float,
    ) -> tuple[float]:
        """
        Evaluate governor state derivatives.

        Parameters
        ----------
        state:
            Governor dynamic state vector.

        omega:
            Rotor speed deviation.

        Returns
        -------
        tuple
            Governor state derivatives.
        """

        if len(state) != 1:
            raise ValueError(
                "GovernorPlugin requires exactly "
                "one dynamic state: Pm."
            )

        Pm = float(state[0])

        dPm_dt = self.model.derivative(
            Pm=Pm,
            omega=omega,
        )

        return (dPm_dt,)

    # =========================================================
    # OUTPUT
    # =========================================================

    def output(
        self,
        state: tuple[float] | list[float],
    ) -> float:
        """
        Return the governor mechanical-power output.
        """

        if len(state) != 1:
            raise ValueError(
                "GovernorPlugin requires exactly "
                "one dynamic state: Pm."
            )

        return self.model.output(
            Pm=float(state[0]),
        )

    # =========================================================
    # EVALUATION
    # =========================================================

    def evaluate(
        self,
        state: tuple[float] | list[float],
        *,
        omega: float,
    ) -> dict:
        """
        Evaluate governor dynamics and output.
        """

        if len(state) != 1:
            raise ValueError(
                "GovernorPlugin requires exactly "
                "one dynamic state: Pm."
            )

        Pm = float(state[0])

        dPm_dt, Pm_output = self.model.evaluate(
            Pm=Pm,
            omega=omega,
        )

        return {
            "derivatives": (
                dPm_dt,
            ),
            "output": Pm_output,
            "Pm": Pm,
        }

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
        omega: float = 0.0,
    ) -> tuple[float]:
        """
        Return the initial dynamic state.
        """

        return self.initial_state(
            omega=omega,
        )

    # =========================================================
    # CONFIGURATION
    # =========================================================

    def configure(
        self,
        *,
        Pref: float | None = None,
        R: float | None = None,
        Tg: float | None = None,
        Pm_min: float | None = None,
        Pm_max: float | None = None,
    ) -> None:
        """
        Update governor parameters through the plugin boundary.
        """

        if Pref is not None:
            self.model.set_reference(Pref)

        if R is not None:
            self.model.set_droop(R)

        if Tg is not None:
            self.model.set_time_constant(Tg)

        if (
            Pm_min is not None
            or Pm_max is not None
        ):
            new_min = (
                self.model.Pm_min
                if Pm_min is None
                else float(Pm_min)
            )

            new_max = (
                self.model.Pm_max
                if Pm_max is None
                else float(Pm_max)
            )

            self.model.set_limits(
                Pm_min=new_min,
                Pm_max=new_max,
            )

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return plugin and model information.
        """

        return {
            "plugin_type": self.plugin_type,
            "model_type": self.model_type,
            "id": self.id,
            "name": self.name,
            "state_names": self.state_names,
            "state_size": self.state_size,
            "model": self.model.summary(),
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(self) -> str:
        return (
            f"<GovernorPlugin "
            f"id={self.id}, "
            f"model={self.model_type}, "
            f"states={self.state_names}>"
        )
