"""GridForge Core domain error contract.

Core-domain mutations expose semantic failures instead of requiring
Application callers to interpret arbitrary built-in exceptions.
"""

from __future__ import annotations


class CoreError(Exception):
    """Base exception for failures owned by the Core layer."""


class InvalidCallerContractError(CoreError):
    """The caller supplied an invalid mutation contract or argument."""


class InvalidDomainStateError(CoreError):
    """A proposed mutation violates Core engineering invariants."""


class InvalidStructuralRelationshipError(CoreError):
    """A proposed local relationship violates Core structural rules."""


class InfrastructureError(CoreError):
    """An infrastructure failure occurred while executing a Core operation."""


__all__ = (
    "CoreError",
    "InvalidCallerContractError",
    "InvalidDomainStateError",
    "InvalidStructuralRelationshipError",
    "InfrastructureError",
)
