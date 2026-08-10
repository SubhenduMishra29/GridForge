```python
"""
GridForge Generator Model
=========================

File:
    core/model/generator.py

Defines the GridForge Generator model.

Architecture
------------

A Generator represents a controllable electrical power injection
connected to a Bus.

The Generator also acts as the integration container for optional
dynamic models:

    Generator
        ├── SynchronousMachine
        ├── Governor
        ├── AVR
        └── PSS

These dynamic components provide their respective equations and
parameters. They do NOT perform numerical integration.

The dynamic / DAE solver owns:

    - Dynamic state vector
    - State initialization
    - Time integration
    - Time stepping
    - Differential-algebraic solution

Generator electrical responsibilities
--------------------------------------

    - Active power injection
    - Reactive power injection
    - Voltage setpoint
    - Reactive power limits
    - Q-limit status
    - Bus connectivity

Dynamic integration responsibilities
------------------------------------

    - Attach synchronous-machine model
    - Attach governor model
    - Attach AVR model
    - Attach PSS model
    - Expose attached dynamic models

The Generator does NOT:

    - Perform Newton-Raphson iterations.
    - Decide PV/PQ bus classification.
    - Build Ybus.
    - Perform load-flow calculations.
    - Perform short-circuit calculations.
    - Perform contingency analysis.
    - Perform dynamic integration.
    - Perform protection calculations.

The power-flow, protection, and dynamic solver layers operate on
this model through its public interface.

Sign Convention
---------------

Generator power is represented as network injection:

    +P -> active power injected into network
    +Q -> reactive power injected into network

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Tuple

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Generator(ElectricalObject, Injection):
    """
    GridForge controllable generator model.

    Parameters
    ----------
    id:
        Unique GridForge object identifier.

    bus:
        Bus to which the generator is connected.

    p:
        Active power injection in per-unit.

    q:
        Reactive power injection in per-unit.

    V_setpoint:
        Voltage magnitude target in per-unit.

    q_limits:
        Reactive power limits as:

            (Qmin, Qmax)

    name:
        Human-readable generator name.

    Notes
    -----
    Dynamic models are optional.

    A generator can therefore be used as a conventional load-flow
    generator without attaching dynamic models.

    Dynamic models may be attached later using:

        attach_machine()
        attach_governor()
        attach_avr()
        attach_pss()
    """

    def __init__(
        self,
        id: str,
        bus,
        p: float = 0.0,
        q: float = 0.0,
        V_setpoint: float = 1.0,
        q_limits: Tuple[float, float] = (
            -float("inf"),
            float("inf"),
        ),
        name: str = "",
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # =========================================================
        # ELECTRICAL CONNECTION
        # =========================================================

        self.terminal = Terminal(bus)

        # =========================================================
        # GENERATOR POWER
        #
        # Positive P/Q = injection into network.
        # =========================================================

        self.p = float(p)
        self.q = float(q)

        # =========================================================
        # VOLTAGE CONTROL
        # =========================================================

        self.V_setpoint = float(V_setpoint)

        # =========================================================
        # REACTIVE POWER LIMITS
        # =========================================================

        try:
            if len(q_limits) != 2:
                raise ValueError(
                    "q_limits must contain exactly "
                    "(Qmin, Qmax)"
                )

            self.q_min = float(q_limits[0])
            self.q_max = float(q_limits[1])

        except TypeError as exc:
            raise TypeError(
                "q_limits must be a two-value sequence "
                "(Qmin, Qmax)"
            ) from exc

        # =========================================================
        # DYNAMIC COMPONENTS
        # =========================================================
        #
        # These are model references only.
        #
        # The Generator does NOT own their numerical states.
        # The dynamic solver owns the authoritative state vector.
        # =========================================================

        self.machine = None
        self.governor = None
        self.avr = None
        self.pss = None

        self._validate()

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate(self) -> None:
        """
        Validate generator parameters.

        Infinite Q limits are permitted.

        NaN values are rejected because they are not valid
        electrical model states.
        """

        if not math.isfinite(self.V_setpoint):
            raise ValueError(
                "Generator voltage setpoint must be finite."
            )

        if self.V_setpoint <= 0.0:
            raise ValueError(
                "Generator voltage setpoint "
                "must be greater than zero."
            )

        if math.isnan(self.p):
            raise ValueError(
                "Generator active power cannot be NaN."
            )

        if math.isnan(self.q):
            raise ValueError(
                "Generator reactive power cannot be NaN."
            )

        if math.isnan(self.q_min):
            raise ValueError(
                "Generator Qmin cannot be NaN."
            )

        if math.isnan(self.q_max):
            raise ValueError(
                "Generator Qmax cannot be NaN."
            )

        if self.q_min > self.q_max:
            raise ValueError(
                "Generator Qmin cannot exceed Qmax."
            )

    # =============================================================
    # INJECTION INTERFACE
    # =============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return generator network injection.

        Returns
        -------
        tuple[float, float]
            (P, Q)

        Positive values represent injection into the network.
        """

        return self.p, self.q

    # =============================================================
    # CONNECTION
    # =============================================================

    @property
    def bus(self):
        """
        Return the Bus connected to this generator.
        """

        return self.terminal.bus

    # =============================================================
    # POWER CONTROL
    # =============================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Set generator active and reactive power.

        Q-limit enforcement is intentionally not performed here.
        """

        p = float(p)
        q = float(q)

        if math.isnan(p):
            raise ValueError(
                "Generator active power cannot be NaN."
            )

        if math.isnan(q):
            raise ValueError(
                "Generator reactive power cannot be NaN."
            )

        self.p = p
        self.q = q

    def set_active_power(
        self,
        p: float,
    ) -> None:
        """
        Set generator active power.
        """

        p = float(p)

        if math.isnan(p):
            raise ValueError(
                "Generator active power cannot be NaN."
            )

        self.p = p

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """
        Set generator reactive power.

        This method does not automatically clamp Q.

        Q-limit enforcement belongs to the power-flow
        control layer.
        """

        q = float(q)

        if math.isnan(q):
            raise ValueError(
                "Generator reactive power cannot be NaN."
            )

        self.q = q

    # =============================================================
    # VOLTAGE CONTROL
    # =============================================================

    def set_voltage_setpoint(
        self,
        V_setpoint: float,
    ) -> None:
        """
        Set the generator voltage-control target.

        Parameters
        ----------
        V_setpoint:
            Voltage magnitude in per-unit.
        """

        V_setpoint = float(V_setpoint)

        if not math.isfinite(V_setpoint):
            raise ValueError(
                "Voltage setpoint must be finite."
            )

        if V_setpoint <= 0.0:
            raise ValueError(
                "Voltage setpoint must be "
                "greater than zero."
            )

        self.V_setpoint = V_setpoint

    # =============================================================
    # REACTIVE POWER LIMITS
    # =============================================================

    @property
    def q_limits(self) -> tuple[float, float]:
        """
        Return reactive power limits.

        Returns
        -------
        tuple
            (Qmin, Qmax)
        """

        return self.q_min, self.q_max

    def set_q_limits(
        self,
        q_min: float,
        q_max: float,
    ) -> None:
        """
        Update generator reactive power limits.

        Infinite limits are permitted.
        """

        q_min = float(q_min)
        q_max = float(q_max)

        if math.isnan(q_min) or math.isnan(q_max):
            raise ValueError(
                "Reactive power limits cannot be NaN."
            )

        if q_min > q_max:
            raise ValueError(
                "Qmin cannot exceed Qmax."
            )

        self.q_min = q_min
        self.q_max = q_max

    def q_limit_status(
        self,
        tolerance: float = 1e-6,
    ) -> str:
        """
        Determine current reactive-power limit status.

        Returns
        -------
        str
            One of:

                "LOW"
                "HIGH"
                "NORMAL"
        """

        tolerance = float(tolerance)

        if math.isnan(tolerance):
            raise ValueError(
                "Q-limit tolerance cannot be NaN."
            )

        if tolerance < 0.0:
            raise ValueError(
                "Q-limit tolerance cannot be negative."
            )

        if self.q < self.q_min - tolerance:
            return "LOW"

        if self.q > self.q_max + tolerance:
            return "HIGH"

        return "NORMAL"

    def enforce_q_limits(self) -> bool:
        """
        Clamp reactive power to its physical limits.

        Returns
        -------
        bool
            True if Q was modified.

        Notes
        -----
        This method only clamps generator Q.

        It does NOT change the associated Bus type.

        PV -> PQ switching belongs to the QLimitHandler.
        """

        original_q = self.q

        if self.q < self.q_min:
            self.q = self.q_min

        elif self.q > self.q_max:
            self.q = self.q_max

        return self.q != original_q

    # =============================================================
    # DYNAMIC MODEL ATTACHMENT
    # =============================================================

    def attach_machine(self, machine) -> None:
        """
        Attach a synchronous-machine dynamic model.

        The machine object supplies the machine equations and
        parameters. Dynamic state ownership remains with the
        dynamic solver.
        """

        if machine is None:
            raise ValueError(
                "Synchronous machine cannot be None."
            )

        self.machine = machine

    def attach_governor(self, governor) -> None:
        """
        Attach a turbine-governor dynamic model.

        The Governor supplies the mechanical-power differential
        equation. Its dynamic state remains owned by the solver.
        """

        if governor is None:
            raise ValueError(
                "Governor cannot be None."
            )

        self.governor = governor

    def attach_avr(self, avr) -> None:
        """
        Attach an automatic-voltage-regulator model.

        The AVR supplies the excitation differential equation.
        Its dynamic state remains owned by the solver.
        """

        if avr is None:
            raise ValueError(
                "AVR cannot be None."
            )

        self.avr = avr

    def attach_pss(self, pss) -> None:
        """
        Attach a power-system-stabilizer model.

        The PSS supplies the supplementary stabilizing equation.
        Its dynamic state remains owned by the solver.
        """

        if pss is None:
            raise ValueError(
                "PSS cannot be None."
            )

        self.pss = pss

    # =============================================================
    # DYNAMIC MODEL STATUS
    # =============================================================

    @property
    def has_dynamic_model(self) -> bool:
        """
        Return True when a synchronous-machine model is attached.
        """

        return self.machine is not None

    @property
    def has_governor(self) -> bool:
        """
        Return True when a governor is attached.
        """

        return self.governor is not None

    @property
    def has_avr(self) -> bool:
        """
        Return True when an AVR is attached.
        """

        return self.avr is not None

    @property
    def has_pss(self) -> bool:
        """
        Return True when a PSS is attached.
        """

        return self.pss is not None

    @property
    def is_dynamically_configured(self) -> bool:
        """
        Return True when the generator has a synchronous-machine
        model attached.

        A governor, AVR, and PSS are optional auxiliary models.
        """

        return self.machine is not None

    # =============================================================
    # DYNAMIC MODEL DETACHMENT
    # =============================================================

    def detach_machine(self):
        """
        Detach the synchronous-machine model.

        Returns
        -------
        object or None
            Previously attached machine.
        """

        machine = self.machine
        self.machine = None
        return machine

    def detach_governor(self):
        """
        Detach the governor model.

        Returns
        -------
        object or None
            Previously attached governor.
        """

        governor = self.governor
        self.governor = None
        return governor

    def detach_avr(self):
        """
        Detach the AVR model.

        Returns
        -------
        object or None
            Previously attached AVR.
        """

        avr = self.avr
        self.avr = None
        return avr

    def detach_pss(self):
        """
        Detach the PSS model.

        Returns
        -------
        object or None
            Previously attached PSS.
        """

        pss = self.pss
        self.pss = None
        return pss

    # =============================================================
    # DYNAMIC MODEL COLLECTION
    # =============================================================

    def dynamic_models(self) -> dict:
        """
        Return attached dynamic models.

        Returns
        -------
        dict
            Mapping containing the optional dynamic components.

        Notes
        -----
        The returned dictionary contains model references only.

        It does not contain or expose authoritative dynamic state.
        """

        return {
            "machine": self.machine,
            "governor": self.governor,
            "avr": self.avr,
            "pss": self.pss,
        }

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict:
        """
        Return generator diagnostic information.

        Dynamic model presence is reported without exposing
        numerical dynamic states.
        """

        return {
            "id": self.id,
            "name": self.name,
            "bus": self.bus.id,
            "P": self.p,
            "Q": self.q,
            "V_setpoint": self.V_setpoint,
            "Qmin": self.q_min,
            "Qmax": self.q_max,
            "Q_status": self.q_limit_status(),
            "dynamic": {
                "machine": self.machine is not None,
                "governor": self.governor is not None,
                "avr": self.avr is not None,
                "pss": self.pss is not None,
            },
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        return (
            f"<Generator "
            f"id={self.id}, "
            f"bus={self.bus.id}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}, "
            f"Vset={self.V_setpoint:.6f}, "
            f"Qmin={self.q_min:.6f}, "
            f"Qmax={self.q_max:.6f}, "
            f"dynamic={self.is_dynamically_configured}>"
        )
```
