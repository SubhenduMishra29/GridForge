# ============================================================
# File: ui/core/qt.py
# GridForge V2 — Qt Compatibility / Abstraction Layer
# ============================================================
"""
Central Qt abstraction layer for GridForge V2.

This module is the ONLY permitted Qt import boundary for the
GridForge UI subsystem.

All UI modules must import Qt classes, enums, signals, slots,
and related Qt functionality from:

    ui.core.qt

GridForge V2 uses PySide6 as its Qt implementation.

This module contains Qt imports and compatibility aliases only.
It contains no GridForge application or engineering logic.
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
    QLineF,
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
    "QLineF",

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
