```python
# ============================================================
# File: ui/core/qt.py
# GridForge V2 — Qt Abstraction Layer
# ============================================================
"""
Centralized Qt abstraction boundary for the GridForge UI.

Purpose
-------
GridForge V2 uses PySide6 exclusively.

All UI modules must import Qt APIs through this module:

    from ui.core.qt import QWidget, QLabel

Direct imports from PySide6/PyQt are prohibited outside this
abstraction boundary.

Architectural Contract
----------------------
1. PySide6 is the only supported Qt binding.
2. UI modules must not import PyQt5, PyQt6, or PySide6 directly.
3. This module contains Qt exports only.
4. This module contains no GridForge application logic.
5. Core/domain modules must never depend on this module.
6. Qt exports are added only when required by the UI architecture.
7. This module is the single Qt binding boundary for GridForge UI.

Dependency Direction
--------------------

    GridForge Core
          ↑
          │
    Application / Controller
          ↑
          │
    UI
          ↑
          │
      ui.core.qt
          ↑
          │
       PySide6

Binding
-------
PySide6 is intentionally imported here and nowhere else in the
GridForge UI layer.
"""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


# ============================================================
# Binding
# ============================================================

BINDING = "PySide6"


# ============================================================
# Qt Core
# ============================================================

Qt = QtCore.Qt

QObject = QtCore.QObject

Signal = QtCore.Signal
Slot = QtCore.Slot

QPointF = QtCore.QPointF
QRectF = QtCore.QRectF
QSize = QtCore.QSize

QEvent = QtCore.QEvent
QPoint = QtCore.QPoint

QTimer = QtCore.QTimer


# ============================================================
# Qt GUI
# ============================================================

QPainter = QtGui.QPainter
QPen = QtGui.QPen
QBrush = QtGui.QBrush
QColor = QtGui.QColor

QFont = QtGui.QFont
QPixmap = QtGui.QPixmap
QIcon = QtGui.QIcon

QKeyEvent = QtGui.QKeyEvent
QMouseEvent = QtGui.QMouseEvent


# ============================================================
# Qt Graphics
# ============================================================

QGraphicsItem = QtWidgets.QGraphicsItem

QGraphicsObject = QtWidgets.QGraphicsObject

QGraphicsScene = QtWidgets.QGraphicsScene

QGraphicsView = QtWidgets.QGraphicsView

QGraphicsItemGroup = QtWidgets.QGraphicsItemGroup

QGraphicsLineItem = QtWidgets.QGraphicsLineItem

QGraphicsRectItem = QtWidgets.QGraphicsRectItem

QGraphicsEllipseItem = QtWidgets.QGraphicsEllipseItem

QGraphicsPathItem = QtWidgets.QGraphicsPathItem

QGraphicsTextItem = QtWidgets.QGraphicsTextItem


# ============================================================
# Qt Application / Window
# ============================================================

QApplication = QtWidgets.QApplication

QMainWindow = QtWidgets.QMainWindow

QDialog = QtWidgets.QDialog

QFrame = QtWidgets.QFrame


# ============================================================
# Qt Layouts
# ============================================================

QVBoxLayout = QtWidgets.QVBoxLayout

QHBoxLayout = QtWidgets.QHBoxLayout

QGridLayout = QtWidgets.QGridLayout

QFormLayout = QtWidgets.QFormLayout


# ============================================================
# Qt Basic Widgets
# ============================================================

QWidget = QtWidgets.QWidget

QLabel = QtWidgets.QLabel

QPushButton = QtWidgets.QPushButton

QToolButton = QtWidgets.QToolButton

QCheckBox = QtWidgets.QCheckBox

QComboBox = QtWidgets.QComboBox

QLineEdit = QtWidgets.QLineEdit

QSpinBox = QtWidgets.QSpinBox

QDoubleSpinBox = QtWidgets.QDoubleSpinBox


# ============================================================
# Qt Item / List Widgets
# ============================================================

QListWidget = QtWidgets.QListWidget

QListWidgetItem = QtWidgets.QListWidgetItem

QTreeWidget = QtWidgets.QTreeWidget

QTreeWidgetItem = QtWidgets.QTreeWidgetItem


# ============================================================
# Qt Text / Display Widgets
# ============================================================

QTextEdit = QtWidgets.QTextEdit

QPlainTextEdit = QtWidgets.QPlainTextEdit


# ============================================================
# Qt Containers / Docking
# ============================================================

QScrollArea = QtWidgets.QScrollArea

QDockWidget = QtWidgets.QDockWidget

QTabWidget = QtWidgets.QTabWidget

QSplitter = QtWidgets.QSplitter


# ============================================================
# Qt Menus / Actions / Toolbars
# ============================================================

QAction = QtGui.QAction

QMenu = QtWidgets.QMenu

QMenuBar = QtWidgets.QMenuBar

QToolBar = QtWidgets.QToolBar


# ============================================================
# Qt Status / Progress
# ============================================================

QStatusBar = QtWidgets.QStatusBar

QProgressBar = QtWidgets.QProgressBar


# ============================================================
# Convenience Geometry Aliases
# ============================================================

Point = QPointF
Rect = QRectF


# ============================================================
# Public API
# ============================================================

__all__ = [
    # --------------------------------------------------------
    # Binding
    # --------------------------------------------------------
    "BINDING",

    # --------------------------------------------------------
    # Qt Core
    # --------------------------------------------------------
    "Qt",
    "QObject",
    "Signal",
    "Slot",
    "QPointF",
    "QRectF",
    "QSize",
    "QEvent",
    "QPoint",
    "QTimer",

    # --------------------------------------------------------
    # Qt GUI
    # --------------------------------------------------------
    "QPainter",
    "QPen",
    "QBrush",
    "QColor",
    "QFont",
    "QPixmap",
    "QIcon",
    "QKeyEvent",
    "QMouseEvent",

    # --------------------------------------------------------
    # Graphics
    # --------------------------------------------------------
    "QGraphicsItem",
    "QGraphicsObject",
    "QGraphicsScene",
    "QGraphicsView",
    "QGraphicsItemGroup",
    "QGraphicsLineItem",
    "QGraphicsRectItem",
    "QGraphicsEllipseItem",
    "QGraphicsPathItem",
    "QGraphicsTextItem",

    # --------------------------------------------------------
    # Application / Windows
    # --------------------------------------------------------
    "QApplication",
    "QMainWindow",
    "QDialog",
    "QFrame",

    # --------------------------------------------------------
    # Layouts
    # --------------------------------------------------------
    "QVBoxLayout",
    "QHBoxLayout",
    "QGridLayout",
    "QFormLayout",

    # --------------------------------------------------------
    # Basic widgets
    # --------------------------------------------------------
    "QWidget",
    "QLabel",
    "QPushButton",
    "QToolButton",
    "QCheckBox",
    "QComboBox",
    "QLineEdit",
    "QSpinBox",
    "QDoubleSpinBox",

    # --------------------------------------------------------
    # List / tree widgets
    # --------------------------------------------------------
    "QListWidget",
    "QListWidgetItem",
    "QTreeWidget",
    "QTreeWidgetItem",

    # --------------------------------------------------------
    # Text / display
    # --------------------------------------------------------
    "QTextEdit",
    "QPlainTextEdit",

    # --------------------------------------------------------
    # Containers / docking
    # --------------------------------------------------------
    "QScrollArea",
    "QDockWidget",
    "QTabWidget",
    "QSplitter",

    # --------------------------------------------------------
    # Menus / actions / toolbars
    # --------------------------------------------------------
    "QAction",
    "QMenu",
    "QMenuBar",
    "QToolBar",

    # --------------------------------------------------------
    # Status / progress
    # --------------------------------------------------------
    "QStatusBar",
    "QProgressBar",

    # --------------------------------------------------------
    # Convenience aliases
    # --------------------------------------------------------
    "Point",
    "Rect",
]
```
