# Author: Subhendu Mishra
"""Resolve an SLD-configured CT to one authoritative network branch.

The resolver consumes Core topology only. The Application layer may supply
an engineer-authored branch identity from the CT's SLD node properties; the
identity is accepted only after its terminal buses are checked against the
CT's primary terminals and the intervening conductive switching path. When
no identity is configured, only a unique branch between the two
switch-connected terminal zones is accepted.
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
        if (
            isinstance(self.current_orientation_sign, bool)
            or not isinstance(self.current_orientation_sign, int)
            or self.current_orientation_sign not in {-1, 1}
        ):
            raise ValueError("current_orientation_sign must be integer -1 or +1.")
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
        branch's FROM/TO Bus pair and switch-connected terminal zones.
        Without it, exactly one active Line, Cable, or Transformer must bridge
        the two zones. Closed switching equipment is traversed; open switching
        equipment is not.
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

        switch_component = self._switch_components(snapshot)
        p1_component = switch_component.get(p1_bus, frozenset({p1_bus}))
        p2_component = switch_component.get(p2_bus, frozenset({p2_bus}))
        if p1_component == p2_component:
            raise CTMeasurementAssociationError(
                f"CT {ct_id!r} P1/P2 are connected through the current conductive switching state; "
                "the CT is bypassed or its monitored path is not separable."
            )

        branches: dict[str, tuple[Any, str, str, bool]] = {}
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
                if from_bus is None or to_bus is None or from_bus == to_bus:
                    continue
                from_component = switch_component.get(from_bus, frozenset({from_bus}))
                to_component = switch_component.get(to_bus, frozenset({to_bus}))
                if from_component == p1_component and to_component == p2_component:
                    branches[branch_id] = (branch, from_bus, to_bus, True)
                elif from_component == p2_component and to_component == p1_component:
                    branches[branch_id] = (branch, from_bus, to_bus, False)

        if monitored_element_id is not None:
            selected = branches.get(monitored_element_id)
            if selected is None:
                raise CTMeasurementAssociationError(
                    f"SLD-selected monitored element {monitored_element_id!r} is not an active, "
                    "fully connected Line, Cable, or Transformer bridging the CT's current "
                    "switch-connected primary terminal zones."
                )
            candidates = [(monitored_element_id, *selected)]
        else:
            candidates = [
                (branch_id, branch, from_bus, to_bus, p1_is_from)
                for branch_id, (branch, from_bus, to_bus, p1_is_from) in branches.items()
            ]
            if not candidates:
                raise CTMeasurementAssociationError(
                    f"CT {ct_id!r} does not resolve to an active branch bridging its two "
                    "switch-connected primary terminal zones. Configure the monitored element "
                    "on the CT's SLD node and verify its electrical connections."
                )
            if len(candidates) > 1:
                candidate_ids = tuple(sorted(item[0] for item in candidates))
                raise CTMeasurementAssociationAmbiguousError(
                    f"CT {ct_id!r} matches multiple parallel branches {candidate_ids!r}; "
                    "select the monitored element on the CT's SLD node."
                )

        branch_id, branch, from_bus, to_bus, p1_is_from = candidates[0]
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
    def _switch_components(snapshot: Any) -> dict[str, frozenset[str]]:
        """Return Bus components formed only by currently conductive switches.

        TopologySnapshot.conductive_edges deliberately contains switching
        boundaries, not numerical Line/Cable/Transformer branches. Using only
        these edges allows CT placement on either side of closed switching
        equipment without accidentally traversing another protected branch.
        """
        adjacency: dict[str, set[str]] = {
            str(bus_id): set() for bus_id in snapshot.bus_ids
        }
        for edge in snapshot.conductive_edges:
            first = str(edge.from_bus_id)
            second = str(edge.to_bus_id)
            if first in adjacency and second in adjacency and first != second:
                adjacency[first].add(second)
                adjacency[second].add(first)

        components: dict[str, frozenset[str]] = {}
        unseen = set(adjacency)
        while unseen:
            start = min(unseen)
            component = {start}
            queue = [start]
            unseen.remove(start)
            while queue:
                current = queue.pop(0)
                for neighbour in sorted(adjacency[current]):
                    if neighbour in unseen:
                        unseen.remove(neighbour)
                        component.add(neighbour)
                        queue.append(neighbour)
            frozen = frozenset(component)
            for bus_id in component:
                components[bus_id] = frozen
        return components


__all__ = [
    "CTMeasurementAssociation",
    "CTMeasurementAssociationAmbiguousError",
    "CTMeasurementAssociationError",
    "CTMeasurementAssociationResolver",
]
