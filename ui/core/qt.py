"""
GridForge V2 — Qt Abstraction Layer
===================================

File:
    ui/core/qt.py

Purpose
-------
Centralized Qt abstraction boundary for the GridForge UI.

GridForge V2 uses PySide6 exclusively. All UI modules that require
Qt APIs must import them through this module rather than importing
PySide6 directly.

Architectural Contract
----------------------
1. PySide6 is the only supported Qt binding.
2. UI modules must not import PyQt6.
3. UI modules should not import PySide6 directly.
4. This module contains no GridForge application logic.
5. Core/domain modules must not depend on this UI abstraction.
6. Additional Qt exports are added only when required by finalized
   UI modules.

Dependency Direction
--------------------
    GridForge Core
        ↑
        │
    UI Controllers
        ↑
        │
    UI Components
        ↑
        │
    ui.core.qt
        ↑
        │
    PySide6
"""

from PySide6 import QtCore, QtGui, QtWidgets


# ============================================================================
# Binding
# ============================================================================

BINDING = "PySide6"


# ============================================================================
# Qt Core
# ============================================================================

Qt = QtCore.Qt
QObject = QtCore.QObject
Signal = QtCore.Signal
Slot = QtCore.Slot

QPointF = QtCore.QPointF
QRectF = QtCore.QRectF
QSize = QtCore.QSize
QTimer = QtCore.QTimer


# ============================================================================
# Qt GUI
# ============================================================================

QPainter = QtGui.QPainter
QPen = QtGui.QPen
QBrush = QtGui.QBrush
QColor = QtGui.QColor


# ============================================================================
# Qt Widgets
# ============================================================================

QWidget = QtWidgets.QWidget
QGraphicsView = QtWidgets.QGraphicsView
QGraphicsScene = QtWidgets.QGraphicsScene
QGraphicsItem = QtWidgets.QGraphicsItem


# ============================================================================
# Convenience Geometry Aliases
# ============================================================================

Point = QPointF
Rect = QRectF


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    # Binding
    "BINDING",

    # Qt Core
    "Qt",
    "QObject",
    "Signal",
    "Slot",
    "QPointF",
    "QRectF",
    "QSize",
    "QTimer",

    # Qt GUI
    "QPainter",
    "QPen",
    "QBrush",
    "QColor",

    # Qt Widgets
    "QWidget",
    "QGraphicsView",
    "QGraphicsScene",
    "QGraphicsItem",

    # Convenience aliases
    "Point",
    "Rect",
]
