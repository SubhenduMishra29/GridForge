# GridForge V2 — Workspace Subsystem
Author: Subhendu Mishra

## Canonical composition

GridForge uses the canonical presentation path:

WorkspaceManager → WorkspaceDefinition / WorkspaceLayout → Area → Editor → Region → EditorContext → Discipline Tool System.

WorkspaceDefinition and WorkspaceLayout are Area-based and Qt-independent.
They do not contain panel/dock placement records.

## Responsibilities

Workspace owns active workspace identity, Area/Editor/Region composition,
presentation activation, focus/maximize state, and document/view presentation
lifecycle.

Editors own their Region composition. Regions are the architectural identity;
Qt widgets are their realization.

The canvas remains responsible for scene, graphics view, coordinate
conversion, navigation, interaction, preview and rendering.

## Legacy boundary

WorkspacePlacement is isolated in ui/workspace/workspace_legacy.py.
PanelArea, DockBinding and QDockWidget mechanics remain only for legacy utility
panels and are not workspace policy.

## Core boundary

Workspace objects are presentation/application objects. They never become the
authoritative electrical model.

Committed engineering operations continue through:

Workspace → EditorContext → Tool → Application Command → Application →
CommandManager → Core.
