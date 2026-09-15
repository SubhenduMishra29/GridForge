"""
GridForge V2 Overcurrent Protection
===================================

Overcurrent protection-function package.

Provides
--------
InstantaneousOvercurrentRelay
    ANSI 50 instantaneous overcurrent protection function.

InstantaneousOvercurrentSettings
    Immutable configuration for an ANSI 50 protection function.

IECOvercurrentRelay
    IEC 51 inverse-time overcurrent protection function.

IECOvercurrentSettings
    Immutable configuration for an IEC 51 protection function.

Architecture
------------
Physical Relay
    |
    +-- ProtectionElement
            |
            +-- InstantaneousOvercurrentRelay / IECOvercurrentRelay
                    |
                    +-- RelayInput
                    |
                    +-- ProtectionDecision

IEC protection mathematics is implemented in:

    core.protection.relay_functions

The package does not own:

    * physical Relay state;
    * MeasurementChannel state;
    * network topology;
    * breaker state;
    * simulation scheduling;
    * persistence;
    * GUI state.
"""

from core.protection.overcurrent.iec_relay import (
    IECOvercurrentRelay,
    IECOvercurrentSettings,
)
from core.protection.overcurrent.instantaneous_relay import (
    InstantaneousOvercurrentRelay,
    InstantaneousOvercurrentSettings,
)


__all__ = [
    "InstantaneousOvercurrentRelay",
    "InstantaneousOvercurrentSettings",
    "IECOvercurrentRelay",
    "IECOvercurrentSettings",
]
