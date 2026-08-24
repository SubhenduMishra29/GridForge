# ============================================================
# File: core/model/base.py
# GridForge V2 — Model Layer
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2
============

Module:
    core.model.base

Purpose
-------
Defines the common identity and validation contract for GridForge
electrical and engineering model objects.

Responsibilities
----------------
ElectricalObject provides only:

    * stable object identity;
    * human-readable name;
    * canonical model type;
    * equality;
    * stable hashing;
    * common validation;
    * common diagnostics;
    * developer-facing representation.

ElectricalObject intentionally contains NO:

    * electrical calculations;
    * per-unit calculations;
    * numerical solver logic;
    * network topology logic;
    * graph algorithms;
    * GUI state;
    * rendering state;
    * dynamic simulation logic;
    * protection logic;
    * control logic.

Those responsibilities belong to their respective GridForge layers.

Identity Contract
-----------------
``id`` is the stable identity of the model object.

The identifier:

    * must be a non-empty string;
    * is assigned during construction;
    * cannot be changed after construction;
    * participates in equality;
    * participates in hashing.

Global identifier uniqueness is NOT enforced by ElectricalObject.

Uniqueness is the responsibility of the owning registry/container.

Name Contract
-------------
``name`` is a human-readable display name.

Unlike ``id``, ``name`` is intentionally mutable because engineers
may rename model objects after creation.

If no name is supplied, the identifier is used as the initial name.

Type Contract
-------------
Specialized model classes should normally define a class-level
``TYPE`` constant.

Example:

    class Bus(ElectricalObject):
        TYPE = "BUS"

Validation Contract
-------------------
ElectricalObject defines the public validation entry point:

    validate()

Base validation is implemented by:

    validate_parameters()

Specialized model classes should override ``validate_parameters()``
when they introduce domain-specific parameter constraints.

Equality Contract
-----------------
Two model objects are equal when:

    1. they have the same concrete model class; and
    2. they have the same stable identifier.

Hashing follows the same identity contract.

Because the identifier is immutable, hash stability is guaranteed.

Architecture
------------
ElectricalObject is a Core Model contract.

It must remain independent of:

    * Application;
    * UI;
    * Qt;
    * SLD;
    * canvas;
    * renderers;
    * plugins;
    * Network graph implementation;
    * solvers;
    * analysis engines.

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

        If omitted or empty, ``id`` is used.

    Notes
    -----
    ``id`` is immutable after construction.

    ``name`` remains mutable because it represents a human-readable
    engineering/display name rather than object identity.
    """

    # =================================================================
    # CANONICAL TYPE
    # =================================================================

    TYPE = "ELECTRICAL_OBJECT"

    # =================================================================
    # CONSTRUCTION
    # =================================================================

    def __init__(
        self,
        id: str,
        name: str = "",
    ) -> None:
        """
        Initialize the common model-object identity.
        """

        # -------------------------------------------------------------
        # Identifier validation
        # -------------------------------------------------------------

        if id is None:
            raise ValueError(
                "Object ID cannot be None."
            )

        if not isinstance(id, str):
            raise TypeError(
                "Object ID must be a string."
            )

        normalized_id = id.strip()

        if not normalized_id:
            raise ValueError(
                "Object ID cannot be empty."
            )

        # -------------------------------------------------------------
        # Name validation
        # -------------------------------------------------------------

        if name is None:
            name = ""

        if not isinstance(name, str):
            raise TypeError(
                "Object name must be a string."
            )

        normalized_name = name.strip()

        # -------------------------------------------------------------
        # Stable identity
        # -------------------------------------------------------------
        #
        # Use object.__setattr__ so subclasses can inherit the
        # immutable identity contract without requiring a property
        # setter.
        #
        # ``_id`` is never reassigned after construction.
        # -------------------------------------------------------------

        object.__setattr__(
            self,
            "_id",
            normalized_id,
        )

        # -------------------------------------------------------------
        # Human-readable name
        # -------------------------------------------------------------

        self.name = normalized_name or normalized_id

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def id(self) -> str:
        """
        Return the stable object identifier.

        The returned identifier cannot be changed through the public
        ``id`` property.
        """

        return self._id

    @id.setter
    def id(self, value: str) -> None:
        """
        Prevent modification of stable object identity.
        """

        raise AttributeError(
            "ElectricalObject.id is immutable after construction."
        )

    # =================================================================
    # TYPE
    # =================================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge model type.

        Specialized model classes should normally define their own
        ``TYPE`` class attribute.
        """

        model_type = getattr(
            self.__class__,
            "TYPE",
            None,
        )

        if not isinstance(model_type, str):
            return self.__class__.__name__

        model_type = model_type.strip()

        return (
            model_type
            or self.__class__.__name__
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate base-object parameters.

        Specialized model classes may override this method and should
        normally call ``super().validate_parameters()`` first.

        Returns
        -------
        bool
            True when validation succeeds.
        """

        # -------------------------------------------------------------
        # Identity
        # -------------------------------------------------------------

        if not isinstance(self._id, str):
            raise TypeError(
                "Object ID must be a string."
            )

        if not self._id.strip():
            raise ValueError(
                "Object ID cannot be empty."
            )

        # -------------------------------------------------------------
        # Name
        # -------------------------------------------------------------

        if not isinstance(self.name, str):
            raise TypeError(
                "Object name must be a string."
            )

        if not self.name.strip():
            raise ValueError(
                "Object name cannot be empty."
            )

        return True

    # -----------------------------------------------------------------

    def validate(self) -> bool:
        """
        Public GridForge model validation entry point.

        Specialized model classes can implement their own parameter
        validation by overriding ``validate_parameters()``.
        """

        return self.validate_parameters()

    # =================================================================
    # EQUALITY
    # =================================================================

    def __eq__(
        self,
        other: object,
    ) -> bool:
        """
        Compare model objects by concrete type and stable identity.

        Equality requires:

            same concrete class
            AND
            same stable object ID.

        Examples
        --------
        Bus("B1") == Bus("B1")
        Bus("B1") != Line("B1")
        """

        if self is other:
            return True

        if other is None:
            return NotImplemented

        if type(self) is not type(other):
            return NotImplemented

        return self.id == other.id  # type: ignore[attr-defined]

    # =================================================================
    # HASHING
    # =================================================================

    def __hash__(self) -> int:
        """
        Return a stable hash based on concrete type and immutable ID.

        Because ``id`` cannot change after construction, the hash
        remains stable for the lifetime of the object.
        """

        return hash(
            (
                type(self),
                self.id,
            )
        )

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return common model-object identity information.

        Specialized models may extend this dictionary with
        domain-specific diagnostic information.

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

            <Bus id=BUS-001>
        """

        return (
            f"<{self.__class__.__name__} "
            f"id={self.id}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ElectricalObject",
]
