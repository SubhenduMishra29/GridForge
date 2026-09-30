"""Protection engineering workstation over Application read models.
Author: Subhendu Mishra
ProtectionDecision and protection/domain state remain Core/Application authority.
"""
from __future__ import annotations
from typing import Any
from core.application.events import ElementCreated, ElementRemoved, ElementUpdated, NetworkChanged, ProjectClosed, ProjectLoaded
from ui.canvas.canvas_framework import CanvasInteractionState, CanvasStateMachine
from ui.canvas.engineering_canvas_contract import CanvasInteractionAdapter
from ui.core.qt import QGroupBox,QHBoxLayout,QLabel,QListWidget,QSplitter,QToolBar,QVBoxLayout,QWidget
from ui.core.selection_manager import SelectionManager

class ProtectionExplorer(QListWidget):
    def __init__(self,application:Any,selection_manager:SelectionManager,parent:QWidget|None=None):
        super().__init__(parent); self._application=application; self._selection_manager=selection_manager
        self.currentRowChanged.connect(self._selection_changed)
    def refresh(self):
        self.clear()
        try: protection=self._application.read_protection()
        except RuntimeError: self.addItem("No active protection project"); return
        for relay in protection.relays: self.addItem(f"{relay.name}  |  {relay.function_type}")
    def _selection_changed(self,row:int):
        try: protection=self._application.read_protection()
        except RuntimeError: return
        if 0<=row<len(protection.relays): self._selection_manager.select_single(protection.relays[row].object_id)

class ProtectionCanvas(QWidget):
    def __init__(self,*,application:Any,selection_manager:SelectionManager,state_machine:CanvasStateMachine,parent:QWidget|None=None):
        super().__init__(parent); self._application=application; self._selection_manager=selection_manager; self._state_machine=state_machine
        self._adapter=CanvasInteractionAdapter(workspace_id="protection",discipline="protection")
        self._items=QListWidget(self); self._items.setObjectName("ProtectionSchemeSurface"); self._items.currentRowChanged.connect(self._select_item)
        layout=QVBoxLayout(self); layout.addWidget(QLabel("Protection Scheme",self)); layout.addWidget(self._items,1)
    def refresh(self):
        self._items.clear()
        try: protection=self._application.read_protection()
        except RuntimeError: self._items.addItem("Protection scheme unavailable."); return
        for relay in protection.relays:
            status=("TRIPPED" if relay.tripped else "OPERATING" if relay.picked_up else "BLOCKED" if relay.blocked else "OUT OF SERVICE" if not relay.in_service else "READY")
            self._items.addItem(f"RELAY  {relay.name}  |  {relay.function_type}  |  {status}")
    def _select_item(self,row:int):
        try: protection=self._application.read_protection()
        except RuntimeError: return
        if 0<=row<len(protection.relays): self._selection_manager.select_single(protection.relays[row].object_id)

class ProtectionInspector(QGroupBox):
    def __init__(self,*,application:Any,selection_manager:SelectionManager,parent:QWidget|None=None):
        super().__init__("Protection Inspector",parent); self._application=application; self._selection_manager=selection_manager
        self._label=QLabel("Select a protection object.",self); self._label.setWordWrap(True)
        layout=QVBoxLayout(self); layout.addWidget(self._label); selection_manager.selection_changed.connect(lambda _ids:self.refresh()); self.refresh()
    def refresh(self):
        selected=self._selection_manager.selected_ids
        if not selected: self._label.setText("Select a protection object."); return
        try: protection=self._application.read_protection()
        except RuntimeError: self._label.setText("Protection read boundary unavailable."); return
        relay=next((item for item in protection.relays if item.object_id==str(selected[0])),None)
        if relay is None: self._label.setText(f"Protection object: {selected[0]}"); return
        status=("TRIPPED" if relay.tripped else "OPERATING" if relay.picked_up else "BLOCKED" if relay.blocked else "OUT OF SERVICE" if not relay.in_service else "READY")
        self._label.setText(f"Identity: {relay.object_id}\nRelay: {relay.name}\nType: {relay.relay_type}\nFunction: {relay.function_type}\nMeasurement inputs: {len(relay.input_channel_bindings)}\nEnabled: {relay.enabled}\nBlocked: {relay.blocked}\nState: {status}\nPickup: {getattr(relay,'pickup','n/a')}\nOperate: {getattr(relay,'operate','n/a')}\nTrip request: {getattr(relay,'trip_request','n/a')}\nDecision reason: {getattr(relay,'decision_reason','n/a')}")

class ProtectionToolbar(QToolBar):
    def __init__(self,parent:QWidget|None=None):
        super().__init__("Protection Engineering",parent)
        self.addAction("Select"); self.addAction("Connect Measurement"); self.addAction("Inspect"); self.addAction("Fit"); self.addAction("Diagnostics")

class ProtectionWorkspace(QWidget):
    workspace_id="protection"
    _EVENT_TYPES=(ElementCreated,ElementRemoved,ElementUpdated,NetworkChanged,ProjectLoaded,ProjectClosed)
    def __init__(self,*,application:Any,selection_manager:SelectionManager|None=None,parent:QWidget|None=None):
        super().__init__(parent)
        if application is None: raise ValueError("application is required.")
        self._application=application
        if selection_manager is None:
            raise ValueError("ProtectionWorkspace requires the canonical SelectionManager.")
        self._selection_manager=selection_manager; self._state_machine=CanvasStateMachine(workspace_id="protection")
        self._explorer=ProtectionExplorer(application,self._selection_manager,self)
        self._canvas=ProtectionCanvas(application=application,selection_manager=self._selection_manager,state_machine=self._state_machine,parent=self)
        self._inspector=ProtectionInspector(application=application,selection_manager=self._selection_manager,parent=self)
        self._toolbar=ProtectionToolbar(self); self._subscriptions=[]
        for event_type in self._EVENT_TYPES:
            application.event_bus.subscribe(event_type,self._on_application_event); self._subscriptions.append((event_type,self._on_application_event))
        splitter=QSplitter(parent=self); splitter.setChildrenCollapsible(False); splitter.addWidget(self._explorer); splitter.addWidget(self._canvas); splitter.addWidget(self._inspector)
        splitter.setStretchFactor(0,0); splitter.setStretchFactor(1,1); splitter.setStretchFactor(2,0)
        layout=QVBoxLayout(self); layout.setContentsMargins(4,4,4,4); layout.addWidget(self._toolbar); layout.addWidget(splitter,1); self.refresh()
    @property
    def selection_manager(self): return self._selection_manager
    @property
    def canvas_state(self): return self._state_machine.state
    def refresh(self): self._explorer.refresh(); self._canvas.refresh(); self._inspector.refresh()
    def _on_application_event(self,_event:Any): self.refresh()
    def dispose(self):
        for event_type,handler in tuple(self._subscriptions): self._application.event_bus.unsubscribe(event_type,handler)
        self._subscriptions.clear(); self._state_machine.cancel()

__all__=["ProtectionWorkspace","ProtectionExplorer","ProtectionCanvas","ProtectionInspector","ProtectionToolbar"]
