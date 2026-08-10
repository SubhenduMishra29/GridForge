"""
Main Toolbar (PLUGIN-READY)

Responsibilities:
------------------
- Provide a container for tool actions
- Allow external plugins to inject actions
- Stay decoupled from business logic

It does NOT:
-------------
- Define tools
- Know about controller logic
- Hardcode actions

Tools are added via:
    toolbar.add_tool(...)
"""

from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction


class MainToolbar(QToolBar):
    """
    Extensible toolbar.

    Tools/actions are injected dynamically by plugins.
    """

    def __init__(self):
        super().__init__("Tools")

        # Store actions (optional, useful later)
        self._actions = {}

    # ------------------------------------------------------------------
    # Public API (USED BY PLUGINS)
    # ------------------------------------------------------------------
    def add_tool(self, name, callback, tool_id=None):
        """
        Add a tool action to the toolbar.

        Args:
            name (str): Display name
            callback (callable): Function to call when clicked
            tool_id (str, optional): Identifier for tracking
        """

        action = QAction(name, self)

        # Connect safely (no lambda capture bug)
        action.triggered.connect(callback)

        self.addAction(action)

        if tool_id:
            self._actions[tool_id] = action

        return action

    # ------------------------------------------------------------------
    # Optional helpers (future use)
    # ------------------------------------------------------------------
    def get_action(self, tool_id):
        return self._actions.get(tool_id)

    def set_active(self, tool_id):
        """
        (Future)
        Highlight active tool
        """
        pass
