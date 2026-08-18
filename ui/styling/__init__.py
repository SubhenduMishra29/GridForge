# ============================================================

# File: ui/styling/**init**.py

# GridForge V2 — UI Styling Package

# ============================================================

"""
GridForge V2 UI Styling
=======================

The `ui.styling` package contains presentation-level styling
infrastructure for the GridForge graphical interface.

## Responsibilities

```
Theme definitions
Qt stylesheet management
Styling resource access
UI visual configuration
```

## Architecture

```
UI Components
     │
     ▼
  ui.styling
     │
     ├── Theme
     ├── StyleManager
     └── Stylesheet Resource
```

The styling subsystem is presentation infrastructure only.

It does not own:

```
- application state
- engineering state
- Core models
- network topology
- controllers
- commands
- tools
- selection
- canvas behavior
- renderers
- plugins
- engineering calculations
```

## Qt Boundary

Qt dependencies must follow the GridForge UI Qt abstraction
boundary where applicable.

Styling must not introduce direct dependencies on the
engineering Core.

## Public API

The package exposes:

```
Theme
    Immutable presentation theme definition.

DEFAULT_THEME
    Default GridForge presentation theme.

StyleManager
    Application-facing stylesheet and theme service.
```

Theme definitions remain Qt-independent.

StyleManager is responsible for loading and applying the
presentation stylesheet through the centralized Qt boundary.
"""

from **future** import annotations

from .theme import (
DEFAULT_THEME,
Theme,
)

from .style_manager import (
StyleManager,
StyleManagerError,
StylesheetApplyError,
StylesheetLoadError,
)

**all** = [
"DEFAULT_THEME",
"Theme",
"StyleManager",
"StyleManagerError",
"StylesheetApplyError",
"StylesheetLoadError",
]
