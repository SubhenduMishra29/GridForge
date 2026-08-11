```python
# core/model/generator.py

"""
GridForge Generator Model
=========================

GridForge Model Layer V2

Defines the GridForge controllable Generator model.

Architecture
------------
A Generator represents a controllable electrical power injection
connected to a Bus through a Terminal.

The Generator also provides the attachment point for optional
dynamic models:

    Generator
        ├── SynchronousMachine
        ├── Governor
        ├── AVR
        └── PSS

These dynamic components provide their respective physical models,
parameters, and equations.

They do NOT own the authoritative dynamic state vector and do NOT
perform numerical integration.

Dynamic / DAE solver responsibilities include:

    - Dynamic state-vector ownership
    - State initialization
    - Algebraic-state management
    - Differential-equation evaluation
    - Time integration
    - Time stepping
    - DAE solution

Generator Electrical Responsibilities
-------------------------------------
The Generator model stores:

    - Active power injection
    - Reactive power injection
    - Voltage-control setpoint
    - Reactive-power limits
    - Reactive-power limit status
    - Bus connectivity

The Generator does NOT:

    - Decide PV/PQ/SLACK bus classification.
    - Build Y-bus.
    - Perform Newton-Raphson iterations.
    - Perform load-flow calculations.
    - Perform short-circuit calculations.
    - Perform contingency analysis.
    - Perform dynamic integration.
    - Perform protection calculations.
    - Own the dynamic solver state vector.
    - Manage GUI objects.

Those responsibilities belong to the appropriate
network/solver/analysis/simulation/UI layers.

Sign Convention
---------------
Generator electrical power follows the GridForge
network-injection convention:

    +P
        Active power injected into the network.

    +Q
        Reactive power injected into the network.

Therefore:

    get_power() -> (P, Q)

Reactive Power Limits
---------------------
Q limits are stored by the Generator as physical generator limits.

Infinite limits are permitted and represent an unrestricted
generator.

The Generator may report and locally clamp its own Q value through
``enforce_q_limits()``.

It does NOT perform PV -> PQ bus conversion.

PV/PQ switching is a power-flow control-layer responsibility.

Dynamic Model Ownership
-----------------------
Dynamic model objects attached to the Generator are references to
physical model definitions.

The Generator does not own their numerical state.

The dynamic solver remains the sole owner of the authoritative
dynamic state vector.

GridForge V2 Status
-------------------
This module is part of the frozen GridForge Model Layer V2 baseline.

Changes require evidence of a genuinely fundamental generator-model
requirement that cannot be implemented through an existing model,
interface, or higher-level layer.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Tuple

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


# =====================================================================
# GENERATOR MODEL
# =====================================================================

class Generator(ElectricalObject, Injection):
    """
    GridForge controllable generator model.

    Parameters
    ----------
    id : str
        Unique GridForge object identifier.

    bus :
        Bus to which the generator is connected.

    p : float, optional
        Active power injection in per-unit.

        Positive values represent injection into the network.

    q : float, optional
        Reactive power injection in per-unit.

        Positive values represent injection into the network.

    V_setpoint : float, optional
        Voltage magnitude control target in per-unit.

    q_limits : tuple[float, float], optional
        Reactive-power limits as:

            (Qmin, Qmax)

        Infinite limits are permitted.

    name : str, optional
        Human-readable generator name.

    Notes
    -----
    Dynamic models are optional.

    A Generator can therefore be used as a conventional
    steady-state load-flow generator without attaching dynamic
    models.

    Dynamic models can be attached using:

        attach_machine()
        attach_governor()
        attach_avr()
        attach_pss()
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

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

        # -------------------------------------------------------------
        # Electrical connection
        # -------------------------------------------------------------

        self.terminal = Terminal(bus)

        # -------------------------------------------------------------
        # Generator electrical power
        #
        # Positive P/Q = injection into the network.
        # -------------------------------------------------------------

        self.p = float(p)
        self.q = float(q)

        # -------------------------------------------------------------
        # Voltage control
        # -------------------------------------------------------------

        self.V_setpoint = float(V_setpoint)

        # -------------------------------------------------------------
        # Reactive-power limits
        # -------------------------------------------------------------

        try:
            if len(q_limits) != 2:
                raise ValueError(
                    "q_limits must contain exactly "
                    "(Qmin, Qmax)."
                )

            self.q_min = float(q_limits[0])
            self.q_max = float(q_limits[1])

        except TypeError as exc:
            raise TypeError(
                "q_limits must be a two-value sequence "
                "(Qmin, Qmax)."
            ) from exc

        # -------------------------------------------------------------
        # Optional dynamic model references
        #
        # These objects define dynamic model parameters/equations.
        # They do not contain the authoritative solver state.
        # -------------------------------------------------------------

        self.machine = None
        self.governor = None
        self.avr = None
        self.pss = None

        # -------------------------------------------------------------
        # Validate complete generator state.
        # -------------------------------------------------------------

        self._validate()

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate(self) -> None:
        """
        Validate generator electrical parameters.

        P and Q must be finite.

        Q limits may be infinite, representing unrestricted
        reactive capability, but NaN is never valid.

        Voltage setpoint must be finite and positive.
        """

        # -------------------------------------------------------------
        # Active and reactive power
        # -------------------------------------------------------------

        if not math.isfinite(self.p):
            raise ValueError(
                "Generator active power must be finite."
            )

        if not math.isfinite(self.q):
            raise ValueError(
                "Generator reactive power must be finite."
            )

        # -------------------------------------------------------------
        # Voltage setpoint
        # -------------------------------------------------------------

        if not math.isfinite(self.V_setpoint):
            raise ValueError(
                "Generator voltage setpoint must be finite."
            )

        if self.V_setpoint <= 0.0:
            raise ValueError(
                "Generator voltage setpoint "
                "must be greater than zero."
            )

        # -------------------------------------------------------------
        # Reactive-power limits
        #
        # Infinite limits are valid.
        # NaN limits are not.
        # -------------------------------------------------------------

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

    # =================================================================
    # INJECTION INTERFACE
    # =================================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return generator network power injection.

        Returns
        -------
        tuple[float, float]
            ``(P, Q)`` in the GridForge network-injection
            convention.

        Positive values represent injection into the network.
        """

        return (
            self.p,
            self.q,
        )

    # =================================================================
    # CONNECTION
    # =================================================================

    @property
    def bus(self):
        """
        Return the Bus connected to this generator.
        """

        return self.terminal.bus

    # =================================================================
    # POWER CONTROL
    # =================================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Set generator active and reactive power.

        Parameters
        ----------
        p : float
            Active power injection in per-unit.

        q : float
            Reactive power injection in per-unit.

        Notes
        -----
        Q-limit enforcement is intentionally not performed here.

        The caller may explicitly use ``enforce_q_limits()`` or the
        appropriate power-flow control layer may manage generator
        reactive limits.
        """

        p = float(p)
        q = float(q)

        if not math.isfinite(p):
            raise ValueError(
                "Generator active power must be finite."
            )

        if not math.isfinite(q):
            raise ValueError(
                "Generator reactive power must be finite."
            )

        self.p = p
        self.q = q

    def set_active_power(
        self,
        p: float,
    ) -> None:
        """
        Set generator active power injection.
        """

        p = float(p)

        if not math.isfinite(p):
            raise ValueError(
                "Generator active power must be finite."
            )

        self.p = p

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """
        Set generator reactive power injection.

        This method does not automatically clamp Q.

        Reactive-power limit handling belongs to the appropriate
        power-flow control workflow.
        """

        q = float(q)

        if not math.isfinite(q):
            raise ValueError(
                "Generator reactive power must be finite."
            )

        self.q = q

    # =================================================================
    # VOLTAGE CONTROL
    # =================================================================

    def set_voltage_setpoint(
        self,
        V_setpoint: float,
    ) -> None:
        """
        Set the generator voltage-control target.

        Parameters
        ----------
        V_setpoint : float
            Voltage magnitude in per-unit.
        """

        V_setpoint = float(V_setpoint)

        if not math.isfinite(V_setpoint):
            raise ValueError(
                "Generator voltage setpoint must be finite."
            )

        if V_setpoint <= 0.0:
            raise ValueError(
                "Generator voltage setpoint "
                "must be greater than zero."
            )

        self.V_setpoint = V_setpoint

    # =================================================================
    # REACTIVE POWER LIMITS
    # =================================================================

    @property
    def q_limits(self) -> tuple[float, float]:
        """
        Return generator reactive-power limits.

        Returns
        -------
        tuple[float, float]
            ``(Qmin, Qmax)``
        """

        return (
            self.q_min,
            self.q_max,
        )

    def set_q_limits(
        self,
        q_min: float,
        q_max: float,
    ) -> None:
        """
        Update generator reactive-power limits.

        Parameters
        ----------
        q_min : float
            Minimum reactive-power injection.

        q_max : float
            Maximum reactive-power injection.

        Notes
        -----
        Infinite limits are permitted.

        The limits are stored only. The current generator Q value
        is not automatically changed.
        """

        q_min = float(q_min)
        q_max = float(q_max)

        if math.isnan(q_min) or math.isnan(q_max):
            raise ValueError(
                "Reactive-power limits cannot be NaN."
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
        Determine the current reactive-power limit status.

        Parameters
        ----------
        tolerance : float, optional
            Numerical tolerance in per-unit.

        Returns
        -------
        str
            One of:

                "LOW"
                "HIGH"
                "NORMAL"

        Notes
        -----
        This method is diagnostic only.

        It does not change generator Q and does not change Bus
        classification.
        """

        tolerance = float(tolerance)

        if not math.isfinite(tolerance):
            raise ValueError(
                "Q-limit tolerance must be finite."
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
        Clamp reactive power to the configured physical limits.

        Returns
        -------
        bool
            True if Q was modified.

        Notes
        -----
        This method changes only the Generator's own reactive-power
        value.

        It does NOT:

        - Change Bus classification.
        - Perform PV -> PQ switching.
        - Modify Bus voltage.
        - Run a power-flow solution.

        PV -> PQ handling belongs to the power-flow control layer.
        """

        original_q = self.q

        if self.q < self.q_min:
            self.q = self.q_min

        elif self.q > self.q_max:
            self.q = self.q_max

        return self.q != original_q

    # =================================================================
    # DYNAMIC MODEL ATTACHMENT
    # =================================================================

    def attach_machine(self, machine) -> None:
        """
        Attach a synchronous-machine dynamic model.

        The machine object provides machine parameters and equations.

        The dynamic solver retains ownership of the authoritative
        dynamic state vector.
        """

        if machine is None:
            raise ValueError(
                "Synchronous machine cannot be None."
            )

        self.machine = machine

    def attach_governor(self, governor) -> None:
        """
        Attach a turbine-governor dynamic model.

        The Governor provides its physical model.

        Dynamic state remains owned by the dynamic solver.
        """

        if governor is None:
            raise ValueError(
                "Governor cannot be None."
            )

        self.governor = governor

    def attach_avr(self, avr) -> None:
        """
        Attach an automatic-voltage-regulator model.

        The AVR provides its physical model.

        Dynamic state remains owned by the dynamic solver.
        """

        if avr is None:
            raise ValueError(
                "AVR cannot be None."
            )

        self.avr = avr

    def attach_pss(self, pss) -> None:
        """
        Attach a power-system-stabilizer model.

        The PSS provides its physical model.

        Dynamic state remains owned by the dynamic solver.
        """

        if pss is None:
            raise ValueError(
                "PSS cannot be None."
            )

        self.pss = pss

    # =================================================================
    # DYNAMIC MODEL STATUS
    # =================================================================

    @property
    def has_dynamic_model(self) -> bool:
        """
        Return True when a synchronous-machine model is attached.

        A synchronous machine is the fundamental dynamic model
        required for a conventional generator dynamic representation.
        """

        return self.machine is not None

    @property
    def has_governor(self) -> bool:
        """
        Return True when a governor model is attached.
        """

        return self.governor is not None

    @property
    def has_avr(self) -> bool:
        """
        Return True when an AVR model is attached.
        """

        return self.avr is not None

    @property
    def has_pss(self) -> bool:
        """
        Return True when a PSS model is attached.
        """

        return self.pss is not None

    @property
    def is_dynamically_configured(self) -> bool:
        """
        Return True when a synchronous-machine model is attached.

        Governor, AVR, and PSS models are optional auxiliary models.
        """

        return self.machine is not None

    # =================================================================
    # DYNAMIC MODEL DETACHMENT
    # =================================================================

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

    # =================================================================
    # DYNAMIC MODEL COLLECTION
    # =================================================================

    def dynamic_models(self) -> dict:
        """
        Return references to the attached dynamic models.

        Returns
        -------
        dict
            Mapping containing:

                machine
                governor
                avr
                pss

        Notes
        -----
        The returned dictionary contains model references only.

        It does not contain or expose authoritative dynamic states.
        """

        return {
            "machine": self.machine,
            "governor": self.governor,
            "avr": self.avr,
            "pss": self.pss,
        }

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured generator diagnostic information.

        Dynamic model presence is reported without exposing dynamic
        solver state.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "generator",
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

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

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
