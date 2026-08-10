"""
injection.py

Defines the Injection interface.

All implementations MUST follow the sign convention:

+P, +Q → injection into the network  
-P, -Q → consumption from the network
"""

from abc import ABC, abstractmethod


class Injection(ABC):
    """
    Abstract base class for power injections.
    """

    @abstractmethod
    def get_power(self):
        """
        Returns
        -------
        (P, Q) : tuple of floats

        Sign Convention:
        ----------------
        +P = power injected into network
        -P = power consumed from network
        """
        pass

    @property
    @abstractmethod
    def bus(self):
        """
        Returns the connected bus.
        """
        pass
