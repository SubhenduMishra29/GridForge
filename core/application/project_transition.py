# ============================================================
# File: core/application/project_transition.py
# GridForge V2 — Application Project Transition Contract
# Author: Subhendu Mishra
# ============================================================

"""Authoritative Application-owned dirty-project transition decisions."""

from __future__ import annotations

from enum import Enum


class ProjectTransitionDecision(str, Enum):
    """Decision supplied by the presentation before a project transition."""

    SAVE = "save"
    DISCARD = "discard"
    CANCEL = "cancel"


class ProjectTransitionRequired(RuntimeError):
    """Raised when a dirty project needs an explicit transition decision."""


__all__ = ["ProjectTransitionDecision", "ProjectTransitionRequired"]
