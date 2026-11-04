"""Application-owned, per-element Protection dependency identities.

These descriptors are evaluation/dispatch provenance, not Core electrical
state. They intentionally exclude live sample values, timestamps, quality and
producer sequence; those belong to the measurement-sample contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping

from core.model import CurrentTransformer, CVT, PT
from core.network.network import Network
from core.protection.configuration_fingerprint import canonical_configuration_value
from core.protection.project_configuration import (
    DifferentialProtectionSchemeConfiguration,
    ProtectionFunctionConfiguration,
    ProtectionProjectConfiguration,
)


def _fingerprint(value: Any) -> str:
    canonical = canonical_configuration_value(value)
    return sha256(repr(canonical).encode("utf-8")).hexdigest()


def _connected_endpoint_identity(endpoint: Any) -> tuple[Any, ...] | None:
    if endpoint is None:
        return None
    owner = getattr(endpoint, "owner", None)
    role = getattr(endpoint, "role", None)
    owner_id = getattr(owner, "id", None)
    if isinstance(owner_id, str) and owner_id and isinstance(role, str) and role:
        return ("terminal", str(getattr(owner, "TYPE", "")), owner_id, role)
    endpoint_id = getattr(endpoint, "id", None)
    if isinstance(endpoint_id, str) and endpoint_id:
        return ("object", endpoint.__class__.__module__, endpoint.__class__.__qualname__, endpoint_id)
    return ("unsupported", endpoint.__class__.__module__, endpoint.__class__.__qualname__)


def _instrument_configuration(instrument: Any) -> Mapping[str, Any]:
    common: dict[str, Any] = {
        "instrument_id": getattr(instrument, "id", None),
        "instrument_type": str(getattr(instrument, "TYPE", "")).strip().lower(),
        "in_service": getattr(instrument, "in_service", None),
    }
    if isinstance(instrument, CurrentTransformer):
        common.update({
            "primary_rated_current_a": instrument.primary_rated_current_a,
            "secondary_rated_current_a": instrument.secondary_rated_current_a,
            "ratio": instrument.ratio,
            "burden_va": instrument.burden_va,
            "accuracy_class": instrument.accuracy_class,
            "frequency_hz": instrument.frequency_hz,
            "polarity": instrument.polarity,
            "endpoints": {
                "P1": _connected_endpoint_identity(instrument.p1_endpoint),
                "P2": _connected_endpoint_identity(instrument.p2_endpoint),
                "S1": _connected_endpoint_identity(instrument.s1_endpoint),
                "S2": _connected_endpoint_identity(instrument.s2_endpoint),
            },
        })
    elif isinstance(instrument, PT):
        common.update({
            "primary_voltage_kv": instrument.primary_voltage_kv,
            "secondary_voltage_v": instrument.secondary_voltage_v,
            "voltage_ratio": instrument.voltage_ratio,
            "accuracy_class": instrument.accuracy_class,
            "burden_va": instrument.burden_va,
            "phase_displacement_deg": instrument.phase_displacement_deg,
            "endpoints": {
                "primary_a": _connected_endpoint_identity(instrument.primary_a_endpoint),
                "primary_b": _connected_endpoint_identity(instrument.primary_b_endpoint),
                "secondary_a": _connected_endpoint_identity(instrument.secondary_a_endpoint),
                "secondary_b": _connected_endpoint_identity(instrument.secondary_b_endpoint),
            },
        })
    elif isinstance(instrument, CVT):
        common.update({
            "rated_primary_voltage_kv": instrument.rated_primary_voltage_kv,
            "rated_secondary_voltage_v": instrument.rated_secondary_voltage_v,
            "voltage_ratio": instrument.voltage_ratio,
            "accuracy_class": instrument.accuracy_class,
            "rated_burden_va": instrument.rated_burden_va,
            "polarity": instrument.polarity,
            "frequency_hz": instrument.frequency_hz,
            "endpoints": {
                "H1": _connected_endpoint_identity(instrument.h1_endpoint),
                "H2": _connected_endpoint_identity(instrument.h2_endpoint),
                "X1": _connected_endpoint_identity(instrument.x1_endpoint),
                "X2": _connected_endpoint_identity(instrument.x2_endpoint),
            },
        })
    else:
        common["unsupported_instrument_type"] = instrument.__class__.__qualname__
    return common


def _relay_configuration(relay: Any) -> Mapping[str, Any]:
    return {
        "relay_id": getattr(relay, "id", None),
        "relay_type": getattr(relay, "relay_type", None),
        "type": getattr(relay, "type", None),
        "function_type": getattr(relay, "function_type", None),
        "plugin_id": getattr(relay, "plugin_id", None),
        "settings": getattr(relay, "settings", {}),
        "in_service": getattr(relay, "in_service", None),
        "enabled": getattr(relay, "enabled", None),
        "blocked": getattr(relay, "blocked", None),
    }


def _channel_configuration(channel: Any) -> Mapping[str, Any]:
    source_terminal = getattr(channel, "source_terminal", None)
    terminal_mapping = (
        dict(source_terminal.to_mapping())
        if source_terminal is not None and callable(getattr(source_terminal, "to_mapping", None))
        else None
    )
    return {
        "channel_id": getattr(channel, "id", None),
        "signal_type": getattr(channel, "signal_type", None),
        "phase": getattr(channel, "phase", None),
        "source_id": getattr(channel, "source_id", None),
        "source_terminal": terminal_mapping,
        "unit": getattr(channel, "unit", None),
        "nominal_value": getattr(channel, "nominal_value", None),
        "scale": getattr(channel, "scale", None),
        "polarity": getattr(channel, "polarity", None),
        "stale_after": getattr(channel, "stale_after", None),
        "producer_id": getattr(channel, "producer_id", None),
    }


@dataclass(frozen=True, slots=True)
class ProtectionDependency:
    """One shared dependency identity and its current state fingerprint."""

    kind: str
    identity: str
    fingerprint: str

    def __post_init__(self) -> None:
        for name in ("kind", "identity", "fingerprint"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())


@dataclass(frozen=True, slots=True)
class ProtectionElementDependencyDescriptor:
    """Complete dependency set for one configured Protection element."""

    project_id: str
    activation_generation: int
    element_id: str
    relay_id: str
    function_code: str
    fingerprint: str
    dependencies: tuple[ProtectionDependency, ...]
    complete: bool
    diagnostics: tuple[str, ...]

    @property
    def dependency_keys(self) -> tuple[tuple[str, str], ...]:
        return tuple((item.kind, item.identity) for item in self.dependencies)


@dataclass(frozen=True, slots=True)
class ProtectionDependencyRegistry:
    """Immutable element descriptors plus reverse dependency-consumer index."""

    project_id: str
    activation_generation: int
    descriptors: Mapping[str, ProtectionElementDependencyDescriptor]
    consumers: Mapping[tuple[str, str], tuple[str, ...]]
    complete: bool
    diagnostics: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "descriptors", MappingProxyType(dict(self.descriptors)))
        object.__setattr__(
            self,
            "consumers",
            MappingProxyType({key: tuple(value) for key, value in self.consumers.items()}),
        )

    def descriptor_for(self, element_id: str) -> ProtectionElementDependencyDescriptor:
        try:
            return self.descriptors[element_id]
        except KeyError as exc:
            raise KeyError(f"Protection dependency descriptor not found: {element_id}") from exc

    def consumers_for(self, kind: str, identity: str) -> tuple[str, ...]:
        return self.consumers.get((kind, identity), ())


def build_protection_dependency_registry(
    network: Network,
    configuration: ProtectionProjectConfiguration,
    channels: Mapping[str, Any],
    *,
    activation_generation: int,
    runtime_channels: Mapping[str, Any] | None = None,
) -> ProtectionDependencyRegistry:
    """Build canonical per-element dependencies without reading sample state."""
    if not isinstance(network, Network):
        raise TypeError("network must be a Network.")
    if not isinstance(configuration, ProtectionProjectConfiguration):
        raise TypeError("configuration must be ProtectionProjectConfiguration.")
    if not isinstance(channels, Mapping):
        raise TypeError("channels must be a mapping.")
    if (
        isinstance(activation_generation, bool)
        or not isinstance(activation_generation, int)
        or activation_generation < 1
    ):
        raise ValueError("activation_generation must be a positive integer.")
    if runtime_channels is not None and not isinstance(runtime_channels, Mapping):
        raise TypeError("runtime_channels must be a mapping or None.")

    bindings_by_element: dict[str, list[Any]] = {}
    bindings_by_id: dict[str, Any] = {}
    diagnostics: list[str] = []
    for binding in configuration.measurement_bindings:
        if binding.binding_id in bindings_by_id:
            diagnostics.append(f"duplicate binding identity {binding.binding_id!r}.")
            continue
        bindings_by_id[binding.binding_id] = binding
        bindings_by_element.setdefault(binding.protection_element_id, []).append(binding)

    descriptors: dict[str, ProtectionElementDependencyDescriptor] = {}
    consumer_sets: dict[tuple[str, str], set[str]] = {}

    for element in configuration.elements:
        element_diagnostics: list[str] = []
        dependencies: list[ProtectionDependency] = []

        def add_dependency(kind: str, identity: str, value: Any) -> None:
            dependencies.append(ProtectionDependency(kind, identity, _fingerprint(value)))

        element_id = element.element_id
        prefix = f"element={element_id!r}"
        add_dependency("protection_element", element_id, element.to_dict())

        try:
            relay = network.get_by_id("relay", element.relay_id)
        except (LookupError, ValueError):
            relay = None
        if relay is None:
            element_diagnostics.append(f"{prefix}: configured Relay {element.relay_id!r} is absent from the active Network.")
        else:
            add_dependency("relay", element.relay_id, _relay_configuration(relay))

        owned_bindings = bindings_by_element.get(element_id, [])
        expected: dict[str, tuple[str, str]] = {}
        if element.function_code in {"50N", "51N"}:
            residual = element.residual_current_input
            if residual is None:
                element_diagnostics.append(f"{prefix}: residual-current configuration is missing.")
            else:
                expected = {
                    binding_id: ("residual_current", None)
                    for binding_id in (
                        (residual.phase_binding_ids or {}).values()
                        if residual.mode == "THREE_PHASE_SUM"
                        else (residual.direct_binding_id,)
                    )
                    if binding_id is not None
                }
        else:
            expected = {
                input_name: (input_name, channel_id)
                for input_name, channel_id in element.input_channel_ids.items()
            }

        selected_bindings: list[Any] = []
        for expected_key, (input_name, expected_channel_id) in expected.items():
            if element.function_code in {"50N", "51N"}:
                matches = [
                    item for item in owned_bindings
                    if item.binding_id == expected_key and item.relay_input_id == input_name
                ]
            else:
                matches = [
                    item for item in owned_bindings
                    if item.relay_input_id == input_name
                ]
            if len(matches) != 1:
                element_diagnostics.append(
                    f"{prefix}, input={input_name!r}: expected exactly one canonical measurement binding; found {len(matches)}."
                )
                continue
            binding = matches[0]
            if expected_channel_id is not None and binding.channel_id != expected_channel_id:
                element_diagnostics.append(
                    f"{prefix}, binding={binding.binding_id!r}: channel identity does not match configured input membership."
                )
                continue
            selected_bindings.append(binding)

        selected_ids = {item.binding_id for item in selected_bindings}
        unexpected = [item.binding_id for item in owned_bindings if item.binding_id not in selected_ids]
        if unexpected:
            element_diagnostics.append(
                f"{prefix}: unclassified or unassociated measurement bindings are present: {tuple(sorted(unexpected))!r}."
            )

        for binding in selected_bindings:
            binding_prefix = f"{prefix}, binding={binding.binding_id!r}"
            if binding.protection_element_id != element_id:
                element_diagnostics.append(f"{binding_prefix}: binding owner does not match its element.")
                continue
            add_dependency("measurement_binding", binding.binding_id, binding.to_dict())
            add_dependency("source_endpoint_association", binding.source_equipment_id, {
                "source_equipment_id": binding.source_equipment_id,
                "source_endpoint": binding.source_endpoint_reference.to_mapping(),
            })

            channel = channels.get(binding.channel_id)
            if channel is None:
                element_diagnostics.append(f"{binding_prefix}: channel {binding.channel_id!r} is missing.")
            else:
                if runtime_channels is not None and runtime_channels.get(binding.channel_id) is not channel:
                    element_diagnostics.append(f"{binding_prefix}: runtime channel object is not the active registry object.")
                add_dependency("measurement_channel", binding.channel_id, {
                    "configuration": _channel_configuration(channel),
                    "runtime_instance_identity": id(channel),
                })

            try:
                instrument = network.get_by_identity(binding.instrument_id)
            except (KeyError, ValueError):
                instrument = None
            if instrument is None:
                element_diagnostics.append(f"{binding_prefix}: instrument {binding.instrument_id!r} is missing.")
            else:
                add_dependency(
                    "instrument",
                    binding.instrument_id,
                    _instrument_configuration(instrument),
                )

            try:
                source_equipment = network.get_by_identity(binding.source_equipment_id)
            except (KeyError, ValueError):
                source_equipment = None
            if source_equipment is None:
                element_diagnostics.append(f"{binding_prefix}: source equipment {binding.source_equipment_id!r} is missing.")
            else:
                add_dependency("source_equipment_model", binding.source_equipment_id, {
                    "type": str(getattr(source_equipment, "TYPE", "")).strip().lower(),
                    "id": getattr(source_equipment, "id", None),
                })

            measurement_type = binding.measurement_type.strip().lower()
            if measurement_type == "current":
                if not isinstance(instrument, CurrentTransformer):
                    element_diagnostics.append(f"{binding_prefix}: current measurement does not resolve to a CurrentTransformer.")
                elif (
                    binding.instrument_primary_side not in {"P1", "P2"}
                    or not binding.instrument_primary_component_fingerprint
                ):
                    element_diagnostics.append(f"{binding_prefix}: CT P1/P2 component identity is missing; explicit rebind is required.")
                else:
                    add_dependency(
                        "ct_primary_component",
                        f"{binding.instrument_id}:{binding.instrument_primary_side}",
                        binding.instrument_primary_component_fingerprint,
                    )
            elif measurement_type == "voltage":
                if not isinstance(instrument, (PT, CVT)):
                    element_diagnostics.append(f"{binding_prefix}: voltage measurement does not resolve to a PT or CVT.")
            else:
                element_diagnostics.append(f"{binding_prefix}: unsupported measurement type {measurement_type!r}.")

        for scheme in configuration.differential_schemes:
            if scheme.protection_element_id != element_id:
                continue
            if not isinstance(scheme, DifferentialProtectionSchemeConfiguration):
                element_diagnostics.append(f"{prefix}: invalid differential scheme value.")
                continue
            for binding_id in scheme.measurement_binding_ids:
                member = bindings_by_id.get(binding_id)
                if member is None or member.protection_element_id != element_id:
                    element_diagnostics.append(
                        f"{prefix}, differential_scheme={scheme.scheme_id!r}: member {binding_id!r} is missing or owned by another element."
                    )
            add_dependency("differential_scheme", scheme.scheme_id, scheme.to_dict())

        if element.action_target_type is not None:
            add_dependency(
                "action_target",
                f"{element.action_target_type}:{element.action_target_id}",
                {
                    "target_type": element.action_target_type,
                    "target_id": element.action_target_id,
                    "action_type": element.action_type,
                },
            )

        dependencies.sort(key=lambda item: (item.kind, item.identity, item.fingerprint))
        descriptor_fingerprint = _fingerprint(tuple(
            (item.kind, item.identity, item.fingerprint) for item in dependencies
        ))
        descriptor = ProtectionElementDependencyDescriptor(
            project_id=configuration.project_id,
            activation_generation=activation_generation,
            element_id=element_id,
            relay_id=element.relay_id,
            function_code=element.function_code,
            fingerprint=descriptor_fingerprint,
            dependencies=tuple(dependencies),
            complete=not element_diagnostics,
            diagnostics=tuple(element_diagnostics),
        )
        descriptors[element_id] = descriptor
        for dependency in dependencies:
            consumer_sets.setdefault((dependency.kind, dependency.identity), set()).add(element_id)
        diagnostics.extend(element_diagnostics)

    consumers = {
        key: tuple(sorted(element_ids))
        for key, element_ids in consumer_sets.items()
    }
    return ProtectionDependencyRegistry(
        project_id=configuration.project_id,
        activation_generation=activation_generation,
        descriptors=descriptors,
        consumers=consumers,
        complete=(
            not diagnostics
            and len(descriptors) == len(configuration.elements)
            and all(item.complete for item in descriptors.values())
        ),
        diagnostics=tuple(diagnostics),
    )


__all__ = [
    "ProtectionDependency",
    "ProtectionElementDependencyDescriptor",
    "ProtectionDependencyRegistry",
    "build_protection_dependency_registry",
]
