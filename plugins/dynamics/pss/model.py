"""
GridForge PSS Dynamic Plugin
============================

Adapter for the frozen GridForge PSS model.

The plugin does not own numerical integration or simulation state.
It exposes the PSS dynamic state and equations to the dynamic solver.
"""

from __future__ import annotations

from core.model.pss import PSS


class PSSPlugin:
    """
    Plugin adapter for the GridForge PSS model.

    Dynamic state
    -------------
    Xw:
        Washout-filter state.
    """

    plugin_type = "dynamics.pss"
    model_type = "FIRST_ORDER_WASHOUT"

    state_names = (
        "Xw",
    )

    def __init__(
        self,
        pss: PSS | None = None,
        *,
        id: str = "",
        name: str = "",
    ) -> None:

        self.id = str(id)
        self.name = str(name)

        self.model = (
            pss
            if pss is not None
            else PSS()
        )

        if not isinstance(self.model, PSS):
            raise TypeError(
                "PSSPlugin requires a "
                "core.model.pss.PSS instance."
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
        Return the initial PSS state vector.
        """

        Xw = self.model.initial_state(
            omega=omega,
        )

        return (Xw,)

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
        Evaluate the PSS state derivative.

        Parameters
        ----------
        state:
            PSS dynamic state vector.

        omega:
            Rotor-speed deviation.

        Returns
        -------
        tuple
            PSS state derivatives.
        """

        if len(state) != 1:
            raise ValueError(
                "PSSPlugin requires exactly "
                "one dynamic state: Xw."
            )

        Xw = float(state[0])

        dXw_dt = self.model.derivative(
            omega=omega,
            state=Xw,
        )

        return (dXw_dt,)

    # =========================================================
    # OUTPUT
    # =========================================================

    def output(
        self,
        state: tuple[float] | list[float],
        *,
        omega: float,
    ) -> float:
        """
        Return the limited PSS stabilizing signal.
        """

        if len(state) != 1:
            raise ValueError(
                "PSSPlugin requires exactly "
                "one dynamic state: Xw."
            )

        Xw = float(state[0])

        return self.model.output(
            omega=omega,
            state=Xw,
        )

    # =========================================================
    # COMBINED EVALUATION
    # =========================================================

    def evaluate(
        self,
        state: tuple[float] | list[float],
        *,
        omega: float,
    ) -> dict:
        """
        Evaluate PSS dynamics and stabilizing output.
        """

        if len(state) != 1:
            raise ValueError(
                "PSSPlugin requires exactly "
                "one dynamic state: Xw."
            )

        Xw = float(state[0])

        dXw_dt, Vpss = self.model.evaluate(
            omega=omega,
            state=Xw,
        )

        return {
            "derivatives": (
                dXw_dt,
            ),
            "output": Vpss,
            "Xw": Xw,
        }

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
        omega: float = 0.0,
    ) -> tuple[float]:
        """
        Return the initial PSS state.
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
        Kpss: float | None = None,
        Tw: float | None = None,
        Vpss_min: float | None = None,
        Vpss_max: float | None = None,
    ) -> None:
        """
        Update PSS parameters through the plugin boundary.
        """

        if Kpss is not None:
            self.model.set_gain(Kpss)

        if Tw is not None:
            self.model.set_washout_time(Tw)

        if (
            Vpss_min is not None
            or Vpss_max is not None
        ):
            new_min = (
                self.model.Vpss_min
                if Vpss_min is None
                else float(Vpss_min)
            )

            new_max = (
                self.model.Vpss_max
                if Vpss_max is None
                else float(Vpss_max)
            )

            self.model.set_limits(
                Vpss_min=new_min,
                Vpss_max=new_max,
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
            f"<PSSPlugin "
            f"id={self.id}, "
            f"model={self.model_type}, "
            f"states={self.state_names}>"
        )
