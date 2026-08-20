# GridForge V2 — Connection Subsystem


## File Location


```text
ui/connections/
Purpose

The connection subsystem owns the logical SLD connection workflow.

It establishes the boundary between:

equipment terminals;
connection candidates;
topology validation;
connection routing;
connection preview;
SLD connection state;
future Core topology synchronization.
Architectural Principle

A line drawn on the canvas is not automatically a valid electrical
connection.

The workflow is:

User interaction
      |
      v
Terminal resolution
      |
      v
Connection candidate
      |
      v
Topology validation
      |
      +---- invalid ----> reject / preview feedback
      |
      v
Connection creation
      |
      v
SLD connection model
      |
      v
Core synchronization boundary
Separation of Responsibilities
Connection

Stores the logical relationship between two terminals.

TerminalResolver

Determines which logical terminal corresponds to a spatial interaction.

ConnectionValidator

Determines whether a proposed connection is structurally valid.

ConnectionManager

Creates, removes and queries logical connections.

ConnectionRouter

Calculates the visual path between terminals.

ConnectionPreview

Stores temporary connection interaction state.

TopologyAdapter

Defines the boundary through which the UI can eventually synchronize
with the authoritative Core network topology.

Important Rule

The UI connection system must not become a second power-system solver.

It may validate UI-level constraints such as:

terminal existence;
duplicate connection;
self connection;
incompatible terminal roles;
connection multiplicity;
required connection direction.

Authoritative electrical-network rules remain in Core.

Rendering Boundary
Connection
     |
     v
ConnectionRouter
     |
     v
LineItem
     |
     v
LineRenderer
     |
     v
Canvas

The connection subsystem therefore does not draw anything.
