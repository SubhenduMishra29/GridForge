# GridForge V2 — Branding & Splash Screen Final Correction

Date: 2026-09-29
Repository: madhuri196mishra-cpu/GridForge
Branch: main
Author: Subhendu Mishra
Verification mode: Static repository inspection only

## Scope

This pass corrects the existing GridForge branding integration without creating replacement artwork or a second branding architecture.

Authoritative repository assets:
- Logo.png — repository root, PNG, 1,186,133 bytes
- splash.png — repository root, PNG, 1,881,570 bytes

The Git tree contains the authoritative branding implementation modules ui/branding.py and ui/splash_screen.py. No lowercase logo.png asset is present in the repository tree.

## Existing defects identified

1. BrandingService searched lowercase/generic icon aliases and did not explicitly resolve the authoritative case-sensitive Logo.png.
2. Branding resource resolution did not use one shared source-tree/installed-resource strategy for both assets.
3. pyproject.toml packaged splash.png but omitted Logo.png.
4. main.py constructed StartupSplash before installing application identity, reversing the required startup order.
5. Missing/corrupt splash/icon handling was not fully failure-safe.
6. BrandingService.icon() could substitute the splash image for an icon; authoritative application identity is now explicitly Logo.png.

## Corrections

### ui/branding.py
- Added one canonical resource resolver used for both assets.
- Explicitly resolves exact, case-sensitive filenames Logo.png and splash.png.
- Source-tree resolution is rooted from the module/project location, not the current working directory.
- Installed resolution uses sysconfig data/share/gridforge.
- Missing assets emit logging diagnostics instead of silently disappearing.
- Logo.png is the only authoritative application icon.
- Splash artwork is never substituted as an icon.
- Corrupt/unloadable Logo.png produces a diagnostic and does not prevent startup.
- Product name/display name/version remain centralized in BrandingService.
- Icon loading is cached within the service so Application and MainWindow reuse the same resolved identity.

### ui/splash_screen.py
- Startup splash construction now handles a missing/corrupt splash.png without preventing application startup.
- The existing splash.png is passed directly to QSplashScreen; no replacement artwork or artificial delay was introduced.
- Splash status messages remain tied to real startup phases.
- finish() and close() remain idempotent and lifecycle-safe.
- Cleanup remains safe when startup raises after the splash has been shown.

### main.py
Startup order is now: QApplication -> BrandingService -> application identity / Logo.png -> StartupSplash -> real startup initialization -> MainWindow -> MainWindow.setWindowIcon(...) -> MainWindow.show() -> StartupSplash.finish(...).
The existing Application composition root remains the only startup composition root.

### pyproject.toml
Canonical package data now declares both authoritative assets: share/gridforge = [Logo.png, splash.png]. This matches the installed-resource resolution used by BrandingService.

## Static chain verification
The complete source-level chain is established as: Logo.png / splash.png -> BrandingService resource resolution -> QApplication.setWindowIcon(...) -> StartupSplash -> MainWindow.setWindowIcon(...) -> MainWindow.show() -> StartupSplash.finish(...).
Packaging chain: repository root assets -> pyproject.toml data-files -> share/gridforge -> BrandingService installed-resource resolver.
No current-working-directory dependency or developer-specific absolute path was introduced.

## DPI/image handling
The implementation leaves the authoritative raster artwork unmodified and passes it through Qt-native QPixmap/QIcon handling. No fixed-pixel rescaling, aspect-ratio distortion, or artificial stretching was introduced.

## Architecture
- Branding remains presentation/application infrastructure.
- No Core imports or domain changes were introduced.
- No second branding service or second resource resolver was introduced.
- No SLD, topology, command, or electrical-domain authority was changed.

## Runtime boundary
GUI startup, installed-package execution, alternate-working-directory execution, splash appearance, icon appearance, and interactive shutdown were not executed in this environment.
Verification status: STATICALLY VERIFIED — RUNTIME VERIFICATION DEFERRED.

## Asset metadata limitation
Repository metadata confirms both assets are PNG files and provides their exact repository paths and byte sizes. The available GitHub text connector does not expose binary PNG dimensions, so pixel dimensions were not independently decoded in this static pass. No artwork was modified or regenerated.

## Affected Master Register
New branding finding: GF-MASTER-0107.
Title: Branding resource discovery, application icon, splash lifecycle, and packaging.
Status: STATICALLY VERIFIED — RUNTIME VERIFICATION DEFERRED.
Evidence: ui/branding.py, ui/splash_screen.py, main.py, pyproject.toml, Logo.png, splash.png.
Remaining issue: GUI/runtime and installed-distribution execution remain deferred; binary pixel dimensions remain unverified by the available repository interface.

## Final disposition
CORRECTED / STATICALLY VERIFIED — RUNTIME VERIFICATION DEFERRED