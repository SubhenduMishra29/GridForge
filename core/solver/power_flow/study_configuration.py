"""Compatibility import for the authoritative Power Flow study configuration.

Author: Subhendu Mishra

The Analysis layer owns study configuration. This module remains only as a
stable import path for existing solver-side callers; it does not define a
second configuration contract.
"""

from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration

__all__ = ["PowerFlowStudyConfiguration"]
