# core/model/base.py

"""
GridForge Model Layer
=====================

Common base class for all GridForge electrical and engineering
domain-model objects.

This module defines the fundamental identity contract shared by
GridForge model objects.

Responsibilities
----------------
- Provide a stable object identifier.
- Provide a human-readable object name.
- Provide type-aware equality.
- Provide a consistent hash implementation.
- Provide common diagnostic information.
- Provide a concise developer-facing representation.

This class intentionally contains NO:
- Electrical calculations
- Per-unit calculations
- Numerical solver logic
- Network topology logic
- Graph algorithms
- GUI state or rendering logic
- Dynamic simulation logic
- Protection logic
- Control logic

Those responsibilities belong to their respective GridForge layers.

Identity and Registry Ownership
--------------------------------
ElectricalObject does not enforce global identifier uniqueness.

Identifier uniqueness is the responsibility of the owning registry or
container, such as Grid.

The object identifier is intended to represent the stable identity of
the model object.

Architecture
------------
All specialized GridForge model objects should derive from
ElectricalObject unless there is a documented architectural reason
not to do so.

Examples
--------
Bus
Line
Transformer
Generator
Load
Breaker
Relay
Shunt
Terminal
etc.

GridForge V2 Status
-------------------
This module is part of the frozen GridForge Model Layer V2 baseline.

Changes to this class should not be made casually. Any proposed
modification must demonstrate a genuinely fundamental requirement
that cannot be satisfied through a specialized model class or
higher-level infrastructure.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


class ElectricalObject:
    """
    Root identity class for GridForge model objects.

    Parameters
    ----------
    id : str
        Unique object identifier within the owning registry.

    name : str, optional
        Human-readable object name. If omitted or empty, the object
        identifier is used as the name.

    Notes
    -----
    ``ElectricalObject`` provides identity and diagnostics only.

    It does not perform electrical calculations, manage topology,
    communicate with the GUI, execute numerical studies, or implement
    protection/simulation behavior.

    Identifier uniqueness is enforced by the owning container,
    such as ``Grid``, rather than by this class.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
    ):
        # ============================================================
        # Identifier Validation
        # ============================================================

        if id is None:
            raise ValueError(
                "Object ID cannot be None."
            )

        if not isinstance(id, str):
            raise TypeError(
                "Object ID must be a string."
            )

        id = id.strip()

        if not id:
            raise ValueError(
                "Object ID cannot be empty."
            )

        # ============================================================
        # Identity
        # ============================================================

        self.id = id

        # ============================================================
        # Name Validation
        # ============================================================

        if name is None:
            name = ""

        if not isinstance(name, str):
            raise TypeError(
                "Object name must be a string."
            )

        name = name.strip()

        # Use the object ID when no explicit display name is supplied.
        self.name = name or id

    # ================================================================
    # IDENTITY
    # ================================================================

    def __eq__(self, other: object) -> bool:
        """
        Compare two model objects by concrete type and identifier.

        Two objects are considered equal when:

        1. They are instances of the same concrete model class, and
        2. They have the same object identifier.

        Objects belonging to different model classes are not considered
        equal even if they have identical identifiers.

        Examples
        --------
        ``Bus("B1") == Bus("B1")``

        ``Bus("B1") != Line("B1")``
        """

        if self is other:
            return True

        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        """
        Return a hash based on concrete object type and identifier.

        The hash follows the same identity definition used by
        ``__eq__``.
        """

        return hash(
            (
                self.__class__,
                self.id,
            )
        )

    # ================================================================
    # DIAGNOSTICS
    # ================================================================

    def summary(self) -> dict:
        """
        Return common object identity information.

        Specialized model classes may extend this method with their
        own domain-specific information.

        Returns
        -------
        dict
            Dictionary containing:

            - ``id``   : object identifier
            - ``name`` : human-readable name
            - ``type`` : concrete model class name

        Notes
        -----
        ``summary()`` is a diagnostic/introspection interface.

        It is not, by itself, the GridForge serialization contract.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.__class__.__name__,
        }

    # ================================================================
    # REPRESENTATION
    # ================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.

        Example
        -------
        ``<Bus id=B1>``
        """

        return (
            f"<{self.__class__.__name__} "
            f"id={self.id}>"
        )
