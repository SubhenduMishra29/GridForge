# GridForge V2 — Batch 26.2 Static Correction Report
# Author: Subhendu Mishra

## Authority
- Repository: pandaraseswari03-collab/GridForge
- Branch: main
- Verification: static/source inspection only
- Runtime verification: deferred

## Confirmed defects and corrections

### 1. Property/editor/list contrast
Root cause: the stylesheet reused the white SLD canvas_background token for text-input and list/table surfaces while retaining light text_primary.

Correction: added semantic editor_background, editor_foreground, editor_border, table_background, and table_alternate_background tokens. Text inputs, combo boxes, spin/date/time controls, lists, and tables now use contrasting engineering surfaces. The SLD canvas remains independently white.

### 2. Element List integration
ElementListPanelWidget now binds to the existing SelectionManager. ElementListProjection remains the authoritative read-model projection for rows. Row selection drives the canonical selection authority and projected selection is reflected back into the table.

### 3. Messages / Events integration
MessagesPanelWidget previously had presentation methods but no semantic Application-event projection, while ValidationProjection could overwrite panel contents.

Correction: added ApplicationEventMessagesProjection through the existing UIProjectionCoordinator/UIUpdateBoundary. MessagesPanelWidget maintains independent validation and event streams. No second event bus was introduced.

### 4. SLD lifecycle/persistence audit
The current renderer uses incremental reconciliation: unchanged realized objects are retained, missing snapshot objects are removed, and ordinary synchronization does not call scene.clear(). The Application pre-commit path creates persistent SLD companions for committed Core equipment/connections, and tool switching is separated from SLD document lifecycle.

The required persistent lifecycle is statically supported. The actual manual Bus → Transformer → Breaker → Wire GUI sequence remains runtime-deferred.

### 5. Editing surface
Added real toolbar actions for Box Select, Move, Drag Move, Rotate, Mirror Horizontal, and Mirror Vertical. Selection/move routes through the existing Select tool. Rotate/mirror update persisted renderer-neutral symbol presentation through Application.execute(SetSLDNodePresentationCommand(...)); no QGraphicsItem state is persisted.

### 6. Workspace geometry
WorkspaceRealizer now applies comfortable initial dock proportions through the MainWindow host while preserving QDockWidget user resizing.

### 7. Control workspace
ControlWorkspace now uses a user-resizable horizontal splitter with bounded palette/inspector widths and a dominant ladder viewport. ControlCanvas establishes a meaningful scene rectangle, ladder rails, rung geometry, and initial ladder fitting.

The Control palette now exposes additional categorized timer, XOR, memory, coil, and interlock entries where the existing Application capability contract supports them.

## Architecture integrity
Static review confirms:
- one CommandManager;
- one canonical SelectionManager;
- one SLDDocument authority;
- one Application event bus;
- one SLD canvas projection/render system;
- no QGraphicsItem persistence;
- no direct UI → Core mutation path introduced;
- no second EquipmentRegistry or SymbolRegistry introduced.

## Changed files
- main.py
- ui/styling/style_tokens.py
- ui/styling/stylesheet.qss
- ui/panels/element_list_panel.py
- ui/panels/messages_panel.py
- ui/projection/validation_projection.py
- ui/projection/application_event_messages.py
- ui/canvas/control_canvas.py
- ui/control/control_workspace.py
- ui/control/control_tool_palette.py
- ui/items/equipment_item.py
- ui/canvas/sld_graphics_item_factory.py
- ui/plugins/toolbar_plugin.py
- ui/main_window.py
- ui/workspace/workspace_realizer.py
- audit/MASTER_AUDIT_REGISTER.csv

## Master Register
- GF-MASTER-0040 — evidence reconciled; runtime deferred.
- GF-MASTER-0042 — evidence reconciled; runtime deferred.
- GF-MASTER-0103 — evidence reconciled; runtime deferred.
- GF-MASTER-0104 — evidence reconciled; runtime deferred.
- GF-MASTER-0105 — evidence reconciled; runtime deferred.
- GF-MASTER-0110 — STATICALLY CORRECTED; runtime deferred.

## Remaining open items
1. Manual runtime verification of Bus → Transformer → Breaker → Wire persistence.
2. Manual verification of toolbar editing actions.
3. Manual verification of Element List ↔ canvas ↔ Properties selection synchronization.
4. Manual verification that semantic Application events populate Messages / Events without duplicate subscriptions.
5. Manual verification of dock proportions and workspace switching.
6. Manual verification of Control ladder geometry, palette operations, inspector updates, zoom/pan, and workspace return.

No runtime closure is claimed.
