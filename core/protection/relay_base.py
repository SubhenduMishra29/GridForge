"""
GridForge V2 Protection Element Base.

File
----
core/protection/relay_base.py

Purpose
-------
Defines the common execution contract for GridForge V2 protection
function plugins.

A RelayBase instance represents ONE executable protection function
hosted by an authoritative physical Relay device.

Examples
--------
50      Instantaneous Overcurrent
51      Time Overcurrent
21      Distance
87T     Transformer Differential
87B     Bus Differential
27      Undervoltage
59      Overvoltage
81U     Underfrequency
32      Reverse Power
46      Negative Sequence
50BF    Breaker Failure

Architectural Boundary
----------------------
The authoritative physical Relay remains:

    core/model/relay.py

RelayBase is NOT a second relay model.

A physical Relay may host multiple independent protection elements:

    Relay
    ├── 50
    ├── 51
    ├── 46
    └── 50BF

Each protection element:

    * owns its function-specific configuration
    * owns its transient runtime state
    * consumes assigned RelayInput objects
    * evaluates measurements and context
    * produces a ProtectionDecision

A protection element must NOT:

    * own the physical Relay
    * own CT/PT/CVT measurement infrastructure
    * directly operate a breaker
    * directly change network topology
    * contain GUI state
    * contain persistence/file I/O
    * duplicate measurement state

Notes
-----
ProtectionDecision, RelayInput, and ProtectionContext are intentionally
referenced through TYPE_CHECKING until their authoritative contracts
are established by their respective files.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from core.model.relay import Relay

    from .decision import ProtectionDecision
    from .relay_input import RelayInput


class RelayBase(ABC):
    """
    Abstract base class for GridForge V2 protection-function plugins.

    One instance represents one protection-function instance.

    A single physical Relay may therefore contain multiple
    RelayBase-derived protection elements.
    """

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
        Create a protection-function instance.

        Parameters
        ----------
        relay:
            Authoritative physical Relay hosting this function.

        element_id:
            Stable identity of this protection-function instance.

            This MUST be different from relay.id because one physical
            relay may host multiple protection functions.

        function_code:
            Protection function designation, for example ``50``,
            ``51``, ``21`` or ``87T``.

        function_name:
            Human-readable function name.

        relay_inputs:
            Assigned RelayInput objects.

            The protection element references these inputs but does not
            own the measurement infrastructure.

        settings:
            Function-specific configuration.

        enabled:
            Whether the protection function is enabled.

        blocked:
            Whether the protection function is statically blocked.
        """

        if relay is None:
            raise ValueError("relay cannot be None.")

        normalized_element_id = str(element_id).strip()

        if not normalized_element_id:
            raise ValueError("element_id cannot be empty.")

        normalized_function_code = str(function_code).strip().upper()

        if not normalized_function_code:
            raise ValueError("function_code cannot be empty.")

        self.relay = relay

        # --------------------------------------------------------------
        # Identity
        # --------------------------------------------------------------

        self.element_id = normalized_element_id
        self.function_code = normalized_function_code

        self.function_name = (
            str(function_name).strip()
            or normalized_function_code
        )

        # --------------------------------------------------------------
        # Execution state
        # --------------------------------------------------------------

        self.enabled = bool(enabled)
        self.blocked = bool(blocked)

        # --------------------------------------------------------------
        # Function configuration
        #
        # Settings are owned by this protection-function instance.
        # They are configuration data, not runtime state.
        # --------------------------------------------------------------

        self._settings: dict[str, Any] = dict(settings or {})

        # --------------------------------------------------------------
        # Measurement/input assignments
        #
        # These are references to externally managed RelayInput
        # objects. The protection element does not own them.
        # --------------------------------------------------------------

        self._relay_inputs: dict[str, RelayInput] = dict(
            relay_inputs or {}
        )

        # --------------------------------------------------------------
        # Transient execution state
        #
        # Examples:
        #     pickup timer
        #     accumulated operating quantity
        #     previous measurement
        #     internal state-machine state
        #
        # This state is NOT authoritative project configuration.
        # --------------------------------------------------------------

        self._runtime: dict[str, Any] = {}

    # ==================================================================
    # Identity
    # ==================================================================

    @property
    def id(self) -> str:
        """
        Return the stable identity of this protection element.

        ``id`` intentionally identifies the protection-function
        instance rather than the physical Relay.
        """
        return self.element_id

    @property
    def relay_id(self) -> Any:
        """
        Return the identity of the authoritative physical Relay.
        """
        return self.relay.id

    # ==================================================================
    # Configuration
    # ==================================================================

    @property
    def settings(self) -> Mapping[str, Any]:
        """
        Return read-only access to function settings.

        The returned mapping prevents accidental replacement of the
        internal settings dictionary by consumers.

        Mutation of individual settings should be controlled by the
        eventual protection configuration API rather than performed
        directly by protection functions.
        """
        return MappingProxyType(self._settings)

    # ==================================================================
    # Operational State
    # ==================================================================

    @property
    def operational(self) -> bool:
        """
        Return whether this protection element is currently eligible
        for evaluation.

        The physical Relay's operational state remains authoritative.

        This property only represents the local execution gate:

            physical relay operational
            AND function enabled
            AND function not statically blocked

        Dynamic blocking/inhibition originating from protection schemes,
        supervision, interlocking, or external signals belongs to the
        execution context/scheme layer and must not be embedded here.
        """
        return (
            bool(getattr(self.relay, "operational", True))
            and self.enabled
            and not self.blocked
        )

    # ==================================================================
    # Inputs
    # ==================================================================

    @property
    def inputs(self) -> Mapping[str, RelayInput]:
        """
        Return read-only access to assigned RelayInput objects.

        RelayBase does not own these inputs.
        """
        return MappingProxyType(self._relay_inputs)

    def has_input(self, name: str) -> bool:
        """
        Return True if an input with the supplied name is assigned.
        """
        return name in self._relay_inputs

    def get_input(self, name: str) -> RelayInput:
        """
        Return an assigned RelayInput.

        The protection element receives the input object itself.

        Interpretation of measurements remains the responsibility of
        the RelayInput/measurement subsystem.
        """
        try:
            return self._relay_inputs[name]
        except KeyError as exc:
            raise KeyError(
                f"Protection element '{self.element_id}' "
                f"({self.function_code}) on relay "
                f"'{self.relay_id}' requires input '{name}'."
            ) from exc

    def require_inputs(self, *names: str) -> None:
        """
        Validate that all specified inputs are assigned.

        Raises
        ------
        ValueError
            If one or more required inputs are missing.
        """
        missing = [
            name
            for name in names
            if name not in self._relay_inputs
        ]

        if missing:
            raise ValueError(
                f"Protection element '{self.element_id}' "
                f"({self.function_code}) on relay "
                f"'{self.relay_id}' is missing required inputs: "
                f"{missing}."
            )

    # ==================================================================
    # Runtime State
    # ==================================================================

    def runtime_get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return transient protection-function runtime state.

        Runtime state is deliberately separate from persistent
        protection settings.
        """
        return self._runtime.get(name, default)

    def runtime_set(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Store transient protection-function runtime state.
        """
        self._runtime[name] = value

    def runtime_has(self, name: str) -> bool:
        """
        Return True if a runtime-state entry exists.
        """
        return name in self._runtime

    # ==================================================================
    # Evaluation
    # ==================================================================

    @abstractmethod
    def evaluate(
        self,
        context: Any = None,
    ) -> ProtectionDecision:
        """
        Evaluate the protection function.

        Parameters
        ----------
        context:
            Protection execution context.

            The final ProtectionContext contract will define the
            authoritative simulation timestamp, system state,
            execution information, supervision state, and other
            contextual information required by protection functions.

        Returns
        -------
        ProtectionDecision
            Structured result of the protection-function evaluation.

        Architectural Rule
        -------------------
        The protection function must NOT directly operate physical
        equipment.

        In particular, implementations must not perform actions such
        as:

            breaker.open()
            breaker.trip()
            switch.open()
            network.topology_change()

        Instead, the function produces a ProtectionDecision which is
        subsequently interpreted by the protection scheme/output
        execution layer.
        """
        raise NotImplementedError

    # ==================================================================
    # Reset
    # ==================================================================

    def reset(self) -> None:
        """
        Reset transient runtime state belonging to this element.

        This method does NOT reset:

            * the physical Relay
            * RelayInput objects
            * measurement channels
            * CT/PT/CVT state
            * protection scheme state
            * network topology
        """
        self._runtime.clear()

    # ==================================================================
    # Diagnostics
    # ==================================================================

    def status(self) -> dict[str, Any]:
        """
        Return diagnostic information for this protection element.

        The returned dictionary is intended for diagnostics,
        inspection, testing, and future monitoring interfaces.

        It is not the authoritative persistence representation.
        """
        return {
            "element_id": self.element_id,
            "relay_id": self.relay_id,
            "function_code": self.function_code,
            "function_name": self.function_name,
            "enabled": self.enabled,
            "blocked": self.blocked,
            "operational": self.operational,
            "inputs": tuple(self._relay_inputs.keys()),
            "runtime": dict(self._runtime),
        }


__all__ = [
    "RelayBase",
]
