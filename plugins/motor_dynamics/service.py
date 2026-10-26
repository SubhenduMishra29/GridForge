"""Compatibility exports for the Application-owned motor draft service.

Author: Subhendu Mishra

Implementation lives in core.application.services so the headless composition
root can construct it without importing UI plugin modules.
"""
from core.application.services.motor_dynamics_service import (
    MotorDraftService,
    MotorDynamicsComposition,
)

__all__ = ["MotorDraftService", "MotorDynamicsComposition"]
