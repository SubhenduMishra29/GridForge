# GridForge V2 — Creation Selection / Read-Type Contract Remediation

**Repository:** pandaraseswari03-collab/GridForge  
**Branch:** main  
**Author:** Subhendu Mishra  
**Verification:** static source inspection only; no pytest, CI, startup, GUI, or runtime execution.

## GF-TRACE-001 — Application/Core element-type vocabulary mismatch

Read-model collections use plural presentation names such as buses, while the Core registry uses singular canonical types such as bus. The Application read boundary now explicitly maps read-model vocabulary to Core vocabulary through _CORE_ELEMENT_TYPES before Network.get_by_id(). The returned ElementReadModel retains the Application read-model type.

This preserves one authoritative Core registry vocabulary and does not add plural aliases to Core.

## GF-TRACE-002 — Creation session remained active after committed placement

Placement previously executed the command, synchronously triggered selection projection, and only then completed CreationContext. A selection/read failure could therefore leave an already-created object paired with an active creation draft.

ModelPlacementTool and BusTool now execute the command, capture the created identity, complete CreationContext, clear transient tool state, and only then perform optional selection projection.

## Corrected call chains

SelectionManager → SelectionProjectionCoordinator → Application.read_network() → read-model element_type → Application.read_element() → NetworkReadService.element() → _CORE_ELEMENT_TYPES → Network.get_by_id(singular Core type) → NetworkRegistry

Placement Tool → Application.execute(command) → committed Core object → CreationContext.complete() → clear transient tool state → SelectionManager.select_single()

## Architecture preservation

No UI/Core direct mutation was introduced. No second CommandManager, registry, topology authority, or selection authority was introduced. Core remains the authoritative electrical/domain model and registry.

## Verification boundary

Static source tracing confirms the corrected contracts. Runtime GUI behavior, selection rendering, repeated placement, and startup remain runtime verification items and are not claimed as closed by this document.
