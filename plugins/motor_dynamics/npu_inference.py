"""Optional ONNX Runtime inference with capability-based NPU/GPU/CPU fallback.

Provider presence is only a capability signal, not proof that a model is
compatible with a provider or that every graph node executes on an accelerator.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


class MotorNPUDiagnosticNode:
    """Inference adapter preferring supported accelerators and retaining CPU fallback."""

    PROVIDER_PRIORITY = (
        # NPU-capable providers are preferred when installed. Provider
        # availability does not guarantee that the device or model is usable.
        "QNNExecutionProvider",
        "VitisAIExecutionProvider",
        "OpenVINOExecutionProvider",
        # GPU providers, followed by the portable CPU fallback.
        "TensorrtExecutionProvider",
        "CUDAExecutionProvider",
        "DmlExecutionProvider",
        "CPUExecutionProvider",
    )

    def __init__(self, model_path: str | Path, intra_op_threads: int = 1) -> None:
        self.model_path = Path(model_path)
        self.session = None
        self.input_name = None
        self.input_shape = None
        self.input_type = None
        self.providers: tuple[str, ...] = ()
        self.requested_provider = None
        self.provider_fallback_used = False
        self.initialization_diagnostics: tuple[str, ...] = ()
        self.runtime_diagnostics: tuple[str, ...] = ()
        self._ort = None
        self._session_options = None

        if not self.model_path.is_file():
            raise FileNotFoundError(self.model_path)
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError("onnxruntime is required for optional motor inference") from exc

        available = set(ort.get_available_providers())
        candidates = [name for name in self.PROVIDER_PRIORITY if name in available]
        if "CPUExecutionProvider" not in candidates:
            raise RuntimeError(
                "CPUExecutionProvider is required as the portable inference fallback."
            )

        diagnostics = []
        options = self._options(ort, intra_op_threads)
        self._ort = ort
        self._session_options = options
        for candidate in candidates:
            # Keep CPU in the session's provider list when selecting an
            # accelerator so unsupported graph nodes can fall back safely.
            selected = (
                [candidate, "CPUExecutionProvider"]
                if candidate != "CPUExecutionProvider"
                else ["CPUExecutionProvider"]
            )
            try:
                session = ort.InferenceSession(
                    str(self.model_path),
                    providers=selected,
                    sess_options=options,
                )
            except Exception as exc:
                diagnostics.append(
                    f"{candidate} initialization failed: {type(exc).__name__}: {exc}"
                )
                continue
            self.session = session
            self.requested_provider = candidate
            self.providers = tuple(session.get_providers())
            break

        self.initialization_diagnostics = tuple(diagnostics)
        # A failed candidate is not itself a fallback if a later accelerator
        # initializes successfully. Report initialization fallback only when
        # CPU was selected after one or more candidate initialization failures.
        self.provider_fallback_used = (
            self.requested_provider == "CPUExecutionProvider" and bool(diagnostics)
        )
        if self.session is None:
            detail = "; ".join(diagnostics) or "no candidate provider initialized"
            raise RuntimeError(f"Could not initialize ONNX inference: {detail}")

        inputs = self.session.get_inputs()
        if not inputs:
            raise ValueError("ONNX model has no input tensor.")
        model_input = inputs[0]
        self.input_name = model_input.name
        self.input_shape = tuple(model_input.shape)
        self.input_type = str(model_input.type)

    @staticmethod
    def _options(ort: Any, threads: int):
        if isinstance(threads, bool) or not isinstance(threads, int) or threads < 1:
            raise ValueError("intra_op_threads must be a positive integer.")
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        return options

    def _prepare(self, features: np.ndarray) -> np.ndarray:
        x = np.asarray(features)
        if not np.issubdtype(x.dtype, np.number) or not np.isrealobj(x) or not np.isfinite(x).all():
            raise ValueError("Inference features must be a finite numeric array.")

        # Do not silently truncate or pad engineering features: that can change
        # the model's meaning while producing plausible-looking output.
        shape = self.input_shape
        if not shape:
            raise ValueError("Scalar ONNX inputs are not supported by this adapter.")
        dimensions = list(shape)
        if len(dimensions) == 1:
            expected = dimensions[0]
            if isinstance(expected, int) and x.size != expected:
                raise ValueError(f"Model requires {expected} features; received {x.size}.")
            target_shape = (x.size,)
        else:
            # Treat the first dimension as batch. Only a dynamic batch dimension
            # is inferred; all remaining dimensions must be statically known.
            sample_shape = dimensions[1:]
            if not sample_shape or any(not isinstance(dim, int) or dim <= 0 for dim in sample_shape):
                raise ValueError(
                    f"Unsupported dynamic/non-positive model input shape: {shape!r}."
                )
            expected = int(np.prod(sample_shape))
            if x.size != expected:
                raise ValueError(f"Model requires {expected} values per sample; received {x.size}.")
            target_shape = (1, *sample_shape)

        tensor_types = {
            "tensor(float)": np.float32,
            "tensor(double)": np.float64,
            "tensor(float16)": np.float16,
        }
        dtype = tensor_types.get(self.input_type)
        if dtype is None:
            raise ValueError(
                f"Unsupported model input type {self.input_type!r}; quantized integer "
                "inputs require an explicit model-specific quantization contract."
            )
        return np.ascontiguousarray(x.astype(dtype, copy=False).reshape(target_shape))

    def infer(self, features: np.ndarray) -> dict[str, Any]:
        if self.session is None or self.input_name is None:
            raise RuntimeError("Inference session is not initialized.")
        prepared = self._prepare(features)
        try:
            values = self.session.run(None, {self.input_name: prepared})
        except Exception as accelerator_error:
            runtime_diagnostics = [
                f"{self.requested_provider} inference failed: "
                f"{type(accelerator_error).__name__}: {accelerator_error}"
            ]
            if (
                self.requested_provider == "CPUExecutionProvider"
                or self._ort is None
                or self._session_options is None
            ):
                raise RuntimeError(
                    f"Motor inference failed on {self.requested_provider!r}; CPU fallback is unavailable."
                ) from accelerator_error

            try:
                cpu_session = self._ort.InferenceSession(
                    str(self.model_path),
                    providers=["CPUExecutionProvider"],
                    sess_options=self._session_options,
                )
                cpu_inputs = cpu_session.get_inputs()
                if not cpu_inputs:
                    raise ValueError("ONNX model has no input tensor.")
                cpu_input = cpu_inputs[0]
                if cpu_input.name != self.input_name:
                    raise ValueError("CPU fallback session input contract differs from the initialized session.")
                values = cpu_session.run(None, {cpu_input.name: prepared})
            except Exception as cpu_error:
                self.runtime_diagnostics = tuple(
                    runtime_diagnostics
                    + [
                        f"CPUExecutionProvider retry failed: "
                        f"{type(cpu_error).__name__}: {cpu_error}"
                    ]
                )
                raise RuntimeError(
                    "Motor inference failed on the selected provider and CPU-only retry also failed."
                ) from cpu_error

            runtime_diagnostics.append(
                "CPUExecutionProvider retry succeeded after provider runtime failure."
            )
            self.runtime_diagnostics = tuple(runtime_diagnostics)
            self.session = cpu_session
            self.providers = tuple(cpu_session.get_providers())
            self.requested_provider = "CPUExecutionProvider"
            self.provider_fallback_used = True

        return {
            "outputs": [np.asarray(value).tolist() for value in values],
            "requested_provider": self.requested_provider,
            "session_providers": list(self.providers),
            "initialization_diagnostics": list(self.initialization_diagnostics),
            "runtime_diagnostics": list(self.runtime_diagnostics),
            "provider_fallback_used": self.provider_fallback_used,
        }
