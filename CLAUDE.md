# GridForge V2 — Engineering Agent Instructions

## Product intent
GridForge is an engineering-grade power-system digital twin and engineering workspace, not a diagram editor with calculations attached. Preserve one authoritative electrical/project model and traceable engineering workflows. Improve the existing V2 architecture; do not introduce architecture churn or speculative abstractions.

## Authoritative source
- Repository: `SubhenduMishra29/GridForge`
- Integration baseline: `main`
- Start each task by fetching the latest `main`, reading the linked GitHub issue and checking related open/merged PRs.
- Do not treat stale branches, old audit notes, issue text or a PR's claims as proof of current implementation. Verify against current source.

## Frozen architecture
- **Core** owns electrical/domain truth: equipment, terminals, topology/connectivity, domain validation, studies, calculations and results.
- **Application** owns commands, services, transactions, lifecycle, controlled mutation, events and read models.
- **UI/SLD** owns projection, geometry, interaction and presentation.
- Canonical flow: UI → Controller → immutable Command → Application → Core → Event/Result → Application Read Model → Projection → UI.
- No Qt, QGraphicsItem, widgets, SLD scene or UI symbols in Core.
- Qt access is routed through `ui/core/qt.py`; update affected package `__init__.py` exports consistently.
- A symbol is not equipment. SLD geometry is not electrical topology. Draft state is not committed engineering state.
- Persistence is project-rooted: `.gridforge` ZIP, `manifest.json` for package/schema/version metadata, canonical `project.json` for supported project state. Never persist Qt runtime objects or live telemetry as project configuration.
- Preserve existing public contracts and canonical service ownership. Do not add parallel registries, command managers, event buses, topology, measurement systems or persistence authorities.

## Execution protocol
1. FETCH → AUDIT → RECONCILE → CORRECT → CHECK → FREEZE.
2. Read the issue, current source, related PRs, architecture docs and relevant entries in `Modification_Register.txt` before editing.
3. Record concrete evidence: exact paths, symbols, callers, data flow and reproduction/acceptance gap.
4. Define a narrow task boundary, dependencies, files expected to change and acceptance criteria before implementation.
5. Use one implementation owner per issue and explicit file ownership. Do not let parallel agents edit the same files.
6. Work on an isolated feature branch/worktree based on current `main`; never push implementation commits directly to `main`.
7. Reconcile with current `main` before PR creation. Avoid force-push, blind rebases and wholesale merging of heavily diverged branches.
8. Review the actual diff for architecture compliance, unintended files, duplicate implementations and package export consistency.
9. Update `Modification_Register.txt` append-only using a safe local full-file workflow. Never truncate or rewrite the historical register. If unavailable, add no substitute entry without explicit approval; report the limitation.
10. Keep the issue open until its stated acceptance evidence is satisfied. Do not claim runtime/GUI/save-reopen verification unless actually performed.

## User acceptance preferences
- Tests and CI are not acceptance gates unless explicitly requested. Do not represent them as mandatory blockers.
- Still inspect source carefully and perform appropriate static checks for syntax/import risks when feasible.
- For UI changes inspect relevant `ui/core/qt.py` compatibility and affected `__init__.py` exports.
- Avoid architecture redesign, unrelated cleanup, unrequested documentation and generated files.
- Preserve existing user work and inspect git status before mutation.

## Agent coordination
- Coordinator assigns exactly one implementation owner to each issue and records dependencies.
- Domain agents may produce read-only audits in parallel; implementation is serialized by file ownership.
- Integration/reviewer agents are read-only until asked to apply a specific accepted correction.
- Agents must not close issues, merge PRs, force-update branches or modify `main` without explicit user authorization.
- Report unresolved assumptions and unsupported engineering cases as unresolved; never fabricate ratings, settings, terminal assignments, signal semantics or physical paths.
