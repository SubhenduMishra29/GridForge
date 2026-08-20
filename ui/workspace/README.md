# GridForge V2 — Workspace Subsystem


## File Location


```text
ui/workspace/
Purpose

The Workspace subsystem provides the application-level organization of
documents, views and viewport state.

GridForge V2 is intended to provide an ETAP-style dockable workflow while
retaining a Blender-style flexible visual workspace.

The workspace therefore sits above the existing canvas subsystem.

Architectural Position
                    MainWindow
                        |
                        v
                   Workspace
                        |
             +----------+----------+
             |                     |
             v                     v
        Documents               Views
             |                     |
             v                     v
        SLDDocument          Canvas/View
                                   |
                                   v
                              ui/canvas/
Important Boundary

The workspace does not replace:

ui/canvas/

The canvas remains responsible for:

scene;
graphics view;
coordinate conversion;
navigation;
interaction;
preview;
rendering.

The workspace is responsible for:

which document is active;
which views are open;
which view displays which document;
viewport state persistence;
view lifecycle.
Document vs View

A document represents the logical content.

A view represents one visual presentation of that document.

Therefore:

Document A
    |
    +---- View 1
    |
    +---- View 2

is valid.

This is important for future:

multi-view workflows;
substation/grid navigation;
synchronized views;
comparison workflows;
multiple canvas layouts.
Viewport State

Viewport state is kept outside the Qt graphics view.

It can contain:

zoom;
center;
pan;
rotation;
grid visibility;
snap visibility.

The actual canvas implementation consumes this state.

Core Boundary

Workspace objects are UI/application objects.

They do not become the authoritative electrical model.

The intended architecture remains:

Workspace
    |
    v
SLD Document
    |
    v
UI SLD Model
    |
    v
Controller / Adapter
    |
    v
GridForge Core
