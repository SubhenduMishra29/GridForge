"""Application-owned, per-element Protection dependency identities.

These descriptors are evaluation/dispatch provenance, not Core electrical
state. They intentionally exclude live sample values, timestamps, quality and
producer sequence; those belong to the measurement-sample contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping

from core.model import CurrentTransformer, CVT, PT, EndpointReference, EquipmentType
from core.network.connectivity import ConnectivityResolver
from core.network.network import Network
from core.network.topology_endpoint_reference import TopologyEndpointReference
from core.protection.configuration_fingerprint import canonical_configuration_value
from core.protection.function_catalog import ProtectionFunctionStatus, get_protection_function
from core.protection.project_configuration import (
    DifferentialProtectionSchemeConfiguration,
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


def _source_endpoint_identity(binding: Any) -> str:
    endpoint = binding.source_endpoint_reference
    if endpoint.is_terminal:
        return (
            f"terminal:{endpoint.equipment_type.value}:"
            f"{endpoint.object_id}:{endpoint.terminal_role}"
        )
    if endpoint.is_bus:
        return f"bus:{endpoint.object_id}:{endpoint.attachment_id}"
    return f"unsupported:{endpoint.kind}"


def _topology_component_fingerprint(
    component: Any,
    *,
    prefix: str = "ct-primary-component:v1:",
) -> str:
    """Match the canonical CT association fingerprint used by the configuration service."""
    identities = []
    for reference in component:
        if reference.is_terminal:
            endpoint = reference.terminal_reference
            identities.append((
                "terminal",
                endpoint.equipment_type.value,
                endpoint.object_id,
                endpoint.terminal_role,
            ))
        elif reference.is_bus:
            endpoint = reference.bus_reference
            identities.append(("bus", endpoint.object_id, endpoint.attachment_id))
        elif reference.is_junction:
            identities.append(("junction", reference.junction_id))
        else:
            raise ValueError(f"Unsupported topology endpoint kind: {reference.kind!r}.")
    payload = json.dumps(sorted(identities), ensure_ascii=True, separators=(",", ":"))
    return prefix + sha256(payload.encode("ascii")).hexdigest()


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
            function_specification = get_protection_function(element.function_code)
        except (KeyError, TypeError, ValueError) as exc:
            element_diagnostics.append(
                f"{prefix}: canonical Protection function specification is unavailable: {exc}."
            )
        else:
            input_contract = function_specification.input_contract
            if (
                function_specification.status is ProtectionFunctionStatus.NOT_IMPLEMENTED
                or input_contract is None
                or not input_contract.supported
            ):
                element_diagnostics.append(
                    f"{prefix}: Protection function {element.function_code!r} has no dispatchable, supported input contract."
                )
            add_dependency(
                "protection_function_contract",
                element.function_code,
                {
                    "status": function_specification.status.value,
                    "implementation": (
                        None
                        if function_specification.implementation is None
                        else (
                            function_specification.implementation.__module__,
                            function_specification.implementation.__qualname__,
                        )
                    ),
                    "input_contract": input_contract,
                },
            )

        try:
            relay = network.get_by_id("relay", element.relay_id)
        except (LookupError, ValueError):
            relay = None
        if relay is None:
            element_diagnostics.append(f"{prefix}: configured Relay {element.relay_id!r} is absent from the active Network.")
        else:
            add_dependency("relay", element.relay_id, _relay_configuration(relay))
            add_dependency(
                "relay_input_registry",
                element.relay_id,
                {
                    name: getattr(channel, "id", None)
                    for name, channel in sorted(relay.input_channels.items())
                },
            )

        owned_bindings = bindings_by_element.get(element_id, [])
        expected: dict[str, tuple[str, str | None]] = {}
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

        # Differential schemes own their member CT bindings explicitly. These
        # bindings are dependencies even when the protection function does not
        # expose them as ordinary scalar RelayInput channel mappings.
        for scheme in configuration.differential_schemes:
            if scheme.protection_element_id != element_id:
                continue
            if not isinstance(scheme, DifferentialProtectionSchemeConfiguration):
                element_diagnostics.append(f"{prefix}: invalid differential scheme value.")
                continue
            for binding_id in scheme.measurement_binding_ids:
                member = bindings_by_id.get(binding_id)
                if member is None:
                    element_diagnostics.append(
                        f"{prefix}, differential_scheme={scheme.scheme_id!r}: member {binding_id!r} is missing."
                    )
                    continue
                if member.protection_element_id != element_id:
                    element_diagnostics.append(
                        f"{prefix}, differential_scheme={scheme.scheme_id!r}: member {binding_id!r} is owned by another element."
                    )
                    continue
                if all(existing.binding_id != binding_id for existing in selected_bindings):
                    selected_bindings.append(member)

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
            add_dependency("source_endpoint_association", _source_endpoint_identity(binding), {
                "source_equipment_id": binding.source_equipment_id,
                "source_endpoint": binding.source_endpoint_reference.to_mapping(),
            })

            channel = channels.get(binding.channel_id)
            if channel is None:
                element_diagnostics.append(f"{binding_prefix}: channel {binding.channel_id!r} is missing.")
            else:
                if runtime_channels is not None and runtime_channels.get(binding.channel_id) is not channel:
                    element_diagnostics.append(f"{binding_prefix}: runtime channel object is not the active registry object.")
                if getattr(channel, "source_terminal", None) is None:
                    element_diagnostics.append(f"{binding_prefix}: physical channel has no canonical source terminal.")
                if (
                    relay is not None
                    and element.function_code not in {"50N", "51N"}
                    and relay.input_channels.get(binding.relay_input_id) is not channel
                ):
                    element_diagnostics.append(
                        f"{binding_prefix}: Relay input is not bound to the active canonical MeasurementChannel object."
                    )
                add_dependency("measurement_channel", binding.channel_id, {
                    "configuration": _channel_configuration(channel),
                    "runtime_instance_identity": id(channel),
                })

            try:
                instrument = network.get_by_identity(binding.instrument_id)
            except (LookupError, ValueError):
                instrument = None
            if instrument is None:
                element_diagnostics.append(f"{binding_prefix}: instrument {binding.instrument_id!r} is missing.")
            else:
                instrument_configuration = _instrument_configuration(instrument)
                endpoint_identities = instrument_configuration.get("endpoints", {})
                if any(
                    identity is not None and identity[0] == "unsupported"
                    for identity in endpoint_identities.values()
                ):
                    element_diagnostics.append(
                        f"{binding_prefix}: instrument endpoint identity cannot be represented canonically."
                    )
                add_dependency(
                    "instrument",
                    binding.instrument_id,
                    instrument_configuration,
                )

            try:
                source_equipment = network.get_by_identity(binding.source_equipment_id)
            except (LookupError, ValueError):
                source_equipment = None
            if source_equipment is None:
                element_diagnostics.append(f"{binding_prefix}: source equipment {binding.source_equipment_id!r} is missing.")
            else:
                add_dependency("source_equipment_model", binding.source_equipment_id, {
                    "type": str(getattr(source_equipment, "TYPE", "")).strip().lower(),
                    "id": getattr(source_equipment, "id", None),
                })

            measurement_type = binding.measurement_type.strip().lower()
            if measurement_type in {"current", "voltage"}:
                expected_instrument = (
                    isinstance(instrument, CurrentTransformer)
                    if measurement_type == "current"
                    else isinstance(instrument, (PT, CVT))
                )
                if not expected_instrument:
                    element_diagnostics.append(
                        f"{binding_prefix}: {measurement_type} measurement does not resolve to its canonical physical instrument type."
                    )
                elif source_equipment is not None:
                    try:
                        resolver = ConnectivityResolver(network)
                        selected_endpoint = (
                            TopologyEndpointReference.from_bus(binding.source_endpoint_reference)
                            if binding.source_endpoint_reference.is_bus
                            else TopologyEndpointReference.from_terminal(binding.source_endpoint_reference)
                        )
                        if measurement_type == "current":
                            primary_roles = ("P1", "P2")
                            equipment_type = EquipmentType("ct")
                        elif isinstance(instrument, PT):
                            primary_roles = ("primary_a", "primary_b")
                            equipment_type = EquipmentType("pt")
                        else:
                            primary_roles = ("H1", "H2")
                            equipment_type = EquipmentType("cvt")
                        primary_components = {
                            role: resolver.topology_component(
                                TopologyEndpointReference.from_terminal(
                                    EndpointReference.terminal(
                                        equipment_type=equipment_type,
                                        equipment_id=binding.instrument_id,
                                        terminal_role=role,
                                    )
                                )
                            )
                            for role in primary_roles
                        }
                        component_sets = {
                            role: set(component)
                            for role, component in primary_components.items()
                        }
                        matching_roles = tuple(
                            role for role, component in component_sets.items()
                            if selected_endpoint in component
                        )
                        if (
                            len(matching_roles) != 1
                            or len({frozenset(value) for value in component_sets.values()}) != len(primary_roles)
                        ):
                            raise ValueError(
                                f"source endpoint resolves to {len(matching_roles)} instrument primary components"
                            )
                        selected_side = matching_roles[0]
                        component_prefix = (
                            "ct-primary-component:v1:"
                            if measurement_type == "current"
                            else "instrument-primary-component:v1:"
                        )
                        for primary_role, primary_component in primary_components.items():
                            add_dependency(
                                (
                                    "ct_primary_component"
                                    if measurement_type == "current"
                                    else "voltage_primary_component"
                                ),
                                f"{binding.instrument_id}:{primary_role}",
                                _topology_component_fingerprint(
                                    primary_component,
                                    prefix=component_prefix,
                                ),
                            )
                        selected_component_fingerprint = _topology_component_fingerprint(
                            primary_components[selected_side],
                            prefix=component_prefix,
                        )
                        if measurement_type == "current":
                            if (
                                binding.instrument_primary_side != selected_side
                                or binding.instrument_primary_component_fingerprint != selected_component_fingerprint
                            ):
                                element_diagnostics.append(
                                    f"{binding_prefix}: persisted CT P1/P2 side or component membership is stale; explicit rebind is required."
                                )
                            # Both P1 and P2 components were captured above; the
                            # persisted side/fingerprint check binds this input to
                            # exactly one of those two component identities.
                    except (KeyError, LookupError, TypeError, ValueError, AttributeError) as exc:
                        element_diagnostics.append(
                            f"{binding_prefix}: instrument primary topology association is incomplete or ambiguous: {exc}."
                        )
            else:
                element_diagnostics.append(f"{binding_prefix}: unsupported measurement type {measurement_type!r}.")

            if instrument is not None:
                if getattr(instrument, "in_service", True) is not True:
                    element_diagnostics.append(f"{binding_prefix}: physical measurement instrument is not in service.")
                ratio_attribute = "ratio" if measurement_type == "current" else "voltage_ratio"
                try:
                    physical_ratio = float(getattr(instrument, ratio_attribute))
                    configured_ratio = float(binding.instrument_ratio)
                except (AttributeError, TypeError, ValueError, OverflowError):
                    physical_ratio = configured_ratio = float("nan")
                if (
                    not isfinite(physical_ratio)
                    or not isfinite(configured_ratio)
                    or physical_ratio <= 0.0
                    or abs(physical_ratio - configured_ratio) > max(1e-9, physical_ratio * 1e-9)
                ):
                    element_diagnostics.append(f"{binding_prefix}: persisted instrument ratio does not match the active physical instrument.")

            if channel is not None and instrument is not None:
                channel_signal = str(getattr(getattr(channel, "signal_type", None), "value", "")).strip().upper()
                expected_signal = "CURRENT" if measurement_type == "current" else "VOLTAGE"
                if channel_signal != expected_signal:
                    element_diagnostics.append(f"{binding_prefix}: channel signal type does not match the binding measurement type.")
                if getattr(channel, "source_id", None) != binding.instrument_id:
                    element_diagnostics.append(f"{binding_prefix}: channel source identity does not match the bound physical instrument.")
                source_terminal = getattr(channel, "source_terminal", None)
                secondary_roles = (
                    {"S1", "S2"} if isinstance(instrument, CurrentTransformer)
                    else {"secondary_a", "secondary_b"} if isinstance(instrument, PT)
                    else {"X1", "X2"} if isinstance(instrument, CVT)
                    else set()
                )
                if (
                    source_terminal is None
                    or not getattr(source_terminal, "is_terminal", False)
                    or getattr(source_terminal, "object_id", None) != binding.instrument_id
                    or getattr(source_terminal, "terminal_role", None) not in secondary_roles
                ):
                    element_diagnostics.append(f"{binding_prefix}: channel source terminal does not match the physical instrument secondary.")
            if source_equipment is not None:
                source_reference = binding.source_endpoint_reference
                if source_reference.is_terminal:
                    source_type = str(getattr(source_equipment, "TYPE", "")).strip().lower()
                    source_roles = {
                        getattr(item, "role", None)
                        for item in getattr(source_equipment, "terminals", ())
                    }
                    if (
                        source_reference.object_id != binding.source_equipment_id
                        or source_reference.equipment_type.value != source_type
                        or source_reference.terminal_role not in source_roles
                    ):
                        element_diagnostics.append(f"{binding_prefix}: source terminal identity does not match active source equipment.")
                elif source_reference.is_bus:
                    if (
                        str(getattr(source_equipment, "TYPE", "")).strip().lower() != "bus"
                        or source_reference.object_id != binding.source_equipment_id
                    ):
                        element_diagnostics.append(f"{binding_prefix}: Bus attachment source does not match active Core Bus.")

        for scheme in configuration.differential_schemes:
            if scheme.protection_element_id != element_id:
                continue
            if not isinstance(scheme, DifferentialProtectionSchemeConfiguration):
                element_diagnostics.append(f"{prefix}: invalid differential scheme value.")
                continue
            try:
                protected_object = network.get_by_id(
                    scheme.protected_object_type,
                    scheme.protected_object_id,
                )
            except (LookupError, ValueError):
                protected_object = None
            if protected_object is None:
                element_diagnostics.append(
                    f"{prefix}, differential_scheme={scheme.scheme_id!r}: protected object "
                    f"{scheme.protected_object_type}:{scheme.protected_object_id} is missing from the active Network."
                )
            else:
                add_dependency(
                    "differential_protected_object",
                    f"{scheme.protected_object_type}:{scheme.protected_object_id}",
                    {
                        "object_type": scheme.protected_object_type,
                        "object_id": scheme.protected_object_id,
                        "in_service": getattr(protected_object, "in_service", None),
                    },
                )
                resolver = ConnectivityResolver(network)
                if scheme.protected_object_type == "bus":
                    protected_endpoints = tuple(
                        (
                            f"attachment-{index}",
                            TopologyEndpointReference.from_bus(
                                EndpointReference.bus(
                                    bus_id=scheme.protected_object_id,
                                    attachment_id=f"attachment-{index}",
                                )
                            ),
                        )
                        for index in range(9)
                    )
                else:
                    object_type = EquipmentType(
                        str(getattr(protected_object, "TYPE", scheme.protected_object_type)).strip().lower()
                    )
                    protected_endpoints = tuple(
                        (
                            str(getattr(terminal, "role", "")),
                            TopologyEndpointReference.from_terminal(
                                EndpointReference.terminal(
                                    equipment_type=object_type,
                                    equipment_id=scheme.protected_object_id,
                                    terminal_role=str(getattr(terminal, "role", "")),
                                )
                            ),
                        )
                        for terminal in getattr(protected_object, "terminals", ())
                    )
                if not protected_endpoints:
                    element_diagnostics.append(
                        f"{prefix}, differential_scheme={scheme.scheme_id!r}: protected object has no canonical terminals or Bus attachments."
                    )
                for endpoint_role, endpoint in protected_endpoints:
                    try:
                        component = resolver.topology_component(endpoint)
                        add_dependency(
                            "differential_zone_component",
                            f"{scheme.scheme_id}:{endpoint_role}",
                            _topology_component_fingerprint(
                                component,
                                prefix="differential-zone-component:v1:",
                            ),
                        )
                    except (KeyError, LookupError, TypeError, ValueError, AttributeError) as exc:
                        element_diagnostics.append(
                            f"{prefix}, differential_scheme={scheme.scheme_id!r}, endpoint={endpoint_role!r}: "
                            f"protected-zone topology is unavailable: {exc}."
                        )

            member_fingerprints = []
            for binding_id in scheme.measurement_binding_ids:
                member = bindings_by_id.get(binding_id)
                if member is None or member.protection_element_id != element_id:
                    element_diagnostics.append(
                        f"{prefix}, differential_scheme={scheme.scheme_id!r}: member {binding_id!r} is missing or owned by another element."
                    )
                else:
                    member_fingerprints.append((binding_id, member.to_dict()))
            if len(member_fingerprints) == len(scheme.measurement_binding_ids):
                add_dependency(
                    "differential_scheme_members",
                    scheme.scheme_id,
                    tuple(sorted(member_fingerprints)),
                )
            add_dependency("differential_scheme", scheme.scheme_id, scheme.to_dict())

        if element.action_target_type is not None:
            target_identity = f"{element.action_target_type}:{element.action_target_id}"
            target_fields = {
                "breaker": ("closed", "in_service"),
                "switch": ("closed", "in_service"),
                "disconnector": ("closed", "in_service"),
                "fuse": ("blown", "in_service"),
                "motor": ("running", "in_service"),
            }.get(element.action_target_type, ())
            try:
                target = network.get_by_id(
                    element.action_target_type,
                    element.action_target_id,
                )
            except (LookupError, ValueError):
                target = None
            if target is None:
                element_diagnostics.append(
                    f"{prefix}: configured action target {target_identity!r} is absent from the active Network."
                )
            else:
                target_state = {
                    field: getattr(target, field)
                    for field in target_fields
                    if hasattr(target, field)
                }
                if len(target_state) != len(target_fields):
                    element_diagnostics.append(
                        f"{prefix}: configured action target does not expose every required authoritative state field."
                    )
                add_dependency(
                    "action_target",
                    target_identity,
                    {
                        "target_type": element.action_target_type,
                        "target_id": element.action_target_id,
                        "action_type": element.action_type,
                        "authoritative_state": target_state,
                    },
                )

        fingerprints_by_key: dict[tuple[str, str], str] = {}
        for dependency in dependencies:
            dependency_key = (dependency.kind, dependency.identity)
            previous_fingerprint = fingerprints_by_key.get(dependency_key)
            if previous_fingerprint is not None and previous_fingerprint != dependency.fingerprint:
                element_diagnostics.append(
                    f"{prefix}: dependency {dependency.kind}:{dependency.identity} changed during descriptor capture."
                )
            fingerprints_by_key[dependency_key] = dependency.fingerprint
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
