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
        Scheme / Output Layer
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


Execution Context
-----------------

ProtectionContext supplies evaluation-time information such as:

    time
    timestep
    event information
    supervision
    simulation/network references

ProtectionContext does not replace RelayInput.

RelayInput provides the protection function's measurement interface.

Evaluation
----------

Every concrete protection function implements:

    evaluate(context) -> ProtectionDecision

The returned ProtectionDecision is the authoritative result of
that protection-function evaluation.

RelayBase must never reduce the result to a boolean or directly
operate physical equipment.

Timing
------

RelayBase does not own a simulation clock.

Time-dependent protection functions may use:

    ProtectionContext.time
    ProtectionContext.timestep

and maintain algorithm-specific transient state in ``runtime``.

System-wide event scheduling belongs to the simulation/event layer.

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
    from .protection_decision import ProtectionDecision
    from .relay_input import RelayInput


class RelayBase(ABC):
    """
    Abstract base class for one executable protection-function
    instance.

    A physical Relay may host multiple RelayBase-derived functions.

    RelayBase therefore represents protection-function execution,
    not physical relay equipment.
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
            Authoritative physical Relay hosting this protection
            function.

        element_id:
            Stable identity of this protection-function instance.

            This identifies the function instance, not the physical
            Relay.

        function_code:
            Protection function designation such as ``50``, ``51``,
            ``21``, ``87T`` or ``50BF``.

        function_name:
            Optional human-readable function name.

        relay_inputs:
            Mapping of function-local input names to RelayInput
            objects.

        settings:
            Function-specific configuration.

        enabled:
            Whether this protection function is enabled.

        blocked:
            Static local blocking state.

        Notes
        -----
        The Relay object is referenced, not duplicated.

        RelayInput objects are referenced, not copied into a separate
        measurement model.
        """

        if relay is None:
            raise ValueError(
                "RelayBase relay cannot be None."
            )

        # --------------------------------------------------------------
        # Element identity
        # --------------------------------------------------------------

        normalized_element_id = str(
            element_id
        ).strip()

        if not normalized_element_id:
            raise ValueError(
                "RelayBase element_id cannot be empty."
            )

        # --------------------------------------------------------------
        # Function code
        # --------------------------------------------------------------

        normalized_function_code = str(
            function_code
        ).strip().upper()

        if not normalized_function_code:
            raise ValueError(
                "RelayBase function_code cannot be empty."
            )

        # --------------------------------------------------------------
        # Physical relay identity
        # --------------------------------------------------------------

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
        # Input bindings
        # --------------------------------------------------------------

        normalized_inputs: dict[
            str,
            RelayInput,
        ] = {}

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

            if normalized_name in normalized_inputs:
                raise ValueError(
                    f"Duplicate RelayBase input name: "
                    f"'{normalized_name}'."
                )

            normalized_inputs[
                normalized_name
            ] = relay_input

        # --------------------------------------------------------------
        # Function configuration
        # --------------------------------------------------------------

        normalized_settings: dict[
            str,
            Any,
        ] = dict(
            settings or {}
        )

        for name in normalized_settings:

            if not isinstance(
                name,
                str,
            ):
                raise TypeError(
                    "RelayBase setting names must be strings."
                )

            if not name.strip():
                raise ValueError(
                    "RelayBase setting names cannot be empty."
                )

        # --------------------------------------------------------------
        # Authoritative references
        # --------------------------------------------------------------

        self.relay = relay

        # --------------------------------------------------------------
        # Function identity
        # --------------------------------------------------------------

        self.element_id = normalized_element_id

        self.function_code = (
            normalized_function_code
        )

        self.function_name = (
            str(function_name).strip()
            or normalized_function_code
        )

        # --------------------------------------------------------------
        # Local execution state
        # --------------------------------------------------------------

        self.enabled = bool(
            enabled
        )

        self.blocked = bool(
            blocked
        )

        # --------------------------------------------------------------
        # Function configuration
        # --------------------------------------------------------------

        self._settings = (
            normalized_settings
        )

        # --------------------------------------------------------------
        # Measurement bindings
        # --------------------------------------------------------------

        self._relay_inputs = (
            normalized_inputs
        )

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
        Return the stable identity of this protection-function
        instance.

        This is NOT the physical Relay identity.
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

        This is an alias for ``function_code``.
        """

        return self.function_code

    # ==================================================================
    # CONFIGURATION
    # ==================================================================

    @property
    def settings(self) -> Mapping[str, Any]:
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

        Parameters
        ----------
        name:
            Setting name.

        default:
            Value returned when the setting is not present.
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
            AND function enabled
            AND function not statically blocked

        Dynamic blocking, permissive logic, interlocking,
        supervision, and scheme-level inhibition belong to the
        ProtectionContext or protection-scheme layer.
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

        RelayBase references these objects but does not own the
        underlying measurement infrastructure.
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

        return name.strip() in self._relay_inputs

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
                f"Protection element "
                f"'{self.element_id}' "
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

        Concrete protection functions should call this during
        initialization or before evaluation when their required
        measurement set is known.
        """

        missing: list[str] = []

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

            if (
                normalized_name
                not in self._relay_inputs
            ):
                missing.append(
                    normalized_name
                )

        if missing:

            raise ValueError(
                f"Protection element "
                f"'{self.element_id}' "
                f"({self.function_code}) on relay "
                f"'{self.relay_id}' is missing "
                f"required inputs: {missing}."
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
        Return transient function runtime state.

        Runtime state is separate from persistent function
        configuration.
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
        Set transient function runtime state.
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

        return (
            normalized_name
            in self._runtime
        )

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
    # EVALUATION
    # ==================================================================

    @abstractmethod
    def evaluate(
        self,
        context: ProtectionContext | None = None,
    ) -> ProtectionDecision:
        """
        Evaluate the protection function.

        Parameters
        ----------
        context:
            Evaluation-time ProtectionContext.

        Returns
        -------
        ProtectionDecision
            Structured result produced by this protection function.

        Architectural Rules
        --------------------
        Implementations must produce a ProtectionDecision.

        Implementations must NOT:

            * reduce the result to a bare boolean;
            * directly open breakers;
            * directly trip breakers;
            * operate switches;
            * modify network topology;
            * invoke BreakerManager;
            * schedule physical equipment actions;
            * perform relay coordination.

        The resulting ProtectionDecision is interpreted by the
        higher-level ProtectionSystem / scheme / output layers.
        """

        raise NotImplementedError

    # ==================================================================
    # RESET
    # ==================================================================

    def reset(
        self,
    ) -> None:
        """
        Reset transient protection-function runtime state.

        This does NOT reset:

            * the physical Relay;
            * RelayInput objects;
            * MeasurementChannels;
            * CT/PT/CVT state;
            * protection schemes;
            * breaker state;
            * network topology;
            * function configuration.
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

        This mapping is intended for:

            * diagnostics;
            * testing;
            * inspection;
            * monitoring.

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


__all__ = [
    "RelayBase",
]
