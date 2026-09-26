"""Canonical adapter boundary for dynamic Control plugins.

Author: Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class DynamicControlEvaluation:
    derivatives: tuple[float, ...]
    outputs: Mapping[str, Any]


class DynamicControlAdapter:
    """Translate a plugin's representation into the solver-neutral contract."""

    def __init__(self, plugin: Any, *, controller_id: str, controller_type: str) -> None:
        if plugin is None:
            raise TypeError("plugin is required.")
        self.plugin = plugin
        self.controller_id = str(controller_id).strip()
        self.controller_type = str(controller_type).strip()
        if not self.controller_id or not self.controller_type:
            raise ValueError("controller identity is required.")
        self.state_names = tuple(str(name) for name in getattr(plugin, "state_names", ()))
        if not self.state_names:
            raise ValueError("Dynamic plugin must expose state_names.")

    @property
    def state_size(self) -> int:
        return len(self.state_names)

    @property
    def plugin_type(self) -> str:
        return str(getattr(self.plugin, "plugin_type", "dynamic"))

    @property
    def plugin_version(self) -> str:
        return str(getattr(self.plugin, "version", "unknown"))

    def initial_state(self, inputs: Mapping[str, Any]) -> tuple[float, ...]:
        state = self.plugin.initial_state(**dict(inputs))
        result = tuple(float(value) for value in state) if not isinstance(state, Mapping) else tuple(float(state[name]) for name in self.state_names)
        self._validate_vector(result)
        return result

    def evaluate(self, state: Sequence[float], inputs: Mapping[str, Any], time: float) -> DynamicControlEvaluation:
        del time
        self._validate_vector(state)
        raw = self.plugin.evaluate(tuple(float(value) for value in state), **dict(inputs))
        derivatives = raw.get("derivatives") if isinstance(raw, Mapping) else None
        output = raw.get("outputs", raw.get("output")) if isinstance(raw, Mapping) else None
        if isinstance(derivatives, Mapping):
            derivatives = tuple(float(derivatives[name]) for name in self.state_names)
        else:
            derivatives = tuple(float(value) for value in derivatives)
        if len(derivatives) != self.state_size:
            raise ValueError(f"Dynamic plugin '{self.controller_id}' returned an invalid derivative vector.")
        if isinstance(output, Mapping):
            outputs = dict(output)
        else:
            outputs = {self.controller_type: output}
        return DynamicControlEvaluation(derivatives=derivatives, outputs=outputs)

    def _validate_vector(self, state: Sequence[float]) -> None:
        if len(state) != self.state_size:
            raise ValueError(f"Dynamic plugin '{self.controller_id}' requires {self.state_size} states, received {len(state)}.")


__all__ = ["DynamicControlAdapter", "DynamicControlEvaluation"]
