# GridForge V2 — Equipment Subsystem


## File Location


```text
ui/equipment/
Purpose

The equipment subsystem defines the logical UI-side representation of electrical equipment used by the GridForge Single Line Diagram (SLD).

It provides the lifecycle boundary for SLD equipment:

Equipment Definition
        |
        v
Equipment Registry
        |
        v
Equipment Factory
        |
        v
Equipment Instance
        |
        +----------------+
        |                |
        v                v
EquipmentTerminal   EquipmentManager
        |
        v
Connection Subsystem

The subsystem is deliberately independent of Qt, rendering, and the authoritative GridForge Core electrical-network model.

Architectural Principle

An SLD equipment object is not a Qt graphics item.

The logical equipment model exists independently from its visual representation.

Logical Equipment
       |
       +---- identity
       +---- type
       +---- name
       +---- position
       +---- properties
       +---- terminal identities
       |
       v
UI Item / Renderer
       |
       v
Canvas

This separation allows equipment to participate in:

SLD serialization
selection
snapping
terminal resolution
connection routing
document/model management
canvas synchronization

without making the logical equipment object dependent on Qt.

Responsibilities

The equipment subsystem is responsible for:

defining available equipment types;
registering equipment definitions;
creating equipment instances;
maintaining runtime equipment instances;
maintaining stable equipment identities;
maintaining logical equipment positions;
maintaining equipment properties;
defining logical terminals;
maintaining stable terminal identities;
providing serialization data.

It is not responsible for:

rendering equipment symbols;
creating QGraphicsItem objects;
manipulating QGraphicsScene;
performing electrical calculations;
calculating Y-bus;
solving power flow;
validating full electrical topology;
owning Core network objects;
replacing the Core electrical model.
Components
EquipmentDefinition
ui/equipment/equipment_definition.py

Defines the metadata for an equipment type.

Examples:

transformer
breaker
generator
motor
bus
load
capacitor
reactor

A definition contains metadata such as:

equipment type;
display name;
terminal names;
symbol identifier;
default properties;
category.

Example:

EquipmentDefinition
    equipment_type = "transformer"
    display_name   = "Transformer"
    terminal_names = ("HV", "LV")
    symbol_id      = "transformer"

A definition describes a type. It is not an individual SLD object.

EquipmentRegistry
ui/equipment/equipment_registry.py

EquipmentRegistry owns the available equipment type definitions.

Its responsibilities are limited to:

registration;
duplicate detection;
lookup;
required lookup;
availability checks;
enumeration;
removal;
clearing.

Conceptually:

EquipmentDefinition
        |
        v
EquipmentRegistry
        |
        +---- Factory
        |
        +---- UI/tool menus

The registry does not own runtime equipment instances.

Runtime instances belong to EquipmentManager.

EquipmentFactory
ui/equipment/equipment_factory.py

EquipmentFactory creates UI-side equipment instances from registered definitions.

Its workflow is:

equipment_type
      |
      v
EquipmentRegistry
      |
      v
EquipmentDefinition
      |
      v
EquipmentFactory
      |
      v
EquipmentBase

The factory:

resolves the equipment definition;
accepts a stable equipment ID;
creates the equipment instance;
copies default properties;
applies instance-specific property overrides;
creates stable terminal identifiers.

It does not create Qt graphics objects.

EquipmentBase
ui/equipment/equipment_base.py

EquipmentBase represents one logical SLD equipment instance.

It stores:

equipment_id;
equipment_type;
name;
logical position;
properties;
terminal identifiers.

Example:

EquipmentBase
    equipment_id   = "T1"
    equipment_type = "transformer"
    name           = "Main Transformer"
    position       = (500.0, 300.0)

The object remains Qt-independent.

EquipmentManager
ui/equipment/equipment_manager.py

EquipmentManager owns the collection of equipment instances currently belonging to the UI-side SLD model/document.

Its responsibilities include:

adding equipment;
removing equipment;
retrieving equipment;
required lookup;
existence checks;
enumerating equipment;
enumerating equipment IDs;
clearing the collection.

The authoritative identity is:

equipment_id

Two equipment objects with the same equipment_id cannot coexist in one manager.

The manager does not automatically create or remove:

connections;
graphics items;
Core network objects.

Those operations belong to higher-level coordination boundaries.

EquipmentTerminal
ui/equipment/terminal.py

EquipmentTerminal represents one logical connection point belonging to an equipment object.

A terminal contains:

terminal_id;
equipment_id;
terminal_name;
local position;
terminal properties.

Example:

Transformer T1
      |
      +---- T1:HV
      |
      +---- T1:LV

Terminal identity is independent of any Qt graphics object.

This is essential for:

connection interaction;
terminal resolution;
snapping;
routing;
serialization;
selection;
future Core synchronization.
Identity Model

GridForge uses stable logical identifiers.

Equipment
    |
    +-- equipment_id
    |
    +-- terminal_ids
             |
             +-- terminal_id

The graphics layer must not become the source of logical identity.

For example:

equipment_id = "T1"
terminal_id  = "T1:HV"

A corresponding QGraphicsItem may exist, but the logical identity remains valid independently of that item.

Terminal Relationship

Equipment owns terminal identities.

The terminal resolver in the connection subsystem resolves those identities to EquipmentTerminal objects.

EquipmentBase
      |
      | terminal_ids
      v
EquipmentTerminal
      |
      v
TerminalResolver
      |
      v
ConnectionValidator

The equipment subsystem therefore defines terminal objects, while the connection subsystem handles connection interaction and structural connection validation.

Position Model

Equipment position is expressed in the logical SLD coordinate system.

EquipmentBase
    position = (x, y)

A terminal position is expressed in the equipment's local coordinate system:

EquipmentTerminal
    local_position = (x, y)

The transformation from local equipment coordinates to canvas/global coordinates belongs to the presentation/canvas layer.

The equipment subsystem does not perform graphical hit testing or canvas transformation.

Serialization

Equipment objects provide Qt-independent serialization.

Conceptually:

EquipmentBase
      |
      v
    to_dict()
      |
      v
Serialized SLD data

Terminal objects also provide serialization:

EquipmentTerminal
      |
      v
    to_dict()

Definitions provide serialization for registry/document metadata.

Serialization must not contain Qt object references.

Relationship With the Connection Subsystem

The equipment subsystem provides the logical endpoints used by the connection subsystem.

Equipment
    |
    +---- Terminal
    |
    +---- Terminal
    |
    v
Connection Subsystem
    |
    +---- TerminalResolver
    +---- ConnectionValidator
    +---- Connection
    +---- ConnectionPreview
    +---- ConnectionRouter
    +---- TopologyAdapter

The connection subsystem does not require equipment graphics objects to identify terminals.

There is no ConnectionManager in the current GridForge V2 connection architecture.

Relationship With Rendering

Rendering is outside this subsystem.

The intended presentation pipeline is:

EquipmentBase
      |
      v
Equipment Item / Adapter
      |
      v
Equipment Renderer
      |
      v
Canvas

The equipment model must never directly create or manipulate:

QGraphicsItem
QGraphicsScene
QPainter
QGraphicsView
Relationship With Core

The equipment subsystem is not the authoritative electrical-network model.

The architectural boundary is:

UI SLD
  |
  v
Equipment
  |
  v
SLD Model / Connection Subsystem
  |
  v
Core Synchronization Boundary
  |
  v
GridForge Core

The UI may maintain the information required to construct and display an SLD, but it must not become a second power-system database or solver.

Electrical-network authority remains in Core.

Separation of Type and Instance

A critical architectural rule is the separation between an equipment definition and an equipment instance.

TYPE
 |
 v
EquipmentDefinition
 |
 v
EquipmentRegistry
 |
 v
EquipmentFactory
 |
 v
INSTANCE
 |
 v
EquipmentBase

For example:

Definition:
    transformer
    terminals = HV, LV


Instances:
    T1 — Main Transformer
    T2 — Auxiliary Transformer
    T3 — Unit Transformer

One definition may therefore create many independent instances.

Runtime Ownership

The ownership boundaries are:

Component	Owns
EquipmentDefinition	One equipment type definition
EquipmentRegistry	Available type definitions
EquipmentFactory	Equipment creation operation
EquipmentBase	One equipment instance
EquipmentManager	Runtime equipment instances
EquipmentTerminal	One logical terminal
Connection subsystem	Connections between terminals
Canvas subsystem	Visual presentation
Core	Authoritative electrical network

No component should silently assume another component's ownership.

Current Public API

The equipment package exposes:

from ui.equipment import (
    EquipmentBase,
    EquipmentDefinition,
    EquipmentRegistry,
    EquipmentFactory,
    EquipmentManager,
    EquipmentTerminal,
)

These constitute the public equipment API.

Architectural Constraints

The following constraints are mandatory.

1. Qt Independence

Logical equipment classes must remain usable without Qt.

2. Stable Identity

equipment_id is the authoritative identity of an equipment instance.

terminal_id is the authoritative identity of a terminal.

3. Definition/Instance Separation

Equipment definitions must not become runtime equipment objects.

4. Registry/Manager Separation

EquipmentRegistry owns definitions.

EquipmentManager owns runtime instances.

5. No Rendering Ownership

Equipment objects must not create or manipulate graphics objects.

6. No Electrical Solver

The equipment subsystem must not perform:

load flow;
short circuit;
OPF;
Y-bus calculation;
protection calculations;
transient simulation;
impedance calculations.
7. No Core Duplication

The UI equipment subsystem must not become a duplicate electrical-network database.

8. Terminal Independence

Terminals must remain valid independently of Qt graphics objects.

9. Connection Separation

Equipment defines terminals.

The connection subsystem defines relationships between terminals.

10. SLD First-Class Status

Equipment is a first-class component of the current GridForge SLD workflow, not a future placeholder.

Overall Architecture
                         GridForge V2 SLD
                                |
                                v
                    +-----------------------+
                    |   EquipmentDefinition |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    |   EquipmentRegistry   |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    |   EquipmentFactory    |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    |    EquipmentBase      |
                    +-----------+-----------+
                                |
                  +-------------+-------------+
                  |                           |
                  v                           v
        +------------------+       +-------------------+
        | EquipmentTerminal|       | EquipmentManager  |
        +--------+---------+       +-------------------+
                 |
                 v
        +-----------------------+
        | Connection Subsystem  |
        +-----------+-----------+
                    |
                    v
             SLD / Canvas Layer
                    |
                    v
              Render System
                    |
                    v
                 Canvas


                    │
                    │ synchronization boundary
                    ▼


              GridForge Core
Current Scope

The equipment subsystem currently provides the logical foundation for SLD equipment.

It intentionally stops at the UI logical-model boundary.

Future specialized equipment classes, symbol adapters, equipment-specific UI items, and Core synchronization may be added without changing the fundamental separation between:

definition
registry
factory
instance
manager
terminal
presentation
Core

That separation is a frozen architectural constraint for GridForge V2.
