# ============================================================
# GridForge V2 — Canonical Application Branding
# Author: Subhendu Mishra
# ============================================================

"""Canonical presentation-side branding/resource discovery for GridForge."""

from __future__ import annotations

import importlib.metadata
import logging
import sysconfig
from dataclasses import dataclass
from pathlib import Path

from ui.core.qt import QApplication, QIcon, QPixmap


LOGGER = logging.getLogger(__name__)


class BrandingError(RuntimeError):
    """Base error for GridForge branding/resource failures."""


class BrandingAssetError(BrandingError):
    """Raised when an authoritative branding asset cannot be loaded."""


@dataclass(frozen=True, slots=True)
class BrandingResources:
    """Resolved presentation resources; no engineering/application state."""

    splash_path: Path | None
    icon_path: Path | None
    version: str


class BrandingService:
    """Single presentation authority for GridForge product identity."""

    PRODUCT_NAME = "GridForge"
    PRODUCT_DESCRIPTION = "Power System Engineering Platform"
    DEFAULT_TITLE = "GridForge — Power System Engineering Platform"

    ICON_FILENAME = "Logo.png"
    SPLASH_FILENAME = "splash.png"

    def __init__(self, project_root: str | Path | None = None) -> None:
        root = (
            Path(project_root).resolve()
            if project_root is not None
            else Path(__file__).resolve().parents[1]
        )
        self._project_root = root
        self._resources = self._discover()

    @property
    def resources(self) -> BrandingResources:
        return self._resources

    @property
    def version(self) -> str:
        return self._resources.version

    @property
    def splash_path(self) -> Path | None:
        return self._resources.splash_path

    @property
    def icon_path(self) -> Path | None:
        return self._resources.icon_path

    def _resource_roots(self) -> tuple[Path, ...]:
        """Return the canonical source-tree and installed data roots."""
        installed_root = Path(sysconfig.get_path("data")) / "share" / "gridforge"
        return (self._project_root, installed_root)

    def _resolve_resource(self, filename: str) -> Path | None:
        """Resolve an exact, case-sensitive filename without using CWD."""
        for root in self._resource_roots():
            candidate = root / filename
            if candidate.is_file():
                return candidate
        return None

    def _discover(self) -> BrandingResources:
        splash_path = self._resolve_resource(self.SPLASH_FILENAME)
        icon_path = self._resolve_resource(self.ICON_FILENAME)

        if splash_path is None:
            LOGGER.error(
                "GridForge splash asset was not found in source or installed "
                "resource locations: %s",
                self.SPLASH_FILENAME,
            )

        return BrandingResources(
            splash_path=splash_path,
            icon_path=icon_path,
            version=self._resolve_version(),
        )

    @staticmethod
    def _resolve_version() -> str:
        try:
            return importlib.metadata.version("gridforge")
        except importlib.metadata.PackageNotFoundError:
            pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
            if pyproject.is_file():
                import tomllib

                data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
                version = data.get("project", {}).get("version")
                if isinstance(version, str) and version.strip():
                    return version.strip()
            return "unknown"

    def icon(self) -> QIcon | None:
        """Load the canonical Logo.png application icon."""
        if self.icon_path is None:
            return None
        icon = QIcon(str(self.icon_path))
        if icon.isNull():
            LOGGER.error("GridForge application icon could not be loaded: %s", self.icon_path)
            return None
        return icon

    def splash_pixmap(self) -> QPixmap:
        """Load the authoritative splash artwork without altering its aspect ratio."""
        if self.splash_path is None:
            raise BrandingAssetError(
                "The canonical GridForge splash asset is missing: splash.png"
            )

        pixmap = QPixmap(str(self.splash_path))
        if pixmap.isNull():
            raise BrandingAssetError(
                f"GridForge splash asset could not be loaded: {self.splash_path}"
            )
        return pixmap

    def apply_application_identity(self, application: QApplication) -> None:
        """Apply product identity and the authoritative Logo.png icon to Qt."""
        if not isinstance(application, QApplication):
            raise TypeError("application must be a QApplication instance.")

        application.setApplicationName(self.PRODUCT_NAME)
        application.setApplicationDisplayName(self.PRODUCT_NAME)
        application.setApplicationVersion(self.version)

        icon = self.icon()
        if icon is not None:
            application.setWindowIcon(icon)


