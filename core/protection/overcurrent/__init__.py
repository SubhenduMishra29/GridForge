"""
GridForge V2 Overcurrent Protection
===================================

Overcurrent protection-function package.

Provides
--------
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
            +-- IECOvercurrentRelay
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


__all__ = [
    "IECOvercurrentRelay",
    "IECOvercurrentSettings",
]
