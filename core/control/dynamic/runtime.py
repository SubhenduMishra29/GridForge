"""Dynamic Control adapter/runtime contracts.

Author: Subhendu Mishra

Plugins remain outside Core Control. The runtime accepts already-constructed
adapters supplied by the Application composition root.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
import numpy as np
from .base import DynamicControlComponent

@dataclass(frozen=True, slots=True)
class ControllerStateSlice:
    association_id: str
    machine_id: str
    start: int
    stop: int
    @property
    def size(self) -> int: return self.stop - self.start

@dataclass(frozen=True, slots=True)
class GlobalStateLayout:
    machine_slices: tuple[Any, ...]
    controller_slices: tuple[ControllerStateSlice, ...]
    state_size: int
    def controller_slice(self, association_id: str) -> ControllerStateSlice:
        for item in self.controller_slices:
            if item.association_id == association_id: return item
        raise KeyError(association_id)

class DynamicControlAdapter(DynamicControlComponent):
    """Translate an external plugin into the Core Control contract."""
    def __init__(self, plugin: Any, *, component_id: str, component_type: str, input_names: Sequence[str] = (), output_names: Sequence[str] = ()) -> None:
        if plugin is None or not callable(getattr(plugin, "derivatives", None)) or not callable(getattr(plugin, "output", None)):
            raise TypeError("plugin must provide derivatives() and output().")
        self._plugin = plugin
        self._component_id = str(component_id).strip()
        self._component_type = str(component_type).strip()
        self._input_names = tuple(str(x) for x in input_names)
        self._output_names = tuple(str(x) for x in output_names)
        self._state_names = tuple(str(x) for x in getattr(plugin, "state_names", ()))
        if not self._state_names:
            self._state_names = tuple(f"x{i}" for i in range(int(getattr(plugin, "state_size", 0))))
        if not self._component_id or not self._component_type or not self._state_names:
            raise ValueError("Dynamic adapter identity/state contract is incomplete.")
    @property
    def component_id(self) -> str: return self._component_id
    @property
    def component_type(self) -> str: return self._component_type
    @property
    def plugin(self) -> Any: return self._plugin
    def input_definition(self):
        from ..base import ControlSignal, SignalRole
        return tuple(ControlSignal(name=n, role=SignalRole.INPUT, value_type=float) for n in self._input_names)
    def output_definition(self):
        from ..base import ControlSignal, SignalRole
        return tuple(ControlSignal(name=n, role=SignalRole.OUTPUT, value_type=float) for n in self._output_names)
    def dynamic_state_definition(self):
        from .base import DynamicStateDefinition
        return tuple(DynamicStateDefinition(name=n) for n in self._state_names)
    def initial_state(self, inputs=None):
        values = tuple(float(v) for v in self._plugin.initial_state(**dict(inputs or {})))
        return self.state_from_vector(values)
    def derivatives(self, state, inputs, time):
        del time
        values = tuple(float(state[n]) for n in self.dynamic_state_names)
        result = self._plugin.derivatives(values, **dict(inputs))
        if len(result) != self.dynamic_state_size: raise ValueError("Dynamic plugin derivative dimension mismatch.")
        return {n: float(v) for n, v in zip(self.dynamic_state_names, result)}
    def output(self, state, inputs, time):
        del time
        values = tuple(float(state[n]) for n in self.dynamic_state_names)
        result = self._plugin.output(values, **dict(inputs))
        if len(self._output_names) == 1: return {self._output_names[0]: float(result)}
        if isinstance(result, Mapping): return {str(k): float(v) for k, v in result.items()}
        raise ValueError("Dynamic plugin returned multiple outputs without a mapping.")

class DynamicControlRuntime:
    """Reconstruct controller runtime from project associations and adapters."""
    def __init__(self, adapters: Mapping[str, DynamicControlAdapter]) -> None: self._adapters = dict(adapters)
    @property
    def adapters(self) -> Mapping[str, DynamicControlAdapter]: return dict(self._adapters)
    def layout(self, machine_layout: Sequence[Any], associations: Sequence[Any]) -> GlobalStateLayout:
        offset = sum(int(item.stop - item.start) for item in machine_layout)
        slices=[]
        for association in associations:
            adapter=self._adapters.get(association.controller_id)
            if adapter is None: raise KeyError(f"No DynamicControlAdapter for {association.controller_id!r}.")
            start=offset; offset += adapter.dynamic_state_size
            slices.append(ControllerStateSlice(association.association_id, association.machine_id, start, offset))
        return GlobalStateLayout(tuple(machine_layout), tuple(slices), offset)
    def derivatives(self, global_state: np.ndarray, layout: GlobalStateLayout, associations: Sequence[Any], inputs_by_controller: Mapping[str, Mapping[str, Any]], time: float) -> tuple[np.ndarray, Mapping[str, Mapping[str, Any]]]:
        x=np.asarray(global_state,dtype=float)
        if x.size != layout.state_size: raise ValueError("Global state size does not match layout.")
        derivative=np.zeros_like(x); outputs={}
        for association in associations:
            adapter=self._adapters[association.controller_id]; sl=layout.controller_slice(association.association_id)
            local=adapter.state_from_vector(x[sl.start:sl.stop]); result=adapter.evaluate_dynamic(state=local,inputs=inputs_by_controller.get(association.controller_id,{}),time=time)
            derivative[sl.start:sl.stop]=np.asarray(adapter.derivative_vector(local,inputs_by_controller.get(association.controller_id,{}),time),dtype=float)
            outputs[association.controller_id]=dict(result.outputs)
        return derivative, outputs
    def initial_controller_state(self, associations: Sequence[Any], inputs_by_controller: Mapping[str, Mapping[str, Any]]) -> Mapping[str, tuple[float, ...]]:
        return {a.association_id: tuple(self._adapters[a.controller_id].state_vector(self._adapters[a.controller_id].initial_state(inputs_by_controller.get(a.controller_id, {})))) for a in associations}

__all__=["ControllerStateSlice","GlobalStateLayout","DynamicControlAdapter","DynamicControlRuntime"]