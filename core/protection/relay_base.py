"""
GridForge V2 Protection Function Base
=====================================

File
----
core/protection/relay_base.py

Purpose
-------
Defines the canonical executable protection-function contract for
GridForge V2.

A RelayBase instance represents ONE protection-function instance
hosted by an authoritative physical Relay.

Examples
--------
50      Instantaneous Overcurrent
51      Time Overcurrent
21      Distance
67      Directional Overcurrent
87T     Transformer Differential
87B     Bus Differential
27      Undervoltage
59      Overvoltage
81U     Underfrequency
32      Reverse Power
46      Negative Sequence
50BF    Breaker Failure

Architectural Position
----------------------

    Physical Relay
          |
          v
    ProtectionElement
          |
          v
       RelayBase
          |
          +--------------------+
          |                    |
          v                    v
     RelayInput          ProtectionContext
          |                    |
          +---------+----------+
                    |
                    v
             ProtectionDecision
                    |
                    v
             ProtectionSystem
                    |
                    v
          Scheme / Output Logic
                    |
                    v
             BreakerManager


Architectural Principles
------------------------

1. RelayBase is an executable protection-function contract.

2. RelayBase is NOT a physical Relay model.

3. A physical Relay may host multiple RelayBase instances.

4. MeasurementChannel remains authoritative for measurements.

5. RelayInput provides the protection-facing measurement binding.

6. ProtectionContext provides execution context.

7. ProtectionDecision is the authoritative result of one evaluation.

8. RelayBase never directly operates physical equipment.

9. Runtime state is transient and belongs to the protection-function
   instance.

10. Function settings are distinct from transient runtime state.

11. ProtectionElement provides composition/orchestration around
    RelayBase.

12. ProtectionSystem orchestrates multiple ProtectionElements.

Execution Contract
------------------

The canonical execution path is:

    MeasurementChannel
            |
            v
        RelayInput
            |
            v
         RelayBase
            |
            +---- ProtectionContext
            |
            v
    ProtectionDecision
            |
            v
    ProtectionElement
            |
            v
    ProtectionSystem


RelayBase does NOT:

    * own CT/PT/CVT equipment;
    * create MeasurementChannels;
    * duplicate measurement values;
    * build network topology;
    * calculate Y-bus;
    * perform load flow;
    * perform short-circuit analysis;
    * coordinate multiple protection functions;
    * operate breakers;
    * perform file I/O;
    * contain GUI state;
    * own system-wide protection state.

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
    Canonical abstract base class for one GridForge protection
    function instance.

    A RelayBase-derived object represents executable protection logic,
    not a physical relay device.

    Example
    -------

        Relay R1
            |
            +-- ProtectionElement OC51
            |       |
            |       +-- RelayBase implementation
            |
            +-- ProtectionElement DIR67
            |       |
            |       +-- RelayBase implementation
            |
            +-- ProtectionElement DIST21
                    |
                    +-- RelayBase implementation

    Concrete protection functions should inherit from this class.
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
        Initialize one executable protection-function instance.

        Parameters
        ----------
        relay:
            Authoritative physical Relay hosting this function.

        element_id:
            Stable identity of this protection-function instance.

            This identifies the function instance, NOT the physical
            Relay.

        function_code:
            Canonical protection designation.

            Examples:

                50
                51
                21
                67
                87T
                50BF

        function_name:
            Human-readable protection-function name.

        relay_inputs:
            Mapping of function-local input names to RelayInput
            instances.

        settings:
            Function-specific configuration.

        enabled:
            Local function enablement.

        blocked:
            Static local blocking/inhibit state.
        """

        if relay is None:
            raise ValueError(
                "relay cannot be None."
            )

        self._validate_identifier(
            element_id,
            "element_id",
        )

        self._validate_identifier(
            function_code,
            "function_code",
        )

        # --------------------------------------------------------------
        # Authoritative Relay reference
        # --------------------------------------------------------------

        self.relay = relay

        # --------------------------------------------------------------
        # Identity
        # --------------------------------------------------------------

        self.element_id = (
            str(element_id).strip()
        )

        self.function_code = (
            str(function_code).strip().upper()
        )

        self.function_name = (
            str(function_name).strip()
            or self.function_code
        )

        # --------------------------------------------------------------
        # Execution gates
        # --------------------------------------------------------------

        self.enabled = bool(enabled)
        self.blocked = bool(blocked)

        # --------------------------------------------------------------
        # Function configuration
        #
        # Settings belong to the protection-function instance.
        #
        # They are intentionally separate from runtime state.
        # --------------------------------------------------------------

        if settings is None:
            self._settings: dict[str, Any] = {}

        else:
            if not isinstance(
                settings,
                Mapping,
            ):
                raise TypeError(
                    "settings must be a mapping."
                )

            self._settings = dict(
                settings
            )

        # --------------------------------------------------------------
        # Measurement bindings
        #
        # These are references only.
        #
        # RelayBase does not own MeasurementChannel state.
        # --------------------------------------------------------------

        if relay_inputs is None:
            self._relay_inputs: dict[
                str,
                RelayInput,
            ] = {}

        else:
            if not isinstance(
                relay_inputs,
                Mapping,
            ):
                raise TypeError(
                    "relay_inputs must be a mapping."
                )

            self._relay_inputs = {}

            for name, relay_input in (
                relay_inputs.items()
            ):
                self.assign_input(
                    name,
                    relay_input,
                )

        # --------------------------------------------------------------
        # Transient execution state
        #
        # Examples:
        #
        #     pickup timer
        #     previous value
        #     accumulated quantity
        #     internal state-machine state
        #
        # This is runtime state, not project configuration.
        # --------------------------------------------------------------

        self._runtime: dict[
            str,
            Any,
        ] = {}

    # ==================================================================
    # VALIDATION
    # ==================================================================

    @staticmethod
    def _validate_identifier(
        value: str,
        name: str,
    ) -> None:
        """
        Validate an identifier-like value.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{name} must be a string."
            )

        if not value.strip():
            raise ValueError(
                f"{name} cannot be empty."
            )

    # ==================================================================
    # IDENTITY
    # ==================================================================

    @property
    def id(self) -> str:
        """
        Return the protection-function instance identifier.

        This is equivalent to ``element_id``.
        """

        return self.element_id

    # ------------------------------------------------------------------

    @property
    def relay_id(self) -> Any:
        """
        Return the identifier of the authoritative physical Relay.
        """

        return getattr(
            self.relay,
            "id",
            None,
        )

    # ==================================================================
    # FUNCTION INFORMATION
    # ==================================================================

    @property
    def code(self) -> str:
        """
        Return the canonical protection-function code.
        """

        return self.function_code

    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """
        Return the human-readable protection-function name.
        """

        return self.function_name

    # ==================================================================
    # SETTINGS
    # ==================================================================

    @property
    def settings(self) -> Mapping[str, Any]:
        """
        Return read-only access to protection-function settings.

        Settings represent function configuration.

        They must not be confused with transient execution state.
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
        Return one protection-function setting.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Setting name must be a string."
            )

        return self._settings.get(
            name,
            default,
        )

    # ==================================================================
    # OPERATIONAL GATE
    # ==================================================================

    @property
    def operational(self) -> bool:
        """
        Return whether the function is locally eligible for execution.

        The physical Relay remains authoritative for Relay-level
        service state.

        The local execution gate is:

            Relay operational
                AND
            function enabled
                AND
            function not statically blocked

        Dynamic scheme blocking, supervision and interlocking should
        normally be represented through ProtectionContext or the
        higher-level protection scheme layer.
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

    # ==================================================================
    # RELAY INPUTS
    # ==================================================================

    @property
    def inputs(
        self,
    ) -> Mapping[str, RelayInput]:
        """
        Return read-only access to assigned RelayInput objects.

        RelayBase does not own the underlying measurements.
        """

        return MappingProxyType(
            self._relay_inputs
        )

    # ------------------------------------------------------------------

    def assign_input(
        self,
        name: str,
        relay_input: RelayInput,
    ) -> None:
        """
        Assign one RelayInput to this protection function.

        The RelayInput remains externally owned.
        """

        self._validate_identifier(
            name,
            "input name",
        )

        if relay_input is None:
            raise ValueError(
                f"RelayInput '{name}' cannot be None."
            )

        self._relay_inputs[
            str(name).strip()
        ] = relay_input

    # ------------------------------------------------------------------

    def remove_input(
        self,
        name: str,
    ) -> RelayInput:
        """
        Remove and return an assigned RelayInput.
        """

        self._validate_identifier(
            name,
            "input name",
        )

        try:
            return self._relay_inputs.pop(
                str(name).strip()
            )

        except KeyError as exc:
            raise KeyError(
                f"Protection function "
                f"'{self.element_id}' ({self.function_code}) "
                f"has no input '{name}'."
            ) from exc

    # ------------------------------------------------------------------

    def has_input(
        self,
        name: str,
    ) -> bool:
        """
        Return True if the specified input is assigned.
        """

        return (
            isinstance(name, str)
            and name.strip()
            in self._relay_inputs
        )

    # ------------------------------------------------------------------

    def get_input(
        self,
        name: str,
    ) -> RelayInput:
        """
        Return an assigned RelayInput.
        """

        self._validate_identifier(
            name,
            "input name",
        )

        key = name.strip()

        try:
            return self._relay_inputs[
                key
            ]

        except KeyError as exc:
            raise KeyError(
                f"Protection function "
                f"'{self.element_id}' ({self.function_code}) "
                f"on relay '{self.relay_id}' "
                f"requires input '{key}'."
            ) from exc

    # ------------------------------------------------------------------

    def require_inputs(
        self,
        *names: str,
    ) -> None:
        """
        Require all specified RelayInputs to be assigned.

        Concrete protection functions should use this during
        evaluation or initialization validation.
        """

        missing = [
            name
            for name in names
            if not self.has_input(name)
        ]

        if missing:
            raise ValueError(
                f"Protection function "
                f"'{self.element_id}' ({self.function_code}) "
                f"on relay '{self.relay_id}' "
                f"is missing required inputs: "
                f"{missing}."
            )

    # ==================================================================
    # RUNTIME STATE
    # ==================================================================

    @property
    def runtime(
        self,
    ) -> Mapping[str, Any]:
        """
        Return read-only diagnostic access to runtime state.

        Runtime state remains mutable internally.
        """

        return MappingProxyType(
            self._runtime
        )

    # ------------------------------------------------------------------

    def runtime_get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return transient runtime state.
        """

        return self._runtime.get(
            name,
            default,
        )

    # ------------------------------------------------------------------

    def runtime_set(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Store transient runtime state.
        """

        self._validate_identifier(
            name,
            "runtime name",
        )

        self._runtime[
            name.strip()
        ] = value

    # ------------------------------------------------------------------

    def runtime_has(
        self,
        name: str,
    ) -> bool:
        """
        Return True if a runtime-state entry exists.
        """

        return (
            isinstance(name, str)
            and name.strip()
            in self._runtime
        )

    # ------------------------------------------------------------------

    def runtime_remove(
        self,
        name: str,
    ) -> Any:
        """
        Remove and return one runtime-state value.
        """

        self._validate_identifier(
            name,
            "runtime name",
        )

        try:
            return self._runtime.pop(
                name.strip()
            )

        except KeyError as exc:
            raise KeyError(
                f"Runtime state '{name}' "
                f"does not exist for protection "
                f"function '{self.element_id}'."
            ) from exc

    # ==================================================================
    # EVALUATION
    # ==================================================================

    @abstractmethod
    def evaluate(
        self,
        context: ProtectionContext | None = None,
    ) -> ProtectionDecision:
        """
        Evaluate this protection function once.

        Parameters
        ----------
        context:
            Protection execution context.

            The context supplies execution-time information such as
            simulation time, supervision/inhibition information and
            other system-level context defined by ProtectionContext.

        Returns
        -------
        ProtectionDecision
            Structured result of the evaluation.

        Contract
        --------
        Concrete implementations must:

            1. consume assigned RelayInput objects;
            2. use ProtectionContext where required;
            3. perform only their own protection-function logic;
            4. return a ProtectionDecision;
            5. preserve diagnostic information in that decision.

        Concrete implementations must NOT:

            * open or trip breakers;
            * modify network topology;
            * modify MeasurementChannel state;
            * modify CT/PT/CVT state;
            * coordinate other protection functions;
            * schedule physical breaker events;
            * perform GUI operations;
            * perform persistence/file I/O.
        """

        raise NotImplementedError

    # ==================================================================
    # RESET
    # ==================================================================

    def reset(self) -> None:
        """
        Reset transient execution state.

        This resets only the runtime belonging to this protection
        function.

        It does NOT reset:

            * the physical Relay;
            * RelayInput objects;
            * MeasurementChannels;
            * CT/PT/CVT equipment;
            * ProtectionSystem;
            * protection schemes;
            * breakers;
            * network topology.
        """

        self._runtime.clear()

    # ==================================================================
    # STATUS
    # ==================================================================

    def status(self) -> dict[str, Any]:
        """
        Return diagnostic information for this function.

        This is intended for diagnostics, testing and monitoring.

        It is NOT the authoritative persistence representation.
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
            "settings": dict(
                self._settings
            ),
            "runtime": dict(
                self._runtime
            ),
        }

    # ==================================================================
    # REPRESENTATION
    # ==================================================================

    def __repr__(self) -> str:
        """
        Return concise developer-facing representation.
        """

        return (
            f"<{self.__class__.__name__} "
            f"element_id={self.element_id!r}, "
            f"relay_id={self.relay_id!r}, "
            f"function_code={self.function_code!r}, "
            f"enabled={self.enabled}, "
            f"blocked={self.blocked}>"
        )


__all__ = [
    "RelayBase",
]
