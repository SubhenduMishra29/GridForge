# ============================================================
# GridForge V2 — Startup Splash
# Author: Subhendu Mishra
# ============================================================

"""Presentation-only startup splash using the existing GridForge artwork."""

from __future__ import annotations

from ui.core.qt import QApplication, QSplashScreen, Qt

from .branding import BrandingService


class StartupSplash:
    """Owns only the Qt splash lifetime during real application startup."""

    def __init__(self, application: QApplication, branding: BrandingService) -> None:
        self._application = application
        self._splash = QSplashScreen(
            branding.splash_pixmap(),
            Qt.WindowType.SplashScreen | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._splash.setWindowTitle(branding.PRODUCT_NAME)
        self._visible = False

    @property
    def widget(self) -> QSplashScreen:
        return self._splash

    @property
    def visible(self) -> bool:
        return self._visible

    def show(self, message: str | None = None) -> None:
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
        if not self._visible:
            return
        self._splash.showMessage(
            message,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        )
        self._application.processEvents()

    def finish(self, main_window: object) -> None:
        if not self._visible:
            return
        self._splash.finish(main_window)
        self._visible = False

    def close(self) -> None:
        if not self._visible:
            return
        self._splash.close()
        self._visible = False
