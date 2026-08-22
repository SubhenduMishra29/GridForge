# ============================================================
# File: core/application/commands/__init__.py
# GridForge V2 — Headless Application Commands
# ============================================================
"""
GridForge V2
============

Package:
    core.application.commands

Purpose
-------
Contains concrete Application Commands representing explicit
user/plugin/application intent.

Commands belong to the Application layer.

They are NOT:

    * Core domain entities;
    * UI actions;
    * Qt events;
    * graphics objects;
    * controller state;
    * domain services.

Architectural flow
------------------

    UI / Plugin / Automation
              |
              v
       Application Command
              |
              v
       CommandManager
              |
              v
       Application Service
              |
              v
             Core

A command expresses intent.

An Application Service performs the use-case orchestration.

The Core remains responsible for domain rules and canonical
electrical state.

Current Status
--------------
Concrete commands are introduced only when the corresponding
Application service and Core operation have been reconciled.

No command should bypass the Application execution boundary.
"""

from __future__ import annotations

__all__: list[str] = []
