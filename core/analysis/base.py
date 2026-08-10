# analysis/base.py

"""
Base Analysis Contract

Defines the standard interface for all analysis modules.
Every analysis must inherit from BaseAnalysis and implement `run()`.
"""


from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAnalysis(ABC):
    """
    Abstract base class for all analysis modules.
    """

    def __init__(self, model: Dict):
        """
        Parameters
        ----------
        model : dict
            System model containing buses, lines, generators, etc.
        """
        self.model = model
        self._results = None

    # -------------------------
    # Public API
    # -------------------------

    def execute(self) -> Any:
        """
        Standard execution pipeline.

        Returns
        -------
        Any
            Analysis results
        """
        self.validate()
        self._results = self.run()
        return self._results

    def get_results(self) -> Any:
        """
        Retrieve last computed results.
        """
        return self._results

    # -------------------------
    # Required Methods
    # -------------------------

    @abstractmethod
    def run(self) -> Any:
        """
        Core computation logic.
        Must be implemented by subclasses.
        """
        pass

    # -------------------------
    # Optional Hooks
    # -------------------------

    def validate(self) -> None:
        """
        Basic validation hook.
        Can be overridden by subclasses.
        """
        if self.model is None:
            raise ValueError("Model cannot be None")

        if not isinstance(self.model, dict):
            raise ValueError("Model must be a dictionary")

        if "buses" not in self.model:
            raise ValueError("Model missing 'buses'")

    def reset(self) -> None:
        """
        Reset stored results.
        """
        self._results = None
