# ============================================================
# File: core/analysis/dynamic_model_association.py
# GridForge V2 — Dynamic Machine Model Association
# Author: Subhendu Mishra
# ============================================================
"""Persistent application-level association of synchronous machines to dynamic models."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from core.solver.dynamics.machine_models import ClassicalMachineParameters


@dataclass(frozen=True, slots=True)
class DynamicMachineModelAssociation:
    """Immutable project-owned dynamic model binding for one machine identity."""

    machine_id: str
    model_type: str
    parameters: ClassicalMachineParameters
    metadata: Mapping[str, Any] = MappingProxyType({})

    def __post_init__(self) -> None:
        if not isinstance(self.machine_id, str) or not self.machine_id.strip():
            raise ValueError("machine_id must be a non-empty string.")
        if not isinstance(self.model_type, str) or not self.model_type.strip():
            raise ValueError("model_type must be a non-empty string.")
        if not isinstance(self.parameters, ClassicalMachineParameters):
            raise TypeError("parameters must be ClassicalMachineParameters.")
        object.__setattr__(self, "machine_id", self.machine_id.strip())
        object.__setattr__(self, "model_type", self.model_type.strip())
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        p = self.parameters
        return {
            "machine_id": self.machine_id,
            "model_type": self.model_type,
            "parameters": {
                "H": p.H,
                "Xd_prime": p.Xd_prime,
                "D": p.D,
                "Efd": p.Efd,
                "initial_delta": p.initial_delta,
                "initial_omega": p.initial_omega,
            },
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DynamicMachineModelAssociation":
        if not isinstance(data, Mapping):
            raise TypeError("Dynamic machine model association must be a mapping.")
        parameters = data.get("parameters")
        if not isinstance(parameters, Mapping):
            raise ValueError("Dynamic machine model parameters are required.")
        return cls(
            machine_id=str(data.get("machine_id", "")),
            model_type=str(data.get("model_type", "")),
            parameters=ClassicalMachineParameters(
                H=float(parameters["H"]),
                Xd_prime=float(parameters["Xd_prime"]),
                D=float(parameters.get("D", 0.0)),
                Efd=float(parameters.get("Efd", 1.0)),
                initial_delta=float(parameters.get("initial_delta", 0.0)),
                initial_omega=float(parameters.get("initial_omega", 0.0)),
            ),
            metadata=data.get("metadata", {}),
        )


class DynamicMachineModelRegistry:
    """Project-scoped binding store; never part of Network topology."""

    def __init__(self, associations: tuple[DynamicMachineModelAssociation, ...] = ()) -> None:
        self._associations = {item.machine_id: item for item in associations}

    def bind(self, association: DynamicMachineModelAssociation) -> None:
        if not isinstance(association, DynamicMachineModelAssociation):
            raise TypeError("association must be DynamicMachineModelAssociation.")
        self._associations[association.machine_id] = association

    def remove(self, machine_id: str) -> None:
        self._associations.pop(str(machine_id), None)

    def get(self, machine_id: str) -> DynamicMachineModelAssociation | None:
        return self._associations.get(str(machine_id))

    def all(self) -> tuple[DynamicMachineModelAssociation, ...]:
        return tuple(self._associations[key] for key in sorted(self._associations))


__all__ = ["DynamicMachineModelAssociation", "DynamicMachineModelRegistry"]
