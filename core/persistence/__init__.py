"""Persistence and migration boundaries for GridForge electrical data.

Persistence owns representation/migration concerns only. It does not own
engineering interpretation, topology mutation, study preparation, or solving.
"""

from .migration import (
    AmbiguousElectricalDataError,
    LegacyElectricalDataMigration,
    MigrationResult,
    ProjectMigration,
    ProjectMigrationError,
    ProjectPersistenceMigration,
    PresentationCollectionMigrationError,
    SLDMigration,
    SLDMigrationError,
    UnsupportedProjectSchemaError,
)
from .project_package import (
    MANIFEST_NAME,
    PACKAGE_SUFFIX,
    PACKAGE_VERSION,
    PROJECT_SCHEMA_VERSION,
    PRESENTATION_SCHEMA_VERSION,
    SLD_SCHEMA_VERSION,
    CORE_SERIALIZATION_VERSION,
    PROJECT_NAME,
    normalize_package_path,
)
from .project_persistence import ProjectPersistenceError, ProjectPersistenceService
from .type_registry import ModelTypeRegistry, UnknownModelTypeError

__all__ = [
    "AmbiguousElectricalDataError",
    "LegacyElectricalDataMigration",
    "MigrationResult",
    "ProjectMigration",
    "ProjectMigrationError",
    "ProjectPersistenceMigration",
    "PresentationCollectionMigrationError",
    "SLDMigration",
    "SLDMigrationError",
    "UnsupportedProjectSchemaError",
    "MANIFEST_NAME",
    "PACKAGE_SUFFIX",
    "PACKAGE_VERSION",
    "PROJECT_SCHEMA_VERSION",
    "PRESENTATION_SCHEMA_VERSION",
    "SLD_SCHEMA_VERSION",
    "CORE_SERIALIZATION_VERSION",
    "PROJECT_NAME",
    "normalize_package_path",
    "ProjectPersistenceError",
    "ProjectPersistenceService",
    "ModelTypeRegistry",
    "UnknownModelTypeError",
]
