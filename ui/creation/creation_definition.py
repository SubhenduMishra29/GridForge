# ============================================================
# File: ui/creation/creation_definition.py
# GridForge V2 — Canonical equipment creation contracts
# Author: Subhendu Mishra
# ============================================================
"""Declarative creation contracts for registered equipment types.

This module is the single creation-schema authority.  It describes
engineering parameters, topology/terminal acquisition, preview support,
and the immutable Application command contract.  It contains no Core
mutation and no UI lifecycle state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from core.application.creation_schema import (
    ConditionalParameterRequirement,
    CreationDefinition,
    CreationTerminalRequirement,
    CreationTopologyRequirement,
    EngineeringParameterDefinition,
    _validate_parameter,
)

from core.application.creation_schema import creation_definition_for


__all__ = [
    "EngineeringParameterDefinition",
    "CreationTerminalRequirement",
    "CreationTopologyRequirement",
    "ConditionalParameterRequirement",
    "CreationDefinition",
    "creation_definition_for",
]
