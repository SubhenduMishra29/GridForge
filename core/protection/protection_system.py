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
- Register protection relay elements.
- Associate relay elements with breakers.
- Supply measurements to the authoritative Relay model.
- Evaluate protection algorithms.
- Generate trip commands.
- Interface with BreakerManager.
- Record protection events.

Architecture
------------

    core/model/relay.py
            |
            | authoritative relay state
            v
    core/protection/
            |
            v
    ProtectionSystem
            |
            v
    BreakerManager

Important
---------
The Relay model in core/model/relay.py is frozen and remains the
authoritative owner of:

    - measurements
    - pickup setting
    - in-service state
    - trip state

ProtectionSystem does not create a second relay state.

Protection algorithms may be supplied as RelayBase-derived objects.
A raw model Relay is also supported for basic model-level evaluation.

ProtectionSystem does NOT:

    - build Ybus
    - perform load flow
    - perform short-circuit analysis
    - calculate protection settings
    - coordinate relays
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
        Optional BreakerManager instance responsible for actual
        breaker operation.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        breaker_manager: Optional[Any] = None,
    ) -> None:

        self.relays: Dict[Any, Dict[str, Any]] = {}

        self.breaker_manager = (
            breaker_manager
        )

        self.events: List[Dict[str, Any]] = []

    # =============================================================
    # RELAY REGISTRATION
    # =============================================================

    def add_relay(
        self,
        relay,
        breaker_id: Any,
    ) -> None:
        """
        Register a protection relay.

        Parameters
        ----------
        relay:
            Either:

                1. a RelayBase-derived protection algorithm, or
                2. the authoritative model Relay.

            RelayBase-derived objects are preferred for detailed
            protection functions.

        breaker_id:
            Identifier of the breaker operated by this relay.

        Notes
        -----
        The relay object itself remains authoritative for relay
        state. ProtectionSystem stores only the association between
        relay and breaker.
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
    # MEASUREMENT INPUT
    # =============================================================

    @staticmethod
    def _apply_measurement(
        relay,
        measurement: Dict[str, Any],
    ) -> None:
        """
        Apply a measurement to the authoritative Relay model.

        Locked model API:

            relay.measure(
                current,
                voltage,
                impedance,
            )

        The protection system accepts measurement dictionaries
        using named fields so positional-order mistakes cannot occur.
        """

        if not isinstance(
            measurement,
            dict,
        ):
            raise TypeError(
                "Relay measurement must be a dictionary."
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

        # ---------------------------------------------------------
        # RelayBase / protection algorithm
        # ---------------------------------------------------------

        relay_measure = getattr(
            relay,
            "measure",
            None,
        )

        if relay_measure is None:
            raise TypeError(
                "Registered relay does not provide "
                "a measure() method."
            )

        relay_measure(
            current=current,
            voltage=voltage,
            impedance=impedance,
        )

    # =============================================================
    # RELAY MODEL ACCESS
    # =============================================================

    @staticmethod
    def _get_relay_model(relay):
        """
        Return the authoritative model Relay.

        RelayBase stores it as:

            relay.relay

        A raw model Relay is returned directly.
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
    # PICKUP / TRIP EVALUATION
    # =============================================================

    @staticmethod
    def _evaluate_relay(
        relay,
    ) -> bool:
        """
        Evaluate a registered relay/protection algorithm.

        Preferred path:
            RelayBase.evaluate()

        Fallback:
            model Relay.evaluate()

        Returns
        -------
        bool
            True when the relay has issued a trip decision.
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
            model_relay.set_trip(False)
            return False

        # ---------------------------------------------------------
        # Preferred protection-layer evaluation
        # ---------------------------------------------------------

        protection_evaluate = getattr(
            relay,
            "evaluate",
            None,
        )

        if callable(
            protection_evaluate
        ):

            result = bool(
                protection_evaluate()
            )

            return bool(
                getattr(
                    model_relay,
                    "trip",
                    False,
                )
            )

        # ---------------------------------------------------------
        # Fallback to locked model-level evaluation
        # ---------------------------------------------------------

        model_evaluate = getattr(
            model_relay,
            "evaluate",
            None,
        )

        if callable(
            model_evaluate
        ):
            model_evaluate()

        return bool(
            getattr(
                model_relay,
                "trip",
                False,
            )
        )

    # =============================================================
    # FAULT / PROTECTION EVALUATION
    # =============================================================

    def evaluate(
        self,
        measurements: Dict[Any, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Evaluate all registered protection relays.

        Parameters
        ----------
        measurements:
            Mapping:

                relay_id -> measurement dictionary

            Example:

                {
                    "R1": {
                        "current": 2500.0,
                        "voltage": 11000.0,
                        "impedance": 4.2 + 1.1j,
                    }
                }

        Returns
        -------
        list
            Trip commands.

        Notes
        -----
        Measurement values are applied to the authoritative model
        Relay through its measure() interface.

        Breakers are NOT operated here.
        """

        if measurements is None:
            raise ValueError(
                "measurements cannot be None."
            )

        trips: List[
            Dict[str, Any]
        ] = []

        for relay_id, data in self.relays.items():

            relay = data["relay"]

            if relay_id not in measurements:
                continue

            measurement = (
                measurements[relay_id]
            )

            # -----------------------------------------------------
            # Apply measurements
            # -----------------------------------------------------

            self._apply_measurement(
                relay,
                measurement,
            )

            # -----------------------------------------------------
            # Evaluate protection logic
            # -----------------------------------------------------

            operated = (
                self._evaluate_relay(
                    relay
                )
            )

            if not operated:
                continue

            trips.append(
                {
                    "relay": relay_id,
                    "breaker": data["breaker"],
                }
            )

        return trips

    # =============================================================
    # EXECUTE TRIP COMMANDS
    # =============================================================

    def operate(
        self,
        trip_commands: List[Dict[str, Any]],
        time: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Execute generated breaker-trip commands.

        Parameters
        ----------
        trip_commands:
            Commands returned by evaluate().

        time:
            Event time in seconds.

        Returns
        -------
        list
            Breaker operation results.

        Notes
        -----
        ProtectionSystem does not directly operate breakers.

        BreakerManager owns breaker operation.
        """

        results: List[
            Dict[str, Any]
        ] = []

        for command in trip_commands:

            breaker_id = command.get(
                "breaker"
            )

            relay_id = command.get(
                "relay"
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
            # Record protection event
            # -----------------------------------------------------

            if success:

                self.events.append(
                    {
                        "time": time,
                        "relay": relay_id,
                        "breaker": breaker_id,
                    }
                )

        return results

    # =============================================================
    # COMPLETE PROTECTION CYCLE
    # =============================================================

    def process_fault(
        self,
        measurements: Dict[Any, Dict[str, Any]],
        time: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Execute one complete protection cycle.

        Sequence:

            measurements
                |
                v
            relay measurement
                |
                v
            protection evaluation
                |
                v
            trip commands
                |
                v
            BreakerManager
                |
                v
            event record

        Returns
        -------
        list
            Breaker operation results.
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
        Reset all registered relay states and clear events.
        """

        for data in self.relays.values():

            relay = data["relay"]

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

        self.events.clear()

    # =============================================================
    # STATUS
    # =============================================================

    def summary(self) -> Dict[str, Any]:
        """
        Return protection-system summary.
        """

        relay_status = {}

        for relay_id, data in self.relays.items():

            relay = data["relay"]

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
