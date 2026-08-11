"""
GridForge AVR Plugin Descriptor
"""

from __future__ import annotations

from .model import AVRPlugin


PLUGIN_ID = "gridforge.dynamics.avr"
PLUGIN_TYPE = "dynamics.avr"
PLUGIN_VERSION = "1.0.0"


def create_avr_plugin(
    *,
    id: str = "",
    name: str = "",
    **parameters,
) -> AVRPlugin:
    """
    Factory used by the GridForge plugin system.
    """

    from core.model.avr import AVR

    avr = AVR(
        **parameters,
    )

    return AVRPlugin(
        avr=avr,
        id=id,
        name=name,
    )


def plugin_info() -> dict:
    """
    Return plugin metadata.
    """

    return {
        "id": PLUGIN_ID,
        "type": PLUGIN_TYPE,
        "version": PLUGIN_VERSION,
        "name": "GridForge First-Order AVR",
        "model": "FIRST_ORDER_AVR",
        "state_names": (
            "Efd",
        ),
        "state_size": 1,
    }
