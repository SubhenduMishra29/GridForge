"""
GridForge AVR Dynamic Plugin
============================

Adapter for the frozen GridForge AVR model.

The plugin exposes the AVR to the dynamic solver without moving
simulation-state ownership into the model.
"""

from __future__ import annotations

from core.model.avr import AVR


class AVRPlugin:
    """
    Plugin adapter for the GridForge AVR model.

    Dynamic state
    -------------
    Efd:
        Excitation / field voltage state.
    """

    plugin_type = "dynamics.avr"
    model_type = "FIRST_ORDER_AVR"

    state_names = (
        "Efd",
    )

    def __init__(
        self,
        avr: AVR | None = None,
        *,
        id: str = "",
        name: str = "",
    ) -> None:

        self.id = str(id)
        self.name = str(name)

        self.model = (
            avr
            if avr is not None
            else AVR()
        )

        if not isinstance(self.model, AVR):
            raise TypeError(
                "AVRPlugin requires a "
                "core.model.avr.AVR instance."
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
        Vt: float = 1.0,
        Vpss: float = 0.0,
    ) -> tuple[float]:
        """
        Return the initial AVR state vector.
        """

        Efd = self.model.initial_state(
            Vt=Vt,
            Vpss=Vpss,
        )

        return (Efd,)

    # =========================================================
    # DIFFERENTIAL EQUATION
    # =========================================================

    def derivatives(
        self,
        state: tuple[float] | list[float],
        *,
        Vt: float,
        Vpss: float = 0.0,
    ) -> tuple[float]:
        """
        Evaluate the AVR state derivative.

        Parameters
        ----------
        state:
            AVR dynamic state vector.

        Vt:
            Generator terminal voltage.

        Vpss:
            Supplementary stabilizing signal.

        Returns
        -------
        tuple
            AVR state derivatives.
        """

        if len(state) != 1:
            raise ValueError(
                "AVRPlugin requires exactly "
                "one dynamic state: Efd."
            )

        Efd = float(state[0])

        dEfd_dt = self.model.derivative(
            Efd=Efd,
            Vt=Vt,
            Vpss=Vpss,
        )

        return (dEfd_dt,)

    # =========================================================
    # OUTPUT
    # =========================================================

    def output(
        self,
        state: tuple[float] | list[float],
    ) -> float:
        """
        Return the limited AVR excitation output.
        """

        if len(state) != 1:
            raise ValueError(
                "AVRPlugin requires exactly "
                "one dynamic state: Efd."
            )

        return self.model.output(
            Efd=float(state[0]),
        )

    # =========================================================
    # COMBINED EVALUATION
    # =========================================================

    def evaluate(
        self,
        state: tuple[float] | list[float],
        *,
        Vt: float,
        Vpss: float = 0.0,
    ) -> dict:
        """
        Evaluate AVR dynamics and output.
        """

        if len(state) != 1:
            raise ValueError(
                "AVRPlugin requires exactly "
                "one dynamic state: Efd."
            )

        Efd = float(state[0])

        dEfd_dt, Efd_output = self.model.evaluate(
            Efd=Efd,
            Vt=Vt,
            Vpss=Vpss,
        )

        return {
            "derivatives": (
                dEfd_dt,
            ),
            "output": Efd_output,
            "Efd": Efd,
        }

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
        Vt: float = 1.0,
        Vpss: float = 0.0,
    ) -> tuple[float]:
        """
        Return the initial AVR state.
        """

        return self.initial_state(
            Vt=Vt,
            Vpss=Vpss,
        )

    # =========================================================
    # CONFIGURATION
    # =========================================================

    def configure(
        self,
        *,
        Ka: float | None = None,
        Ta: float | None = None,
        Vref: float | None = None,
        Efd_min: float | None = None,
        Efd_max: float | None = None,
    ) -> None:
        """
        Update AVR parameters through the plugin boundary.
        """

        if Ka is not None:
            self.model.set_gain(Ka)

        if Ta is not None:
            self.model.set_time_constant(Ta)

        if Vref is not None:
            self.model.set_reference(Vref)

        if (
            Efd_min is not None
            or Efd_max is not None
        ):
            new_min = (
                self.model.Efd_min
                if Efd_min is None
                else float(Efd_min)
            )

            new_max = (
                self.model.Efd_max
                if Efd_max is None
                else float(Efd_max)
            )

            self.model.set_limits(
                Efd_min=new_min,
                Efd_max=new_max,
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
            f"<AVRPlugin "
            f"id={self.id}, "
            f"model={self.model_type}, "
            f"states={self.state_names}>"
        )
