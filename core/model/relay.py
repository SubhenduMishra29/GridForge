"""
GridForge Relay Model V2
========================

File:
    core/model/relay.py

Purpose
-------
Defines the canonical GridForge V2 protection Relay model.

Architectural Principle
-----------------------
A Relay is a protection-device model.

The Relay does NOT directly own measured current, voltage,
impedance, power, frequency, or other electrical quantities.

Those signals are supplied through MeasurementChannel objects.

Architecture
------------

    Physical measurement equipment
              │
        ┌─────┴─────┐
        │           │
       CT        PT / CVT
        │           │
        └─────┬─────┘
              │
              ▼
      MeasurementChannel
              │
              ▼
            Relay
              │
              ▼
     Protection Function
              │
              ▼
       ProtectionSystem
              │
              ▼
       BreakerManager

The Relay model is therefore independent of the specific protection
algorithm.

Examples:

    Relay
       │
       ├── current_channel
       └── overcurrent plugin

    Relay
       │
       ├── current_channel
       ├── voltage_channel
       └── directional plugin

    Relay
       │
       ├── current_channel
       ├── voltage_channel
       └── distance plugin

    Relay
       │
       ├── current_channel_A
       ├── current_channel_B
       ├── current_channel_C
       └── differential plugin

Responsibilities
----------------
The Relay model is responsible for:

    - relay identity
    - relay function/type
    - service state
    - measurement-channel associations
    - protection settings
    - operating state
    - pickup state
    - trip state
    - reset state
    - local configuration validation
    - diagnostics

The Relay model does NOT:

    - calculate electrical measurements
    - transform CT/PT/CVT signals
    - calculate impedance
    - calculate directional quantities
    - calculate differential current
    - calculate fault current
    - perform TCC calculations
    - coordinate relays
    - perform load flow
    - perform short circuit
    - operate circuit breakers
    - schedule protection events
    - implement protection algorithms

Those responsibilities belong to:

    core/measurement
    core/protection
    core/analysis
    core/simulation

Measurement Ownership
---------------------
The Relay does not duplicate MeasurementChannel state.

The channel remains authoritative for its signal:

    channel.value
    channel.quality
    channel.available
    channel.timestamp

The Relay stores only references to the channels it consumes.

Protection plugins obtain their required inputs through the Relay.

Settings
--------
The Relay provides generic protection settings storage.

The model does not interpret protection-specific settings.

For example:

    OVER_CURRENT:
        pickup
        time_dial
        curve

    DISTANCE:
        zone_1
        zone_2
        zone_3
        reach

    DIFFERENTIAL:
        slope
        bias
        pickup

Such interpretation belongs to the protection implementation.

The Relay may provide generic settings access without embedding
algorithm-specific mathematics.

Relay Type
----------
The relay type identifies the intended protection function family.

Supported canonical types:

    OVER_CURRENT
    DIRECTIONAL
    DISTANCE
    DIFFERENTIAL
    VOLTAGE
    FREQUENCY
    POWER
    CUSTOM

Protection plugins may support additional function types without
requiring changes to the Relay model.

Trip State
----------
The Relay maintains its own logical operating state.

The states are intentionally simple:

    pickup
        Protection element has asserted pickup.

    trip
        Relay has issued a logical trip decision.

A logical relay trip does NOT directly operate a breaker.

Breaker operation belongs to ProtectionSystem / BreakerManager.

GridForge V2 Status
-------------------
Canonical GridForge Model Layer V2 protection-device model.

This module replaces the former Relay model that stored raw
current/voltage/impedance measurements internally.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from enum import Enum
from math import isfinite
from typing import Any, Mapping

from .base import ElectricalObject


# =====================================================================
# RELAY TYPE
# =====================================================================


class RelayType(Enum):
    """
    Canonical GridForge relay function families.
    """

    OVER_CURRENT = "OVER_CURRENT"
    DIRECTIONAL = "DIRECTIONAL"
    DISTANCE = "DISTANCE"
    DIFFERENTIAL = "DIFFERENTIAL"
    VOLTAGE = "VOLTAGE"
    FREQUENCY = "FREQUENCY"
    POWER = "POWER"
    CUSTOM = "CUSTOM"


# =====================================================================
# RELAY
# =====================================================================


class Relay(ElectricalObject):
    """
    Canonical GridForge V2 protection Relay model.

    Parameters
    ----------
    id : str
        Unique GridForge relay identifier.

    relay_type : RelayType or str
        Protection function family.

    name : str, optional
        Human-readable relay name.

    settings : mapping, optional
        Generic protection settings.

        The Relay stores these settings but does not interpret
        protection-specific mathematics.

    in_service : bool, optional
        Relay service state.

    Notes
    -----
    Measurement signals are connected separately through
    ``connect_input()``.

    The Relay never copies MeasurementChannel values into local
    current/voltage/impedance attributes.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        id: str,
        relay_type: RelayType | str,
        name: str = "",
        settings: Mapping[str, Any] | None = None,
        in_service: bool = True,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # ---------------------------------------------------------
        # Relay type
        # ---------------------------------------------------------

        self.type = self._normalize_type(
            relay_type
        )

        # ---------------------------------------------------------
        # Service state
        # ---------------------------------------------------------

        self.in_service = bool(
            in_service
        )

        # ---------------------------------------------------------
        # Protection settings
        #
        # These are configuration data only.
        # Protection plugins interpret them.
        # ---------------------------------------------------------

        self.settings: dict[str, Any] = dict(
            settings or {}
        )

        # ---------------------------------------------------------
        # Measurement inputs
        #
        # Key:
        #     logical input name
        #
        # Value:
        #     MeasurementChannel reference
        # ---------------------------------------------------------

        self._inputs: dict[str, Any] = {}

        # ---------------------------------------------------------
        # Operating state
        # ---------------------------------------------------------

        self.pickup = False
        self.trip = False

        # ---------------------------------------------------------
        # Optional operating metadata
        #
        # These do not represent electrical measurements.
        # They represent relay-device state.
        # ---------------------------------------------------------

        self.operation_count = 0

    # =============================================================
    # TYPE
    # =============================================================

    @staticmethod
    def _normalize_type(
        relay_type: RelayType | str,
    ) -> RelayType:
        """
        Normalize a relay type to RelayType.
        """

        if isinstance(
            relay_type,
            RelayType,
        ):
            return relay_type

        if not isinstance(
            relay_type,
            str,
        ):
            raise TypeError(
                "relay_type must be a RelayType or string."
            )

        value = relay_type.strip().upper()

        try:
            return RelayType(value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid relay type '{relay_type}'. "
                f"Supported types: "
                f"{[item.value for item in RelayType]}"
            ) from exc

    # =============================================================
    # INPUT CHANNELS
    # =============================================================

    @staticmethod
    def _validate_channel(
        channel: Any,
    ) -> None:
        """
        Validate the minimum MeasurementChannel contract.

        The Relay deliberately does not import a concrete
        MeasurementChannel implementation.

        This preserves plugin and dependency flexibility.
        """

        if channel is None:
            raise ValueError(
                "Measurement channel cannot be None."
            )

        if not hasattr(channel, "id"):
            raise TypeError(
                "Measurement channel must expose an 'id' attribute."
            )

        channel_id = getattr(
            channel,
            "id",
        )

        if not isinstance(
            channel_id,
            str,
        ):
            raise TypeError(
                "Measurement channel id must be a string."
            )

        if not channel_id.strip():
            raise ValueError(
                "Measurement channel id cannot be empty."
            )

    # -------------------------------------------------------------

    def connect_input(
        self,
        name: str,
        channel: Any,
    ) -> None:
        """
        Connect a logical relay input to a MeasurementChannel.

        Parameters
        ----------
        name : str
            Logical input name.

            Examples:

                "current"
                "voltage"
                "current_a"
                "current_b"
                "current_c"
                "voltage_a"
                "voltage_b"
                "voltage_c"

        channel :
            MeasurementChannel reference.

        Notes
        -----
        This stores a reference only.

        It does not modify the MeasurementChannel and does not
        create any physical network connection.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Relay input name must be a string."
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "Relay input name cannot be empty."
            )

        self._validate_channel(
            channel
        )

        self._inputs[name] = channel

    # -------------------------------------------------------------

    def disconnect_input(
        self,
        name: str,
    ) -> None:
        """
        Remove a logical measurement input.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Relay input name must be a string."
            )

        self._inputs.pop(
            name,
            None,
        )

    # -------------------------------------------------------------

    def get_input(
        self,
        name: str,
    ) -> Any | None:
        """
        Return the MeasurementChannel associated with a logical
        relay input.
        """

        return self._inputs.get(
            name
        )

    # -------------------------------------------------------------

    def require_input(
        self,
        name: str,
    ) -> Any:
        """
        Return a required input channel.

        Raises
        ------
        KeyError
            If the requested input is not connected.
        """

        channel = self.get_input(
            name
        )

        if channel is None:
            raise KeyError(
                f"Relay '{self.id}' has no input "
                f"channel named '{name}'."
            )

        return channel

    # -------------------------------------------------------------

    @property
    def inputs(self) -> dict[str, Any]:
        """
        Return a read-only-style copy of the input mapping.

        The contained channel objects remain the authoritative
        MeasurementChannel objects.
        """

        return dict(
            self._inputs
        )

    # =============================================================
    # INPUT STATUS
    # =============================================================

    def input_available(
        self,
        name: str,
    ) -> bool:
        """
        Return whether a connected input is available.
        """

        channel = self.require_input(
            name
        )

        return bool(
            channel.available
        )

    # -------------------------------------------------------------

    def input_valid(
        self,
        name: str,
    ) -> bool:
        """
        Return whether a connected input is suitable for normal
        engineering consumption.

        The channel remains authoritative for signal validity.
        """

        channel = self.require_input(
            name
        )

        return bool(
            channel.is_valid
        )

    # -------------------------------------------------------------

    def all_inputs_valid(self) -> bool:
        """
        Return True when all connected inputs are valid.

        A relay with no inputs returns False because it cannot
        perform a meaningful protection operation.
        """

        if not self._inputs:
            return False

        return all(
            bool(channel.is_valid)
            for channel in self._inputs.values()
        )

    # =============================================================
    # SETTINGS
    # =============================================================

    def set_setting(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Set a generic protection setting.

        The Relay stores the value without interpreting it.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Setting name must be a string."
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "Setting name cannot be empty."
            )

        self.settings[name] = value

    # -------------------------------------------------------------

    def get_setting(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return a protection setting.
        """

        return self.settings.get(
            name,
            default,
        )

    # -------------------------------------------------------------

    def require_setting(
        self,
        name: str,
    ) -> Any:
        """
        Return a required protection setting.

        Raises
        ------
        KeyError
            If the setting is absent.
        """

        if name not in self.settings:
            raise KeyError(
                f"Relay '{self.id}' requires setting '{name}'."
            )

        return self.settings[name]

    # -------------------------------------------------------------

    def update_settings(
        self,
        settings: Mapping[str, Any],
    ) -> None:
        """
        Update multiple generic protection settings.
        """

        if not isinstance(
            settings,
            Mapping,
        ):
            raise TypeError(
                "settings must be a mapping."
            )

        for name, value in settings.items():
            self.set_setting(
                name,
                value,
            )

    # =============================================================
    # SERVICE STATE
    # =============================================================

    def set_in_service(
        self,
        in_service: bool,
    ) -> None:
        """
        Set relay service state.

        Removing a relay from service clears its operating state.
        """

        self.in_service = bool(
            in_service
        )

        if not self.in_service:
            self.clear_operation()

    # -------------------------------------------------------------

    def trip_out(self) -> None:
        """
        Remove the relay from service.
        """

        self.set_in_service(
            False
        )

    # -------------------------------------------------------------

    def close(self) -> None:
        """
        Return the relay to service.
        """

        self.in_service = True

    # =============================================================
    # OPERATING STATE
    # =============================================================

    def set_pickup(
        self,
        state: bool,
    ) -> None:
        """
        Set logical relay pickup state.

        This represents protection-element pickup only.

        It does not operate a breaker.
        """

        if not self.in_service:
            self.pickup = False
            return

        self.pickup = bool(
            state
        )

    # -------------------------------------------------------------

    def set_trip(
        self,
        state: bool,
    ) -> None:
        """
        Set logical relay trip state.

        This represents a relay trip command.

        It does NOT operate a circuit breaker.
        """

        if not self.in_service:
            self.trip = False
            return

        new_state = bool(
            state
        )

        if new_state and not self.trip:
            self.operation_count += 1

        self.trip = new_state

    # -------------------------------------------------------------

    def clear_operation(self) -> None:
        """
        Clear pickup and trip states.
        """

        self.pickup = False
        self.trip = False

    # -------------------------------------------------------------

    def reset(self) -> None:
        """
        Reset relay operating state.

        Measurement channels and their values are not modified.

        Protection-plugin transient state must be reset by the
        corresponding protection implementation.
        """

        self.clear_operation()

    # =============================================================
    # PROTECTION INPUT SNAPSHOT
    # =============================================================

    def input_snapshot(self) -> dict[str, Any]:
        """
        Return the current state of all connected measurement
        channels.

        This is a diagnostic/consumer snapshot.

        The returned data does not become authoritative Relay state.
        """

        snapshot: dict[str, Any] = {}

        for name, channel in self._inputs.items():

            snapshot[name] = {
                "channel_id": channel.id,
                "value": channel.value,
                "engineering_value": (
                    channel.engineering_value
                ),
                "unit": channel.unit,
                "signal_type": (
                    channel.signal_type.value
                ),
                "phase": channel.phase.value,
                "available": channel.available,
                "quality": channel.quality.value,
                "usable": channel.is_usable,
                "timestamp": channel.timestamp,
            }

        return snapshot

    # =============================================================
    # CONFIGURATION VALIDATION
    # =============================================================

    def validate_configuration(self) -> list[str]:
        """
        Perform local Relay configuration validation.

        Returns
        -------
        list[str]
            Configuration errors.

        Notes
        -----
        This method intentionally does not know the detailed input
        requirements of every protection algorithm.

        Protection plugins may add specialized validation.

        Examples:

            An overcurrent plugin may require "current".

            A directional plugin may require "current" and "voltage".

            A distance plugin may require voltage and current.

            A differential plugin may require multiple current inputs.
        """

        errors: list[str] = []

        if not self.id.strip():
            errors.append(
                "Relay ID cannot be empty."
            )

        if not isinstance(
            self.type,
            RelayType,
        ):
            errors.append(
                "Relay type is invalid."
            )

        for name, channel in self._inputs.items():

            try:
                self._validate_channel(
                    channel
                )
            except (
                TypeError,
                ValueError,
            ) as exc:

                errors.append(
                    f"Input '{name}': {exc}"
                )

        for name in self.settings:

            if not isinstance(
                name,
                str,
            ) or not name.strip():

                errors.append(
                    "Relay setting names must be "
                    "non-empty strings."
                )

        return errors

    # =============================================================
    # STATUS
    # =============================================================

    def status(self) -> dict[str, Any]:
        """
        Return structured Relay status.

        Measurement values are intentionally obtained from the
        connected MeasurementChannels rather than duplicated in
        Relay state.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "in_service": self.in_service,
            "pickup": self.pickup,
            "trip": self.trip,
            "operation_count": self.operation_count,
            "settings": dict(
                self.settings
            ),
            "inputs": self.input_snapshot(),
        }

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return a compact Relay engineering summary.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "in_service": self.in_service,
            "pickup": self.pickup,
            "trip": self.trip,
            "input_count": len(
                self._inputs
            ),
            "inputs": {
                name: channel.id
                for name, channel
                in self._inputs.items()
            },
            "setting_names": sorted(
                self.settings.keys()
            ),
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<Relay "
            f"id={self.id}, "
            f"type={self.type.value}, "
            f"inputs={len(self._inputs)}, "
            f"in_service={self.in_service}, "
            f"pickup={self.pickup}, "
            f"trip={self.trip}>"
        )


__all__ = [
    "RelayType",
    "Relay",
]
```
