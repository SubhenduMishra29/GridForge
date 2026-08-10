"""
injection.py

Defines the abstract interface for all power injections.

An Injection is anything that contributes power (P, Q)
to a bus in the network.

This includes:
- Generators
- Loads
- Future devices (storage, EVs, DERs, etc.)

Design Rules:
-------------
- No topology
- No solver logic
- No state mutation
- Only returns power values
"""


class Injection:
    """
    Abstract interface for power injection devices.
    """

    def get_power(self):
        """
        Return the power injection at the connected bus.

        Returns
        -------
        (p, q) : tuple of floats
            Active and reactive power in per-unit

        Convention:
        -----------
        +P, +Q → injection into the network
        -P, -Q → consumption from the network
        """
        raise NotImplementedError(
            "Injection subclasses must implement get_power()"
        )
