# ============================================================
# File: ui/panels/__init__.py
# GridForge V2 — UI Panels Package
# ============================================================
"""
GridForge V2 UI panel package.

This package contains presentation-only panel widgets used by
the GridForge desktop UI.

Architecture
------------

    Application / Controller
             │
             ▼
        UI Panels
             │
             ▼
       Presentation

Panels are UI components only. They do not own authoritative
Core state and must not perform Core mutations, electrical
calculations, simulation, protection processing, measurement
processing, or persistence.

Available Panels
----------------

    ProjectPanel
        Project structure / file presentation.

    PropertiesPanel
        Read-only presentation of the currently selected object.

    ConsolePanel
        System messages, diagnostics, and validation output.

    LayersPanel
        Canvas/layer visibility presentation.

    SimulationPanel
        Simulation controls and simulation-state presentation.

    ResultsPanel
        Analysis and simulation result presentation.

    EquipmentPanel
        Equipment/model-element presentation.

    NetworkPanel
        Network/topology presentation.

    ProtectionPanel
        Protection and relay information presentation.

    MeasurementPanel
        Measurement infrastructure presentation.

Qt Architecture
---------------

Individual panel modules are responsible for importing Qt
classes through:

    ui.core.qt

This package initializer does not import Qt directly.

Plugin Architecture
-------------------

Panels are UI components, not plugins by themselves.

Plugin modules may import these classes when composing the
application UI. Importing ``ui.panels`` therefore does not
perform plugin discovery or registration.
"""

from __future__ import annotations

from ui.panels.console_panel import ConsolePanel
from ui.panels.equipment_panel import EquipmentPanel
from ui.panels.layers_panel import LayersPanel
from ui.panels.measurement_panel import MeasurementPanel
from ui.panels.network_panel import NetworkPanel
from ui.panels.project_panel import ProjectPanel
from ui.panels.properties_panel import PropertiesPanel
from ui.panels.protection_panel import ProtectionPanel
from ui.panels.results_panel import ResultsPanel
from ui.panels.simulation_panel import SimulationPanel


__all__ = [
    "ConsolePanel",
    "EquipmentPanel",
    "LayersPanel",
    "MeasurementPanel",
    "NetworkPanel",
    "ProjectPanel",
    "PropertiesPanel",
    "ProtectionPanel",
    "ResultsPanel",
    "SimulationPanel",
]
