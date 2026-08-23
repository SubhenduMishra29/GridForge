# core/model/relay.py
"""
GridForge V2 Relay Model
========================

Author:
    Subhendu Mishra

File:
    core/model/relay.py

Purpose
-------
Defines the canonical GridForge protection Relay device model.

Architectural role
------------------
The Relay is a physical protection device in the GridForge model
layer. It represents:

    - relay identity
    - relay type/function identity
    - measurement-channel bindings
    - configuration/settings
    - device operating state
    - pickup/trip state

The Relay does NOT implement protection algorithms.

Protection algorithms belong to:

    core/protection/

The Relay does not own measured electrical quantities. Measurement
channels remain authoritative for their signals.

Signal architecture:

    Electrical Equipment
            |
        CT / PT / CVT
            |
            v
    MeasurementChannel
            |
            v
          Relay
            |
            v
    Protection Function / Plugin
            |
            v
    Protection System
            |
            v
    Breaker / Switching Control

The Relay does NOT:

    - calculate CT transformation
    - calculate PT/CVT transformation
    - calculate fault current
    - build Y-bus
    - perform load flow
    - perform short circuit
    - calculate TCC curves
    - implement directional logic
    - implement distance zones
    - perform relay coordination
    - operate breakers directly
    - own topology
    - own GUI state

Protection settings are stored but not interpreted by the Relay.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


class Relay:
    """
    Canonical GridForge V2 protection relay model.

    The Relay is intentionally independent of executable protection
    algorithms.

    Parameters
    ----------
    id:
        Stable GridForge relay identifier.

    relay_type:
        Stable relay/function category.

    name:
        Human-readable relay name.

    function_type:
        Protection-function identifier. Defaults to relay_type.

    plugin_id:
        Optional stable protection-plugin identifier.

    settings:
        Protection configuration dictionary.

    in_service:
        Physical relay service state.

    enabled:
        Whether the relay is enabled.

    blocked:
        Whether relay operation is blocked.
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

        self._validate_id(id)

        self.id = id
        self.name = str(name)

        # ---------------------------------------------------------
        # Relay type
        # ---------------------------------------------------------

        self.type = self._validate_identifier(
            relay_type,
            "relay_type",
        ).upper()

        if self.type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid relay type '{self.type}'. "
                f"Supported types: "
                f"{sorted(self.VALID_TYPES)}"
            )

        # ---------------------------------------------------------
        # Protection function
        # ---------------------------------------------------------

        if function_type is None:
            function_type = self.type

        self.function_type = self._validate_identifier(
            function_type,
            "function_type",
        ).upper()

        # ---------------------------------------------------------
        # Protection plugin identity
        # ---------------------------------------------------------

        if plugin_id is None:
            self.plugin_id = None
        else:
            self.plugin_id = self._validate_identifier(
                plugin_id,
                "plugin_id",
            )

        # ---------------------------------------------------------
        # Protection settings
        # ---------------------------------------------------------

        self.settings = self._copy_settings(
            settings
        )

        # ---------------------------------------------------------
        # Service / operating state
        # ---------------------------------------------------------

        self._validate_bool(
            in_service,
            "in_service",
        )

        self._validate_bool(
            enabled,
            "enabled",
        )

        self._validate_bool(
            blocked,
            "blocked",
        )

        self.in_service = in_service
        self.enabled = enabled
        self.blocked = blocked

        # ---------------------------------------------------------
        # Protection operating state
        #
        # These are state results maintained by the protection
        # subsystem through the Relay API.
        # ---------------------------------------------------------

        self.picked_up = False
        self.tripped = False

        # ---------------------------------------------------------
        # Measurement-channel bindings
        #
        # MeasurementChannel objects remain authoritative for
        # measured values.
        # ---------------------------------------------------------

        self._input_channels: dict[str, Any] = {}

        # ---------------------------------------------------------
        # Final local validation
        # ---------------------------------------------------------

        self.validate()

    # =============================================================
    # IDENTITY
    # =============================================================

    @property
    def relay_type(self) -> str:
        """
        Return the canonical relay type.

        ``type`` is retained as the underlying compatibility
        attribute.
        """

        return self.type

    @property
    def protection_function(self) -> str:
        """Return the protection function identifier."""

        return self.function_type

    # =============================================================
    # VALIDATION
    # =============================================================

    def validate(self) -> bool:
        """
        Validate the complete Relay model.

        The Relay validates only model-local invariants.

        It does not validate protection algorithms or topology.
        """

        self._validate_id(
            self.id
        )

        if not isinstance(
            self.name,
            str,
        ):
            raise TypeError(
                "Relay name must be a string."
            )

        if self.type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid relay type '{self.type}'."
            )

        self.function_type = self._validate_identifier(
            self.function_type,
            "function_type",
        ).upper()

        if self.plugin_id is not None:
            self.plugin_id = self._validate_identifier(
                self.plugin_id,
                "plugin_id",
            )

        self.settings = self._copy_settings(
            self.settings
        )

        self._validate_bool(
            self.in_service,
            "in_service",
        )

        self._validate_bool(
            self.enabled,
            "enabled",
        )

        self._validate_bool(
            self.blocked,
            "blocked",
        )

        self._validate_bool(
            self.picked_up,
            "picked_up",
        )

        self._validate_bool(
            self.tripped,
            "tripped",
        )

        for name, channel in self._input_channels.items():
            self._validate_input_name(name)
            self._validate_channel(channel)

        return True

    # =============================================================
    # SERVICE STATE
    # =============================================================

    @property
    def is_in_service(self) -> bool:
        """Return whether the relay is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the relay is out of service."""

        return not self.in_service

    @property
    def is_operational(self) -> bool:
        """
        Return whether the relay is available for protection
        operation.

        A relay is operational only when:

            in_service
            AND enabled
            AND not blocked
        """

        return (
            self.in_service
            and self.enabled
            and not self.blocked
        )

    def put_in_service(self) -> None:
        """Place the relay in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take the relay out of service."""

        self.in_service = False

        # Removing the relay from service also clears active
        # operating state.
        self.clear_operating_state()

    # Compatibility aliases.

    def connect(self) -> None:
        """
        Compatibility alias for put_in_service().

        This does not mean terminal/network connectivity.
        """

        self.put_in_service()

    def disconnect(self) -> None:
        """
        Compatibility alias for take_out_of_service().

        This does not modify network topology.
        """

        self.take_out_of_service()

    # =============================================================
    # ENABLE / BLOCK STATE
    # =============================================================

    def enable(self) -> None:
        """Enable relay operation."""

        self.enabled = True

    def disable(self) -> None:
        """
        Disable relay operation and clear active protection state.
        """

        self.enabled = False
        self.clear_operating_state()

    def block(self) -> None:
        """
        Block relay operation and clear active protection state.
        """

        self.blocked = True
        self.clear_operating_state()

    def unblock(self) -> None:
        """Remove relay blocking."""

        self.blocked = False

    # =============================================================
    # PICKUP / TRIP STATE
    # =============================================================

    @property
    def is_picked_up(self) -> bool:
        """Return whether the relay is picked up."""

        return self.picked_up

    @property
    def is_tripped(self) -> bool:
        """Return whether the relay is tripped."""

        return self.tripped

    def set_pickup(
        self,
        value: bool,
    ) -> None:
        """
        Set pickup state.

        Protection logic decides whether pickup should occur;
        the Relay only stores the resulting device state.
        """

        self._validate_bool(
            value,
            "picked_up",
        )

        if value and not self.is_operational:
            raise RuntimeError(
                f"Relay '{self.id}' cannot pick up while "
                "out of service, disabled, or blocked."
            )

        self.picked_up = value

    def pickup(self) -> None:
        """Set the relay to pickup state."""

        self.set_pickup(True)

    def clear_pickup(self) -> None:
        """Clear pickup state."""

        self.picked_up = False

    def set_trip(
        self,
        value: bool,
    ) -> None:
        """
        Set trip state.

        The Relay records the protection result but does not
        operate a breaker itself.
        """

        self._validate_bool(
            value,
            "tripped",
        )

        if value and not self.is_operational:
            raise RuntimeError(
                f"Relay '{self.id}' cannot trip while "
                "out of service, disabled, or blocked."
            )

        self.tripped = value

    def trip(self) -> None:
        """Set the relay to tripped state."""

        self.set_trip(True)

    def clear_trip(self) -> None:
        """Clear trip state."""

        self.tripped = False

    def reset(self) -> None:
        """
        Reset pickup and trip states.

        Resetting the relay does not alter configuration or
        measurement-channel bindings.
        """

        self.picked_up = False
        self.tripped = False

    def clear_operating_state(self) -> None:
        """
        Clear protection operating state.

        Used when the relay becomes unavailable for operation.
        """

        self.picked_up = False
        self.tripped = False

    # =============================================================
    # SETTINGS
    # =============================================================

    def set_setting(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Set one protection setting.

        The value is stored without interpretation.
        """

        name = self._validate_identifier(
            name,
            "setting name",
        )

        self.settings[name] = value

    def get_setting(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """Return a protection setting."""

        name = self._validate_identifier(
            name,
            "setting name",
        )

        return self.settings.get(
            name,
            default,
        )

    def remove_setting(
        self,
        name: str,
    ) -> Any | None:
        """Remove and return one protection setting."""

        name = self._validate_identifier(
            name,
            "setting name",
        )

        return self.settings.pop(
            name,
            None,
        )

    def set_settings(
        self,
        settings: Mapping[str, Any],
    ) -> None:
        """
        Replace the complete protection settings dictionary.
        """

        self.settings = self._copy_settings(
            settings
        )

    def clear_settings(self) -> None:
        """Remove all protection settings."""

        self.settings.clear()

    # =============================================================
    # MEASUREMENT CHANNELS
    # =============================================================

    @property
    def input_channels(self) -> dict[str, Any]:
        """
        Return a shallow copy of relay input bindings.

        The Relay retains ownership of the binding map.
        """

        return dict(
            self._input_channels
        )

    def bind_input(
        self,
        name: str,
        channel: Any,
    ) -> None:
        """
        Bind a MeasurementChannel to a relay input.

        The channel object itself remains authoritative for the
        measured signal.
        """

        name = self._validate_input_name(
            name
        )

        self._validate_channel(
            channel
        )

        self._input_channels[name] = channel

    def unbind_input(
        self,
        name: str,
    ) -> Any | None:
        """
        Remove and return a measurement-channel binding.
        """

        name = self._validate_input_name(
            name
        )

        return self._input_channels.pop(
            name,
            None,
        )

    def clear_inputs(self) -> None:
        """Remove all measurement-channel bindings."""

        self._input_channels.clear()

    def has_input(
        self,
        name: str,
    ) -> bool:
        """Return whether a relay input is bound."""

        name = self._validate_input_name(
            name
        )

        return name in self._input_channels

    def get_input(
        self,
        name: str,
    ) -> Any:
        """
        Return the MeasurementChannel bound to a relay input.

        The channel itself, not a copied measurement value, is
        returned.
        """

        name = self._validate_input_name(
            name
        )

        try:
            return self._input_channels[name]

        except KeyError as exc:
            raise KeyError(
                f"Relay '{self.id}' has no input channel "
                f"bound to '{name}'."
            ) from exc

    def get_input_value(
        self,
        name: str,
    ) -> Any:
        """
        Obtain the current measurement value from the bound channel.

        The Relay does not cache or own the measured value.

        Supported channel interfaces:

            channel.value
            channel.get_value()
        """

        channel = self.get_input(
            name
        )

        if hasattr(
            channel,
            "value",
        ):
            value = channel.value

            if callable(value):
                return value()

            return value

        if hasattr(
            channel,
            "get_value",
        ):
            return channel.get_value()

        raise TypeError(
            f"Measurement channel bound to relay input "
            f"'{name}' does not expose a supported value interface."
        )

    def input_values(self) -> dict[str, Any]:
        """
        Return current values for all bound relay inputs.

        Values are read directly from MeasurementChannel objects.
        """

        return {
            name: self.get_input_value(name)
            for name in self._input_channels
        }

    # =============================================================
    # REQUIRED INPUTS
    # =============================================================

    def missing_inputs(
        self,
        required_inputs: set[str] | tuple[str, ...] | list[str],
    ) -> tuple[str, ...]:
        """
        Return required relay inputs that are not currently bound.
        """

        if required_inputs is None:
            raise TypeError(
                "required_inputs cannot be None."
            )

        missing = []

        for name in required_inputs:
            name = self._validate_input_name(
                name
            )

            if name not in self._input_channels:
                missing.append(name)

        return tuple(
            sorted(
                set(missing)
            )
        )

    def has_required_inputs(
        self,
        required_inputs: set[str] | tuple[str, ...] | list[str],
    ) -> bool:
        """
        Return True when all required inputs are bound.
        """

        return not self.missing_inputs(
            required_inputs
        )

    # =============================================================
    # PLUGIN IDENTITY
    # =============================================================

    def set_plugin_id(
        self,
        plugin_id: str | None,
    ) -> None:
        """
        Set the protection-plugin identifier.

        This stores metadata only; no plugin is imported or created.
        """

        if plugin_id is None:
            self.plugin_id = None
            return

        self.plugin_id = self._validate_identifier(
            plugin_id,
            "plugin_id",
        )

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def status(self) -> dict[str, Any]:
        """
        Return device-level protection status.

        No calculated electrical quantities are included.
        """

        return {
            "id": self.id,
            "name": self.name,
            "relay_type": self.type,
            "function_type": self.function_type,
            "plugin_id": self.plugin_id,

            "in_service": self.in_service,
            "enabled": self.enabled,
            "blocked": self.blocked,
            "operational": self.is_operational,

            "picked_up": self.picked_up,
            "tripped": self.tripped,

            "input_count": len(
                self._input_channels
            ),
            "inputs": tuple(
                sorted(
                    self._input_channels
                )
            ),

            "setting_count": len(
                self.settings
            ),
        }

    def summary(self) -> dict[str, Any]:
        """
        Return a structured Relay summary.

        Settings are copied so callers cannot mutate the Relay
        configuration through the returned dictionary.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "relay_type": self.type,
            "function_type": self.function_type,
            "plugin_id": self.plugin_id,

            "in_service": self.in_service,
            "enabled": self.enabled,
            "blocked": self.blocked,
            "operational": self.is_operational,

            "picked_up": self.picked_up,
            "tripped": self.tripped,

            "settings": deepcopy(
                self.settings
            ),

            "inputs": tuple(
                sorted(
                    self._input_channels
                )
            ),
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        return (
            f"<Relay "
            f"id={self.id}, "
            f"type={self.type}, "
            f"function={self.function_type}, "
            f"operational={self.is_operational}, "
            f"picked_up={self.picked_up}, "
            f"tripped={self.tripped}>"
        )

    # =============================================================
    # VALIDATION HELPERS
    # =============================================================

    @staticmethod
    def _validate_id(
        value: str,
    ) -> None:
        """Validate a stable GridForge identifier."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "Relay id must be a string."
            )

        if not value.strip():
            raise ValueError(
                "Relay id cannot be empty."
            )

    @staticmethod
    def _validate_identifier(
        value: str,
        name: str,
    ) -> str:
        """
        Validate and normalize a string identifier.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{name} must be a string."
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{name} cannot be empty."
            )

        return value

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> None:
        """
        Require an actual boolean.

        Values such as 0, 1, \"true\", and \"false\" are deliberately
        rejected instead of silently coerced.
        """

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be boolean."
            )

    @classmethod
    def _copy_settings(
        cls,
        settings: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Validate and copy protection settings.
        """

        if settings is None:
            return {}

        if not isinstance(
            settings,
            Mapping,
        ):
            raise TypeError(
                "settings must be a mapping or None."
            )

        result: dict[str, Any] = {}

        for name, value in settings.items():

            name = cls._validate_identifier(
                name,
                "setting name",
            )

            result[name] = value

        return result

    @staticmethod
    def _validate_input_name(
        name: str,
    ) -> str:
        """
        Validate and normalize a protection input name.
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

        return name

    @staticmethod
    def _validate_channel(
        channel: Any,
    ) -> None:
        """
        Validate the minimum MeasurementChannel binding contract.

        The Relay intentionally does not require a concrete
        MeasurementChannel class import. This keeps the model
        independent of a specific measurement implementation.
        """

        if channel is None:
            raise ValueError(
                "MeasurementChannel cannot be None."
            )

        if not hasattr(
            channel,
            "id",
        ):
            raise TypeError(
                "MeasurementChannel must expose an 'id' attribute."
            )


__all__ = [
    "Relay",
]
