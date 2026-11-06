# ============================================================
# GridForge V2 — Startup Splash
# Author: Subhendu Mishra
# ============================================================

"""Presentation-only startup splash using the existing GridForge artwork."""

from __future__ import annotations

import logging

from ui.core.qt import QApplication, QEventLoop, QSplashScreen, Qt, QTimer

from .branding import BrandingAssetError, BrandingService


LOGGER = logging.getLogger(__name__)


class StartupSplash:
    """Owns only the Qt splash lifetime during real application startup."""

    MIN_DISPLAY_MS = 1500

    def __init__(self, application: QApplication, branding: BrandingService) -> None:
        self._application = application
        self._splash: QSplashScreen | None = None
        self._visible = False

        try:
            pixmap = branding.splash_pixmap()
        except BrandingAssetError as exc:
            LOGGER.error("GridForge startup splash unavailable: %s", exc)
            return

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

    def hold(self, milliseconds: int | None = None) -> None:
        """Keep the splash visible long enough for its artwork to be painted."""
        if not self._visible or self._splash is None:
            return
        delay = self.MIN_DISPLAY_MS if milliseconds is None else max(0, int(milliseconds))
        if delay == 0:
            self._application.processEvents()
            return
        loop = QEventLoop()
        QTimer.singleShot(delay, loop.quit)
        loop.exec()
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
