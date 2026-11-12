"""Canonical StudyService adapter for sampled generator transient execution.

The Application StudyService owns scheduling, cancellation, provenance and
result persistence. The host composition supplies the numerical transient
solver; this plugin adapter never creates a second scheduler or integrator.
"""
from __future__ import annotations

from typing import Any

from core.application.study import (
    StudyCancellationToken,
    StudyExecutionContext,
    StudyRequest,
)

from .ggov1_execution import GGOV1SampledExecutionAdapter


class GeneratorTransientStudyHandler:
    """Delegate a provenance-bound generator study to the host solver.

    The injected solver must expose solve_generator_transient(request=...,
    execution_context=..., cancellation=..., sampled_adapter=...). Its
    implementation owns integration, accepted/rejected-step policy, rollback
    and partial-result evidence. This adapter only connects it to StudyService.
    """

    def __init__(self, solver: Any, sampled_adapter: GGOV1SampledExecutionAdapter) -> None:
        if solver is None or not callable(getattr(solver, "solve_generator_transient", None)):
            raise TypeError("generator transient solver must expose solve_generator_transient(...)")
        if not isinstance(sampled_adapter, GGOV1SampledExecutionAdapter):
            raise TypeError("sampled_adapter must be GGOV1SampledExecutionAdapter")
        self._solver = solver
        self._sampled_adapter = sampled_adapter

    def __call__(
        self,
        request: StudyRequest,
        execution_context: StudyExecutionContext,
        cancellation: StudyCancellationToken,
    ) -> Any:
        if not isinstance(request, StudyRequest):
            raise TypeError("request must be StudyRequest")
        if not isinstance(execution_context, StudyExecutionContext):
            raise TypeError("execution_context must be StudyExecutionContext")
        if not isinstance(cancellation, StudyCancellationToken):
            raise TypeError("cancellation must be StudyCancellationToken")
        if request.study_type != "generator_transient":
            raise ValueError("GeneratorTransientStudyHandler only accepts generator_transient")
        if (
            request.project_id != execution_context.project_id
            or request.activation_generation != execution_context.activation_generation
            or request.source_revision != execution_context.source_revision
        ):
            raise ValueError("generator transient request/context provenance mismatch")
        if cancellation.cancelled:
            return None
        # Return the solver-owned detached result unchanged. StudyService is
        # responsible for terminal status, durable persistence and events.
        return self._solver.solve_generator_transient(
            request=request,
            execution_context=execution_context,
            cancellation=cancellation,
            sampled_adapter=self._sampled_adapter,
        )


__all__ = ["GeneratorTransientStudyHandler"]
