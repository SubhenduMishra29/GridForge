# Core Topology

## Authoritative package ownership

This directory is a documentation-only placeholder; it contains no topology implementation and is not a Python package facade.

The authoritative topology and connectivity implementation belongs to **`core.network`**:

- `core/network/topology.py` — `TopologyManager` and Network-owned topology lifecycle.
- `core/network/connectivity.py` — canonical Simple Wire connectivity resolution and storage.
- `core/network/topology_endpoint_reference.py` — typed endpoint references used while resolving topology.
- `core/network/topology_snapshot.py` — immutable derived topology snapshot and provenance.
- `core/network/electrical_boundary.py` — electrical boundary and endpoint compatibility policy.

The `Network` facade coordinates topology rebuild/invalidation. Application owns commands and transactions that request engineering mutations; Core Network derives connectivity from canonical model relationships and operating state.

## Explicitly separate representations

- Conventional Simple Wire connectivity is owned by `core.network.connectivity`.
- Phase-domain physical conductor topology is represented by `core.network.phase_domain_conductor_network` and `core.network.physical_conductor_topology`. It is a separate study/physical representation, not a replacement for Simple Wire connectivity or SLD route geometry.
- CT measurement association contracts are exposed from `core.network.ct_measurement_association`; they do not create a second topology manager or make measurement-secondary terminals part of power-network connectivity.

Do not add a second `TopologyManager`, `ConnectivityResolver`, topology registry, graph store, or lifecycle under `core.topology`. New implementation belongs in the authoritative `core.network` package and must preserve the frozen Core/Application/UI boundaries.
