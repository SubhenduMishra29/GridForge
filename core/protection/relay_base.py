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
functions:

    Relay R1
        |
        +-- 50
        +-- 51
        +-- 46
        +-- 50BF

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
        # Physical Relay
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

        if relay_id is None:
            raise TypeError(
                "RelayBase relay must expose an 'id' attribute."
            )

        # --------------------------------------------------------------
        # Element identity
        # --------------------------------------------------------------

        if not isinstance(
            element_id,
            str,
        ):
            raise TypeError(
                "RelayBase element_id must be a string."
            )

        normalized_element_id = element_id.strip()

        if not normalized_element_id:
            raise ValueError(
                "RelayBase element_id cannot be empty."
            )

        # --------------------------------------------------------------
        # Function code
        # --------------------------------------------------------------

        if not isinstance(
            function_code,
            str,
        ):
            raise TypeError(
                "RelayBase function_code must be a string."
            )

        normalized_function_code = (
            function_code.strip().upper()
        )

        if not normalized_function_code:
            raise ValueError(
                "RelayBase function_code cannot be empty."
            )

        # --------------------------------------------------------------
        # Function name
        # --------------------------------------------------------------

        if not isinstance(
            function_name,
            str,
        ):
            raise TypeError(
                "RelayBase function_name must be a string."
            )

        normalized_function_name = (
            function_name.strip()
        )

        if not normalized_function_name:
            normalized_function_name = (
                normalized_function_code
            )

        # --------------------------------------------------------------
        # Enabled / blocked state
        # --------------------------------------------------------------

        if not isinstance(
            enabled,
            bool,
        ):
            raise TypeError(
                "RelayBase enabled must be a boolean."
            )

        if not isinstance(
            blocked,
            bool,
        ):
            raise TypeError(
                "RelayBase blocked must be a boolean."
            )

        # --------------------------------------------------------------
        # Relay-input validation
        # --------------------------------------------------------------

        normalized_inputs: dict[
            str,
            RelayInput,
        ] = {}

        if relay_inputs is not None and not isinstance(
            relay_inputs,
            Mapping,
        ):
            raise TypeError(
                "RelayBase relay_inputs must be a mapping."
            )

        for name, relay_input in (
            dict(relay_inputs or {})
        ).items():

            if not isinstance(
                name,
                str,
            ):
                raise TypeError(
                    "RelayBase relay-input names must be strings."
                )

            normalized_name = name.strip()

            if not normalized_name:
                raise ValueError(
                    "RelayBase relay-input names cannot be empty."
                )

            if relay_input is None:
                raise ValueError(
                    f"RelayBase input '{normalized_name}' "
                    "cannot be None."
                )

            # Runtime import is deliberately local. This avoids a
            # module-level dependency cycle while still validating the
            # authoritative RelayInput contract.
            from .relay_input import RelayInput

            if not isinstance(
                relay_input,
                RelayInput,
            ):
                raise TypeError(
                    f"RelayBase input '{normalized_name}' "
                    "must be a RelayInput."
                )

            if normalized_name in normalized_inputs:
                raise ValueError(
                    f"Duplicate normalized RelayBase input name "
                    f"'{normalized_name}'."
                )

            normalized_inputs[
                normalized_name
            ] = relay_input

        # --------------------------------------------------------------
        # Function configuration validation
        # --------------------------------------------------------------

        if settings is not None and not isinstance(
            settings,
            Mapping,
        ):
            raise TypeError(
                "RelayBase settings must be a mapping."
            )

        normalized_settings: dict[
            str,
            Any,
        ] = {}

        for name, value in dict(
            settings or {}
        ).items():

            if not isinstance(
                name,
                str,
            ):
                raise TypeError(
                    "RelayBase setting names must be strings."
                )

            normalized_name = name.strip()

            if not normalized_name:
                raise ValueError(
                    "RelayBase setting names cannot be empty."
                )

            if normalized_name in normalized_settings:
                raise ValueError(
                    f"Duplicate normalized RelayBase setting "
                    f"name '{normalized_name}'."
                )

            normalized_settings[
                normalized_name
            ] = value

        # --------------------------------------------------------------
        # Authoritative physical Relay reference
        # --------------------------------------------------------------

        self.relay = relay

        # --------------------------------------------------------------
        # Protection-function identity
        # --------------------------------------------------------------

        self.element_id = normalized_element_id

        self.function_code = (
            normalized_function_code
        )

        self.function_name = (
            normalized_function_name
        )

        # --------------------------------------------------------------
        # Local execution state
        # --------------------------------------------------------------

        self.enabled = enabled
        self.blocked = blocked

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

        self._runtime: dict[
            str,
            Any,
        ] = {}

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

        return self.element_id

    # ------------------------------------------------------------------

    @property
    def relay_id(self) -> Any:
        """
        Return the identity of the authoritative physical Relay.
        """

        return self.relay.id

    # ------------------------------------------------------------------

    @property
    def code(self) -> str:
        """
        Return the canonical protection-function designation.

        Alias for ``function_code``.
        """

        return self.function_code

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

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Setting name must be a string."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Setting name cannot be empty."
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
        """

        relay_operational = bool(
            getattr(
                self.relay,
                "operational",
                True,
            )
        )

        return (
            relay_operational
            and self.enabled
            and not self.blocked
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

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Protection input name must be a string."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Protection input name cannot be empty."
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

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Protection input name must be a string."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Protection input name cannot be empty."
            )

        try:
            return self._relay_inputs[
                normalized_name
            ]

        except KeyError as exc:

            raise KeyError(
                f"Protection element '{self.element_id}' "
                f"({self.function_code}) on relay "
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

        missing: list[str] = []
        seen: set[str] = set()

        for name in names:

            if not isinstance(
                name,
                str,
            ):
                raise TypeError(
                    "Protection input names must be strings."
                )

            normalized_name = name.strip()

            if not normalized_name:
                raise ValueError(
                    "Protection input names cannot be empty."
                )

            if normalized_name in seen:
                continue

            seen.add(normalized_name)

            if normalized_name not in self._relay_inputs:
                missing.append(
                    normalized_name
                )

        if missing:
            raise ValueError(
                f"Protection element '{self.element_id}' "
                f"({self.function_code}) on relay "
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

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Runtime-state name must be a string."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Runtime-state name cannot be empty."
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

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Runtime-state name must be a string."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Runtime-state name cannot be empty."
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

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Runtime-state name must be a string."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Runtime-state name cannot be empty."
            )

        return normalized_name in self._runtime

    # ------------------------------------------------------------------

    @property
    def runtime(
        self,
    ) -> Mapping[str, Any]:
        """
        Return read-only access to transient runtime state.

        Intended primarily for diagnostics and testing.
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
            element_id=self.element_id,
            function_code=self.function_code,
            pickup=pickup,
            operate=operate,
            trip_request=trip_request,
            blocked=blocked,
            valid=valid,
            operating_time=operating_time,
            timestamp=timestamp,
            reason=reason,
            metadata=metadata or {},
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
            element_id=self.element_id,
            function_code=self.function_code,
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
            element_id=self.element_id,
            function_code=self.function_code,
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
            element_id=self.element_id,
            function_code=self.function_code,
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
            element_id=self.element_id,
            function_code=self.function_code,
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
            element_id=self.element_id,
            function_code=self.function_code,
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
        context: ProtectionContext | None = None,
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
            "element_id": self.element_id,
            "relay_id": self.relay_id,
            "function_code": self.function_code,
            "function_name": self.function_name,
            "enabled": self.enabled,
            "blocked": self.blocked,
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
            f"id={self.element_id!r}, "
            f"relay_id={self.relay_id!r}, "
            f"code={self.function_code!r}, "
            f"enabled={self.enabled}, "
            f"blocked={self.blocked}>"
        )


# ======================================================================
# PUBLIC API
# ======================================================================

__all__ = [
    "RelayBase",
]
