# ============================================================
# File: ui/sld/sld_read_adapter.py
# GridForge V2 — SLD Read Adapter
# Author: Subhendu Mishra
# ============================================================
"""Adapt Application read snapshots into canonical SLD semantics."""

from __future__ import annotations

from core.application.read_models import ElementReadModel, NetworkReadModel, ProtectionReadModel

from .sld_vocabulary import semantic_type


class SLDReadAdapter:
    """Presentation-owned adapter from Application read DTOs to SLD DTOs."""

    def element(self, read_model: ElementReadModel) -> ElementReadModel:
        """Map one immutable Application element snapshot to SLD semantics."""
        if not isinstance(read_model, ElementReadModel):
            raise TypeError("read_model must be an ElementReadModel")
        return ElementReadModel(
            object_id=read_model.object_id,
            element_type=semantic_type(read_model.element_type),
            labels=read_model.labels,
            connectivity_refs=read_model.connectivity_refs,
            attributes=read_model.attributes,
        )

    def network(self, read_model: NetworkReadModel) -> NetworkReadModel:
        """Map the complete Application network snapshot without Core access."""
        if not isinstance(read_model, NetworkReadModel):
            raise TypeError("read_model must be a NetworkReadModel")
        return NetworkReadModel(elements=tuple(self.element(element) for element in read_model.elements))

    def protection(self, read_model: ProtectionReadModel) -> NetworkReadModel:
        """Project protection-domain associations into the SLD Relay vocabulary."""
        if not isinstance(read_model, ProtectionReadModel):
            raise TypeError("read_model must be a ProtectionReadModel")
        elements = []
        for relay in read_model.relays:
            binding_refs = tuple(
                binding.channel_id
                for binding in relay.input_channel_bindings
                if binding.channel_id is not None
            )
            bindings = tuple(
                (binding.input_name, binding.channel_id)
                for binding in relay.input_channel_bindings
            )
            elements.append(ElementReadModel(
                object_id=relay.object_id,
                element_type=semantic_type("RELAY"),
                labels={"name": relay.name},
                connectivity_refs=binding_refs,
                attributes={
                    "association_domain": "protection",
                    "relay_type": relay.relay_type,
                    "function_type": relay.function_type,
                    "plugin_id": relay.plugin_id,
                    "settings": relay.settings,
                    "in_service": relay.in_service,
                    "enabled": relay.enabled,
                    "blocked": relay.blocked,
                    "picked_up": relay.picked_up,
                    "tripped": relay.tripped,
                    "input_channel_bindings": bindings,
                },
            ))
        return NetworkReadModel(elements=tuple(elements))


__all__ = ["SLDReadAdapter"]
