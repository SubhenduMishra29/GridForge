"""
base.py

Foundational object definitions for the unified power system model.

This module provides the lowest-level abstractions used across all
grid components. It defines identity, naming, metadata, and operational
state handling.

Design Rules:
-------------
- No electrical calculations
- No solver logic
- No topology logic
- No numerical indexing
- Must remain stable once finalized

All higher-level objects (Bus, Line, Generator, etc.) inherit from here.
"""


class GridObject:
    """
    Root class for all model objects.

    Responsibilities:
    - Unique identification
    - Human-readable naming
    - Extensible metadata storage

    This class must remain minimal and stable.
    """

    def __init__(self, id: str, name: str = ""):
        """
        Parameters
        ----------
        id : str
            Globally unique identifier for the object.
            This is used internally for indexing and mapping.

        name : str, optional
            Human-readable name (not required to be unique).
        """

        if not id or not isinstance(id, str):
            raise ValueError("GridObject 'id' must be a non-empty string")

        # Unique identifier (critical for mapping and indexing)
        self.id = id

        # Optional display name
        self.name = name

        # Flexible metadata container for extensions
        # Example uses:
        #   - GIS data (lat/lon)
        #   - external system IDs
        #   - custom tags
        self.metadata: dict = {}

    def __repr__(self):
        """
        Developer-friendly representation.
        """
        return f"<{self.__class__.__name__} id='{self.id}'>"

    def __eq__(self, other):
        """
        Equality based on unique ID.
        """
        if not isinstance(other, GridObject):
            return False
        return self.id == other.id

    def __hash__(self):
        """
        Allows object to be used in sets/dicts.
        """
        return hash(self.id)
class ElectricalObject(GridObject):
    """
    Base class for all electrical components in the network.

    Extends GridObject by adding operational state.

    Examples of subclasses:
    - Bus
    - Line
    - Transformer
    - Generator
    - Load
    - Shunt
    """

    def __init__(self, id: str, name: str = "", in_service: bool = True):
        """
        Parameters
        ----------
        in_service : bool
            Indicates whether the element is active in the network.

            If False:
            - It should be ignored in Y-bus formation
            - It should be excluded from topology
            - It should not participate in power flow
        """

        super().__init__(id, name)

        # Operational flag
        self.in_service = bool(in_service)

    def is_active(self) -> bool:
        """
        Returns True if the element is active in the system.
        """
        return self.in_service

    def deactivate(self):
        """
        Set element out of service.
        """
        self.in_service = False

    def activate(self):
        """
        Set element in service.
        """
        self.in_service = True
