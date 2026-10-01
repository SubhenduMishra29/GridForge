# ============================================================
# GridForge V2 — Startup Splash
# Author: Subhendu Mishra
# ============================================================

"""Presentation-only startup splash using the existing GridForge artwork."""

from __future__ import annotations

import logging

from ui.core.qt import QApplication, QColor, QPixmap, QSplashScreen, Qt

from .branding import BrandingService


LOGGER = logging.getLogger(__name__)


class StartupSplash:
    """Owns only the Qt splash lifetime during real application startup."""

    def __init__(self, application: QApplication, branding: BrandingService) -> None:
        self._application = application
        self._splash: QSplashScreen | None = None
        self._visible = False

        # Keep the startup splash lifecycle and status messaging, but do not
        # render the application logo/artwork on the splash surface.
        pixmap = QPixmap(520, 180)
        pixmap.fill(QColor("#FFFFFF"))

        self._splash = QSplashScreen(
            pixmap,
            Qt.WindowType.SplashScreen | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._splash.setWindowTitle(branding.PRODUCT_NAME)

    @property
    def widget(self) -> QSplashScreen | None:
        return self._splash

    @property
    def visible(self) -> bool:
        return self._visible

    def show(self, message: str | None = None) -> None:
        if self._splash is None:
            return
        if message:
            self._splash.showMessage(
                message,
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            )
        self._splash.show()
        self._splash.raise_()
        self._visible = True
        self._application.processEvents()

    def status(self, message: str) -> None:
        if not self._visible or self._splash is None:
            return
        self._splash.showMessage(
            message,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        )
        self._application.processEvents()

    def finish(self, main_window: object) -> None:
        if not self._visible or self._splash is None:
            return
        self._splash.finish(main_window)
        self._visible = False

    def close(self) -> None:
        if not self._visible or self._splash is None:
            return
        self._splash.close()
        self._visible = False
