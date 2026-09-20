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

    def validate_project(self, *, context: Any | None = None, presentation: Any | None = None) -> ValidationResult:
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
            sld_validation = self.validate_sld_associations(context, self._network, presentation)
            issues.extend(sld_validation.issues)

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
            model_revision=self._network.state.model_revision,
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
        """Validate persistent SLD equipment references without mutating state.

        The presentation argument may be an SLDDocument-like object exposing
        to_dict() or its persisted Mapping form. This keeps SLD structure
        outside Core while placing cross-domain association validation at the
        Application boundary.

        No orphan/repair policy is inferred here. A missing equipment ID is
        reported as UNRESOLVED and remains observable for an architectural
        decision.
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
        for index, node in enumerate(nodes):
            if not isinstance(node, Mapping):
                issues.append(ValidationIssue(
                    code="SLD_NODE_INVALID",
                    message=f"Persistent SLD node at index {index} must be a mapping.",
                    severity=ValidationSeverity.ERROR,
                ))
                continue
            node_id = str(node.get("node_id", f"<index:{index}>"))
            equipment_id = node.get("equipment_id")
            if equipment_id is None:
                references.append(SLDAssociationReference(
                    node_id=node_id, equipment_id=None, state=SLDAssociationState.UNREFERENCED
                ))
                continue
            equipment_id = str(equipment_id)
            try:
                network.get_by_identity(equipment_id)
            except KeyError:
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
                node_id=node_id, equipment_id=equipment_id, state=state
            ))

        return SLDAssociationValidationResult(
            project_id=context.project_id, references=tuple(references), issues=tuple(issues)
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
