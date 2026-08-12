"""
GridForge Relay Model V2
========================

File:
    core/model/relay.py

Purpose
-------
Defines the canonical GridForge protection Relay device model.

Architectural role
------------------
The Relay is a physical protection device in the GridForge model
layer. It represents the relay itself, its configuration, its
measurement-channel bindings, and its operating state.

The Relay does NOT implement protection algorithms.

Protection algorithms are supplied by:

    core/protection/

The Relay receives electrical signals indirectly through
MeasurementChannel objects.

Signal architecture
-------------------

    Power-System Equipment
            |
       CT / PT / CVT
            |
            v
    MeasurementChannel
            |
            v
        Relay V2
            |
            v
    Protection Plugin
            |
            v
    ProtectionSystem
            |
            v
    BreakerManager

Important architectural rule
----------------------------

The Relay does NOT store independent copies of:

    current
    voltage
    impedance
    frequency
    power
    phase angle
    sequence components

Those quantities belong to the measurement path.

The authoritative measurement chain is:

    CT / PT / CVT
        ->
    MeasurementChannel
        ->
    Relay input

Protection plugins consume Relay inputs through the Relay interface.

Responsibilities
----------------
Relay V2 is responsible for:

- relay identity
- relay type/function identity
- relay service state
- relay enable/block state
- relay configuration/settings
- measurement-channel bindings
- protection-function/plugin identity
- pickup state
- trip state
- reset state
- input availability
- local configuration validation
- diagnostic/status reporting

Relay V2 does NOT:

- calculate CT transformation
- calculate PT transformation
- calculate CVT behaviour
- simulate measurement channels
- calculate fault current
- build Y-bus
- perform load flow
- perform short circuit
- implement overcurrent curves
- implement directional algorithms
- implement distance zones
- implement differential algorithms
- perform relay coordination
- calculate TCC coordination
- operate circuit breakers
- schedule protection events
- manage GUI objects

Those responsibilities belong to the appropriate GridForge
model, measurement, protection, analysis, simulation, and system
layers.

Measurement ownership
---------------------

The Relay stores references to MeasurementChannel objects.

It does not copy their measured values.

Example:

    relay.bind_input(
        "IA",
        current_channel
    )

The protection plugin can then obtain the current signal through:

    relay.get_input("IA")

The MeasurementChannel remains authoritative for the signal.

Plugin architecture
-------------------

The Relay does not import or instantiate a protection algorithm.

A protection plugin is associated with the relay by a stable
function/plugin identifier.

Example:

    relay.function_type = "OVER_CURRENT"
    relay.plugin_id = "iec_overcurrent"

The protection subsystem is responsible for resolving that identifier
to an executable protection implementation.

This preserves the separation:

    Model
        ->
    Protection Plugin
        ->
    Protection System

Input naming
------------

Relay inputs are intentionally named by protection meaning rather
than hard-coded electrical quantities.

Examples:

    "IA"
    "IB"
    "IC"
    "IN"
    "VA"
    "VB"
    "VC"
    "VN"
    "V1"
    "I1"
    "Z1"
    "Z2"
    "Z0"

The Relay does not impose which inputs a particular protection
function requires.

The protection plugin defines its required input contract.

Settings
--------

Protection settings are stored as a model configuration dictionary.

Examples:

    {
        "pickup": 1.2,
        "curve": "IEC_STANDARD_INVERSE",
        "time_multiplier": 0.1
    }

or:

    {
        "zone1_impedance": 8.5,
        "zone1_time": 0.0,
        "zone2_impedance": 18.0
    }

The Relay stores these settings but does not interpret them.

Interpretation belongs to the protection plugin.

Operating state
---------------

The Relay maintains only device-level operating state:

    in_service
    enabled
    blocked
    picked_up
    tripped

Protection algorithms determine when pickup/trip should occur.

The Relay provides explicit state mutation methods so that the
protection subsystem does not directly manipulate internal model
attributes.

GridForge V2 status
-------------------

Canonical Model Layer V2 protection-device model.

This file supersedes the previous Relay implementation that directly
stored current, voltage, impedance, generic pickup, and generic
time-delay behaviour.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class Relay:
    """
    Canonical GridForge V2 protection relay model.

    Parameters
    ----------
    id:
        Unique GridForge relay identifier.

    relay_type:
        Stable protection-device/function category.

        Examples:

            "OVER_CURRENT"
            "DIRECTIONAL"
            "DISTANCE"
            "DIFFERENTIAL"
            "VOLTAGE"
            "FREQUENCY"

        The model stores the value but does not implement the
        associated protection algorithm.

    name:
        Human-readable relay name.

    function_type:
        Protection function represented by the relay.

        If omitted, ``relay_type`` is used.

    plugin_id:
        Optional stable protection-plugin identifier.

        This is metadata/configuration only. The Relay does not
        import or instantiate the plugin.

    settings:
        Protection configuration supplied to the protection layer.

    in_service:
        Whether the physical relay is in service.

    enabled:
        Whether the relay is enabled for operation.

    blocked:
        Whether relay operation is externally blocked.
    """

    # =============================================================
    # VALID RELAY TYPES
    # =============================================================

    VALID_TYPES = frozenset(
        {
            "OVER_CURRENT",
            "DIRECTIONAL",
            "DISTANCE",
            "DIFFERENTIAL",
            "VOLTAGE",
            "FREQUENCY",
        }
    )

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        id: str,
        relay_type: str,
        name: str = "",
        *,
        function_type: str | None = None,
        plugin_id: str | None = None,
        settings: Mapping[str, Any] | None = None,
        in_service: bool = True,
        enabled: bool = True,
        blocked: bool = False,
    ) -> None:

        # ---------------------------------------------------------
        # Identity
        # ---------------------------------------------------------

        self._validate_id(id)

        self.id = id
        self.name = str(name)

        # ---------------------------------------------------------
        # Relay type
        # ---------------------------------------------------------

        relay_type = str(relay_type).upper()

        if relay_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid relay type '{relay_type}'. "
                f"Supported types: {sorted(self.VALID_TYPES)}"
            )

        self.type = relay_type

        # ---------------------------------------------------------
        # Protection function
        # ---------------------------------------------------------

        if function_type is None:
            function_type = relay_type

        function_type = str(function_type).strip().upper()

        if not function_type:
            raise ValueError(
                "function_type cannot be empty."
            )

        self.function_type = function_type

        # ---------------------------------------------------------
        # Protection plugin identity
        # ---------------------------------------------------------

        if plugin_id is not None:

            plugin_id = str(plugin_id).strip()

            if not plugin_id:
                raise ValueError(
                    "plugin_id cannot be empty when supplied."
                )

        self.plugin_id = plugin_id

        # ---------------------------------------------------------
        # Protection settings
        #
        # The Relay stores configuration.
        #
        # It does NOT interpret protection settings.
        # ---------------------------------------------------------

        if settings is None:
            self.settings: dict[str, Any] = {}

        elif isinstance(settings, Mapping):
            self.settings = dict(settings)

        else:
            raise TypeError(
                "settings must be a mapping or None."
            )

        # ---------------------------------------------------------
        # Measurement-channel bindings
        #
        # Key:
        #     relay input name
        #
        # Value:
        #     MeasurementChannel object
        #
        # The channel remains authoritative for measurements.
        # ---------------------------------------------------------

        self._input_channels: dict[str, Any] = {}

        # ---------------------------------------------------------
        # Service state
        # ---------------------------------------------------------

        self.in_service = bool(in_service)
        self.enabled = bool(enabled)
        self.blocked = bool(blocked)

        # ---------------------------------------------------------
        # Operating state
        # ---------------------------------------------------------

        self.picked_up = False
        self.tripped = False

    # =============================================================
    # VALIDATION
    # =============================================================

    @staticmethod
    def _validate_id(
        id: str,
    ) -> None:
        """
        Validate the Relay identifier.
        """

        if not isinstance(id, str):
            raise TypeError(
                "Relay id must be a string."
            )

        if not id.strip():
            raise ValueError(
                "Relay id cannot be empty."
            )

    # =============================================================
    # FUNCTION IDENTITY
    # =============================================================

    @property
    def relay_type(self) -> str:
        """
        Compatibility accessor for the relay type.

        ``type`` remains the stored canonical attribute.
        """

        return self.type

    # -------------------------------------------------------------

    @property
    def protection_function(self) -> str:
        """
        Return the protection function identifier.
        """

        return self.function_type

    # =============================================================
    # SETTINGS
    # =============================================================

    def set_setting(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Set one protection configuration parameter.

        The Relay stores the setting but does not interpret it.
        """

        if not isinstance(name, str):
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
        Return one protection configuration parameter.
        """

        return self.settings.get(
            name,
            default,
        )

    # -------------------------------------------------------------

    def remove_setting(
        self,
        name: str,
    ) -> None:
        """
        Remove one protection configuration parameter.
        """

        self.settings.pop(
            name,
            None,
        )

    # -------------------------------------------------------------

    def set_settings(
        self,
        settings: Mapping[str, Any],
    ) -> None:
        """
        Replace the complete protection configuration.

        A shallow copy is stored so the caller's mapping remains
        independent of the Relay settings dictionary.
        """

        if not isinstance(settings, Mapping):
            raise TypeError(
                "settings must be a mapping."
            )

        self.settings = dict(settings)

    # =============================================================
    # MEASUREMENT CHANNELS
    # =============================================================

    @property
    def input_channels(self) -> dict[str, Any]:
        """
        Return the relay's measurement-channel bindings.

        A shallow copy is returned so callers cannot directly
        replace the Relay's binding dictionary.
        """

        return dict(
            self._input_channels
        )

    # -------------------------------------------------------------

    def bind_input(
        self,
        name: str,
        channel: Any,
    ) -> None:
        """
        Bind a MeasurementChannel to a named relay input.

        Parameters
        ----------
        name:
            Protection input name.

            Examples:

                "IA"
                "IB"
                "IC"
                "IN"
                "VA"
                "VB"
                "VC"
                "V1"
                "I1"

        channel:
            MeasurementChannel instance.

        Notes
        -----
        The Relay deliberately validates only the minimum channel
        interface here.

        The detailed measurement-channel contract belongs to
        ``core/model/measurement_channel.py``.
        """

        self._validate_input_name(
            name
        )

        self._validate_channel(
            channel
        )

        self._input_channels[name] = channel

    # -------------------------------------------------------------

    def unbind_input(
        self,
        name: str,
    ) -> None:
        """
        Remove a named measurement-channel binding.
        """

        self._validate_input_name(
            name
        )

        self._input_channels.pop(
            name,
            None,
        )

    # -------------------------------------------------------------

    def has_input(
        self,
        name: str,
    ) -> bool:
        """
        Return True when the named relay input is bound.
        """

        self._validate_input_name(
            name
        )

        return name in self._input_channels

    # -------------------------------------------------------------

    def get_input(
        self,
        name: str,
    ) -> Any:
        """
        Return the MeasurementChannel bound to a relay input.

        Raises
        ------
        KeyError
            If the input is not bound.
        """

        self._validate_input_name(
            name
        )

        try:
            return self._input_channels[name]

        except KeyError as exc:

            raise KeyError(
                f"Relay '{self.id}' has no input "
                f"channel bound to '{name}'."
            ) from exc

    # -------------------------------------------------------------

    def get_input_value(
        self,
        name: str,
    ) -> Any:
        """
        Return the current signal value from a named
        MeasurementChannel.

        The Relay does not store a copy of the value.

        This method intentionally supports the finalized
        MeasurementChannel interface without requiring the Relay
        to know how the channel internally represents its signal.
        """

        channel = self.get_input(
            name
        )

        # Preferred V2 measurement interface.
        if hasattr(channel, "value"):

            value = channel.value

            if callable(value):
                return value()

            return value

        # Explicit signal accessor.
        if hasattr(channel, "get_value"):

            return channel.get_value()

        raise TypeError(
            f"Measurement channel bound to relay input "
            f"'{name}' does not expose a supported value interface."
        )

    # -------------------------------------------------------------

    def input_values(self) -> dict[str, Any]:
        """
        Return the current values of all bound relay inputs.

        Values are read from the authoritative
        MeasurementChannel objects.

        No measurement values are stored in the Relay.
        """

        return {
            name: self.get_input_value(name)
            for name in self._input_channels
        }

    # -------------------------------------------------------------

    @staticmethod
    def _validate_input_name(
        name: str,
    ) -> None:
        """
        Validate a relay input name.
        """

        if not isinstance(name, str):
            raise TypeError(
                "Relay input name must be a string."
            )

        if not name.strip():
            raise ValueError(
                "Relay input name cannot be empty."
            )

    # -------------------------------------------------------------

    @staticmethod
    def _validate_channel(
        channel: Any,
    ) -> None:
        """
        Validate the minimum MeasurementChannel contract.

        The complete channel semantics remain defined by
        core.model.measurement_channel.
        """

        if channel is None:
            raise ValueError(
                "MeasurementChannel cannot be None."
            )

        if not hasattr(channel, "id"):
            raise TypeError(
                "MeasurementChannel must expose an 'id' attribute."
            )

        channel_id = getattr(
            channel,
            "id",
        )

        if not isinstance(channel_id, str):
            raise TypeError(
                "MeasurementChannel id must be a string."
            )

        if not channel_id.strip():
            raise ValueError(
                "MeasurementChannel id cannot be empty."
            )

    # =============================================================
    # INPUT AVAILABILITY
    # =============================================================

    def required_inputs_available(
        self,
        required_inputs,
    ) -> bool:
        """
        Return True when all requested relay inputs are bound.

        This checks binding existence only.

        It does not determine whether the measurement itself is
        electrically valid or numerically healthy.
        """

        for name in required_inputs:

            if not self.has_input(name):
                return False

        return True

    # -------------------------------------------------------------

    def available_inputs(self) -> tuple[str, ...]:
        """
        Return names of currently bound relay inputs.
        """

        return tuple(
            self._input_channels.keys()
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
            self.clear_operating_state()

    # -------------------------------------------------------------

    def enable(self) -> None:
        """
        Enable the relay.
        """

        self.enabled = True

    # -------------------------------------------------------------

    def disable(self) -> None:
        """
        Disable the relay.

        Disabled relays cannot operate.
        """

        self.enabled = False
        self.clear_operating_state()

    # -------------------------------------------------------------

    def block(self) -> None:
        """
        Block relay operation.
        """

        self.blocked = True
        self.clear_operating_state()

    # -------------------------------------------------------------

    def unblock(self) -> None:
        """
        Remove the relay operating block.
        """

        self.blocked = False

    # =============================================================
    # OPERATIONAL AVAILABILITY
    # =============================================================

    @property
    def operational(self) -> bool:
        """
        Return whether the relay is available for protection
        evaluation.
        """

        return (
            self.in_service
            and self.enabled
            and not self.blocked
        )

    # =============================================================
    # OPERATING STATE
    # =============================================================

    @property
    def pickup(self) -> bool:
        """
        Compatibility/readability alias for pickup state.

        ``picked_up`` is the canonical stored state.
        """

        return self.picked_up

    # -------------------------------------------------------------

    def set_pickup(
        self,
        state: bool,
    ) -> None:
        """
        Set relay pickup state.

        Protection algorithms determine when this state should
        change.
        """

        if not self.operational:
            self.picked_up = False
            return

        self.picked_up = bool(
            state
        )

    # -------------------------------------------------------------

    def set_trip(
        self,
        state: bool,
    ) -> None:
        """
        Set relay trip state.

        This changes relay state only.

        It does NOT operate a circuit breaker.
        """

        if not self.operational:
            self.tripped = False
            return

        self.tripped = bool(
            state
        )

    # -------------------------------------------------------------

    def trip(
        self,
    ) -> None:
        """
        Put the relay into the tripped state.

        Breaker operation belongs to ProtectionSystem /
        BreakerManager.
        """

        self.set_trip(
            True
        )

    # -------------------------------------------------------------

    def reset(
        self,
    ) -> None:
        """
        Reset relay operating state.

        Measurement channels are NOT reset here.

        Protection-plugin transient state must be reset by the
        protection subsystem/plugin.
        """

        self.picked_up = False
        self.tripped = False

    # -------------------------------------------------------------

    def clear_operating_state(
        self,
    ) -> None:
        """
        Clear relay pickup and trip states.
        """

        self.picked_up = False
        self.tripped = False

    # =============================================================
    # STATUS
    # =============================================================

    def status(self) -> dict[str, Any]:
        """
        Return structured relay status.

        Measurement values are intentionally not duplicated into
        the Relay status object.

        The ``inputs`` section reports channel identity and
        availability rather than copying measurement state.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "function_type": self.function_type,
            "plugin_id": self.plugin_id,
            "settings": dict(
                self.settings
            ),
            "inputs": {
                name: {
                    "channel_id": channel.id,
                    "available": True,
                }
                for name, channel
                in self._input_channels.items()
            },
            "in_service": self.in_service,
            "enabled": self.enabled,
            "blocked": self.blocked,
            "operational": self.operational,
            "picked_up": self.picked_up,
            "tripped": self.tripped,
        }

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return a compact engineering summary.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "function_type": self.function_type,
            "plugin_id": self.plugin_id,
            "input_count": len(
                self._input_channels
            ),
            "inputs": tuple(
                self._input_channels.keys()
            ),
            "in_service": self.in_service,
            "enabled": self.enabled,
            "blocked": self.blocked,
            "operational": self.operational,
            "picked_up": self.picked_up,
            "tripped": self.tripped,
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
            f"type={self.type}, "
            f"function={self.function_type}, "
            f"inputs={len(self._input_channels)}, "
            f"operational={self.operational}, "
            f"pickup={self.picked_up}, "
            f"trip={self.tripped}>"
        )


__all__ = [
    "Relay",
]
