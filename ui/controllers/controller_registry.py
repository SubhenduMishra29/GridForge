# ============================================================
# File: ui/controllers/controller_registry.py
# GridForge V2 — UI Controller Registry
# ============================================================
"""
UI Controller Registry for GridForge V2.

Purpose
-------
ControllerRegistry provides explicit registration and lookup of
UI controller instances.

It is intentionally small and deterministic.

The registry does NOT:

    - discover controllers automatically;
    - import concrete controllers automatically;
    - instantiate controllers;
    - modify Core state;
    - manage controller lifecycle;
    - implement controller behavior;
    - create plugins;
    - own application state.

Controller construction and dependency injection belong to the
application/plugin composition layer.

Architecture
------------

    Application Bootstrap
            │
            ├── construct controllers
            │
            └── register(...)
                    │
                    ▼
             ControllerRegistry
                    │
                    ▼
              UI Components

Design Rule
-----------
Concrete controller imports remain explicit.

This registry intentionally contains no imports of:

    CanvasController
    InteractionController
    NavigationController
    SelectionController
    ToolController
    CommandController

That keeps the registry generic and prevents circular
dependencies during UI composition.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any


class ControllerRegistry:
    """
    Registry of explicitly constructed UI controllers.

    Controller identifiers are strings.

    Example
    -------

        registry = ControllerRegistry()

        registry.register(
            "canvas",
            canvas_controller,
        )

        controller = registry.get("canvas")
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        """
        Initialize an empty controller registry.
        """

        self._controllers: dict[
            str,
            Any,
        ] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        controller_id: str,
        controller: Any,
        *,
        replace: bool = False,
    ) -> Any:
        """
        Register a controller instance.

        Parameters
        ----------
        controller_id:
            Stable registry identifier.

        controller:
            Already-constructed controller instance.

        replace:
            Allow replacing an existing controller when True.

        Returns
        -------
        Any
            The registered controller.

        Raises
        ------
        TypeError
            If controller_id is not a string.

        ValueError
            If controller_id is empty or controller is None.

        KeyError
            If the identifier is already registered and
            replacement is disabled.
        """

        self._validate_id(
            controller_id
        )

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        if (
            controller_id in self._controllers
            and not replace
        ):
            raise KeyError(
                f"Controller '{controller_id}' "
                "is already registered."
            )

        self._controllers[
            controller_id
        ] = controller

        return controller

    # --------------------------------------------------------

    def unregister(
        self,
        controller_id: str,
    ) -> Any:
        """
        Remove and return a registered controller.

        The registry does not dispose the controller.

        Lifecycle ownership remains with the composition layer.
        """

        self._validate_id(
            controller_id
        )

        try:
            return self._controllers.pop(
                controller_id
            )
        except KeyError as exc:
            raise KeyError(
                f"Controller '{controller_id}' "
                "is not registered."
            ) from exc

    # ========================================================
    # LOOKUP
    # ========================================================

    def get(
        self,
        controller_id: str,
    ) -> Any:
        """
        Return a registered controller.

        Raises
        ------
        KeyError
            If the controller is not registered.
        """

        self._validate_id(
            controller_id
        )

        try:
            return self._controllers[
                controller_id
            ]
        except KeyError as exc:
            raise KeyError(
                f"Controller '{controller_id}' "
                "is not registered."
            ) from exc

    # --------------------------------------------------------

    def get_optional(
        self,
        controller_id: str,
    ) -> Any:
        """
        Return a registered controller or None.

        This method is useful for optional UI infrastructure.
        """

        self._validate_id(
            controller_id
        )

        return self._controllers.get(
            controller_id
        )

    # --------------------------------------------------------

    def resolve(
        self,
        controller_id: str,
    ) -> Any:
        """
        Resolve a controller by identifier.

        This is an explicit alias for get().
        """

        return self.get(
            controller_id
        )

    # ========================================================
    # QUERY
    # ========================================================

    def contains(
        self,
        controller_id: str,
    ) -> bool:
        """
        Return True when controller_id is registered.
        """

        self._validate_id(
            controller_id
        )

        return (
            controller_id
            in self._controllers
        )

    # --------------------------------------------------------

    def has(
        self,
        controller_id: str,
    ) -> bool:
        """
        Alias for contains().
        """

        return self.contains(
            controller_id
        )

    # --------------------------------------------------------

    def __contains__(
        self,
        controller_id: object,
    ) -> bool:
        """
        Support:

            "canvas" in registry

        Invalid/non-string identifiers simply return False.
        """

        if not isinstance(
            controller_id,
            str,
        ):
            return False

        return (
            controller_id
            in self._controllers
        )

    # ========================================================
    # IDENTIFIERS
    # ========================================================

    def ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return all registered controller identifiers.

        Registration order is preserved.
        """

        return tuple(
            self._controllers.keys()
        )

    # --------------------------------------------------------

    def keys(
        self,
    ) -> tuple[str, ...]:
        """
        Alias for ids().
        """

        return self.ids()

    # ========================================================
    # VALUES
    # ========================================================

    def values(
        self,
    ) -> tuple[Any, ...]:
        """
        Return all registered controller instances.

        Registration order is preserved.
        """

        return tuple(
            self._controllers.values()
        )

    # ========================================================
    # ITEMS
    # ========================================================

    def items(
        self,
    ) -> tuple[
        tuple[str, Any],
        ...,
    ]:
        """
        Return registered controller identifier/instance pairs.
        """

        return tuple(
            self._controllers.items()
        )

    # ========================================================
    # ITERATION
    # ========================================================

    def __iter__(
        self,
    ) -> Iterator[str]:
        """
        Iterate over registered controller identifiers.
        """

        return iter(
            self._controllers
        )

    # --------------------------------------------------------

    def __len__(
        self,
    ) -> int:
        """
        Return the number of registered controllers.
        """

        return len(
            self._controllers
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove all registered controllers.

        Controllers themselves are not disposed.
        """

        self._controllers.clear()

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_id(
        controller_id: str,
    ) -> None:
        """
        Validate a controller identifier.

        This validates only the registry key format.

        It does not validate controller implementation types.
        """

        if not isinstance(
            controller_id,
            str,
        ):
            raise TypeError(
                "controller_id must be a string."
            )

        if not controller_id.strip():
            raise ValueError(
                "controller_id must not be empty."
            )

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot.

        Controller instances themselves are not serialized.
        """

        return {
            "count": len(
                self._controllers
            ),
            "controller_ids": self.ids(),
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "ControllerRegistry("
            f"count={len(self._controllers)}, "
            f"ids={self.ids()!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ControllerRegistry",
]
