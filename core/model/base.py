"""
base.py

Core abstract object definitions for the power system model.

This module defines the foundational classes used across all
grid components. These classes provide identity, naming, and
basic operational status.

No electrical behavior or solver logic should exist here.
"""


class GridObject:
    """
    Base class for ALL objects in the grid model.

    Responsibilities:
    - Unique identification
    - Human-readable naming
    - Extensible metadata storage

    This is intentionally minimal and should remain stable.
    """

    def __init__(self, id: str, name: str = ""):
        """
        Parameters
        ----------
        id : str
            Unique identifier (must be globally unique in the model)
        name : str, optional
            Human-readable label (not required to be unique)
        """

        # Unique identifier used internally (critical for indexing, mapping)
        self.id = id

        # Optional descriptive name (useful for UI, debugging, reporting)
        self.name = name

        # Flexible dictionary for future extensions
        # Examples:
        #   - GIS coordinates
        #   - external IDs
        #   - tags
        self.metadata = {}

    def __repr__(self):
        """
        Developer-friendly representation.
        """
        return f"<{self.__class__.__name__} id={self.id}>"
