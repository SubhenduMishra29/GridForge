# ============================================================
# File: core/application/services/__init__.py
# GridForge V2 — Headless Application Services
# ============================================================
"""
GridForge V2
============

Package:
    core.application.services

Purpose
-------
Contains Application Services implementing GridForge V2
use cases.

Application Services are the orchestration layer between
Application Commands and the headless Core.

Architectural flow
------------------

    Command
       |
       v
    Service
       |
       v
    Core API
       |
       v
    ApplicationResult
       |
       v
    Application Event

Responsibilities
----------------
Application Services may:

    * validate Application-level input;
    * coordinate multiple Core operations;
    * call public Core APIs;
    * translate expected Core failures;
    * construct Application results;
    * produce Application events where appropriate.

Application Services must NOT:

    * own canonical electrical state;
    * duplicate domain invariants;
    * directly manipulate private Core state;
    * manipulate NetworkX topology internals;
    * calculate engineering results themselves;
    * depend on Qt;
    * depend on UI controllers;
    * manipulate SLD graphics objects.

Core remains authoritative for engineering/domain behavior.

Current Status
--------------
Concrete services are introduced only after their corresponding
Core public API has been reconciled.

This package intentionally starts empty.
"""

from __future__ import annotations

__all__: list[str] = []
