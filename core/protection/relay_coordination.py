```python
"""
GridForge Relay Coordination
============================

Purpose
-------
Provides protection-relay coordination at the protection-system
orchestration level.

Responsibilities
----------------
This module:

    - builds a read-only protection topology view
    - determines source-to-bus topological depth
    - orders relays for coordination
    - applies explicitly supplied relay settings
    - establishes distance-relay zone reaches
    - establishes coordination/grading margins
    - validates relay coordination data

This module does NOT:

    - calculate fault current
    - perform load flow
    - calculate relay pickup from arbitrary topology distance
    - calculate TMS from arbitrary topology distance
    - build Ybus
    - modify the authoritative Network topology
    - operate breakers

Architecture
------------

    Network
       |
       v
    RelayCoordinator
       |
       +--> topology ordering
       |
       +--> explicit overcurrent settings
       |
       +--> distance-zone settings
       |
       v
    ProtectionSystem

Electrical calculations required for determining actual protection
settings belong to the appropriate analysis/solver layer.

The coordinator applies and validates those settings; it does not
invent them from graph distance.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import isfinite
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =====================================================================
# DEFAULTS
# =====================================================================

DEFAULT_ZONE1_REACH = 0.80
DEFAULT_ZONE2_REACH = 1.20
DEFAULT_GRADING_MARGIN = 0.30


# =====================================================================
# COORDINATION SETTINGS
# =====================================================================


@dataclass(frozen=True)
class OvercurrentSettings:
    """
    Explicit overcurrent-relay settings.

    Parameters
    ----------
    pickup:
        Relay pickup setting in the relay's configured current
        convention.

    TMS:
        Time Multiplier Setting.

    Notes
    -----
    These values must come from an engineering setting calculation
    or an explicitly supplied protection study. They are deliberately
    not derived from graph distance.
    """

    pickup: float
    TMS: float

    def __post_init__(self) -> None:
        pickup = float(self.pickup)
        tms = float(self.TMS)

        if not isfinite(pickup) or pickup <= 0.0:
            raise ValueError(
                "Overcurrent pickup must be finite and greater than zero."
            )

        if not isfinite(tms) or tms < 0.0:
            raise ValueError(
                "Overcurrent TMS must be finite and non-negative."
            )


@dataclass(frozen=True)
class DistanceSettings:
    """
    Explicit distance-relay zone settings.

    Zone reaches are expressed as multiples of the protected-line
    impedance.

    Parameters
    ----------
    zone1_reach:
        Zone-1 reach multiplier.

    zone2_reach:
        Zone-2 reach multiplier.

    zone2_delay:
        Zone-2 backup delay in seconds.

    grading_margin:
        Required coordination/grading margin in seconds.
    """

    zone1_reach: float = DEFAULT_ZONE1_REACH
    zone2_reach: float = DEFAULT_ZONE2_REACH
    zone2_delay: float = DEFAULT_GRADING_MARGIN
    grading_margin: float = DEFAULT_GRADING_MARGIN

    def __post_init__(self) -> None:
        values = (
            self.zone1_reach,
            self.zone2_reach,
            self.zone2_delay,
            self.grading_margin,
        )

        if not all(isfinite(float(value)) for value in values):
            raise ValueError(
                "Distance settings must contain finite values."
            )

        if self.zone1_reach <= 0.0:
            raise ValueError(
                "Zone-1 reach must be greater than zero."
            )

        if self.zone2_reach <= self.zone1_reach:
            raise ValueError(
                "Zone-2 reach must be greater than Zone-1 reach."
            )

        if self.zone2_delay < 0.0:
            raise ValueError(
                "Zone-2 delay cannot be negative."
            )

        if self.grading_margin < 0.0:
            raise ValueError(
                "Grading margin cannot be negative."
            )


# =====================================================================
# RELAY COORDINATOR
# =====================================================================


class RelayCoordinator:
    """
    Coordinate protection relays without modifying network topology.

    The coordinator uses network topology only to determine
    coordination order/depth.

    Electrical relay settings must be explicitly supplied.
    """

    def __init__(
        self,
        network: Any,
        *,
        grading_margin: float = DEFAULT_GRADING_MARGIN,
    ) -> None:
        self.network = network

        try:
            grading_margin = float(grading_margin)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "grading_margin must be numeric."
            ) from exc

        if not isfinite(grading_margin):
            raise ValueError(
                "grading_margin must be finite."
            )

        if grading_margin < 0.0:
            raise ValueError(
                "grading_margin cannot be negative."
            )

        self.grading_margin = grading_margin

    # =================================================================
    # TOPOLOGY
    # =================================================================

    def _build_adjacency(
        self,
    ) -> Dict[Any, List[Tuple[Any, Any]]]:
        """
        Build a read-only bus adjacency representation.

        Lines are treated as undirected for topology traversal.

        No Network state is modified.
        """

        adjacency: Dict[
            Any,
            List[Tuple[Any, Any]]
        ] = {}

        for line in self.network.lines:

            if not getattr(
                line,
                "in_service",
                True,
            ):
                continue

            from_bus = line.from_bus
            to_bus = line.to_bus

            if from_bus is None or to_bus is None:
                continue

            i = from_bus.id
            j = to_bus.id

            adjacency.setdefault(
                i,
                [],
            ).append(
                (j, line)
            )

            adjacency.setdefault(
                j,
                [],
            ).append(
                (i, line)
            )

        # Transformers also represent network connectivity.
        for transformer in getattr(
            self.network,
            "transformers",
            [],
        ):

            if not getattr(
                transformer,
                "in_service",
                True,
            ):
                continue

            from_bus = getattr(
                transformer,
                "from_bus",
                None,
            )

            to_bus = getattr(
                transformer,
                "to_bus",
                None,
            )

            if from_bus is None or to_bus is None:
                continue

            i = from_bus.id
            j = to_bus.id

            adjacency.setdefault(
                i,
                [],
            ).append(
                (j, transformer)
            )

            adjacency.setdefault(
                j,
                [],
            ).append(
                (i, transformer)
            )

        return adjacency

    # =================================================================
    # SOURCE DISTANCE
    # =================================================================

    def _distance_from_generators(
        self,
    ) -> Dict[Any, float]:
        """
        Determine topological depth from generator buses.

        This value is used ONLY for ordering and topology analysis.

        It must never be interpreted as electrical impedance,
        fault-current severity, relay pickup, or TMS.
        """

        adjacency = self._build_adjacency()

        distances: Dict[Any, float] = {
            bus.id: float("inf")
            for bus in self.network.buses
        }

        queue: deque[Any] = deque()

        for generator in self.network.generators:

            if not getattr(
                generator,
                "in_service",
                True,
            ):
                continue

            bus = getattr(
                generator,
                "bus",
                None,
            )

            if bus is None:
                continue

            bus_id = bus.id

            if distances.get(
                bus_id,
                float("inf"),
            ) != 0:

                distances[bus_id] = 0
                queue.append(bus_id)

        while queue:

            current = queue.popleft()

            current_distance = distances[
                current
            ]

            for neighbour, _ in adjacency.get(
                current,
                [],
            ):

                new_distance = (
                    current_distance + 1
                )

                if (
                    neighbour not in distances
                    or new_distance < distances[neighbour]
                ):
                    distances[neighbour] = new_distance
                    queue.append(neighbour)

        return distances

    # =================================================================
    # RELAY ORDERING
    # =================================================================

    def order_overcurrent_relays(
        self,
        protection_system: Any,
    ) -> List[Any]:
        """
        Return overcurrent relays ordered from electrically/topologically
        downstream toward source-side relays.

        Topological depth is used only as an ordering aid.

        No relay settings are changed.
        """

        distances = self._distance_from_generators()

        relays = list(
            getattr(
                protection_system,
                "oc_relays",
                [],
            )
        )

        def relay_depth(relay: Any) -> float:

            line = getattr(
                relay,
                "line",
                None,
            )

            if line is None:
                return float("inf")

            to_bus = getattr(
                line,
                "to_bus",
                None,
            )

            if to_bus is None:
                return float("inf")

            return distances.get(
                to_bus.id,
                float("inf"),
            )

        return sorted(
            relays,
            key=relay_depth,
            reverse=True,
        )

    # =================================================================
    # OVERCURRENT COORDINATION
    # =================================================================

    def coordinate_overcurrent(
        self,
        protection_system: Any,
        settings: Optional[
            Dict[Any, OvercurrentSettings]
        ] = None,
    ) -> List[Any]:
        """
        Apply explicitly supplied overcurrent settings.

        Parameters
        ----------
        protection_system:
            GridForge protection system.

        settings:
            Mapping:

                relay_id -> OvercurrentSettings

        Returns
        -------
        list
            Relays in downstream-to-source coordination order.

        Important
        ---------
        Pickup and TMS are NOT calculated from graph distance.

        If settings are omitted, this method performs ordering only
        and leaves existing relay settings unchanged.
        """

        relays = self.order_overcurrent_relays(
            protection_system
        )

        if settings is None:
            return relays

        for relay in relays:

            relay_id = getattr(
                relay,
                "id",
                None,
            )

            relay_settings = settings.get(
                relay_id
            )

            if relay_settings is None:
                continue

            if not isinstance(
                relay_settings,
                OvercurrentSettings,
            ):
                raise TypeError(
                    "Overcurrent settings for relay "
                    f"{relay_id!r} must be an "
                    "OvercurrentSettings instance."
                )

            relay.pickup = (
                relay_settings.pickup
            )

            relay.TMS = (
                relay_settings.TMS
            )

        return relays

    # =================================================================
    # DISTANCE COORDINATION
    # =================================================================

    def coordinate_distance(
        self,
        protection_system: Any,
        settings: Optional[
            Dict[Any, DistanceSettings]
        ] = None,
    ) -> List[Any]:
        """
        Configure distance-relay zones.

        If explicit settings are supplied, they are applied to the
        corresponding relays.

        Otherwise the engineering defaults are used:

            Zone 1 = 80% of protected-line impedance
            Zone 2 = 120% of protected-line impedance

        Zone-2 delay uses the coordinator grading margin.

        This method assumes relay line impedance is available in
        per-unit as:

            relay.line.r_pu
            relay.line.x_pu
        """

        relays = list(
            getattr(
                protection_system,
                "distance_relays",
                [],
            )
        )

        for relay in relays:

            relay_id = getattr(
                relay,
                "id",
                None,
            )

            if settings is not None:
                relay_settings = settings.get(
                    relay_id
                )

                if relay_settings is None:
                    relay_settings = DistanceSettings(
                        grading_margin=self.grading_margin,
                        zone2_delay=self.grading_margin,
                    )

                if not isinstance(
                    relay_settings,
                    DistanceSettings,
                ):
                    raise TypeError(
                        "Distance settings for relay "
                        f"{relay_id!r} must be a "
                        "DistanceSettings instance."
                    )
            else:
                relay_settings = DistanceSettings(
                    grading_margin=self.grading_margin,
                    zone2_delay=self.grading_margin,
                )

            line = getattr(
                relay,
                "line",
                None,
            )

            if line is None:
                raise ValueError(
                    f"Distance relay {relay_id!r} "
                    "has no associated line."
                )

            try:
                r_pu = float(line.r_pu)
                x_pu = float(line.x_pu)
            except (
                AttributeError,
                TypeError,
                ValueError,
            ) as exc:
                raise ValueError(
                    f"Distance relay {relay_id!r} "
                    "requires line r_pu and x_pu."
                ) from exc

            line_impedance = complex(
                r_pu,
                x_pu,
            )

            relay.Z1 = (
                relay_settings.zone1_reach
                * line_impedance
            )

            relay.Z2 = (
                relay_settings.zone2_reach
                * line_impedance
            )

            relay.delay_zone2 = (
                relay_settings.zone2_delay
            )

            relay.grading_margin = (
                relay_settings.grading_margin
            )

        return relays

    # =================================================================
    # GLOBAL COORDINATION
    # =================================================================

    def run(
        self,
        protection_system: Any,
        *,
        overcurrent_settings: Optional[
            Dict[Any, OvercurrentSettings]
        ] = None,
        distance_settings: Optional[
            Dict[Any, DistanceSettings]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Execute the protection coordination workflow.

        The workflow:

            1. determine topology-based relay ordering
            2. apply explicit overcurrent settings
            3. configure distance zones
            4. return coordination information

        No Network topology is modified.
        """

        overcurrent_relays = (
            self.coordinate_overcurrent(
                protection_system,
                settings=overcurrent_settings,
            )
        )

        distance_relays = (
            self.coordinate_distance(
                protection_system,
                settings=distance_settings,
            )
        )

        return {
            "overcurrent_relays": [
                getattr(
                    relay,
                    "id",
                    None,
                )
                for relay in overcurrent_relays
            ],
            "distance_relays": [
                getattr(
                    relay,
                    "id",
                    None,
                )
                for relay in distance_relays
            ],
            "grading_margin": self.grading_margin,
        }


__all__ = [
    "RelayCoordinator",
    "OvercurrentSettings",
    "DistanceSettings",
    "DEFAULT_ZONE1_REACH",
    "DEFAULT_ZONE2_REACH",
    "DEFAULT_GRADING_MARGIN",
]
```
