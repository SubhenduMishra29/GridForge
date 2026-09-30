"""Professional Control engineering toolbar.
Author: Subhendu Mishra
"""
from __future__ import annotations
from typing import Any,Callable
from ui.core.qt import QHBoxLayout,QLabel,QPushButton,QVBoxLayout,QWidget

class ControlToolbar(QWidget):
    """Contextual Control action groups using the existing Application boundary."""
    def __init__(self,*,application:Any,on_add_rung:Callable[[],None],on_remove_rung:Callable[[],None],on_toggle_rung:Callable[[],None],on_move_rung_up:Callable[[],None],on_cancel_tool:Callable[[],None],on_execute_cycle:Callable[[],None],parent:QWidget|None=None):
        super().__init__(parent); self.setObjectName("ControlToolbar"); self._application=application; self._editing_widgets=[]
        root=QHBoxLayout(self); root.setContentsMargins(4,2,4,2); root.setSpacing(8)
        groups=(("Rung",(("Add Rung",on_add_rung,"Create a new ladder rung."),("Remove Rung",on_remove_rung,"Remove the selected ladder rung."),("Move Up",on_move_rung_up,"Move the selected rung upward."),("Enable / Disable",on_toggle_rung,"Toggle the selected rung state."))),("Tool",(("Cancel",on_cancel_tool,"Cancel only transient Control tool state."),)),("Study",(("Execute Cycle",on_execute_cycle,"Execute the current Control study cycle."),)),("History",(("Undo",lambda:application.undo(),"Undo the last Application command."),("Redo",lambda:application.redo(),"Redo the last Application command."))))
        for title,actions in groups:
            group=QVBoxLayout(); label=QLabel(title,self); label.setObjectName("ControlToolbarGroup"); group.addWidget(label)
            for text,callback,tooltip in actions:
                button=QPushButton(text,self); button.setObjectName("ControlToolbarAction"); button.setToolTip(tooltip); button.clicked.connect(lambda _checked=False,callback=callback:callback()); group.addWidget(button); self._editing_widgets.append(button)
            root.addLayout(group)
        root.addStretch(1)
    def set_editing_enabled(self,enabled:bool):
        for widget in self._editing_widgets: widget.setEnabled(bool(enabled))
__all__=["ControlToolbar"]
