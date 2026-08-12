"""
GridForge V2 Protection Element Base

File:
    core/protection/relay_base.py

Purpose
-------
Defines the common execution contract for GridForge V2 protection
function plugins.

A RelayBase instance represents one protection element/function hosted
by an authoritative physical Relay device.

Examples:

    50   Instantaneous Overcurrent
    51   Time Overcurrent
    21   Distance
    87T  Transformer Differential
    87B  Bus Differential
    27   Undervoltage
    59   Overvoltage
    81U  Underfrequency
    32   Reverse Power
    46   Negative Sequence
    50BF Breaker Failure

The authoritative physical relay remains:

    core/model/relay.py

RelayBase is an executable protection-element plugin.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class RelayBase(ABC):
    """
    Base class for GridForge protection-element plugins.
    """

    def __init__(
        self,
        relay: Any,
        *,
        function_code: str,
        function_name: str = "",
        relay_inputs: Mapping[str, Any] | None = None,
        settings: Mapping[str, Any] | None = None,
        enabled: bool = True,
        blocked: bool = False,
    ) -> None:

        if relay is None:
            raise ValueError("relay cannot be None.")

        function_code = str(function_code).strip().upper()

        if not function_code:
            raise ValueError("function_code cannot be empty.")

        self.relay = relay

        self.function_code = function_code
        self.function_name = (
            str(function_name).strip()
            or function_code
        )

        self.enabled = bool(enabled)
        self.blocked = bool(blocked)

        self.settings = dict(settings or {})
        self._relay_inputs = dict(relay_inputs or {})

        # Runtime state belongs to the protection element.
        self._runtime: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    @property
    def id(self) -> Any:
        return self.relay.id

    @property
    def operational(self) -> bool:
        return (
            bool(getattr(self.relay, "operational", True))
            and self.enabled
            and not self.blocked
        )

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------

    def has_input(self, name: str) -> bool:
        return name in self._relay_inputs

    def get_input(self, name: str) -> Any:
        try:
            return self._relay_inputs[name]
        except KeyError as exc:
            raise KeyError(
                f"Protection element {self.function_code} "
                f"on relay {self.id} requires input '{name}'."
            ) from exc

    def input_signal(self, name: str) -> Any:
        channel = self.get_input(name)

        if hasattr(channel, "engineering_value"):
            return channel.engineering_value

        if hasattr(channel, "value"):
            value = channel.value
            return value() if callable(value) else value

        raise AttributeError(
            f"Input '{name}' has no supported signal interface."
        )

    def require_inputs(self, *names: str) -> None:
        missing = [n for n in names if n not in self._relay_inputs]

        if missing:
            raise ValueError(
                f"{self.function_code} on relay {self.id} "
                f"is missing inputs {missing}."
            )

    # ------------------------------------------------------------------
    # Runtime state
    # ------------------------------------------------------------------

    def runtime_get(self, name: str, default: Any = None) -> Any:
        return self._runtime.get(name, default)

    def runtime_set(self, name: str, value: Any) -> None:
        self._runtime[name] = value

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    @abstractmethod
    def evaluate(self, context: Any = None) -> Any:
        """
        Evaluate this protection element.

        Returns a ProtectionDecision or compatible decision object.

        Implementations must not operate breakers directly.
        """

        raise NotImplementedError

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """
        Reset element-specific runtime state.

        The authoritative Relay device is not reset here because
        multiple protection elements may share the same relay.
        """

        self._runtime.clear()

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        return {
            "relay_id": self.id,
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
