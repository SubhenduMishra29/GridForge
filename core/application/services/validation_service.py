# ============================================================
# File: core/application/services/validation_service.py
# GridForge V2 — Application Validation Service
# Author: Subhendu Mishra
# ============================================================

"""Application-owned validation lifecycle over authoritative Core state."""

from __future__ import annotations

from typing import Any

from core.network import Network

from ..validation import (
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

    def validate_project(self) -> ValidationResult:
        """Validate every registered Core model and current topology state."""
        issues: list[ValidationIssue] = []
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
            *registry.lines,
            *registry.cables,
            *registry.transformers,
            *registry.breakers,
            *registry.switches,
            *registry.disconnectors,
            *registry.fuses,
        )


__all__ = ["ValidationService"]
