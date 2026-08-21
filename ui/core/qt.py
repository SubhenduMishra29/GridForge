# ============================================================
# File: ui/core/qt.py
# GridForge V2 — Qt Compatibility / Abstraction Layer
# ============================================================

"""
Central Qt abstraction layer for GridForge V2.

Architectural role
------------------
This module is the ONLY permitted direct Qt import boundary for
the GridForge UI subsystem.

All UI modules must import Qt classes, enums, signals, slots,
and related Qt functionality from:

    ui.core.qt

GridForge V2 uses PySide6 as its Qt implementation.

This module contains ONLY:
    - PySide6 imports
    - Qt compatibility aliases
    - Qt public API exposure

This module MUST NOT contain:
    - GridForge application logic
    - electrical/model logic
    - workspace policy
    - panel policy
    - canvas logic
    - rendering logic
    - controller logic
    - service construction
    - application state

Architectural boundary
----------------------

    GridForge UI
         |
         v
      ui.core.qt
         |
         v
       PySide6

No UI subsystem component should bypass this boundary by importing
PySide6 directly.

Ownership
---------

ui.core.qt does NOT own any Qt object.

It only exposes Qt types.

Application/UI components remain responsible for creating and
owning their respective Qt objects according to their architectural
contracts.
"""

from __future__ import annotations


# ============================================================
# QtCore
# ============================================================

from PySide6.QtCore import (
    QAbstractItemModel,
    QLineF,
    QModelIndex,
    QObject,
    QPoint,
    QPointF,
    QRectF,
    QSize,
    QSizeF,
    QTimer,
    Qt,
    Property,
    Signal,
    Slot,
)


# ============================================================
# QtGui
# ============================================================

from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QBrush,
    QColor,
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
    QLayout,
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
    "QLineF",
    "QModelIndex",
    "QObject",

    "QPoint",
    "QPointF",

    "QRectF",

    "QSize",
    "QSizeF",

    "QTimer",

    "Qt",

    "Property",
    "Signal",
    "Slot",

    # --------------------------------------------------------
    # QtGui
    # --------------------------------------------------------

    "QAction",
    "QActionGroup",

    "QBrush",
    "QColor",
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

    "QLayout",

    "QMainWindow",

    "QMessageBox",

    "QPushButton",

    "QStatusBar",

    "QToolBar",

    "QVBoxLayout",

    "QWidget",
]
