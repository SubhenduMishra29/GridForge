"""Application-facing protection runtime composition boundary."""

from __future__ import annotations

from typing import Any, Mapping

from core.network.network import Network

from .factory import ProtectionFactory
from .project_configuration import ProtectionProjectConfiguration
from .protection_system import ProtectionSystem
from .relay_input import DerivedRelayMeasurement, RelayInput
from .input_contracts import validate_protection_input_contracts
from .configuration_fingerprint import canonical_configuration_value
from .directional.snapshot import _AuthoritativeDirectionalSnapshot, _DIRECTIONAL_SNAPSHOT_SEAL
import math


class ProtectionRuntime:
    """Compose project protection configuration against authoritative Core objects."""

    def __init__(
        self,
        network: Network,
        configuration: ProtectionProjectConfiguration,
        *,
        activation_generation: int,
        snapshot_issuance_capability: object | None = None,
    ) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        if not isinstance(configuration, ProtectionProjectConfiguration):
            raise TypeError("configuration must be ProtectionProjectConfiguration.")
        if isinstance(activation_generation, bool) or not isinstance(activation_generation, int) or activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        self._network = network
        self._configuration = configuration
        self._project_id = str(configuration.project_id)
        self._activation_generation = activation_generation
        self._snapshot_issuance_capability = snapshot_issuance_capability
        self._snapshot_issuer = object()
        self._system = ProtectionSystem()
        self._channels: dict[str, Any] = {}
        self._composed_configuration_snapshot: Any | None = None
        self._composed_equipment_state_snapshot: Any | None = None

    def issue_directional_snapshot(
        self,
        *,
        capability: object,
        element_id: str,
        voltage_channel_id: str,
        current_channel_id: str,
        voltage_channel: Any,
        current_channel: Any,
        voltage_value: complex,
        current_value: complex,
        sample_timestamp: float,
        voltage_sample_sequence: Any,
        current_sample_sequence: Any,
    ) -> _AuthoritativeDirectionalSnapshot:
        """Issue a snapshot for this exact composed runtime.

        Application supplies the private capability only after validating
        live sample quality, freshness, timestamp and sequence coherence.
        All project/runtime/configuration/channel identities are derived
        here, never accepted as caller assertions.
        """
        if self._snapshot_issuance_capability is None or capability is not self._snapshot_issuance_capability:
            raise PermissionError("Directional snapshot issuance requires the owning Application capability.")
        if self._composed_configuration_snapshot is None or not self.configuration_matches_composition:
            raise RuntimeError("Directional snapshot issuance requires the active composed configuration.")
        if self._composed_equipment_state_snapshot is None or not self.equipment_state_matches_composition:
            raise RuntimeError("Directional snapshot issuance requires unchanged composed equipment state.")
        element = next((item for item in self._configuration.elements if item.element_id == element_id), None)
        if element is None or not element.enabled or str(element.function_code).strip().upper() != "67":
            raise ValueError("Directional snapshot element is not an enabled ANSI 67 element in this runtime.")
        if element.input_channel_ids.get("voltage") != voltage_channel_id or element.input_channel_ids.get("current") != current_channel_id:
            raise ValueError("Directional snapshot channel IDs do not match configured element bindings.")
        if self._channels.get(voltage_channel_id) is not voltage_channel or self._channels.get(current_channel_id) is not current_channel:
            raise ValueError("Directional snapshot channel objects do not belong to this composed runtime.")
        if voltage_channel is current_channel or voltage_channel_id == current_channel_id:
            raise ValueError("Directional voltage and current channels must be distinct.")
        if not isinstance(voltage_value, complex) or not isinstance(current_value, complex):
            raise TypeError("Directional snapshots require complex voltage and current phasors.")
        for name, value in (("voltage", voltage_value), ("current", current_value)):
            if not math.isfinite(value.real) or not math.isfinite(value.imag) or abs(value) == 0.0:
                raise ValueError(f"Directional {name} phasor must be finite and nonzero.")
        if getattr(voltage_channel, "sample_sequence", None) != voltage_sample_sequence or getattr(current_channel, "sample_sequence", None) != current_sample_sequence:
            raise RuntimeError("Directional sample sequence changed after Application validation.")
        timestamp = float(sample_timestamp)
        if not math.isfinite(timestamp):
            raise ValueError("Directional sample timestamp must be finite.")
        return _AuthoritativeDirectionalSnapshot(
            _seal=_DIRECTIONAL_SNAPSHOT_SEAL,
            _issuer=self._snapshot_issuer,
            element_id=element_id,
            voltage_value=voltage_value,
            current_value=current_value,
            voltage_angle=math.degrees(math.atan2(voltage_value.imag, voltage_value.real)),
            current_angle=math.degrees(math.atan2(current_value.imag, current_value.real)),
            voltage_channel_id=voltage_channel_id,
            current_channel_id=current_channel_id,
            voltage_channel_identity=id(voltage_channel),
            current_channel_identity=id(current_channel),
            sample_timestamp=timestamp,
            voltage_sample_sequence=voltage_sample_sequence,
            current_sample_sequence=current_sample_sequence,
            project_id=self._project_id,
            activation_generation=self._activation_generation,
            configuration_identity=id(self._configuration),
            runtime_identity=id(self),
        )
    @property
    def snapshot_issuer(self) -> object:
        """Opaque per-runtime identity token for validating issued snapshots."""
        return self._snapshot_issuer

    @property
    def activation_generation(self) -> int:
        """Project lifecycle generation for which this runtime was composed."""
        return self._activation_generation

    @property
    def project_id(self) -> str:
        """Project identity captured from the configuration at construction."""
        return self._project_id

    @property
    def network(self) -> Network:
        return self._network

    @property
    def system(self) -> ProtectionSystem:
        return self._system

    @property
    def configuration(self) -> ProtectionProjectConfiguration:
        return self._configuration

    @property
    def channels(self) -> Mapping[str, Any]:
        """Exact channel objects used by the current runtime composition."""
        return dict(self._channels)

    @property
    def configuration_matches_composition(self) -> bool:
        """Whether mutable project configuration still matches the composed runtime."""
        snapshot = self._composed_configuration_snapshot
        if snapshot is None:
            return False
        try:
            return canonical_configuration_value(self._configuration.to_dict()) == snapshot
        except (TypeError, ValueError):
            return False


    @staticmethod
    def _equipment_state_fingerprint(network: Network) -> tuple[Any, ...]:
        """Capture composition-relevant CT/CVT/PT and Relay state, excluding samples."""
        specifications = (
            ("ct", getattr(network, "current_transformers", ()),
             ("name", "primary_rated_current_a", "secondary_rated_current_a", "burden_va", "accuracy_class", "frequency_hz", "polarity", "in_service"),
             ("p1_endpoint", "p2_endpoint", "s1_endpoint", "s2_endpoint")),
            ("cvt", getattr(network, "capacitive_voltage_transformers", ()),
             ("name", "rated_primary_voltage_kv", "rated_secondary_voltage_v", "accuracy_class", "rated_burden_va", "polarity", "frequency_hz", "in_service"),
             ("h1_endpoint", "h2_endpoint", "x1_endpoint", "x2_endpoint")),
            ("pt", getattr(network, "potential_transformers", ()),
             ("name", "primary_voltage_kv", "secondary_voltage_v", "accuracy_class", "burden_va", "phase_displacement_deg", "in_service"),
             ("primary_a_endpoint", "primary_b_endpoint", "secondary_a_endpoint", "secondary_b_endpoint")),
        )
        captured: list[tuple[Any, ...]] = []
        for kind, equipment, fields, endpoint_fields in specifications:
            for item in equipment:
                values = tuple((field, repr(getattr(item, field, None))) for field in fields)
                endpoints = tuple(
                    (field, None if (endpoint := getattr(item, field, None)) is None
                     else (type(endpoint).__name__, getattr(endpoint, "id", None), id(endpoint)))
                    for field in endpoint_fields
                )
                captured.append((kind, str(getattr(item, "id", "")), values, endpoints))
        for relay in getattr(network, "relays", ()):
            values = tuple((field, repr(getattr(relay, field, default))) for field, default in (
                ("relay_type", ""), ("type", ""), ("function_type", ""),
                ("plugin_id", None), ("settings", {}),
                ("in_service", False), ("enabled", False), ("blocked", False),
                ("picked_up", False), ("tripped", False),
            ))
            captured.append(("relay", str(getattr(relay, "id", "")), values, ()))
        return tuple(sorted(captured, key=lambda item: (item[0], item[1])))

    @property
    def equipment_state_snapshot(self) -> tuple[Any, ...] | None:
        """Return the immutable equipment-state baseline for transactional refresh/restore."""
        return self._composed_equipment_state_snapshot

    def refresh_equipment_state_snapshot(self) -> tuple[Any, ...]:
        """Advance the equipment-state baseline after an in-place Application mutation.

        Application may use this only when a complete per-element dependency
        registry will independently guard every pending Protection decision.
        """
        snapshot = self._equipment_state_fingerprint(self._network)
        self._composed_equipment_state_snapshot = snapshot
        return snapshot

    def restore_equipment_state_snapshot(self, snapshot: tuple[Any, ...] | None) -> None:
        """Restore a prior equipment-state baseline after transaction rollback."""
        if snapshot is not None and not isinstance(snapshot, tuple):
            raise TypeError("equipment state snapshot must be a tuple or None.")
        self._composed_equipment_state_snapshot = snapshot

    @property
    def equipment_state_matches_composition(self) -> bool:
        """Whether authoritative instrument/Relay state still matches this composition."""
        snapshot = self._composed_equipment_state_snapshot
        if snapshot is None:
            return False
        try:
            return self._equipment_state_fingerprint(self._network) == snapshot
        except (AttributeError, TypeError, ValueError):
            return False

    def compose(self, channels: Mapping[str, Any]) -> ProtectionSystem:
        """Rebuild runtime composition from project configuration and live channels."""
        if not isinstance(channels, Mapping):
            raise TypeError("channels must be a mapping of channel IDs to MeasurementChannel objects.")

        # Invalidate the previously composed system before any validation or
        # construction work. A failed recomposition must never leave an older
        # system publicly evaluable under a changed configuration or channel
        # mapping. Application transactions retain the previous runtime object
        # separately and restore it through their existing undo/rollback path.
        self._system = ProtectionSystem()
        self._channels = {}
        self._composed_configuration_snapshot = None
        self._composed_equipment_state_snapshot = None

        contract_diagnostics = validate_protection_input_contracts(self._configuration, channels)
        if contract_diagnostics:
            raise ValueError("Protection input-contract validation failed before composition: " + " | ".join(contract_diagnostics))
        configuration_snapshot = canonical_configuration_value(self._configuration.to_dict())

        composed_system = ProtectionSystem()
        composed_channels = dict(channels)
        for item in self._configuration.elements:
            relay = self._network.get_by_id("relay", item.relay_id)
            relay_inputs: dict[str, RelayInput] = {}
            for name, channel_id in item.input_channel_ids.items():
                try:
                    channel = channels[channel_id]
                except KeyError as exc:
                    raise KeyError(
                        f"MeasurementChannel '{channel_id}' required by protection element "
                        f"'{item.element_id}' is not available."
                    ) from exc
                relay_inputs[name] = RelayInput(name, channel)

            if item.function_code in {"50N", "51N"}:
                if item.residual_current_input is None:
                    raise ValueError(
                        f"ANSI {item.function_code} element '{item.element_id}' requires an explicit residual_current_input configuration."
                    )
                if "residual_current" in item.input_channel_ids:
                    raise ValueError(
                        "Residual current is a derived relay input and must not be configured as a physical MeasurementChannel."
                    )
                derived_source = DerivedRelayMeasurement(
                    f"derived:{item.element_id}:residual_current"
                )
                relay_inputs["residual_current"] = RelayInput(
                    "residual_current",
                    derived_source,
                    description="Application-resolved residual-current phasor",
                    metadata={"source_kind": "DERIVED_RESIDUAL_CURRENT"},
                )

            element = ProtectionFactory.create_element(
                relay=relay,
                element_id=item.element_id,
                function_code=item.function_code,
                relay_inputs=relay_inputs,
                settings=item.settings,
                enabled=item.enabled,
                blocked=item.blocked,
                name=item.name,
                priority=item.priority,
                metadata=item.metadata,
            )
            composed_system.add_element(element)
        # The aggregate itself is mutable (transactional updates replace
        # entries in-place), so object identity alone cannot prove that the
        # currently composed system reflects its current contents.
        self._system = composed_system
        self._channels = composed_channels
        self._composed_configuration_snapshot = configuration_snapshot
        self._composed_equipment_state_snapshot = self._equipment_state_fingerprint(self._network)
        return self._system


__all__ = ["ProtectionRuntime"]
