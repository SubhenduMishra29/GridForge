```python
"""
GridForge Relay Coordination
============================

File:
    core/protection/relay_coordination.py

Purpose
-------
Coordinates protection algorithms operating on the authoritative
GridForge Relay models.

The Relay model is defined in:

    core/model/relay.py

The model layer is frozen and therefore this module adapts to its
existing API.

Responsibilities
----------------
- Build a read-only protection topology view.
- Determine source-to-bus topological depth.
- Order relays for coordination.
- Apply valid model-level relay settings.
- Store protection-specific coordination settings externally.
- Configure distance protection algorithm settings.
- Provide coordination results.

This module does NOT:
- Modify network topology.
- Build Ybus.
- Perform load flow.
- Perform short-circuit calculations.
- Calculate fault current.
- Operate circuit breakers.
- Invent overcurrent pickup/TMS values from topology distance.
- Add attributes to the frozen Relay model.

Architecture
------------

    core/model/relay.py
             |
             | authoritative Relay
             v
    RelayCoordinator
             |
       +-----+------+
       |            |
       v            v
 Overcurrent     Distance
 coordination   coordination
       |            |
       +-----+------+
             |
             v
    ProtectionSystem
             |
             v
      BreakerManager

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import isfinite
from typing import Any, Dict, List, Optional, Tuple


# =====================================================================
# DEFAULTS
# =====================================================================

DEFAULT_ZONE1_REACH = 0.80
DEFAULT_ZONE2_REACH = 1.20
DEFAULT_GRADING_MARGIN = 0.30


# =====================================================================
# PROTECTION-SPECIFIC SETTINGS
# =====================================================================


@dataclass(frozen=True)
class OvercurrentSettings:
    """
    Protection-layer overcurrent coordination settings.

    Parameters
    ----------
    pickup:
        Relay pickup setting in the relay's configured current
        convention.

    TMS:
        Time Multiplier Setting.

    Notes
    -----
    These settings are NOT derived from topology distance.

    They must come from an engineering coordination calculation
    or be explicitly supplied by the user/study.
    """

    pickup: float
    TMS: float

    def __post_init__(self) -> None:

        pickup = float(self.pickup)
        tms = float(self.TMS)

        if not isfinite(pickup) or pickup < 0.0:
            raise ValueError(
                "Overcurrent pickup must be finite and >= 0."
            )

        if not isfinite(tms) or tms < 0.0:
            raise ValueError(
                "Overcurrent TMS must be finite and >= 0."
            )


@dataclass(frozen=True)
class DistanceSettings:
    """
    Protection-layer distance coordination settings.

    Zone reaches are expressed as multiples of the protected
    line impedance.

    Parameters
    ----------
    zone1_reach:
        Zone-1 impedance reach multiplier.

    zone2_reach:
        Zone-2 impedance reach multiplier.

    zone2_delay:
        Zone-2 operating delay in seconds.

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

        if not all(
            isfinite(float(value))
            for value in values
        ):
            raise ValueError(
                "Distance settings must be finite."
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
    Protection relay coordination service.

    The coordinator works with the frozen Network and Relay model
    interfaces without modifying their structure.

    Protection-specific settings such as TMS and distance zones are
    maintained by this layer rather than injected into the frozen
    Relay model.
    """

    def __init__(
        self,
        network: Any,
        *,
        grading_margin: float = DEFAULT_GRADING_MARGIN,
    ) -> None:

        if network is None:
            raise ValueError(
                "network cannot be None."
            )

        self.network = network

        try:
            grading_margin = float(
                grading_margin
            )
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

        # -------------------------------------------------------------
        # Protection-layer settings.
        #
        # These dictionaries deliberately do not modify the frozen
        # core/model/relay.py API.
        # -------------------------------------------------------------

        self.overcurrent_settings: Dict[
            Any,
            OvercurrentSettings,
        ] = {}

        self.distance_settings: Dict[
            Any,
            DistanceSettings,
        ] = {}

    # =================================================================
    # TOPOLOGY
    # =================================================================

    def _build_adjacency(
        self,
    ) -> Dict[
        Any,
        List[Tuple[Any, Any]],
    ]:
        """
        Build a read-only bus adjacency map.

        Lines and transformers are treated as topology connections.

        The authoritative Network is never modified.
        """

        adjacency: Dict[
            Any,
            List[Tuple[Any, Any]],
        ] = {}

        # -------------------------------------------------------------
        # Lines
        # -------------------------------------------------------------

        for line in getattr(
            self.network,
            "lines",
            [],
        ):

            if not getattr(
                line,
                "in_service",
                True,
            ):
                continue

            from_bus = getattr(
                line,
                "from_bus",
                None,
            )

            to_bus = getattr(
                line,
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
                (j, line)
            )

            adjacency.setdefault(
                j,
                [],
            ).append(
                (i, line)
            )

        # -------------------------------------------------------------
        # Transformers
        # -------------------------------------------------------------

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
        Calculate topological depth from generator buses.

        This is a graph metric only.

        It MUST NOT be interpreted as:
            - electrical distance
            - impedance
            - fault-current severity
            - pickup setting
            - TMS
        """

        adjacency = self._build_adjacency()

        distances: Dict[
            Any,
            float,
        ] = {
            bus.id: float("inf")
            for bus in getattr(
                self.network,
                "buses",
                [],
            )
        }

        queue: deque[Any] = deque()

        for generator in getattr(
            self.network,
            "generators",
            [],
        ):

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
            ) != 0.0:

                distances[bus_id] = 0.0
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
                    current_distance + 1.0
                )

                if (
                    neighbour not in distances
                    or new_distance < distances[neighbour]
                ):

                    distances[neighbour] = (
                        new_distance
                    )

                    queue.append(
                        neighbour
                    )

        return distances

    # =================================================================
    # OVERCURRENT ORDERING
    # =================================================================

    def order_overcurrent_relays(
        self,
        protection_system: Any,
    ) -> List[Any]:
        """
        Order overcurrent relay algorithms from downstream toward
        source.

        Topological depth is used only for ordering.
        """

        distances = (
            self._distance_from_generators()
        )

        relays = list(
            getattr(
                protection_system,
                "oc_relays",
                [],
            )
        )

        def depth(
            relay_algorithm: Any,
        ) -> float:

            relay = getattr(
                relay_algorithm,
                "relay",
                relay_algorithm,
            )

            line = getattr(
                relay_algorithm,
                "line",
                getattr(
                    relay,
                    "line",
                    None,
                ),
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
            key=depth,
            reverse=True,
        )

    # =================================================================
    # OVERCURRENT SETTINGS
    # =================================================================

    def set_overcurrent_settings(
        self,
        relay: Any,
        settings: OvercurrentSettings,
    ) -> None:
        """
        Register protection-layer overcurrent settings.

        The frozen Relay model receives only its supported pickup
        setting through set_pickup().

        TMS remains in the protection layer.
        """

        if not isinstance(
            settings,
            OvercurrentSettings,
        ):
            raise TypeError(
                "settings must be an "
                "OvercurrentSettings instance."
            )

        relay_model = getattr(
            relay,
            "relay",
            relay,
        )

        relay_model.set_pickup(
            settings.pickup
        )

        relay_id = relay_model.id

        self.overcurrent_settings[
            relay_id
        ] = settings

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
        Coordinate overcurrent relays.

        If settings are supplied, they are explicitly applied.

        No pickup or TMS value is derived from graph distance.
        """

        if settings is not None:

            for relay_id, relay_settings in (
                settings.items()
            ):

                if not isinstance(
                    relay_settings,
                    OvercurrentSettings,
                ):
                    raise TypeError(
                        "Overcurrent settings for relay "
                        f"{relay_id!r} must be an "
                        "OvercurrentSettings instance."
                    )

        relays = (
            self.order_overcurrent_relays(
                protection_system
            )
        )

        if settings is not None:

            for relay_algorithm in relays:

                relay_model = getattr(
                    relay_algorithm,
                    "relay",
                    relay_algorithm,
                )

                relay_id = relay_model.id

                relay_settings = settings.get(
                    relay_id
                )

                if relay_settings is None:
                    continue

                self.set_overcurrent_settings(
                    relay_algorithm,
                    relay_settings,
                )

        return relays

    # =================================================================
    # DISTANCE SETTINGS
    # =================================================================

    def set_distance_settings(
        self,
        relay: Any,
        settings: DistanceSettings,
    ) -> None:
        """
        Register distance-protection settings.

        Distance-zone settings remain in the protection layer and
        are not injected into the frozen Relay model.
        """

        if not isinstance(
            settings,
            DistanceSettings,
        ):
            raise TypeError(
                "settings must be a "
                "DistanceSettings instance."
            )

        relay_model = getattr(
            relay,
            "relay",
            relay,
        )

        self.distance_settings[
            relay_model.id
        ] = settings

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
        Configure distance-protection coordination settings.

        The protected-line impedance is obtained from the associated
        line model.

        Zone settings remain external to the frozen Relay model.
        """

        relays = list(
            getattr(
                protection_system,
                "distance_relays",
                [],
            )
        )

        for relay_algorithm in relays:

            relay_model = getattr(
                relay_algorithm,
                "relay",
                relay_algorithm,
            )

            relay_id = relay_model.id

            relay_settings = None

            if settings is not None:
                relay_settings = settings.get(
                    relay_id
                )

            if relay_settings is None:

                relay_settings = (
                    self.distance_settings.get(
                        relay_id
                    )
                )

            if relay_settings is None:

                relay_settings = DistanceSettings(
                    zone1_reach=DEFAULT_ZONE1_REACH,
                    zone2_reach=DEFAULT_ZONE2_REACH,
                    zone2_delay=self.grading_margin,
                    grading_margin=self.grading_margin,
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

            self.distance_settings[
                relay_id
            ] = relay_settings

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
        Execute the complete relay coordination workflow.

        Returns
        -------
        dict
            Coordination information and registered settings.

        Notes
        -----
        The authoritative Network topology is never modified.
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
                    getattr(
                        relay,
                        "relay",
                        relay,
                    ),
                    "id",
                    None,
                )
                for relay in overcurrent_relays
            ],
            "distance_relays": [
                getattr(
                    getattr(
                        relay,
                        "relay",
                        relay,
                    ),
                    "id",
                    None,
                )
                for relay in distance_relays
            ],
            "grading_margin": self.grading_margin,
            "overcurrent_settings": dict(
                self.overcurrent_settings
            ),
            "distance_settings": dict(
                self.distance_settings
            ),
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
