"""
GridForge Dynamic Plugin Contract
=================================

Defines the common interface implemented by all GridForge dynamic
component plugins.

The contract separates:

    - physical/model equations
    - plugin adaptation
    - dynamic solver state ownership

The dynamic solver owns the global state vector and numerical
integration. Dynamic plugins only evaluate equations and outputs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DynamicPlugin(ABC):
    """
    Abstract base contract for GridForge dynamic plugins.

    A dynamic plugin represents one dynamic component or one
    dynamic control model.

    State Ownership
    ---------------
    The plugin does NOT own authoritative simulation state.

    The solver owns:

        x(t)

    The plugin receives its local state and returns derivatives.

    This allows multiple dynamic models to participate in one
    global DAE system.
    """

    # =========================================================
    # METADATA
    # =========================================================

    plugin_type: str = "dynamics"
    model_type: str = "UNKNOWN"

    state_names: tuple[str, ...] = ()

    # =========================================================
    # STATE INFORMATION
    # =========================================================

    @property
    def state_size(self) -> int:
        """
        Return the number of dynamic states contributed by the
        plugin.
        """

        return len(self.state_names)

    # =========================================================
    # INITIAL STATE
    # =========================================================

    @abstractmethod
    def initial_state(
        self,
        **inputs: Any,
    ) -> tuple[float, ...]:
        """
        Return the initial dynamic state vector.

        The returned vector must have exactly ``state_size``
        elements.
        """

        raise NotImplementedError

    # =========================================================
    # DIFFERENTIAL EQUATIONS
    # =========================================================

    @abstractmethod
    def derivatives(
        self,
        state: tuple[float, ...] | list[float],
        **inputs: Any,
    ) -> tuple[float, ...]:
        """
        Evaluate the differential equations.

        Parameters
        ----------
        state:
            Local dynamic state vector.

        **inputs:
            Algebraic or control inputs supplied by the solver.

        Returns
        -------
        tuple
            Local state derivatives.
        """

        raise NotImplementedError

    # =========================================================
    # OUTPUT
    # =========================================================

    @abstractmethod
    def output(
        self,
        state: tuple[float, ...] | list[float],
        **inputs: Any,
    ) -> Any:
        """
        Calculate the plugin's externally relevant output.
        """

        raise NotImplementedError

    # =========================================================
    # COMBINED EVALUATION
    # =========================================================

    def evaluate(
        self,
        state: tuple[float, ...] | list[float],
        **inputs: Any,
    ) -> dict[str, Any]:
        """
        Evaluate derivatives and output together.

        Subclasses may override this method when the underlying
        model provides a more efficient combined evaluation.
        """

        derivatives = self.derivatives(
            state,
            **inputs,
        )

        output = self.output(
            state,
            **inputs,
        )

        return {
            "derivatives": derivatives,
            "output": output,
        }

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
        **inputs: Any,
    ) -> tuple[float, ...]:
        """
        Return the initial state used to reset the component.
        """

        return self.initial_state(
            **inputs,
        )

    # =========================================================
    # VALIDATION
    # =========================================================

    def validate_state(
        self,
        state: tuple[float, ...] | list[float],
    ) -> None:
        """
        Validate the size of a local dynamic state vector.
        """

        if len(state) != self.state_size:
            raise ValueError(
                f"{self.__class__.__name__} requires "
                f"{self.state_size} states, "
                f"received {len(state)}."
            )

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    @abstractmethod
    def summary(self) -> dict[str, Any]:
        """
        Return plugin configuration and diagnostic information.
        """

        raise NotImplementedError
