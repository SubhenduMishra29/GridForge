"""
GridForge V2 Protection Function Base
=====================================

File
----
core/protection/relay_base.py

Purpose
-------
Defines the abstract execution contract for GridForge V2 protection
function implementations.

A RelayBase instance represents ONE executable protection function
hosted by an authoritative physical Relay.

Examples
--------
50      Instantaneous Overcurrent
51      Time Overcurrent
21      Distance
27      Undervoltage
32      Reverse Power
46      Negative Sequence
50BF    Breaker Failure
59      Overvoltage
81U     Underfrequency
87B     Bus Differential
87T     Transformer Differential

Architectural Position
----------------------

    Physical Relay
          |
          +---- ProtectionElement
                    |
                    v
                 RelayBase
                    |
          +---------+---------+
          |                   |
     RelayInput         ProtectionContext
          |                   |
          +---------+---------+
                    |
                    v
           ProtectionDecision
                    |
                    v
           ProtectionSystem
                    |
                    v
        Protection Output Layer
                    |
                    v
             BreakerManager

Architectural Rules
-------------------

RelayBase is NOT a second Relay model.

The authoritative physical Relay remains:

    core.model.relay.Relay

A physical Relay may host multiple independent protection
functions.

Each RelayBase-derived function:

    * owns function-specific configuration;
    * owns transient function runtime state;
    * references assigned RelayInput objects;
    * evaluates measurements and execution context;
    * produces a ProtectionDecision.

RelayBase does NOT:

    * own physical Relay identity/state;
    * own CT/PT/CVT equipment;
    * own MeasurementChannel state;
    * duplicate measurement values;
    * perform network calculations;
    * perform fault calculations;
    * operate breakers;
    * modify network topology;
    * execute protection schemes;
    * perform relay coordination;
    * contain GUI state;
    * perform persistence or file I/O.

Measurement Architecture
------------------------

    CT / PT / CVT
          |
          v
    MeasurementChannel
          |
          v
       RelayInput
          |
          v
       RelayBase
          |
          v
    ProtectionDecision

RelayBase references RelayInput objects but never owns the underlying
measurement infrastructure.

Execution Context
-----------------

ProtectionContext supplies evaluation-time information such as:

    time
    timestep
    event information
    supervision
    simulation/network references

ProtectionContext does not replace RelayInput.

Evaluation
----------

Every concrete protection function implements:

    evaluate(context) -> ProtectionDecision

The returned ProtectionDecision is the canonical result of one
protection-function evaluation.

RelayBase must never reduce the result to a boolean or directly
operate physical equipment.

Decision Contract
-----------------

The canonical decision implementation is:

    core.protection.decision.ProtectionDecision

There is intentionally no second decision implementation.

The removed legacy module:

    core.protection.protection_decision

must not be imported or referenced.

State Ownership
---------------

RelayBase owns only function-local configuration and transient
execution state.

The following remain authoritative elsewhere:

    Physical Relay
        -> core.model.relay.Relay

    MeasurementChannel
        -> core.measurement.measurement_channel.MeasurementChannel

    ProtectionDecision
        -> core.protection.decision.ProtectionDecision

    ProtectionElement lifecycle
        -> core.protection.protection_element.ProtectionElement

    Breaker operation
        -> core.model.breaker.Breaker
           through the protection/control boundary

Threading / Concurrency
-----------------------

RelayBase does not provide thread synchronization.

Its runtime state is intended to be accessed by the owning
simulation/protection execution context.

Concurrent evaluation of the same RelayBase instance is therefore
outside this class's contract.

Persistence
-----------

RelayBase contains no persistence or serialization logic.

The settings and runtime mappings exposed by this class are
configuration/runtime interfaces only.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from core.model.relay import Relay

    from .context import ProtectionContext
    from .decision import ProtectionDecision
    from .relay_input import RelayInput


class RelayBase(ABC):
    """
    Abstract base class for ONE executable protection-function
    instance.

    RelayBase represents protection-function execution.

    It does not represent physical relay equipment.

    One physical Relay may host multiple independent RelayBase
    instances through ProtectionElement objects.
    """

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def __init__(
        self,
        relay: Relay,
        *,
        element_id: str,
        function_code: str,
        function_name: str = "",
        relay_inputs: Mapping[str, RelayInput] | None = None,
        settings: Mapping[str, Any] | None = None,
        enabled: bool = True,
        blocked: bool = False,
    ) -> None:
        """
        Initialize one protection-function instance.

        Parameters
        ----------
        relay:
            Authoritative physical Relay hosting this function.

        element_id:
            Stable identity of this protection-function instance.

        function_code:
            Protection-function designation such as ``50``, ``51``,
            ``21``, ``87T`` or ``50BF``.

        function_name:
            Optional human-readable function name.

        relay_inputs:
            Mapping of function-local names to RelayInput objects.

        settings:
            Function-specific configuration.

        enabled:
            Whether this protection function is enabled.

        blocked:
            Static local blocking state.

        Notes
        -----
        The Relay object is referenced, not duplicated.

        RelayInput objects are referenced, not copied into another
        measurement model.
        """

        # --------------------------------------------------------------
        # Authoritative physical Relay
        # --------------------------------------------------------------

        if relay is None:
            raise ValueError(
                "RelayBase relay cannot be None."
            )

        relay_id = getattr(
            relay,
            "id",
            None,
        )

        if not isinstance(
            relay_id,
            str,
        ):
            raise TypeError(
                "RelayBase relay must expose a string 'id' attribute."
            )

        if not relay_id.strip():
            raise ValueError(
                "RelayBase relay id cannot be empty."
            )

        # --------------------------------------------------------------
        # Protection-function identity
        # --------------------------------------------------------------

        normalized_element_id = self._normalize_identifier(
            element_id,
            field="element_id",
        )

        normalized_function_code = self._normalize_identifier(
            function_code,
            field="function_code",
        ).upper()

        normalized_function_name = (
            self._normalize_optional_string(
                function_name,
                field="function_name",
            )
        )

        if not normalized_function_name:
            normalized_function_name = (
                normalized_function_code
            )

        # --------------------------------------------------------------
        # Boolean state
        # --------------------------------------------------------------

        self._validate_bool(
            enabled,
            field="enabled",
        )

        self._validate_bool(
            blocked,
            field="blocked",
        )

        # --------------------------------------------------------------
        # Relay inputs
        # --------------------------------------------------------------

        normalized_inputs = self._normalize_inputs(
            relay_inputs
        )

        # --------------------------------------------------------------
        # Function settings
        # --------------------------------------------------------------

        normalized_settings = self._normalize_settings(
            settings
        )

        # --------------------------------------------------------------
        # Authoritative references
        # --------------------------------------------------------------

        self._relay = relay

        # --------------------------------------------------------------
        # Stable function identity
        # --------------------------------------------------------------

        self._element_id = normalized_element_id
        self._function_code = normalized_function_code
        self._function_name = normalized_function_name

        # --------------------------------------------------------------
        # Local execution state
        # --------------------------------------------------------------

        self._enabled = enabled
        self._blocked = blocked

        # --------------------------------------------------------------
        # Function configuration
        # --------------------------------------------------------------

        self._settings = normalized_settings

        # --------------------------------------------------------------
        # Measurement bindings
        # --------------------------------------------------------------

        self._relay_inputs = normalized_inputs

        # --------------------------------------------------------------
        # Transient execution state
        # --------------------------------------------------------------

        self._runtime: dict[str, Any] = {}

    # ==================================================================
    # VALIDATION HELPERS
    # ==================================================================

    @staticmethod
    def _normalize_identifier(
        value: str,
        *,
        field: str,
    ) -> str:
        """
        Validate and normalize a required string identifier.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"RelayBase {field} must be a string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"RelayBase {field} cannot be empty."
            )

        return normalized

    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_optional_string(
        value: str,
        *,
        field: str,
    ) -> str:
        """
        Validate and normalize an optional string field.

        Empty strings are accepted and normalized to ``""``.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"RelayBase {field} must be a string."
            )

        return value.strip()

    # ------------------------------------------------------------------

    @staticmethod
    def _validate_bool(
        value: bool,
        *,
        field: str,
    ) -> None:
        """
        Validate a strict boolean value.

        ``bool`` is intentionally validated explicitly because Python
        treats integers as a subclass of ``int`` and permissive coercion
        would hide configuration errors.
        """

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"RelayBase {field} must be a boolean."
            )

    # ------------------------------------------------------------------

    @classmethod
    def _normalize_inputs(
        cls,
        relay_inputs: Mapping[str, RelayInput] | None,
    ) -> dict[str, RelayInput]:
        """
        Validate and normalize RelayInput bindings.
        """

        if relay_inputs is None:
            return {}

        if not isinstance(
            relay_inputs,
            Mapping,
        ):
            raise TypeError(
                "RelayBase relay_inputs must be a mapping."
            )

        # Local import intentionally avoids a module-level cycle.
        from .relay_input import RelayInput

        normalized: dict[str, RelayInput] = {}

        for name, relay_input in relay_inputs.items():

            normalized_name = cls._normalize_identifier(
                name,
                field="relay-input name",
            )

            if not isinstance(
                relay_input,
                RelayInput,
            ):
                raise TypeError(
                    f"RelayBase input '{normalized_name}' "
                    "must be a RelayInput."
                )

            if normalized_name in normalized:
                raise ValueError(
                    f"Duplicate normalized RelayBase input name "
                    f"'{normalized_name}'."
                )

            normalized[
                normalized_name
            ] = relay_input

        return normalized

    # ------------------------------------------------------------------

    @classmethod
    def _normalize_settings(
        cls,
        settings: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Validate and normalize function-specific settings.
        """

        if settings is None:
            return {}

        if not isinstance(
            settings,
            Mapping,
        ):
            raise TypeError(
                "RelayBase settings must be a mapping."
            )

        normalized: dict[str, Any] = {}

        for name, value in settings.items():

            normalized_name = cls._normalize_identifier(
                name,
                field="setting name",
            )

            if normalized_name in normalized:
                raise ValueError(
                    f"Duplicate normalized RelayBase setting "
                    f"name '{normalized_name}'."
                )

            normalized[
                normalized_name
            ] = value

        return normalized

    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_runtime_name(
        name: str,
    ) -> str:
        """
        Validate and normalize a runtime-state key.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Runtime-state name must be a string."
            )

        normalized = name.strip()

        if not normalized:
            raise ValueError(
                "Runtime-state name cannot be empty."
            )

        return normalized

    # ==================================================================
    # AUTHORITATIVE RELAY
    # ==================================================================

    @property
    def relay(self) -> Relay:
        """
        Return the authoritative physical Relay reference.

        The reference is intentionally read-only through this API.
        """

        return self._relay

    # ------------------------------------------------------------------

    @property
    def relay_id(self) -> str:
        """
        Return the identity of the authoritative physical Relay.
        """

        return self._relay.id

    # ==================================================================
    # IDENTITY
    # ==================================================================

    @property
    def id(self) -> str:
        """
        Return the stable protection-function instance identity.

        This is the ProtectionElement/function identity.

        It is not the physical Relay identity.
        """

        return self._element_id

    # ------------------------------------------------------------------

    @property
    def element_id(self) -> str:
        """
        Return the stable protection-function instance identity.
        """

        return self._element_id

    # ------------------------------------------------------------------

    @property
    def function_code(self) -> str:
        """
        Return the canonical protection-function designation.
        """

        return self._function_code

    # ------------------------------------------------------------------

    @property
    def code(self) -> str:
        """
        Return the canonical protection-function designation.

        Alias for ``function_code``.
        """

        return self._function_code

    # ------------------------------------------------------------------

    @property
    def function_name(self) -> str:
        """
        Return the human-readable protection-function name.
        """

        return self._function_name

    # ==================================================================
    # ENABLE / BLOCK STATE
    # ==================================================================

    @property
    def enabled(self) -> bool:
        """
        Return whether this protection function is enabled.
        """

        return self._enabled

    @enabled.setter
    def enabled(
        self,
        value: bool,
    ) -> None:
        """
        Set the local enabled state.
        """

        self._validate_bool(
            value,
            field="enabled",
        )

        self._enabled = value

    # ------------------------------------------------------------------

    @property
    def blocked(self) -> bool:
        """
        Return the static local blocking state.
        """

        return self._blocked

    @blocked.setter
    def blocked(
        self,
        value: bool,
    ) -> None:
        """
        Set the static local blocking state.
        """

        self._validate_bool(
            value,
            field="blocked",
        )

        self._blocked = value

    # ==================================================================
    # CONFIGURATION
    # ==================================================================

    @property
    def settings(
        self,
    ) -> Mapping[str, Any]:
        """
        Return read-only access to function-specific settings.

        Settings belong to this protection-function instance.

        They must not duplicate authoritative physical Relay
        configuration or measurement configuration.
        """

        return MappingProxyType(
            self._settings
        )

    # ------------------------------------------------------------------

    def get_setting(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return one function-specific setting.
        """

        normalized_name = self._normalize_identifier(
            name,
            field="setting name",
        )

        return self._settings.get(
            normalized_name,
            default,
        )

    # ==================================================================
    # EXECUTION ELIGIBILITY
    # ==================================================================

    @property
    def operational(self) -> bool:
        """
        Return whether this protection function is locally eligible
        for evaluation.

        Local eligibility consists of:

            physical Relay operational
            AND
            function enabled
            AND
            function not statically blocked

        Dynamic supervision, interlocking, permissive logic,
        scheme-level blocking and other dynamic inhibition belong to
        ProtectionContext or the protection-system/scheme layer.

        If the authoritative Relay does not expose ``operational``,
        the Relay is treated as operational by compatibility fallback.
        """

        relay_operational = bool(
            getattr(
                self._relay,
                "operational",
                True,
            )
        )

        return (
            relay_operational
            and self._enabled
            and not self._blocked
        )

    # ------------------------------------------------------------------

    @property
    def active(self) -> bool:
        """
        Semantic alias for ``operational``.
        """

        return self.operational

    # ==================================================================
    # INPUTS
    # ==================================================================

    @property
    def inputs(
        self,
    ) -> Mapping[str, RelayInput]:
        """
        Return read-only access to assigned RelayInput objects.

        RelayBase does not own these objects.
        """

        return MappingProxyType(
            self._relay_inputs
        )

    # ------------------------------------------------------------------

    def has_input(
        self,
        name: str,
    ) -> bool:
        """
        Return True when the specified input is assigned.
        """

        normalized_name = self._normalize_identifier(
            name,
            field="protection input name",
        )

        return normalized_name in self._relay_inputs

    # ------------------------------------------------------------------

    def get_input(
        self,
        name: str,
    ) -> RelayInput:
        """
        Return an assigned RelayInput.

        Raises
        ------
        KeyError
            If the requested input is not assigned.
        """

        normalized_name = self._normalize_identifier(
            name,
            field="protection input name",
        )

        try:
            return self._relay_inputs[
                normalized_name
            ]

        except KeyError as exc:

            raise KeyError(
                f"Protection element '{self._element_id}' "
                f"({self._function_code}) on relay "
                f"'{self.relay_id}' requires input "
                f"'{normalized_name}'."
            ) from exc

    # ------------------------------------------------------------------

    def require_inputs(
        self,
        *names: str,
    ) -> None:
        """
        Validate that all specified inputs are assigned.

        Concrete protection functions should call this before
        evaluating their required measurement set.
        """

        missing: list[str] = set()
        normalized_names: set[str] = set()

        for name in names:

            normalized_name = self._normalize_identifier(
                name,
                field="protection input name",
            )

            if normalized_name in normalized_names:
                continue

            normalized_names.add(
                normalized_name
            )

            if normalized_name not in self._relay_inputs:
                missing.append(
                    normalized_name
                )

        if missing:
            raise ValueError(
                f"Protection element '{self._element_id}' "
                f"({self._function_code}) on relay "
                f"'{self.relay_id}' is missing required "
                f"inputs: {missing}."
            )

    # ==================================================================
    # RUNTIME STATE
    # ==================================================================

    def runtime_get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return transient protection-function runtime state.
        """

        normalized_name = self._normalize_runtime_name(
            name
        )

        return self._runtime.get(
            normalized_name,
            default,
        )

    # ------------------------------------------------------------------

    def runtime_set(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Set transient protection-function runtime state.
        """

        normalized_name = self._normalize_runtime_name(
            name
        )

        self._runtime[
            normalized_name
        ] = value

    # ------------------------------------------------------------------

    def runtime_has(
        self,
        name: str,
    ) -> bool:
        """
        Return True when a runtime-state entry exists.
        """

        normalized_name = self._normalize_runtime_name(
            name
        )

        return normalized_name in self._runtime

    # ------------------------------------------------------------------

    def runtime_remove(
        self,
        name: str,
    ) -> Any:
        """
        Remove and return one transient runtime-state entry.

        Raises
        ------
        KeyError
            If the runtime-state entry does not exist.
        """

        normalized_name = self._normalize_runtime_name(
            name
        )

        try:
            return self._runtime.pop(
                normalized_name
            )

        except KeyError as exc:

            raise KeyError(
                f"Runtime-state entry not found: "
                f"{normalized_name}"
            ) from exc

    # ------------------------------------------------------------------

    @property
    def runtime(
        self,
    ) -> Mapping[str, Any]:
        """
        Return read-only access to transient runtime state.

        Intended primarily for diagnostics and testing.

        Runtime values themselves are not deep-copied.
        """

        return MappingProxyType(
            self._runtime
        )

    # ==================================================================
    # DECISION CONSTRUCTION
    # ==================================================================

    def make_decision(
        self,
        *,
        pickup: bool = False,
        operate: bool = False,
        trip_request: bool = False,
        blocked: bool = False,
        valid: bool = True,
        operating_time: float | None = None,
        timestamp: float | None = None,
        reason: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> ProtectionDecision:
        """
        Construct a ProtectionDecision for this function.

        The authoritative identity is automatically supplied:

            relay_id
            element_id
            function_code

        Concrete protection functions should normally use this helper
        rather than constructing ProtectionDecision directly.

        Decision-state validation remains the responsibility of
        ProtectionDecision.
        """

        from .decision import ProtectionDecision

        return ProtectionDecision(
            relay_id=self.relay_id,
            element_id=self._element_id,
            function_code=self._function_code,
            pickup=pickup,
            operate=operate,
            trip_request=trip_request,
            blocked=blocked,
            valid=valid,
            operating_time=operating_time,
            timestamp=timestamp,
            reason=reason,
            metadata={} if metadata is None else metadata,
        )

    # ------------------------------------------------------------------

    def no_operation(
        self,
        *,
        reason: str = "",
        timestamp: float | None = None,
        operating_time: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ProtectionDecision:
        """
        Construct a valid non-operating decision.
        """

        from .decision import ProtectionDecision

        return ProtectionDecision.no_operation(
            relay_id=self.relay_id,
            element_id=self._element_id,
            function_code=self._function_code,
            reason=reason,
            timestamp=timestamp,
            operating_time=operating_time,
            metadata=metadata,
        )

    # ------------------------------------------------------------------

    def pickup_decision(
        self,
        *,
        reason: str = "",
        timestamp: float | None = None,
        operating_time: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ProtectionDecision:
        """
        Construct a valid pickup-only decision.
        """

        from .decision import ProtectionDecision

        return ProtectionDecision.pickup_decision(
            relay_id=self.relay_id,
            element_id=self._element_id,
            function_code=self._function_code,
            reason=reason,
            timestamp=timestamp,
            operating_time=operating_time,
            metadata=metadata,
        )

    # ------------------------------------------------------------------

    def trip_decision(
        self,
        *,
        reason: str = "",
        timestamp: float | None = None,
        operating_time: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ProtectionDecision:
        """
        Construct a valid actionable trip-request decision.

        This creates a decision only.

        It does NOT:

            * operate a breaker;
            * call BreakerManager;
            * modify Relay state;
            * modify network topology.
        """

        from .decision import ProtectionDecision

        return ProtectionDecision.trip(
            relay_id=self.relay_id,
            element_id=self._element_id,
            function_code=self._function_code,
            reason=reason,
            timestamp=timestamp,
            operating_time=operating_time,
            metadata=metadata,
        )

    # ------------------------------------------------------------------

    def blocked_decision(
        self,
        *,
        reason: str = "Protection element blocked.",
        timestamp: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ProtectionDecision:
        """
        Construct a valid blocked decision.
        """

        from .decision import ProtectionDecision

        return ProtectionDecision.blocked_decision(
            relay_id=self.relay_id,
            element_id=self._element_id,
            function_code=self._function_code,
            reason=reason,
            timestamp=timestamp,
            metadata=metadata,
        )

    # ------------------------------------------------------------------

    def invalid_decision(
        self,
        *,
        reason: str,
        timestamp: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ProtectionDecision:
        """
        Construct an invalid decision.

        Invalid decisions cannot request a trip.
        """

        if not isinstance(
            reason,
            str,
        ):
            raise TypeError(
                "Invalid protection decision reason "
                "must be a string."
            )

        if not reason.strip():
            raise ValueError(
                "Invalid protection decisions require a reason."
            )

        from .decision import ProtectionDecision

        return ProtectionDecision.invalid(
            relay_id=self.relay_id,
            element_id=self._element_id,
            function_code=self._function_code,
            reason=reason,
            timestamp=timestamp,
            metadata=metadata,
        )

    # ==================================================================
    # EVALUATION
    # ==================================================================

    @abstractmethod
    def evaluate(
        self,
        context: ProtectionContext,
    ) -> ProtectionDecision:
        """
        Evaluate this protection function.

        Parameters
        ----------
        context:
            ProtectionContext containing evaluation-time information.

        Returns
        -------
        ProtectionDecision
            Canonical structured result of the protection-function
            evaluation.

        Architectural Rule
        ------------------
        Concrete implementations MUST return ProtectionDecision.

        They MUST NOT:

            * return a bare boolean;
            * call Relay.set_trip();
            * operate breakers;
            * invoke BreakerManager;
            * modify network topology;
            * schedule physical equipment actions;
            * execute protection schemes;
            * coordinate other protection functions.

        The resulting decision is interpreted by the surrounding
        ProtectionElement / ProtectionSystem / protection-output layer.
        """

        raise NotImplementedError

    # ==================================================================
    # RESET
    # ==================================================================

    def reset(self) -> None:
        """
        Reset transient protection-function runtime state.

        This does not reset:

            * physical Relay state;
            * RelayInput objects;
            * MeasurementChannels;
            * CT/PT/CVT state;
            * protection schemes;
            * breaker state;
            * network topology.
        """

        self._runtime.clear()

    # ==================================================================
    # DIAGNOSTICS
    # ==================================================================

    def status(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic information for this protection function.

        This is not the authoritative persistence representation.
        """

        return {
            "element_id": self._element_id,
            "relay_id": self.relay_id,
            "function_code": self._function_code,
            "function_name": self._function_name,
            "enabled": self._enabled,
            "blocked": self._blocked,
            "operational": self.operational,
            "inputs": tuple(
                self._relay_inputs.keys()
            ),
            "runtime": dict(
                self._runtime
            ),
        }

    # ==================================================================
    # REPRESENTATION
    # ==================================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<{self.__class__.__name__} "
            f"id={self._element_id!r}, "
            f"relay_id={self.relay_id!r}, "
            f"code={self._function_code!r}, "
            f"enabled={self._enabled}, "
            f"blocked={self._blocked}>"
        )


# ======================================================================
# PUBLIC API
# ======================================================================

__all__ = [
    "RelayBase",
]
