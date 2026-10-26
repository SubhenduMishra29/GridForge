"""Optional ONNX Runtime INT8 inference; provider availability is detected, never assumed."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import numpy as np

class MotorNPUDiagnosticNode:
    def __init__(self, model_path: str | Path, intra_op_threads: int = 1) -> None:
        self.model_path = Path(model_path); self.session = None; self.input_name = None; self.input_shape = None; self.providers = ()
        if not self.model_path.is_file(): raise FileNotFoundError(self.model_path)
        try: import onnxruntime as ort
        except ImportError as exc: raise RuntimeError("onnxruntime is required for NPU inference") from exc
        available = set(ort.get_available_providers())
        ordered = [p for p in ("VitisAIExecutionProvider", "CPUExecutionProvider") if p in available]
        if not ordered: raise RuntimeError("neither VitisAIExecutionProvider nor CPUExecutionProvider is available")
        # Vitis AI EP requires a compatible quantized model and provider-specific configuration.
        self.session = ort.InferenceSession(str(self.model_path), providers=ordered, sess_options=self._options(ort, intra_op_threads))
        inp = self.session.get_inputs()[0]; self.input_name, self.input_shape = inp.name, inp.shape
        self.providers = tuple(self.session.get_providers())
    @staticmethod
    def _options(ort: Any, threads: int):
        options = ort.SessionOptions(); options.intra_op_num_threads = max(1, int(threads)); options.inter_op_num_threads = 1; options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        return options
    def _prepare(self, features: np.ndarray) -> np.ndarray:
        x = np.asarray(features, dtype=np.float32)
        shape = self.input_shape
        if len(shape) == 2:
            target = shape[1] if isinstance(shape[1], int) else x.size
            if x.size > target: x = x[:target]
            elif x.size < target: x = np.pad(x, (0, target-x.size))
            x = x.reshape(1, target)
        else: x = x.reshape(1, -1)
        return np.ascontiguousarray(x)
    def infer(self, features: np.ndarray) -> dict[str, Any]:
        values = self.session.run(None, {self.input_name: self._prepare(features)})
        # Return plain Python values, not runtime-owned tensors.
        return {"outputs": [np.asarray(v).tolist() for v in values], "providers": list(self.providers)}
