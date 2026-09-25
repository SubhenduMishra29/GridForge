# GridForge V2 — Simple Wire Connectivity Schema

## Version contract

- Package metadata (`.gridforge/manifest.json`): existing package version contract remains unchanged.
- Project schema: **2** for newly saved projects.
- Network serialization schema: **1**.
- `project.json.connectivity.schema`: **1**.
- Projects with project schema **1** and no `connectivity` section remain loadable; the missing section is interpreted as an empty authoritative relationship collection.
- A present but unsupported connectivity schema is a persistence error.
- SLD geometry is never a migration source for authoritative connectivity.

## Persisted shape

`project.json` contains `project`, `network`, `connectivity`, and the existing `measurement`, `dynamic_models`, `protection`, and `sld` sections as applicable.

The connectivity section is represented by an object containing `schema: 1` and a `simple_wires` array. Each entry contains `connection_id`, `kind: SIMPLE_WIRE`, and canonical terminal `endpoint_a` / `endpoint_b` references.

## Load ordering

Equipment is registered first, terminal endpoint state is restored next, then authoritative Simple Wire relationships are restored and validated, and only then is derived topology rebuilt and the project validated.

A dangling Simple Wire is a hard persistence-integrity failure. It is not silently discarded.

## Identity

`connection_id` is an independent persistent relationship identity. Endpoint order is normalized only for duplicate comparison; `A ↔ B` and `B ↔ A` represent the same relationship for duplicate detection, while the relationship's own identity remains stable across undo/redo and save/load.

## Presentation

SLD stores only a projection identified by the same `connection_id`. Connection geometry is presentation state and is not used to reconstruct the authoritative relationship.
