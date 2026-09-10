"""Persistence and migration boundaries for GridForge electrical data.

Persistence owns representation/migration concerns only. It does not own
engineering interpretation, topology mutation, study preparation, or solving.
"""

from .migration import (
    AmbiguousElectricalDataError,
    LegacyElectricalDataMigration,
    MigrationResult,
)

__all__ = [
    "AmbiguousElectricalDataError",
    "LegacyElectricalDataMigration",
    "MigrationResult",
]
