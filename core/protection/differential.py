"""Pure, headless numerical kernel for configured current differential protection.

Inputs are fundamental-frequency RMS complex phasors in amperes, already
normalised to one explicitly declared common relay reference basis. Instrument
conversion, transformer compensation, waveform supervision and trip logic are
outside this kernel.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from types import MappingProxyType
from typing import Mapping

from .project_configuration import DifferentialProtectionSchemeConfiguration

_PHASES = ("A", "B", "C")


class DifferentialRestraintMethod(str, Enum):
    """Selectable restraint-current definitions; no vendor default is implied."""
    HALF_SUM_MAGNITUDES = "HALF_SUM_MAGNITUDES"
    SUM_MAGNITUDES = "SUM_MAGNITUDES"
    MAX_MAGNITUDE = "MAX_MAGNITUDE"


@dataclass(frozen=True, slots=True)
class DifferentialProtectionSettings:
    """Explicit percentage-bias characteristic in the declared common ampere base."""
    pickup_current_a: float
    restraint_method: DifferentialRestraintMethod | str
    slopes: tuple[float, ...]
    breakpoints_a: tuple[float, ...] = ()
    high_set_pickup_a: float | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "pickup_current_a": self.pickup_current_a,
            "restraint_method": self.restraint_method.value,
            "slopes": list(self.slopes),
            "breakpoints_a": list(self.breakpoints_a),
            "high_set_pickup_a": self.high_set_pickup_a,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "DifferentialProtectionSettings":
        if not isinstance(data, Mapping):
            raise TypeError("differential settings must be a mapping.")
        return cls(
            pickup_current_a=data["pickup_current_a"],
            restraint_method=data["restraint_method"],
            slopes=tuple(data["slopes"]),
            breakpoints_a=tuple(data.get("breakpoints_a", ())),
            high_set_pickup_a=data.get("high_set_pickup_a"),
        )

    def __post_init__(self) -> None:
        pickup = _finite_nonnegative(self.pickup_current_a, "pickup_current_a")
        if pickup <= 0.0:
            raise ValueError("pickup_current_a must be greater than zero.")
        object.__setattr__(self, "pickup_current_a", pickup)
        try:
            method = DifferentialRestraintMethod(self.restraint_method)
        except (TypeError, ValueError) as exc:
            raise ValueError("Unsupported differential restraint method.") from exc
        object.__setattr__(self, "restraint_method", method)
        if not isinstance(self.slopes, (tuple, list)) or not self.slopes:
            raise ValueError("At least one percentage-bias slope is required.")
        slopes = tuple(_finite_nonnegative(value, "slope") for value in self.slopes)
        if not isinstance(self.breakpoints_a, (tuple, list)):
            raise TypeError("breakpoints_a must be a tuple or list.")
        breakpoints = tuple(_finite_nonnegative(value, "breakpoint") for value in self.breakpoints_a)
        if len(slopes) != len(breakpoints) + 1:
            raise ValueError("The number of slopes must equal the number of breakpoints plus one.")
        if any(value <= 0.0 for value in breakpoints):
            raise ValueError("Every restraint breakpoint must be greater than zero.")
        if any(right <= left for left, right in zip(breakpoints, breakpoints[1:])):
            raise ValueError("Restraint breakpoints must be strictly increasing.")
        object.__setattr__(self, "slopes", slopes)
        object.__setattr__(self, "breakpoints_a", breakpoints)
        if self.high_set_pickup_a is not None:
            high_set = _finite_nonnegative(self.high_set_pickup_a, "high_set_pickup_a")
            if high_set <= 0.0:
                raise ValueError("high_set_pickup_a must be greater than zero.")
            object.__setattr__(self, "high_set_pickup_a", high_set)


@dataclass(frozen=True, slots=True)
class DifferentialCurrentSample:
    """Detached three-phase RMS phasors for one CT binding, in amperes."""
    binding_id: str
    reference_basis_id: str
    current_phasors_a: Mapping[str, complex]

    def __post_init__(self) -> None:
        for name in ("binding_id", "reference_basis_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())
        if not isinstance(self.current_phasors_a, Mapping):
            raise TypeError("current_phasors_a must be a phase-to-complex-phasor mapping.")
        if set(self.current_phasors_a) != set(_PHASES):
            raise ValueError("Every differential sample must provide exactly phases A, B and C.")
        normalized: dict[str, complex] = {}
        for phase in _PHASES:
            value = self.current_phasors_a[phase]
            if isinstance(value, bool) or not isinstance(value, (int, float, complex)):
                raise TypeError(f"Phase {phase} current must be a real or complex numeric phasor.")
            phasor = complex(value)
            if not math.isfinite(phasor.real) or not math.isfinite(phasor.imag):
                raise ValueError(f"Phase {phase} current phasor must be finite.")
            normalized[phase] = phasor
        object.__setattr__(self, "current_phasors_a", MappingProxyType(normalized))


@dataclass(frozen=True, slots=True)
class DifferentialPhaseResult:
    """Per-phase differential operating and restraint quantities."""
    phase: str
    operate_current_a: float
    restraint_current_a: float
    bias_threshold_a: float
    bias_margin_a: float
    high_set_margin_a: float | None
    operates: bool


@dataclass(frozen=True, slots=True)
class DifferentialProtectionResult:
    """Immutable, non-actuating result from one differential calculation."""
    scheme_id: str
    reference_basis_id: str
    input_binding_ids: tuple[str, ...]
    phase_results: Mapping[str, DifferentialPhaseResult]
    operates: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_binding_ids", tuple(self.input_binding_ids))
        object.__setattr__(self, "phase_results", MappingProxyType(dict(self.phase_results)))


def evaluate_differential_scheme(
    scheme: DifferentialProtectionSchemeConfiguration,
    settings: DifferentialProtectionSettings | None,
    samples: Mapping[str, DifferentialCurrentSample],
) -> DifferentialProtectionResult:
    """Evaluate a configured scheme without side effects or inferred topology."""
    if not isinstance(scheme, DifferentialProtectionSchemeConfiguration):
        raise TypeError("scheme must be a DifferentialProtectionSchemeConfiguration.")
    if settings is None:
        if not scheme.differential_settings:
            raise ValueError("Differential settings must be supplied or persisted on the scheme.")
        settings = DifferentialProtectionSettings.from_dict(scheme.differential_settings)
    if not isinstance(settings, DifferentialProtectionSettings):
        raise TypeError("settings must be DifferentialProtectionSettings or None.")
    if not scheme.enabled:
        raise ValueError("A disabled differential scheme cannot be evaluated.")
    if not isinstance(samples, Mapping):
        raise TypeError("samples must be keyed by measurement binding ID.")

    expected_ids = set(scheme.measurement_binding_ids)
    if set(samples) != expected_ids:
        missing = sorted(expected_ids - set(samples))
        unexpected = sorted(set(samples) - expected_ids)
        raise ValueError(
            f"Differential sample set does not match scheme membership; "
            f"missing={missing}, unexpected={unexpected}."
        )
    if any(value != 0.0 for value in scheme.phase_compensation_degrees.values()):
        raise NotImplementedError(
            "Configured phase compensation requires an equipment-specific adapter; "
            "the generic differential kernel will not ignore it."
        )

    ordered_samples: list[DifferentialCurrentSample] = []
    for binding_id in scheme.measurement_binding_ids:
        sample = samples[binding_id]
        if not isinstance(sample, DifferentialCurrentSample):
            raise TypeError(f"Sample for binding {binding_id!r} has an unsupported type.")
        if sample.binding_id != binding_id:
            raise ValueError(f"Sample key and binding identity differ for {binding_id!r}.")
        ordered_samples.append(sample)

    basis_ids = {sample.reference_basis_id for sample in ordered_samples}
    if len(basis_ids) != 1:
        raise ValueError("All differential samples must use the same explicit reference_basis_id.")
    reference_basis_id = next(iter(basis_ids))

    phase_results: dict[str, DifferentialPhaseResult] = {}
    for phase in _PHASES:
        signed_sum = 0j
        magnitudes: list[float] = []
        for sample in ordered_samples:
            phasor = sample.current_phasors_a[phase]
            direction = scheme.current_directions[sample.binding_id]
            signed_sum += phasor if direction == "INTO_ZONE" else -phasor
            magnitudes.append(abs(phasor))
        operate_current = abs(signed_sum)
        restraint_current = _restraint_current(settings.restraint_method, magnitudes)
        threshold = _bias_threshold(settings, restraint_current)
        if not all(math.isfinite(value) for value in (operate_current, restraint_current, threshold)):
            raise ValueError(f"Differential calculation overflowed for phase {phase}.")
        bias_margin = operate_current - threshold
        high_set_margin = (
            None if settings.high_set_pickup_a is None
            else operate_current - settings.high_set_pickup_a
        )
        bias_operates = bias_margin > 0.0
        high_set_operates = high_set_margin is not None and high_set_margin > 0.0
        phase_results[phase] = DifferentialPhaseResult(
            phase=phase,
            operate_current_a=operate_current,
            restraint_current_a=restraint_current,
            bias_threshold_a=threshold,
            bias_margin_a=bias_margin,
            high_set_margin_a=high_set_margin,
            operates=bias_operates or high_set_operates,
        )
    return DifferentialProtectionResult(
        scheme_id=scheme.scheme_id,
        reference_basis_id=reference_basis_id,
        input_binding_ids=scheme.measurement_binding_ids,
        phase_results=phase_results,
        operates=any(result.operates for result in phase_results.values()),
    )


def _restraint_current(method: DifferentialRestraintMethod, magnitudes: list[float]) -> float:
    if method is DifferentialRestraintMethod.HALF_SUM_MAGNITUDES:
        return 0.5 * sum(magnitudes)
    if method is DifferentialRestraintMethod.SUM_MAGNITUDES:
        return sum(magnitudes)
    if method is DifferentialRestraintMethod.MAX_MAGNITUDE:
        return max(magnitudes)
    raise ValueError(f"Unsupported restraint method: {method!r}.")


def _bias_threshold(settings: DifferentialProtectionSettings, restraint_a: float) -> float:
    threshold = settings.pickup_current_a
    lower_bound = 0.0
    for index, slope in enumerate(settings.slopes):
        upper_bound = settings.breakpoints_a[index] if index < len(settings.breakpoints_a) else restraint_a
        segment_width = max(0.0, min(restraint_a, upper_bound) - lower_bound)
        threshold += slope * segment_width
        if restraint_a <= upper_bound:
            break
        lower_bound = upper_bound
    return threshold


def _finite_nonnegative(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric, not boolean.")
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be numeric.") from exc
    if not math.isfinite(normalized) or normalized < 0.0:
        raise ValueError(f"{name} must be finite and non-negative.")
    return normalized


__all__ = [
    "DifferentialRestraintMethod", "DifferentialProtectionSettings",
    "DifferentialCurrentSample", "DifferentialPhaseResult",
    "DifferentialProtectionResult", "evaluate_differential_scheme",
]
