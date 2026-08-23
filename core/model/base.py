# core/model/base.py
"""
GridForge V2 Model Layer
========================

Author:
    Subhendu Mishra

Common base class for all GridForge electrical and engineering
domain-model objects.

Responsibilities
----------------
ElectricalObject provides only the common model-object contract:

    - stable object identifier
    - human-readable object name
    - type-aware equality
    - consistent hashing
    - common diagnostics
    - validation entry point
    - developer-facing representation

ElectricalObject intentionally contains NO:

    - electrical calculations
    - per-unit calculations
    - numerical solver logic
    - network topology logic
    - graph algorithms
    - GUI state
    - rendering state
    - dynamic simulation logic
    - protection logic
    - control logic

Those responsibilities belong to their respective GridForge layers.

Identity and Registry Ownership
--------------------------------
ElectricalObject does not enforce global identifier uniqueness.

Identifier uniqueness is the responsibility of the owning registry
or container, such as Grid.

The object identifier represents the stable identity of the model
object.

Architecture
------------
All specialized GridForge model objects should derive from
ElectricalObject unless there is a documented architectural reason
not to do so.

Specialized models may define a class-level ``TYPE`` constant.

Example:

    class Bus(ElectricalObject):
        TYPE = "BUS"

The base class uses ``TYPE`` when available for canonical diagnostic
type information.

Validation Contract
-------------------
ElectricalObject defines the common public validation interface:

    validate()

The default implementation performs only base-object validation.

Specialized model classes should override:

    validate_parameters()

when they have domain-specific parameter constraints.

The base class must not know the electrical parameters of derived
objects.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any


class ElectricalObject:
    """
    Root identity class for GridForge model objects.

    Parameters
    ----------
    id:
        Stable object identifier within the owning registry.

    name:
        Human-readable object name.

        If omitted or empty, ``id`` is used as the name.

    Notes
    -----
    ElectricalObject provides identity, validation, and diagnostics
    only.

    It does not perform electrical calculations, manage topology,
    communicate with the GUI, execute numerical studies, or implement
    protection/simulation behaviour.

    Identifier uniqueness is enforced by the owning container,
    such as Grid.
    """

    # -----------------------------------------------------------------
    # Canonical type
    # -----------------------------------------------------------------

    TYPE = "ELECTRICAL_OBJECT"

    def __init__(
        self,
        id: str,
        name: str = "",
    ) -> None:
        """
        Initialize the common model-object identity.
        """

        # =============================================================
        # IDENTIFIER VALIDATION
        # =============================================================

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

        # =============================================================
        # IDENTITY
        # =============================================================

        self.id = id

        # =============================================================
        # NAME VALIDATION
        # =============================================================

        if name is None:
            name = ""

        if not isinstance(name, str):
            raise TypeError(
                "Object name must be a string."
            )

        name = name.strip()

        # If no explicit display name is supplied, use the ID.
        self.name = name or id

    # =================================================================
    # TYPE
    # =================================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge model type.

        Specialized models should normally define their own ``TYPE``.
        """

        model_type = getattr(
            self.__class__,
            "TYPE",
            None,
        )

        if not isinstance(model_type, str):
            return self.__class__.__name__

        model_type = model_type.strip()

        return model_type or self.__class__.__name__

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate base-object parameters.

        The base object has only identity/name constraints, which are
        already enforced during construction.

        Specialized models should override this method when they have
        domain-specific parameters to validate.

        Returns
        -------
        bool
            ``True`` when validation succeeds.
        """

        if not isinstance(self.id, str):
            raise TypeError(
                "Object ID must be a string."
            )

        if not self.id.strip():
            raise ValueError(
                "Object ID cannot be empty."
            )

        if not isinstance(self.name, str):
            raise TypeError(
                "Object name must be a string."
            )

        if not self.name.strip():
            raise ValueError(
                "Object name cannot be empty."
            )

        return True

    def validate(self) -> bool:
        """
        Public GridForge model validation entry point.

        Specialized model classes may override
        ``validate_parameters()`` and inherit this method.
        """

        return self.validate_parameters()

    # =================================================================
    # IDENTITY
    # =================================================================

    def __eq__(
        self,
        other: object,
    ) -> bool:
        """
        Compare two model objects by concrete type and identifier.

        Two objects are equal when:

            1. They have the same concrete model class.
            2. They have the same stable identifier.

        Objects from different model classes are not equal even when
        their identifiers are identical.

        Examples
        --------
        ``Bus("B1") == Bus("B1")``

        ``Bus("B1") != Line("B1")``
        """

        if self is other:
            return True

        if not isinstance(
            other,
            self.__class__,
        ):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        """
        Return a hash consistent with ``__eq__``.
        """

        return hash(
            (
                self.__class__,
                self.id,
            )
        )

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return common model-object identity information.

        Specialized model classes may extend this dictionary with
        domain-specific information.

        Returns
        -------
        dict
            Contains:

                id
                name
                type
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.element_type,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

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


__all__ = [
    "ElectricalObject",
]
