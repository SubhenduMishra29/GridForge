# GF-AUD-170 — canonical detached transient switching-target validation

Date: 2026-11-06

## Finding
Transient breaker events could schedule an unknown ID. At execution, `TransientEventState.set_breaker()` used `dict.get()` and then inserted the unknown ID into mutable event state. The detached network solver iterates only the immutable captured switch registry, so the event could be reported as executed without changing a modeled switch.

## Correction
- Add one Core detached-state validator for canonical switch identity. A target must exist in all three captured registries: `switch_connections`, `breaker_states`, and `switch_available_states`.
- Validate any explicitly affected branch/transformer/shunt IDs against the detached snapshot and require their terminal Bus set to be incident to at least one of the target switch's captured endpoint Buses. Duplicate, non-canonical, unknown or topologically unrelated IDs are rejected.
- `TransientEventState.set_breaker()` repeats this validation before reading/mutating state. It rejects non-bool state requests and returns target Bus IDs and affected equipment identities in the transition record.
- Both breaker-open and breaker-close schedulers validate before registering an event and include canonical target Bus IDs in event metadata.
- Application transient event configuration delegates to the same Core validator instead of maintaining a weaker parallel known-equipment check.
- Generic equipment-state events also validate their target against the captured equipment/switch registries and require an explicit bool; unknown targets cannot add new dictionary keys.
- Unknown or invalid targets therefore fail before state mutation, topology-revision advancement or event registration.

## Scope
The change preserves detached study ownership. No live Network mutation, Core/UI dependency, plugin dependency, or second switching registry is introduced. Protection/Control-generated transient switching adapters that call the shared `TransientEventState.set_breaker()` boundary inherit the same target guard.

## Verification boundary
Static source/diff inspection only. No tests, CI, syntax/import execution or transient solver runtime experiment performed.

## Register handling
The full authoritative `Modification_Register.txt` could not be retrieved safely through the available GitHub file interface. It was not overwritten or truncated; this audit note is supplementary.
