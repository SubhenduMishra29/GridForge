
# GridForge V2 — Dockable Panel Subsystem


## Location


```text
ui/panels/
Purpose

The panel subsystem provides the application-level architecture for
GridForge V2's dockable workspace.

The target workflow is:

+---------------------------------------------------------------+
| Menu / Toolbar                                                |
+----------+---------------------------------------+------------+
|          |                                       |            |
| Project  |                                       | Properties |
| Explorer |             SLD CANVAS                |            |
|          |                                       |            |
|          |                                       |            |
+----------+---------------------------------------+------------+
| Status / Diagnostics / Output                                 |
+---------------------------------------------------------------+

The central SLD canvas remains the primary visual workspace.

Panels surround and support the canvas.

Design Principles
1. SLD remains first-class

Panels must never become the primary representation of the electrical
network.

The canvas remains responsible for:

equipment symbols;
topology;
connections;
navigation;
selection;
snapping;
coordinates;
preview;
rendering.
2. Panels are independent

A panel should not directly reach into arbitrary Qt widgets.

Instead:

Panel
  |
  v
Controller / Manager
  |
  v
Application State
3. Panel state is separate from panel widgets

Visibility, docking position and activation state should not be stored
only inside Qt widgets.

4. Panel lifecycle is explicit
Registered
    |
    v
Created
    |
    v
Visible
    |
    v
Hidden
    |
    v
Destroyed
5. Core remains authoritative

Panels may display Core information, but they do not become the owner
of Core network state.

Planned V2 Panels

The architecture supports future panels such as:

Project Explorer
Equipment Browser
Properties
Inspector
Selection
Network Data
Layers
Navigator
Messages
Diagnostics
Command History
Results
Protection
Analysis

Not all panels need to be implemented immediately.

Qt Boundary

PanelBase describes the logical panel contract.

PanelInstance represents the runtime panel.

PanelArea describes where the panel belongs.

The actual Qt QDockWidget integration belongs to the composition/UI
layer.
