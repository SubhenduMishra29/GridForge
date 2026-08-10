"""
GridForge Electrical Object Base Model
======================================

File:
    core/model/base.py

Defines the common base class for all GridForge electrical
and engineering model objects.

Responsibilities
----------------
- Provide a stable object identifier.
- Provide a human-readable name.
- Provide common identity/diagnostic behavior.

This class intentionally contains NO:
- Electrical calculations
- Numerical solver logic
- Network topology logic
- GUI logic
- Simulation logic
- Protection logic

All specialized model objects inherit from this class.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


class ElectricalObject:
    """
    Base class for GridForge model objects.

    Parameters
    ----------
    id : str
        Unique object identifier within its owning registry.

    name : str, optional
        Human-readable object name.

    Notes
    -----
    ``ElectricalObject`` does not enforce global ID uniqueness.

    ID uniqueness is the responsibility of the owning container,
    such as ``Grid``.
    """

    def __init__(
        self,
        id: str,
        name: str = ""
    ):
        # ---------------------------------------------------------
        # Validate identifier
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Store identity
        # ---------------------------------------------------------

        self.id = id

        # Empty names fall back to the object ID.
        if name is None:
            name = ""

        if not isinstance(name, str):
            raise TypeError(
                "Object name must be a string."
            )

        name = name.strip()

        self.name = name or id

    # =============================================================
    # IDENTITY
    # =============================================================

    def __eq__(self, other):
        """
        Compare model objects by type and identifier.

        Objects of different model classes are not considered equal
        even if they happen to have the same ID.
        """

        if self is other:
            return True

        if not isinstance(
            other,
            self.__class__
        ):
            return NotImplemented

        return self.id == other.id

    def __hash__(self):
        """
        Hash based on object type and stable identifier.
        """

        return hash(
            (
                self.__class__,
                self.id
            )
        )

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict:
        """
        Return the common object identity information.

        Specialized models may extend this method with additional
        electrical parameters.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.__class__.__name__
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<{self.__class__.__name__} "
            f"id={self.id}>"
        )
