"""Evidence binding for transformer phase-domain zero-sequence matrices.

This contract does not manufacture winding/core physics. It binds an exact,
ordered terminal admittance matrix to manufacturer or test-report evidence
for its zero-sequence core-return and any delta circulating-current paths.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from types import MappingProxyType
from typing import Mapping, Sequence


def transformer_multiport_fingerprint(
    matrix: Sequence[Sequence[complex]],
    terminal_labels: Sequence[str],
) -> str:
    """Return a deterministic digest for the ordered SI terminal matrix."""
    labels = tuple(str(label).strip() for label in terminal_labels)
    rows = tuple(tuple(complex(value) for value in row) for row in matrix)
    payload = "\n".join(
        [*labels, "--MATRIX--"]
        + [
            ",".join(f"{value.real.hex()}:{value.imag.hex()}" for value in row)
            for row in rows
        ]
    )
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class TransformerDeltaLoopState:
    """One explicitly resolved internal delta circulating-current loop."""

    loop_id: str
    winding: str
    coupling_coefficients: tuple[complex, ...]
    impedance_ohm: complex

    def __post_init__(self) -> None:
        loop_id = str(self.loop_id).strip()
        winding = str(self.winding).strip().upper()
        if not loop_id or winding not in {"HV", "LV"}:
            raise ValueError("Delta loop requires a non-empty id and HV/LV winding.")
        coefficients = tuple(complex(value) for value in self.coupling_coefficients)
        if not coefficients or any(not (math.isfinite(v.real) and math.isfinite(v.imag)) for v in coefficients):
            raise ValueError("Delta loop coupling coefficients must be finite and non-empty.")
        if not any(value != 0j for value in coefficients):
            raise ValueError("Delta loop must couple to at least one terminal.")
        impedance = complex(self.impedance_ohm)
        if not math.isfinite(impedance.real) or not math.isfinite(impedance.imag) or impedance.real <= 0.0:
            raise ValueError("Delta loop impedance must be finite with strictly positive resistance.")
        object.__setattr__(self, "loop_id", loop_id)
        object.__setattr__(self, "winding", winding)
        object.__setattr__(self, "coupling_coefficients", coefficients)
        object.__setattr__(self, "impedance_ohm", impedance)


def transformer_delta_loop_fingerprint(loop_states: Sequence[TransformerDeltaLoopState]) -> str:
    """Fingerprint ordered internal loop ids, windings, coupling and impedances."""
    payload = []
    for item in loop_states:
        payload.append(
            "|".join((
                item.loop_id,
                item.winding,
                ",".join(f"{value.real.hex()}:{value.imag.hex()}" for value in item.coupling_coefficients),
                f"{complex(item.impedance_ohm).real.hex()}:{complex(item.impedance_ohm).imag.hex()}",
            ))
        )
    return sha256("\n".join(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class TransformerZeroSequenceMultiportEvidence:
    """Manufacturer/test evidence attached to one exact transformer matrix."""

    matrix_sha256: str
    terminal_labels: tuple[str, ...]
    core_construction: str
    core_zero_sequence_test_reference: str
    delta_circulating_test_references: Mapping[str, str]
    delta_loop_sha256: str | None = None

    def __post_init__(self) -> None:
        digest = str(self.matrix_sha256).strip().lower()
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("matrix_sha256 must be a 64-character SHA-256 digest.")
        object.__setattr__(self, "matrix_sha256", digest)
        labels = tuple(str(value).strip() for value in self.terminal_labels)
        if len(labels) < 6 or any(not value for value in labels) or len(set(labels)) != len(labels):
            raise ValueError("Evidence terminal_labels must be a unique ordered terminal inventory.")
        object.__setattr__(self, "terminal_labels", labels)
        core = str(getattr(self.core_construction, "value", self.core_construction)).strip().upper()
        if core not in {"THREE_LIMB", "FIVE_LIMB", "SHELL_FORM"}:
            raise ValueError("Evidence requires THREE_LIMB, FIVE_LIMB or SHELL_FORM core construction.")
        object.__setattr__(self, "core_construction", core)
        reference = str(self.core_zero_sequence_test_reference).strip()
        if not reference:
            raise ValueError("A core zero-sequence test/manufacturer reference is required.")
        object.__setattr__(self, "core_zero_sequence_test_reference", reference)
        refs = {}
        for winding, value in dict(self.delta_circulating_test_references).items():
            key = str(winding).strip().upper()
            ref = str(value).strip()
            if key not in {"HV", "LV"} or not ref:
                raise ValueError("Delta circulating test references must map HV/LV to non-empty sources.")
            refs[key] = ref
        object.__setattr__(self, "delta_circulating_test_references", MappingProxyType(refs))
        loop_digest = None if self.delta_loop_sha256 is None else str(self.delta_loop_sha256).strip().lower()
        if loop_digest is not None and (len(loop_digest) != 64 or any(ch not in "0123456789abcdef" for ch in loop_digest)):
            raise ValueError("delta_loop_sha256 must be a 64-character SHA-256 digest.")
        if refs and loop_digest is None:
            raise ValueError("Delta circulating-current evidence requires a fingerprint of the explicit loop states.")
        if not refs and loop_digest is not None:
            raise ValueError("A delta-loop fingerprint is invalid when no delta winding is configured.")
        object.__setattr__(self, "delta_loop_sha256", loop_digest)


def validate_transformer_zero_sequence_multiport_evidence(
    evidence: TransformerZeroSequenceMultiportEvidence | None,
    *,
    matrix: Sequence[Sequence[complex]],
    terminal_labels: Sequence[str],
    core_construction: str,
    delta_windings: Sequence[str],
    delta_loop_states: Sequence[TransformerDeltaLoopState] = (),
) -> None:
    """Fail closed unless evidence is bound to this exact matrix and topology."""
    if not isinstance(evidence, TransformerZeroSequenceMultiportEvidence):
        raise ValueError("Transformer zero-sequence multiport requires explicit core/delta test evidence.")
    labels = tuple(terminal_labels)
    if evidence.terminal_labels != labels:
        raise ValueError("Transformer zero-sequence evidence terminal order does not match the generated multiport.")
    if evidence.matrix_sha256 != transformer_multiport_fingerprint(matrix, labels):
        raise ValueError("Transformer zero-sequence evidence SHA-256 does not match the active terminal admittance matrix.")
    core = str(getattr(core_construction, "value", core_construction)).strip().upper()
    if evidence.core_construction != core:
        raise ValueError("Transformer zero-sequence evidence core construction does not match the physical model.")
    required = {str(value).strip().upper() for value in delta_windings}
    supplied = set(evidence.delta_circulating_test_references)
    loop_states = tuple(delta_loop_states)
    loop_windings = {item.winding for item in loop_states}
    if loop_windings != required:
        raise ValueError(
            "Explicit internal delta-loop states must cover exactly the delta-connected windings; "
            f"required={sorted(required)}, supplied={sorted(loop_windings)}."
        )
    if required and evidence.delta_loop_sha256 != transformer_delta_loop_fingerprint(loop_states):
        raise ValueError("Transformer delta-loop evidence fingerprint does not match the active internal loop states.")
    if supplied != required:
        raise ValueError(
            "Delta circulating-current evidence must identify exactly the delta-connected windings; "
            f"required={sorted(required)}, supplied={sorted(supplied)}."
        )


__all__ = [
    "TransformerDeltaLoopState",
    "transformer_delta_loop_fingerprint",
    "TransformerZeroSequenceMultiportEvidence",
    "transformer_multiport_fingerprint",
    "validate_transformer_zero_sequence_multiport_evidence",
]
