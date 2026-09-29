# ============================================================
# GridForge V2 — Canonical Application Branding
# Author: Subhendu Mishra
# ============================================================

"""Canonical presentation-side branding/resource discovery for GridForge."""

from __future__ import annotations

import importlib.metadata
import sysconfig
from dataclasses import dataclass
from pathlib import Path

from ui.core.qt import QApplication, QIcon, QPixmap


class BrandingError(RuntimeError):
    """Base error for GridForge branding/resource failures."""


class BrandingAssetError(BrandingError):
    """Raised when an authoritative branding asset cannot be loaded."""


@dataclass(frozen=True, slots=True)
class BrandingResources:
    """Resolved presentation resources; no engineering/application state."""

    splash_path: Path
    icon_path: Path | None
    version: str


class BrandingService:
    """Single presentation authority for GridForge product identity."""

    PRODUCT_NAME = "GridForge"
    PRODUCT_DESCRIPTION = "Power System Engineering Platform"
    DEFAULT_TITLE = "GridForge — Power System Engineering Platform"
    SPLASH_FILENAME = "splash.png"

    _ICON_CANDIDATES = (
        "logo.svg", "logo.png",
        "gridforge-logo.svg", "gridforge-logo.png",
        "gridforge_logo.svg", "gridforge_logo.png",
        "icon.svg", "icon.png",
        "app_icon.svg", "app_icon.png",
        "GridForgeLogo.svg", "GridForgeLogo.png",
    )
    _ICON_DIRECTORIES = (
        Path("."), Path("assets"), Path("branding"), Path("icons"),
        Path("ui") / "assets", Path("ui") / "branding", Path("ui") / "icons",
    )

    def __init__(self, project_root: str | Path | None = None) -> None:
        root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parents[1]
        self._project_root = root
        self._resources = self._discover()

    @property
    def resources(self) -> BrandingResources:
        return self._resources

    @property
    def version(self) -> str:
        return self._resources.version

    @property
    def splash_path(self) -> Path:
        return self._resources.splash_path

    @property
    def icon_path(self) -> Path | None:
        return self._resources.icon_path

    def _discover(self) -> BrandingResources:
        return BrandingResources(
            splash_path=self._resolve_splash(),
            icon_path=self._resolve_icon(),
            version=self._resolve_version(),
        )

    def _resolve_splash(self) -> Path:
        candidates = (
            self._project_root / self.SPLASH_FILENAME,
            Path(sysconfig.get_path("data")) / "share" / "gridforge" / self.SPLASH_FILENAME,
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        raise BrandingAssetError(
            "The canonical GridForge splash asset is missing: splash.png"
        )

    def _resolve_icon(self) -> Path | None:
        for directory in self._ICON_DIRECTORIES:
            for filename in self._ICON_CANDIDATES:
                candidate = self._project_root / directory / filename
                if candidate.is_file():
                    return candidate
        return None

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
        if self.icon_path is None:
            return None
        icon = QIcon(str(self.icon_path))
        if icon.isNull():
            raise BrandingAssetError(
                f"GridForge application icon could not be loaded: {self.icon_path}"
            )
        return icon

    def splash_pixmap(self) -> QPixmap:
        pixmap = QPixmap(str(self.splash_path))
        if pixmap.isNull():
            raise BrandingAssetError(
                f"GridForge splash asset could not be loaded: {self.splash_path}"
            )
        return pixmap

    def apply_application_identity(self, application: QApplication) -> None:
        if not isinstance(application, QApplication):
            raise TypeError("application must be a QApplication instance.")
        application.setApplicationName(self.PRODUCT_NAME)
        application.setApplicationDisplayName(self.PRODUCT_NAME)
        application.setApplicationVersion(self.version)
        icon = self.icon()
        if icon is not None:
            application.setWindowIcon(icon)
