# Author: Subhendu Mishra
"""Resolve an SLD-configured CT to one authoritative network branch.

The resolver consumes Core topology only. The Application layer may supply
an engineer-authored branch identity from the CT's SLD node properties; the
identity is accepted only after its terminal buses are checked against the
CT's primary terminals. When no identity is configured, only a unique exact
terminal-pair match is accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.model import Cable, CurrentTransformer, Line, Transformer


class CTMeasurementAssociationError(ValueError):
    """Base error for invalid or unresolved CT-to-branch associations."""


class CTMeasurementAssociationAmbiguousError(CTMeasurementAssociationError):
    """Raised when multiple branches satisfy the CT's terminal topology."""


@dataclass(frozen=True, slots=True)
class CTMeasurementAssociation:
    """Immutable, topology-revision-scoped CT measurement association."""

    ct_id: str
    monitored_element_id: str
    monitored_element_type: str
    ct_p1_bus_id: str
    ct_p2_bus_id: str
    branch_from_bus_id: str
    branch_to_bus_id: str
    measurement_side: str
    current_orientation_sign: int
    project_id: str
    activation_generation: int
    topology_revision: int

    def __post_init__(self) -> None:
        for name in (
            "ct_id", "monitored_element_id", "monitored_element_type",
            "ct_p1_bus_id", "ct_p2_bus_id", "branch_from_bus_id",
            "branch_to_bus_id", "measurement_side", "project_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())
        if self.ct_p1_bus_id == self.ct_p2_bus_id:
            raise ValueError("CT primary terminals must resolve to distinct Buses.")
        if self.branch_from_bus_id == self.branch_to_bus_id:
            raise ValueError("Monitored branch must connect distinct Buses.")
        if self.measurement_side not in {"from", "to"}:
            raise ValueError("measurement_side must be 'from' or 'to'.")
        if self.current_orientation_sign not in {-1, 1}:
            raise ValueError("current_orientation_sign must be -1 or +1.")
        for name in ("activation_generation", "topology_revision"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer.")
        if self.activation_generation < 1:
            raise ValueError("activation_generation must be positive.")


class CTMeasurementAssociationResolver:
    """Resolve engineer-configured CT placement against canonical Core topology."""

    _BRANCH_TYPES = (Line, Cable, Transformer)

    def __init__(self, network: Any) -> None:
        if network is None or not hasattr(network, "get_by_identity"):
            raise TypeError("network must be an authoritative Core Network.")
        self._network = network

    def resolve(
        self,
        ct_id: str,
        *,
        monitored_element_id: str | None = None,
    ) -> CTMeasurementAssociation:
        """Resolve one CT to a branch, rejecting missing or ambiguous topology.

        monitored_element_id is an optional engineer-authored SLD association.
        It is not trusted until the CT P1/P2 Bus pair matches the selected
        branch's FROM/TO Bus pair. Without it, an exact pair must identify one
        and only one active Line, Cable, or Transformer.
        """
        if not isinstance(ct_id, str) or not ct_id.strip():
            raise ValueError("ct_id must be a non-empty string.")
        ct_id = ct_id.strip()
        if monitored_element_id is not None:
            if not isinstance(monitored_element_id, str) or not monitored_element_id.strip():
                raise ValueError("monitored_element_id must be a non-empty string when supplied.")
            monitored_element_id = monitored_element_id.strip()

        if not bool(getattr(self._network, "topology_valid", False)):
            self._network.rebuild_topology()
        snapshot = getattr(self._network, "topology_snapshot", None)
        if snapshot is None:
            raise CTMeasurementAssociationError("A canonical, valid TopologySnapshot is required.")

        try:
            ct = self._network.get_by_identity(ct_id)
        except KeyError as exc:
            raise CTMeasurementAssociationError(f"CT {ct_id!r} is not registered in the active Network.") from exc
        if not isinstance(ct, CurrentTransformer):
            raise CTMeasurementAssociationError(f"Equipment {ct_id!r} is not a CurrentTransformer.")
        if not bool(getattr(ct, "in_service", True)):
            raise CTMeasurementAssociationError(f"CT {ct_id!r} is out of service.")

        attachments: dict[tuple[str, str], list[str]] = {}
        for item in snapshot.equipment_bus_attachments:
            attachments.setdefault((str(item.equipment_id), str(item.terminal_role)), []).append(str(item.bus_id))

        p1_bus = self._single_attachment(attachments, ct_id, "P1")
        p2_bus = self._single_attachment(attachments, ct_id, "P2")
        if p1_bus == p2_bus:
            raise CTMeasurementAssociationError(
                f"CT {ct_id!r} primary terminals P1 and P2 resolve to the same Bus {p1_bus!r}."
            )

        branches: dict[str, tuple[Any, str, str]] = {}
        for collection_name in ("lines", "cables", "transformers"):
            for branch in getattr(self._network, collection_name, ()) or ():
                if not isinstance(branch, self._BRANCH_TYPES) or not bool(getattr(branch, "in_service", True)):
                    continue
                branch_id = str(getattr(branch, "id", "")).strip()
                if not branch_id:
                    continue
                from_role = getattr(getattr(branch, "from_terminal", None), "role", None)
                to_role = getattr(getattr(branch, "to_terminal", None), "role", None)
                if not isinstance(from_role, str) or not isinstance(to_role, str):
                    continue
                from_bus = self._single_attachment(attachments, branch_id, from_role, required=False)
                to_bus = self._single_attachment(attachments, branch_id, to_role, required=False)
                if from_bus is not None and to_bus is not None and from_bus != to_bus:
                    branches[branch_id] = (branch, from_bus, to_bus)

        if monitored_element_id is not None:
            selected = branches.get(monitored_element_id)
            if selected is None:
                raise CTMeasurementAssociationError(
                    f"SLD-selected monitored element {monitored_element_id!r} is not an active, "
                    "fully connected Line, Cable, or Transformer in the current topology."
                )
            candidates = [(monitored_element_id, *selected)]
            if not self._matches_pair(p1_bus, p2_bus, selected[1], selected[2]):
                raise CTMeasurementAssociationError(
                    f"CT {ct_id!r} primary Bus pair ({p1_bus!r}, {p2_bus!r}) does not match "
                    f"SLD-selected element {monitored_element_id!r} terminal Bus pair "
                    f"({selected[1]!r}, {selected[2]!r})."
                )
        else:
            candidates = [
                (branch_id, branch, from_bus, to_bus)
                for branch_id, (branch, from_bus, to_bus) in branches.items()
                if self._matches_pair(p1_bus, p2_bus, from_bus, to_bus)
            ]
            if not candidates:
                raise CTMeasurementAssociationError(
                    f"CT {ct_id!r} does not resolve to an active branch with the same P1/P2 Bus pair. "
                    "Configure the monitored element on the CT's SLD node and verify its electrical connections."
                )
            if len(candidates) > 1:
                candidate_ids = tuple(sorted(item[0] for item in candidates))
                raise CTMeasurementAssociationAmbiguousError(
                    f"CT {ct_id!r} matches multiple parallel branches {candidate_ids!r}; "
                    "select the monitored element on the CT's SLD node."
                )

        branch_id, branch, from_bus, to_bus = candidates[0]
        p1_is_from = p1_bus == from_bus and p2_bus == to_bus
        return CTMeasurementAssociation(
            ct_id=ct_id,
            monitored_element_id=branch_id,
            monitored_element_type=type(branch).__name__,
            ct_p1_bus_id=p1_bus,
            ct_p2_bus_id=p2_bus,
            branch_from_bus_id=from_bus,
            branch_to_bus_id=to_bus,
            measurement_side="from" if p1_is_from else "to",
            current_orientation_sign=1 if p1_is_from else -1,
            project_id=str(snapshot.project_id),
            activation_generation=int(snapshot.activation_generation),
            topology_revision=int(snapshot.topology_revision),
        )

    @staticmethod
    def _single_attachment(
        attachments: dict[tuple[str, str], list[str]],
        equipment_id: str,
        terminal_role: str,
        *,
        required: bool = True,
    ) -> str | None:
        matches = attachments.get((equipment_id, terminal_role), [])
        if len(matches) > 1:
            raise CTMeasurementAssociationError(
                f"Terminal {equipment_id!r}:{terminal_role!r} resolves to multiple Buses {tuple(matches)!r}."
            )
        if not matches:
            if required:
                raise CTMeasurementAssociationError(
                    f"Terminal {equipment_id!r}:{terminal_role!r} has no resolved Bus attachment."
                )
            return None
        return matches[0]

    @staticmethod
    def _matches_pair(p1_bus: str, p2_bus: str, from_bus: str, to_bus: str) -> bool:
        return (p1_bus == from_bus and p2_bus == to_bus) or (
            p1_bus == to_bus and p2_bus == from_bus
        )


__all__ = [
    "CTMeasurementAssociation",
    "CTMeasurementAssociationAmbiguousError",
    "CTMeasurementAssociationError",
    "CTMeasurementAssociationResolver",
]
