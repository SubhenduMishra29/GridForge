# GridForge V2 — Simple Wire Connectivity Remediation Register
Date: 2026-09-25
Branch: main
Status basis: static repository inspection only; tests and CI intentionally not run.

## Consolidation rule

The listed findings are reconciled against one implementation contract. No duplicate Network, CommandManager, history, connectivity authority, SLD connection model, or UI-owned engineering relationship was introduced.

## Finding status

| Finding | Status | Basis |
|---|---|---|
| GF-CONN-018 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-019 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-020 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-023 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-076 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-077 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-079 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-080 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-085 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-087 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-088 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-089 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-101 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-102 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-103 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-104 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-105 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-106 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-107 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-108 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-109 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-110 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-115 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-116 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-117 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-118 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-122 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-123 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-126 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-128 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-130 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-131 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-132 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-133 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-134 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-135 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-136 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-137 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-138 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-139 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-140 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-141 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-142 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-143 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-144 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-145 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-146 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-147 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-148 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-149 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-150 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-151 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-152 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-153 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-154 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-155 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-156 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-CONN-157 | STATICALLY VERIFIED | Consolidated Simple Wire authoritative relationship/connectivity contract |
| GF-UI-03-004 | STATICALLY VERIFIED | WireTool/SLD projection/selection-preview contract |
| GF-UI-03-016 | STATICALLY VERIFIED | WireTool/SLD projection/selection-preview contract |
| GF-UI-03-017 | STATICALLY VERIFIED | WireTool/SLD projection/selection-preview contract |
| GF-UI-03-018 | STATICALLY VERIFIED | WireTool/SLD projection/selection-preview contract |
| GF-PROT-042 | VERIFICATION DEFERRED | Canonical topology boundary is preserved, but protection-specific runtime verification was intentionally not run in this pass |
| GF-PROT-043 | VERIFICATION DEFERRED | Canonical topology boundary is preserved, but protection-specific runtime verification was intentionally not run in this pass |

## Static verification scope

Verified by source inspection:

1. Dedicated immutable SimpleWireConnection identity and terminal references.
2. Network-owned ConnectivityStore; no NetworkRegistry membership.
3. Duplicate/reversed-endpoint rejection and terminal compatibility/cardinality contract.
4. Terminal-reference resolution through resolve_terminal_reference(), including unconnected terminals.
5. Dedicated create/remove commands and CommandManager registration.
6. Existing transaction/history path, including stable relationship identity on redo.
7. NetworkState topology invalidation and topology revision integration.
8. ConnectivityResolver → TopologyManager derived topology boundary.
9. Existing resolve_terminal_bus() remains narrow; it was not converted into a graph walker.
10. Option-B equipment deletion rejection at Network mutation boundary.
11. Dedicated semantic relationship events and post-commit publication path.
12. Immutable Application SimpleWireReadModel.
13. project.json connectivity section, explicit schema versioning, backward-compatible missing-section load, and dangling-reference failure.
14. Load order restores relationships before topology rebuild.
15. Existing SLDConnection reused with authoritative connection_id traceability.
16. WireTool uses CreateSimpleWireConnectionCommand through Application.execute().
17. PreviewLayer is transient and cleared on completion/cancel/reset.
18. SLD selection/deletion routes committed Simple Wire selection through RemoveSimpleWireConnectionCommand and Application.execute().
19. Simple Wire inspector exposes relationship data and no line/cable engineering parameters.
20. Power Flow continues to consume numerical branch models; Simple Wire is not added to YBus.
21. Runtime testing, CI, Qt rendering, package reopen, and protection/dynamics runtime behavior were not executed in this pass.

## Important verification note

The repository did not contain a master connectivity register file matching the supplied finding IDs. This document is therefore the repository-local reconciliation/status record for the supplied register entries rather than a claim that an external register was edited.
