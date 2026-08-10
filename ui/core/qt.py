"""
Qt Abstraction Layer

## Purpose:
Centralizes ALL Qt imports so the entire project depends on ONE binding.

If you ever switch bindings (PySide6 ↔ PyQt6),
you only modify THIS file.
"""

# ===== Binding Selection =====
# (Easy future switch support)

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    BINDING = "PySide6"
except ImportError:
    from PyQt6 import QtCore, QtGui, QtWidgets
    BINDING = "PyQt6"


# ===== Core Exports =====
Qt = QtCore.Qt
QObject = QtCore.QObject
Signal = QtCore.Signal if BINDING == "PySide6" else QtCore.pyqtSignal
Slot = QtCore.Slot if BINDING == "PySide6" else QtCore.pyqtSlot

QPointF = QtCore.QPointF
QRectF = QtCore.QRectF
QSize = QtCore.QSize
QTimer = QtCore.QTimer


# ===== GUI Exports =====
QPainter = QtGui.QPainter
QPen = QtGui.QPen
QBrush = QtGui.QBrush
QColor = QtGui.QColor


# ===== Widgets Exports =====
QWidget = QtWidgets.QWidget
QGraphicsView = QtWidgets.QGraphicsView
QGraphicsScene = QtWidgets.QGraphicsScene
QGraphicsItem = QtWidgets.QGraphicsItem


# ===== Optional Short Aliases =====
Point = QPointF
Rect = QRectF


# ===== Public API =====
__all__ = [
    # Core
    "Qt",
    "QObject",
    "Signal",
    "Slot",
    "QPointF",
    "QRectF",
    "QSize",
    "QTimer",

    # GUI
    "QPainter",
    "QPen",
    "QBrush",
    "QColor",

    # Widgets
    "QWidget",
    "QGraphicsView",
    "QGraphicsScene",
    "QGraphicsItem",

    # Aliases
    "Point",
    "Rect",

    # Debug
    "BINDING",
]
