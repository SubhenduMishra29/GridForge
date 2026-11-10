# ============================================================
# File: core/application/services/validation_service.py
# GridForge V2 — Application Validation Service
# Author: Subhendu Mishra
# ============================================================

"""Application-owned validation lifecycle over authoritative Core state."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.network import Network

from ..validation import (
    SLDAssociationReference,
    SLDAssociationState,
    SLDAssociationValidationResult,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    ValidationSummary,
)


class ValidationService:
    """Validate the authoritative Network without mutating it."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("ValidationService requires a Network.")
        self._network = network
        self._result: ValidationResult | None = None

    @property
    def result(self) -> ValidationResult | None:
        return self._result

    def validate_project(
        self,
        *,
        context: Any | None = None,
        presentation: Any | None = None,
        presentation_documents: tuple[Any, ...] | None = None,
        sld_connection_diagnostics: tuple[Mapping[str, Any], ...] = (),
    ) -> ValidationResult:
        """Validate Core state plus optional Application-owned SLD associations.

        SLD association diagnostics are read-only. They do not choose an orphan
        repair/deletion policy and do not mutate the persistent document.
        """
        issues: list[ValidationIssue] = []
        try:
            self._network.validate()
        except Exception as exc:
            issues.append(
                ValidationIssue(
                    code="NETWORK_INTEGRITY_FAILED",
                    message=str(exc),
                    severity=ValidationSeverity.ERROR,
                )
            )
        for element in self._elements():
            try:
                valid = element.validate()
            except Exception as exc:  # noqa: BLE001 - domain diagnostics are surfaced as issues
                issues.append(
                    ValidationIssue(
                        code="MODEL_VALIDATION_EXCEPTION",
                        message=str(exc),
                        severity=ValidationSeverity.ERROR,
                        element_id=getattr(element, "id", None),
                        element_type=getattr(element, "element_type", type(element).__name__),
                    )
                )
                continue
            if valid is False:
                issues.append(
                    ValidationIssue(
                        code="MODEL_VALIDATION_FAILED",
                        message=f"Model validation failed for {getattr(element, 'id', '<unknown>')}",
                        severity=ValidationSeverity.ERROR,
                        element_id=getattr(element, "id", None),
                        element_type=getattr(element, "element_type", type(element).__name__),
                    )
                )

        if context is not None:
            documents = (
                tuple(presentation_documents)
                if presentation_documents is not None
                else ((presentation,) if presentation is not None else ())
            )
            seen_documents: set[int] = set()
            for document in documents:
                if document is None or id(document) in seen_documents:
                    continue
                seen_documents.add(id(document))
                sld_validation = self.validate_sld_associations(context, self._network, document)
                document_id = getattr(document, "document_id", None)
                for issue in sld_validation.issues:
                    prefix = f"SLD document {document_id!r}: " if document_id is not None else ""
                    issues.append(ValidationIssue(
                        code=issue.code,
                        message=prefix + issue.message,
                        severity=issue.severity,
                        element_id=issue.element_id,
                        element_type=issue.element_type,
                    ))

        for diagnostic in sld_connection_diagnostics:
            if not isinstance(diagnostic, Mapping):
                issues.append(ValidationIssue(
                    code="SLD_CONNECTION_AUDIT_FAILED",
                    message="SLD connection audit returned a non-mapping diagnostic.",
                    severity=ValidationSeverity.ERROR,
                    element_type="SLD_CONNECTION",
                ))
                continue
            source_code = str(diagnostic.get("code") or "")
            issue_code = {
                "SLD_WIRE_WITHOUT_CORE": "SLD_WIRE_WITHOUT_CORE",
                "PRESENTATION_ID_MISMATCH": "SLD_PRESENTATION_ID_MISMATCH",
                "DUPLICATE_PRESENTATION_COMPANION": "SLD_DUPLICATE_CORE_WIRE_COMPANION",
                "ENDPOINT_MISMATCH": "SLD_CONNECTION_ENDPOINT_MISMATCH",
                "CORE_WIRE_WITHOUT_SLD_COMPANION": "SLD_CORE_WIRE_WITHOUT_SLD_COMPANION",
                "SLD_ENDPOINT_NODE_UNRESOLVED": "SLD_ENDPOINT_NODE_UNRESOLVED",
                "SLD_CONNECTION_AUDIT_UNAVAILABLE": "SLD_CONNECTION_AUDIT_UNAVAILABLE",
                "SLD_PRESENTATION_COLLECTION_UNAVAILABLE": "SLD_PRESENTATION_COLLECTION_UNAVAILABLE",
                "SLD_ACTIVE_PRESENTATION_NOT_IN_COLLECTION": "SLD_ACTIVE_PRESENTATION_NOT_IN_COLLECTION",
                "SLD_ACTIVE_PRESENTATION_COLLECTION_MISMATCH": "SLD_ACTIVE_PRESENTATION_COLLECTION_MISMATCH",
                "SLD_PRESENTATION_COLLECTION_AUDIT_FAILED": "SLD_PRESENTATION_COLLECTION_AUDIT_FAILED",
                "SLD_DOCUMENT_PROJECT_MISMATCH": "SLD_DOCUMENT_PROJECT_MISMATCH",
                "SLD_DOCUMENT_ID_INVALID": "SLD_DOCUMENT_ID_INVALID",
                "SLD_PRESENTATION_DOCUMENT_ID_DUPLICATE": "SLD_PRESENTATION_DOCUMENT_ID_DUPLICATE",
            }.get(source_code, "SLD_CONNECTION_AUDIT_FAILED")
            connection_id = diagnostic.get("connection_id")
            core_connection_id = diagnostic.get("core_connection_id")
            reason = diagnostic.get("reason")
            document_id = diagnostic.get("document_id")
            identity_prefix = f"SLD document {document_id!r}: " if document_id is not None else ""
            if source_code in {
                "SLD_PRESENTATION_COLLECTION_UNAVAILABLE",
                "SLD_ACTIVE_PRESENTATION_NOT_IN_COLLECTION",
                "SLD_ACTIVE_PRESENTATION_COLLECTION_MISMATCH",
                "SLD_PRESENTATION_COLLECTION_AUDIT_FAILED",
                "SLD_DOCUMENT_PROJECT_MISMATCH",
                "SLD_DOCUMENT_ID_INVALID",
                "SLD_PRESENTATION_DOCUMENT_ID_DUPLICATE",
            }:
                message = f"{identity_prefix}presentation collection integrity failed: {reason or source_code}."
            else:
                identity = (
                    f"{identity_prefix}connection {connection_id!r}"
                    if connection_id is not None
                    else f"{identity_prefix}Simple-Wire/Core connection association"
                )
                details = []
                if core_connection_id is not None:
                    details.append(f"Core connection {core_connection_id!r}")
                if reason:
                    details.append(str(reason))
                suffix = f" ({'; '.join(details)})" if details else ""
                message = f"{identity} failed semantic association validation{suffix}."
            issues.append(ValidationIssue(
                code=issue_code,
                message=message,
                severity=ValidationSeverity.ERROR,
                element_id=str(connection_id or core_connection_id) if (connection_id or core_connection_id) else None,
                element_type="SLD_CONNECTION" if connection_id is not None or core_connection_id is not None else "SLD_DOCUMENT",
            ))

        if self._network.topology_dirty:
            issues.append(
                ValidationIssue(
                    code="TOPOLOGY_NOT_REBUILT",
                    message="Authoritative topology is not rebuilt for the current network state.",
                    severity=ValidationSeverity.WARNING,
                )
            )

        summary = ValidationSummary(
            errors=sum(issue.severity is ValidationSeverity.ERROR for issue in issues),
            warnings=sum(issue.severity is ValidationSeverity.WARNING for issue in issues),
            infos=sum(issue.severity is ValidationSeverity.INFO for issue in issues),
        )
        self._result = ValidationResult(
            model_revision=getattr(self._network.state, "model_revision", self._network.state.topology_revision),
            topology_revision=self._network.topology_revision,
            issues=tuple(issues),
            summary=summary,
        )
        return self._result

    @staticmethod
    def validate_sld_associations(
        context: Any,
        network: Network,
        presentation: Any,
    ) -> SLDAssociationValidationResult:
        """Validate persistent SLD/Core associations and retained orphan state.

        SLD structure remains presentation data. This Application-owned audit is
        read-only: it diagnoses stale or malformed references but never repairs
        presentation or infers Core connectivity from geometry.
        """
        if not hasattr(context, "project_id") or not isinstance(context.project_id, str):
            raise TypeError("context must expose a string project_id.")
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        if presentation is None:
            return SLDAssociationValidationResult(project_id=context.project_id)
        payload = presentation.to_dict() if hasattr(presentation, "to_dict") else presentation
        if not isinstance(payload, Mapping):
            raise TypeError("presentation must be an SLDDocument-like object or Mapping.")

        issues: list[ValidationIssue] = []
        presentation_project_id = payload.get("project_id")
        if presentation_project_id is not None and presentation_project_id != context.project_id:
            issues.append(ValidationIssue(
                code="SLD_PROJECT_ID_MISMATCH",
                message="Persistent SLD project_id does not match ProjectContext.project_id.",
                severity=ValidationSeverity.ERROR,
            ))

        model = payload.get("model", {})
        if not isinstance(model, Mapping):
            issues.append(ValidationIssue(
                code="SLD_MODEL_INVALID",
                message="Persistent SLD model must be a mapping.",
                severity=ValidationSeverity.ERROR,
            ))
            return SLDAssociationValidationResult(project_id=context.project_id, issues=tuple(issues))

        nodes = model.get("nodes", ())
        if not isinstance(nodes, (list, tuple)):
            issues.append(ValidationIssue(
                code="SLD_NODES_INVALID",
                message="Persistent SLD nodes must be an array.",
                severity=ValidationSeverity.ERROR,
            ))
            return SLDAssociationValidationResult(project_id=context.project_id, issues=tuple(issues))

        references: list[SLDAssociationReference] = []
        node_by_id: dict[str, Mapping[str, Any]] = {}
        for index, node in enumerate(nodes):
            if not isinstance(node, Mapping):
                issues.append(ValidationIssue(
                    code="SLD_NODE_INVALID",
                    message=f"Persistent SLD node at index {index} must be a mapping.",
                    severity=ValidationSeverity.ERROR,
                    element_type="SLD_NODE",
                ))
                continue

            node_id = str(node.get("node_id", f"<index:{index}>"))
            if node_id in node_by_id:
                issues.append(ValidationIssue(
                    code="SLD_NODE_ID_DUPLICATE",
                    message=f"Persistent SLD node identity {node_id!r} is duplicated.",
                    severity=ValidationSeverity.ERROR,
                    element_id=node_id,
                    element_type="SLD_NODE",
                ))
            else:
                node_by_id[node_id] = node

            properties = node.get("properties", {})
            if not isinstance(properties, Mapping):
                issues.append(ValidationIssue(
                    code="SLD_NODE_PROPERTIES_INVALID",
                    message=f"Persistent SLD node {node_id!r} properties must be a mapping.",
                    severity=ValidationSeverity.ERROR,
                    element_id=node_id,
                    element_type="SLD_NODE",
                ))
                properties = {}

            lifecycle = str(properties.get("lifecycle_state", "BOUND")).strip().upper()
            equipment_id_value = node.get("equipment_id")
            equipment_id = (
                None
                if equipment_id_value is None or not str(equipment_id_value).strip()
                else str(equipment_id_value).strip()
            )

            if lifecycle == "ORPHANED":
                former_id = properties.get("orphaned_equipment_id")
                former_text = f" from former Core equipment {former_id!r}" if former_id else ""
                issues.append(ValidationIssue(
                    code="SLD_NODE_ORPHANED",
                    message=f"SLD node {node_id!r} is retained as an authored orphan{former_text}.",
                    severity=ValidationSeverity.WARNING,
                    element_id=node_id,
                    element_type="SLD_NODE",
                ))
                if equipment_id is not None:
                    issues.append(ValidationIssue(
                        code="SLD_ORPHAN_NODE_HAS_ACTIVE_EQUIPMENT_BINDING",
                        message=f"Orphaned SLD node {node_id!r} still carries active Core equipment binding {equipment_id!r}.",
                        severity=ValidationSeverity.ERROR,
                        element_id=equipment_id,
                        element_type="SLD_NODE",
                    ))
            elif lifecycle != "BOUND":
                issues.append(ValidationIssue(
                    code="SLD_NODE_LIFECYCLE_INVALID",
                    message=f"SLD node {node_id!r} has unsupported lifecycle state {lifecycle!r}.",
                    severity=ValidationSeverity.ERROR,
                    element_id=node_id,
                    element_type="SLD_NODE",
                ))

            if equipment_id is None:
                references.append(SLDAssociationReference(
                    node_id=node_id,
                    equipment_id=None,
                    state=SLDAssociationState.UNREFERENCED,
                ))
                if lifecycle != "ORPHANED":
                    issues.append(ValidationIssue(
                        code="SLD_NODE_EQUIPMENT_REFERENCE_MISSING",
                        message=f"Non-orphan SLD node {node_id!r} has no Core equipment identity.",
                        severity=ValidationSeverity.ERROR,
                        element_id=node_id,
                        element_type="SLD_NODE",
                    ))
                continue

            try:
                network.get_by_identity(equipment_id)
            except (KeyError, TypeError, ValueError):
                state = SLDAssociationState.UNRESOLVED
                issues.append(ValidationIssue(
                    code="SLD_EQUIPMENT_REFERENCE_UNRESOLVED",
                    message=f"Persistent SLD node {node_id!r} references missing Core equipment {equipment_id!r}.",
                    severity=ValidationSeverity.ERROR,
                    element_id=equipment_id,
                    element_type="SLD_NODE",
                ))
            else:
                state = SLDAssociationState.RESOLVED
            references.append(SLDAssociationReference(
                node_id=node_id,
                equipment_id=equipment_id,
                state=state,
            ))

        connections = model.get("connections", ())
        if not isinstance(connections, (list, tuple)):
            issues.append(ValidationIssue(
                code="SLD_CONNECTIONS_INVALID",
                message="Persistent SLD connections must be an array.",
                severity=ValidationSeverity.ERROR,
            ))
        else:
            for index, connection in enumerate(connections):
                if not isinstance(connection, Mapping):
                    issues.append(ValidationIssue(
                        code="SLD_CONNECTION_INVALID",
                        message=f"Persistent SLD connection at index {index} must be a mapping.",
                        severity=ValidationSeverity.ERROR,
                        element_type="SLD_CONNECTION",
                    ))
                    continue

                connection_id = str(connection.get("connection_id", f"<index:{index}>"))
                properties = connection.get("properties", {})
                if not isinstance(properties, Mapping):
                    issues.append(ValidationIssue(
                        code="SLD_CONNECTION_PROPERTIES_INVALID",
                        message=f"SLD connection {connection_id!r} properties must be a mapping.",
                        severity=ValidationSeverity.ERROR,
                        element_id=connection_id,
                        element_type="SLD_CONNECTION",
                    ))
                    properties = {}

                lifecycle = str(properties.get("lifecycle_state", "BOUND")).strip().upper()
                if lifecycle == "ORPHANED":
                    former_id = properties.get("orphaned_from_core_connection_id")
                    former_text = f" from former Core connection {former_id!r}" if former_id else ""
                    issues.append(ValidationIssue(
                        code="SLD_CONNECTION_ORPHANED",
                        message=f"SLD connection {connection_id!r} is retained as an authored orphan{former_text}.",
                        severity=ValidationSeverity.WARNING,
                        element_id=connection_id,
                        element_type="SLD_CONNECTION",
                    ))
                    if properties.get("core_connection_id") is not None:
                        issues.append(ValidationIssue(
                            code="SLD_ORPHAN_CONNECTION_HAS_ACTIVE_CORE_BINDING",
                            message=f"Orphaned SLD connection {connection_id!r} still carries an active Core connection binding.",
                            severity=ValidationSeverity.ERROR,
                            element_id=connection_id,
                            element_type="SLD_CONNECTION",
                        ))
                    if connection.get("source_endpoint") is not None or connection.get("target_endpoint") is not None:
                        issues.append(ValidationIssue(
                            code="SLD_ORPHAN_CONNECTION_HAS_SEMANTIC_ENDPOINT",
                            message=f"Orphaned SLD connection {connection_id!r} still carries semantic endpoint identity.",
                            severity=ValidationSeverity.ERROR,
                            element_id=connection_id,
                            element_type="SLD_CONNECTION",
                        ))
                elif lifecycle != "BOUND":
                    issues.append(ValidationIssue(
                        code="SLD_CONNECTION_LIFECYCLE_INVALID",
                        message=f"SLD connection {connection_id!r} has unsupported lifecycle state {lifecycle!r}.",
                        severity=ValidationSeverity.ERROR,
                        element_id=connection_id,
                        element_type="SLD_CONNECTION",
                    ))
                else:
                    connection_kind = str(properties.get("connection_kind", "")).strip().upper()
                    core_connection_id = properties.get("core_connection_id")
                    if connection_kind == "SIMPLE_WIRE" or core_connection_id is not None:
                        if not isinstance(core_connection_id, str) or not core_connection_id.strip():
                            issues.append(ValidationIssue(
                                code="SLD_WIRE_WITHOUT_CORE",
                                message=f"BOUND SLD Simple-Wire connection {connection_id!r} has no canonical Core connection identity.",
                                severity=ValidationSeverity.ERROR,
                                element_id=connection_id,
                                element_type="SLD_CONNECTION",
                            ))
                        elif connection_kind != "SIMPLE_WIRE":
                            issues.append(ValidationIssue(
                                code="SLD_CONNECTION_CORE_KIND_MISMATCH",
                                message=f"SLD connection {connection_id!r} carries a Core Simple-Wire identity but is not typed SIMPLE_WIRE.",
                                severity=ValidationSeverity.ERROR,
                                element_id=connection_id,
                                element_type="SLD_CONNECTION",
                            ))
                        else:
                            try:
                                core_connection = network.connectivity.get(core_connection_id.strip())
                            except (AttributeError, KeyError, TypeError, ValueError) as exc:
                                issues.append(ValidationIssue(
                                    code="SLD_CORE_CONNECTION_REFERENCE_UNRESOLVED",
                                    message=f"BOUND SLD connection {connection_id!r} references missing Core Simple-Wire connection {core_connection_id!r}: {exc}",
                                    severity=ValidationSeverity.ERROR,
                                    element_id=connection_id,
                                    element_type="SLD_CONNECTION",
                                ))
                            else:
                                expected_endpoints = []
                                endpoint_error = None
                                for core_endpoint in (core_connection.endpoint_a, core_connection.endpoint_b):
                                    endpoint_mapping = core_endpoint.to_mapping()
                                    endpoint_kind = str(endpoint_mapping.get("kind") or "")
                                    endpoint_data = endpoint_mapping.get("endpoint")
                                    if endpoint_kind not in {"bus", "terminal"} or not isinstance(endpoint_data, Mapping):
                                        endpoint_error = f"unsupported Core endpoint kind {endpoint_kind!r}"
                                        break
                                    object_id = str(endpoint_data.get("object_id") or "")
                                    matching_nodes = []
                                    for candidate_id, candidate in node_by_id.items():
                                        candidate_properties = candidate.get("properties", {})
                                        if not isinstance(candidate_properties, Mapping):
                                            continue
                                        if (
                                            str(candidate.get("equipment_id") or "") == object_id
                                            and str(candidate_properties.get("lifecycle_state", "BOUND")).strip().upper() == "BOUND"
                                        ):
                                            matching_nodes.append((candidate_id, candidate))
                                    if len(matching_nodes) != 1:
                                        endpoint_error = (
                                            f"Core endpoint {endpoint_kind}:{object_id} resolves to "
                                            f"{len(matching_nodes)} BOUND SLD nodes; expected exactly one"
                                        )
                                        break
                                    node_id, _node = matching_nodes[0]
                                    expected_endpoints.append({
                                        "kind": "bus" if endpoint_kind == "bus" else "equipment",
                                        "node_id": node_id,
                                        "equipment_id": object_id if endpoint_kind == "terminal" else None,
                                        "terminal_role": endpoint_data.get("terminal_role") if endpoint_kind == "terminal" else None,
                                        "bus_id": object_id if endpoint_kind == "bus" else None,
                                        "attachment_id": endpoint_data.get("attachment_id") if endpoint_kind == "bus" else None,
                                    })
                                if endpoint_error is not None:
                                    issues.append(ValidationIssue(
                                        code="SLD_CORE_ENDPOINT_NODE_UNRESOLVED",
                                        message=f"BOUND SLD connection {connection_id!r} cannot resolve its canonical Core endpoint to one BOUND SLD node: {endpoint_error}.",
                                        severity=ValidationSeverity.ERROR,
                                        element_id=connection_id,
                                        element_type="SLD_CONNECTION",
                                    ))
                                else:
                                    actual_endpoints = (
                                        connection.get("source_endpoint"),
                                        connection.get("target_endpoint"),
                                    )
                                    actual_node_ids = (
                                        connection.get("source_node_id"),
                                        connection.get("target_node_id"),
                                    )
                                    expected_node_ids = tuple(item["node_id"] for item in expected_endpoints)
                                    if (
                                        tuple(actual_endpoints) != tuple(expected_endpoints)
                                        or tuple(actual_node_ids) != expected_node_ids
                                    ):
                                        issues.append(ValidationIssue(
                                            code="SLD_CORE_ENDPOINT_MISMATCH",
                                            message=f"BOUND SLD connection {connection_id!r} endpoint descriptors or node identities do not match Core Simple-Wire {core_connection_id!r}.",
                                            severity=ValidationSeverity.ERROR,
                                            element_id=connection_id,
                                            element_type="SLD_CONNECTION",
                                        ))

        return SLDAssociationValidationResult(
            project_id=context.project_id,
            references=tuple(references),
            issues=tuple(issues),
        )
    def invalidate(self) -> None:
        """Discard the previous result after authoritative model mutation."""
        self._result = None

    def read_validation(self) -> ValidationResult | None:
        """Return the latest validation snapshot, if one exists."""
        return self._result

    def _elements(self) -> tuple[Any, ...]:
        registry = self._network.registry
        return (
            *registry.buses,
            *registry.grids,
            *registry.generators,
            *registry.synchronous_machines,
            *registry.loads,
            *registry.motors,
            *registry.shunts,
            *registry.capacitors,
            *registry.reactors,
            *registry.solar,
            *registry.batteries,
            *registry.current_transformers,
            *registry.potential_transformers,
            *registry.capacitive_voltage_transformers,
            *registry.relays,
            *registry.lines,
            *registry.cables,
            *registry.transformers,
            *registry.breakers,
            *registry.switches,
            *registry.disconnectors,
            *registry.fuses,
        )


__all__ = ["ValidationService"]
