# ============================================================
# File: ui/core/qt.py
# GridForge V2 — Qt Compatibility / Abstraction Layer
# ============================================================
"""
Central Qt abstraction layer for GridForge V2.

Purpose
-------
This module is the ONLY permitted Qt import boundary for the
GridForge UI subsystem.

All UI modules must import Qt classes, enums, signals, slots,
and related Qt functionality from:

    ui.core.qt

No UI module should import directly from:

    PySide6
    PyQt5
    PyQt6

GridForge V2 uses PySide6 as its Qt implementation.

Architecture
------------

    UI modules
        │
        ▼
    ui.core.qt
        │
        ▼
    PySide6

Design principles
-----------------
1. PySide6 is the sole Qt backend.

2. This module contains imports and compatibility aliases only.

3. It must not contain GridForge application logic.

4. It must not import Controller, Tools, Renderers, Canvas,
   Core, or any other GridForge subsystem.

5. It must not create application-level singleton objects.

6. It must not hide behavioral differences between UI modules.

7. New Qt dependencies should be added deliberately and only
   when actually required by the UI architecture.

8. Public names exported by this module form the internal
   GridForge Qt API.

Qt module grouping
------------------
The exported API is organized into:

    Core
        QAbstractItemModel, QModelIndex, QObject,
        QPoint, QPointF, QRectF, QSize, QSizeF,
        QTimer, Qt, Signal, Slot, Property

    GUI / Actions
        QAction, QActionGroup,
        QColor, QBrush, QFont, QIcon, QImage,
        QPainter, QPainterPath, QPen, QPixmap, QTransform

    Widgets
        QApplication, QDockWidget,
        QGraphicsItem, QGraphicsObject,
        QGraphicsEllipseItem, QGraphicsLineItem,
        QGraphicsPathItem, QGraphicsRectItem,
        QGraphicsScene, QGraphicsView,
        QHBoxLayout, QLabel, QMainWindow,
        QMessageBox, QPushButton, QStatusBar,
        QToolBar, QVBoxLayout, QWidget

This list is intentionally explicit.

Do not use:

    from PySide6 import *

or equivalent wildcard imports.

Qt ownership
------------
QObject ownership and parent-child lifetime remain governed by Qt.

GridForge UI classes remain responsible for their own
application-level ownership and lifecycle contracts.

Threading
---------
This module does not define threading policy.

Qt signals/slots remain the mechanism for Qt-thread-safe
communication where required.

The GridForge Core remains independent of Qt.

Testing
-------
Tests may import Qt types through this module so that the same
internal import boundary is exercised as production UI code.

Public API
----------
Only names listed in __all__ are considered part of the
GridForge internal Qt abstraction contract.
"""

from __future__ import annotations


# ============================================================
# QtCore
# ============================================================

from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QObject,
    QPoint,
    QPointF,
    QRectF,
    QSize,
    QSizeF,
    QTimer,
    Qt,
    Signal,
    Slot,
    Property,
)


# ============================================================
# QtGui
# ============================================================

from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QBrush,
    QFont,
    QIcon,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QTransform,
)


# ============================================================
# QtWidgets
# ============================================================

from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsObject,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [

    # --------------------------------------------------------
    # QtCore
    # --------------------------------------------------------

    "QAbstractItemModel",
    "QModelIndex",
    "QObject",

    "QPoint",
    "QPointF",

    "QRectF",

    "QSize",
    "QSizeF",

    "QTimer",

    "Qt",

    "Signal",
    "Slot",
    "Property",

    # --------------------------------------------------------
    # QtGui / Actions
    # --------------------------------------------------------

    "QAction",
    "QActionGroup",

    "QColor",
    "QBrush",
    "QFont",
    "QIcon",
    "QImage",
    "QPainter",
    "QPainterPath",
    "QPen",
    "QPixmap",
    "QTransform",

    # --------------------------------------------------------
    # QtWidgets
    # --------------------------------------------------------

    "QApplication",

    "QDockWidget",

    "QGraphicsEllipseItem",
    "QGraphicsItem",
    "QGraphicsLineItem",
    "QGraphicsObject",
    "QGraphicsPathItem",
    "QGraphicsRectItem",
    "QGraphicsScene",
    "QGraphicsView",

    "QHBoxLayout",

    "QLabel",

    "QMainWindow",

    "QMessageBox",

    "QPushButton",

    "QStatusBar",

    "QToolBar",

    "QVBoxLayout",

    "QWidget",
]
