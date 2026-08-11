```python
"""
GridForge Protection System
===========================

File:
    core/protection/protection_system.py

Purpose
-------
Central protection-system coordinator.

Responsibilities
----------------
- Register protection relay algorithms.
- Associate relay algorithms with breakers.
- Supply measurements to the authoritative Relay model.
- Dispatch protection-specific evaluation.
- Generate breaker trip commands.
- Interface with BreakerManager.
- Record protection events.

Architecture
------------

    core/model/relay.py
            |
            | authoritative relay state
            v
    core/protection/relay_base.py
            |
            +---- Overcurrent
            +---- Distance
            +---- Directional
            |
            v
    ProtectionSystem
            |
            v
    BreakerManager
            |
            v
    core/model/breaker.py

Important
---------
The Relay model in core/model/relay.py is frozen.

It remains the authoritative owner of:

    - relay identity
    - relay type
    - pickup setting
    - time delay
    - current
    - voltage
    - impedance
    - in-service state
    - trip state

ProtectionSystem stores only:

    - protection algorithm registration
    - relay-to-breaker association
    - protection events

Protection-specific settings remain inside the corresponding
protection algorithm.

ProtectionSystem does NOT:

    - build Ybus
    - perform load flow
    - perform short-circuit analysis
    - calculate protection settings
    - coordinate multiple relays
    - modify Network topology

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ProtectionSystem:
    """
    Central coordinator for GridForge protection operations.

    Parameters
    ----------
    breaker_manager:
        Optional BreakerManager responsible for actual breaker
        operation.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        breaker_manager: Optional[Any] = None,
    ) -> None:

        self.relays: Dict[Any, Dict[str, Any]] = {}

        self.breaker_manager = breaker_manager

        self.events: List[
            Dict[str, Any]
        ] = []

    # =============================================================
    # RELAY REGISTRATION
    # =============================================================

    def add_relay(
        self,
        relay,
        breaker_id: Any,
    ) -> None:
        """
        Register a protection algorithm and associate it with
        a breaker.

        Parameters
        ----------
        relay:
            Preferred input is a RelayBase-derived protection
            algorithm.

        breaker_id:
            Identifier of the breaker operated by the relay.
        """

        if relay is None:
            raise ValueError(
                "relay cannot be None."
            )

        relay_id = getattr(
            relay,
            "id",
            None,
        )

        if relay_id is None:
            raise ValueError(
                "Registered relay must provide an id."
            )

        if relay_id in self.relays:
            raise ValueError(
                f"Relay '{relay_id}' is already registered."
            )

        self.relays[relay_id] = {
            "relay": relay,
            "breaker": breaker_id,
        }

    # =============================================================
    # RELAY REMOVAL
    # =============================================================

    def remove_relay(
        self,
        relay_id: Any,
    ) -> None:
        """
        Remove a relay from the protection system.
        """

        self.relays.pop(
            relay_id,
            None,
        )

    # =============================================================
    # AUTHORITATIVE MODEL ACCESS
    # =============================================================

    @staticmethod
    def _get_relay_model(
        relay,
    ):
        """
        Return the authoritative Relay model.

        RelayBase-derived protection algorithms store the model
        Relay as:

            relay.relay

        A raw Relay model is returned directly.
        """

        model_relay = getattr(
            relay,
            "relay",
            None,
        )

        if model_relay is not None:
            return model_relay

        return relay

    # =============================================================
    # MEASUREMENT INPUT
    # =============================================================

    @classmethod
    def _apply_measurement(
        cls,
        relay,
        measurement: Dict[str, Any],
    ) -> None:
        """
        Apply a measurement to the authoritative Relay model.

        Measurement dictionary:

            {
                "current": ...,
                "voltage": ...,
                "impedance": ...
            }

        Optional directional quantities:

            {
                "voltage_angle": ...,
                "current_angle": ...
            }

        Notes
        -----
        The authoritative model is always updated through
        core/model/relay.py.

        Distance protection additionally requires apparent
        impedance. When impedance is not explicitly supplied,
        the distance protection algorithm may calculate it from
        voltage/current during evaluation preparation.
        """

        if not isinstance(
            measurement,
            dict,
        ):
            raise TypeError(
                "Relay measurement must be a dictionary."
            )

        model_relay = cls._get_relay_model(
            relay
        )

        current = measurement.get(
            "current",
            0.0,
        )

        voltage = measurement.get(
            "voltage",
            1.0,
        )

        impedance = measurement.get(
            "impedance",
            0.0,
        )

        model_relay.measure(
            current=current,
            voltage=voltage,
            impedance=impedance,
        )

    # =============================================================
    # PROTECTION-SPECIFIC MEASUREMENT PREPARATION
    # =============================================================

    @staticmethod
    def _prepare_protection_measurement(
        relay,
        measurement: Dict[str, Any],
    ) -> None:
        """
        Prepare protection-specific quantities.

        This method does not create duplicate relay state.

        Distance protection:
            If voltage/current are supplied and impedance is not
            explicitly supplied, calculate apparent impedance
            through the distance protection algorithm.

        Other protection algorithms use the authoritative Relay
        measurements directly.
        """

        # ---------------------------------------------------------
        # Distance protection
        # ---------------------------------------------------------

        calculate_impedance = getattr(
            relay,
            "calculate_impedance",
            None,
        )

        if (
            callable(calculate_impedance)
            and "impedance" not in measurement
        ):

            voltage = measurement.get(
                "voltage",
                1.0,
            )

            current = measurement.get(
                "current",
                0.0,
            )

            impedance = calculate_impedance(
                voltage,
                current,
            )

            model_relay = (
                ProtectionSystem._get_relay_model(
                    relay
                )
            )

            model_relay.measure(
                current=current,
                voltage=voltage,
                impedance=impedance,
            )

    # =============================================================
    # PROTECTION EVALUATION
    # =============================================================

    @staticmethod
    def _evaluate_relay(
        relay,
        measurement: Dict[str, Any],
    ) -> bool:
        """
        Evaluate a registered protection algorithm.

        Protection-specific evaluation is delegated to the
        protection plugin.

        Supported evaluation forms:

        Normal protection algorithm:

            evaluate()

        Directional protection:

            evaluate(
                voltage_angle=...,
                current_angle=...
            )

        Raw Relay models may use their model-level evaluate()
        only as a compatibility fallback.
        """

        model_relay = (
            ProtectionSystem._get_relay_model(
                relay
            )
        )

        if not getattr(
            model_relay,
            "in_service",
            True,
        ):
            model_relay.set_trip(
                False
            )
            return False

        protection_evaluate = getattr(
            relay,
            "evaluate",
            None,
        )

        if not callable(
            protection_evaluate
        ):
            raise TypeError(
                "Registered protection relay does not "
                "provide an evaluate() method."
            )

        # ---------------------------------------------------------
        # Directional protection
        # ---------------------------------------------------------

        voltage_angle = measurement.get(
            "voltage_angle"
        )

        current_angle = measurement.get(
            "current_angle"
        )

        if (
            voltage_angle is not None
            or current_angle is not None
        ):

            if (
                voltage_angle is None
                or current_angle is None
            ):
                raise ValueError(
                    f"Directional relay '{model_relay.id}' "
                    "requires both voltage_angle and "
                    "current_angle."
                )

            result = protection_evaluate(
                voltage_angle=voltage_angle,
                current_angle=current_angle,
            )

        # ---------------------------------------------------------
        # Standard protection algorithms
        # ---------------------------------------------------------

        else:

            result = protection_evaluate()

        return bool(
            getattr(
                model_relay,
                "trip",
                bool(result),
            )
        )

    # =============================================================
    # FAULT / PROTECTION EVALUATION
    # =============================================================

    def evaluate(
        self,
        measurements: Dict[
            Any,
            Dict[str, Any]
        ],
    ) -> List[
        Dict[str, Any]
    ]:
        """
        Evaluate all registered protection relays.

        Parameters
        ----------
        measurements:
            Mapping:

                relay_id -> measurement dictionary

        Example
        -------

            {
                "R1": {
                    "current": 2500.0,
                    "voltage": 11000.0,
                    "impedance": 4.2 + 1.1j,
                }
            }

        Directional example:

            {
                "R2": {
                    "current": 2500.0,
                    "voltage": 11000.0,
                    "voltage_angle": 0.0,
                    "current_angle": -85.0,
                }
            }

        Returns
        -------
        list
            Breaker trip commands.

        Notes
        -----
        Breakers are not operated by this method.
        """

        if measurements is None:
            raise ValueError(
                "measurements cannot be None."
            )

        if not isinstance(
            measurements,
            dict,
        ):
            raise TypeError(
                "measurements must be a dictionary."
            )

        trips: List[
            Dict[str, Any]
        ] = []

        for relay_id, data in self.relays.items():

            if relay_id not in measurements:
                continue

            relay = data[
                "relay"
            ]

            measurement = measurements[
                relay_id
            ]

            # -----------------------------------------------------
            # Apply authoritative measurements
            # -----------------------------------------------------

            self._apply_measurement(
                relay,
                measurement,
            )

            # -----------------------------------------------------
            # Prepare protection-specific quantities
            # -----------------------------------------------------

            self._prepare_protection_measurement(
                relay,
                measurement,
            )

            # -----------------------------------------------------
            # Evaluate protection algorithm
            # -----------------------------------------------------

            operated = (
                self._evaluate_relay(
                    relay,
                    measurement,
                )
            )

            if not operated:
                continue

            trips.append(
                {
                    "relay": relay_id,
                    "breaker": data[
                        "breaker"
                    ],
                }
            )

        return trips

    # =============================================================
    # EXECUTE TRIP COMMANDS
    # =============================================================

    def operate(
        self,
        trip_commands: List[
            Dict[str, Any]
        ],
        time: float = 0.0,
    ) -> List[
        Dict[str, Any]
    ]:
        """
        Execute generated breaker-trip commands.

        BreakerManager owns actual breaker operation.
        """

        if trip_commands is None:
            raise ValueError(
                "trip_commands cannot be None."
            )

        results: List[
            Dict[str, Any]
        ] = []

        for command in trip_commands:

            if not isinstance(
                command,
                dict,
            ):
                raise TypeError(
                    "Each trip command must be a dictionary."
                )

            breaker_id = command.get(
                "breaker"
            )

            relay_id = command.get(
                "relay"
            )

            if breaker_id is None:
                raise ValueError(
                    "Trip command is missing breaker id."
                )

            # -----------------------------------------------------
            # No breaker manager
            # -----------------------------------------------------

            if self.breaker_manager is None:

                results.append(
                    {
                        "relay": relay_id,
                        "breaker": breaker_id,
                        "success": False,
                    }
                )

                continue

            # -----------------------------------------------------
            # Execute breaker operation
            # -----------------------------------------------------

            result = (
                self.breaker_manager.trip(
                    breaker_id,
                    time,
                )
            )

            success = bool(
                result
            )

            results.append(
                {
                    "relay": relay_id,
                    "breaker": breaker_id,
                    "success": success,
                }
            )

            # -----------------------------------------------------
            # Protection event
            # -----------------------------------------------------

            self.events.append(
                {
                    "time": float(time),
                    "relay": relay_id,
                    "breaker": breaker_id,
                    "action": "TRIP",
                    "success": success,
                }
            )

        return results

    # =============================================================
    # COMPLETE PROTECTION CYCLE
    # =============================================================

    def process_fault(
        self,
        measurements: Dict[
            Any,
            Dict[str, Any]
        ],
        time: float = 0.0,
    ) -> List[
        Dict[str, Any]
    ]:
        """
        Execute one complete protection cycle.

        Sequence:

            measurements
                |
                v
            authoritative Relay
                |
                v
            protection algorithm
                |
                v
            trip command
                |
                v
            BreakerManager
                |
                v
            Breaker.open()
                |
                v
            protection event
        """

        commands = self.evaluate(
            measurements
        )

        return self.operate(
            commands,
            time=time,
        )

    # =============================================================
    # RESET
    # =============================================================

    def reset(self) -> None:
        """
        Reset all registered protection relay states and
        clear protection events.

        Protection settings remain unchanged.
        """

        for data in self.relays.values():

            relay = data[
                "relay"
            ]

            model_relay = (
                self._get_relay_model(
                    relay
                )
            )

            reset = getattr(
                model_relay,
                "reset",
                None,
            )

            if callable(reset):
                reset()

            # Protection algorithms may maintain transient
            # algorithmic state such as active_zone or direction.

            protection_reset = getattr(
                relay,
                "reset",
                None,
            )

            if (
                callable(protection_reset)
                and relay is not model_relay
            ):
                protection_reset()

        self.events.clear()

    # =============================================================
    # STATUS
    # =============================================================

    def summary(
        self,
    ) -> Dict[str, Any]:
        """
        Return structured protection-system status.
        """

        relay_status: Dict[
            Any,
            Dict[str, Any]
        ] = {}

        for relay_id, data in self.relays.items():

            relay = data[
                "relay"
            ]

            model_relay = (
                self._get_relay_model(
                    relay
                )
            )

            relay_status[
                relay_id
            ] = {
                "type": getattr(
                    model_relay,
                    "type",
                    None,
                ),
                "breaker": data[
                    "breaker"
                ],
                "in_service": getattr(
                    model_relay,
                    "in_service",
                    False,
                ),
                "trip": getattr(
                    model_relay,
                    "trip",
                    False,
                ),
            }

        return {
            "relays": list(
                self.relays.keys()
            ),
            "relay_status": relay_status,
            "events": list(
                self.events
            ),
        }


__all__ = [
    "ProtectionSystem",
]
```
