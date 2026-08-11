```python
"""
GridForge Governor Dynamic Plugin
=================================

File:
    plugins/dynamics/governor/plugin.py

Purpose
-------
Provides the plugin adapter for the GridForge Governor model.

The underlying physical model remains in:

    core.model.governor.Governor

This plugin does NOT replace or modify that model.

Architecture
------------
The plugin layer adapts the frozen model layer to the future
GridForge dynamic / DAE simulation framework.

The plugin does NOT:

    - own authoritative simulation state
    - perform numerical integration
    - perform time stepping
    - modify the network
    - solve algebraic equations

The dynamic solver owns:

    - global dynamic state vector
    - state indexing
    - numerical integration
    - time stepping
    - simulation events

The plugin provides:

    - state definition
    - derivative evaluation
    - output evaluation
    - initial-state generation
    - validation
    - diagnostics
    - access to the underlying Governor model

Dynamic State
-------------
The Governor exposes one dynamic state:

    Pm

Input
-----
    omega
        Rotor speed deviation in per-unit.

Output
------
    Pm_output
        Limited mechanical power supplied to the
        synchronous-machine model.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

from core.model.governor import Governor


class GovernorPlugin:
    """
    GridForge Governor dynamic plugin.

    This class is an adapter around the frozen
    :class:`core.model.governor.Governor` model.

    No authoritative dynamic state is stored inside this class.
    """

    # =========================================================
    # PLUGIN METADATA
    # =========================================================

    plugin_id = "gridforge.dynamics.governor"

    plugin_type = "dynamic_component"

    model_type = "GOVERNOR"

    version = "1.0.0"

    # ---------------------------------------------------------
    # Dynamic interface definition
    # ---------------------------------------------------------

    state_names = (
        "Pm",
    )

    input_names = (
        "omega",
    )

    output_names = (
        "Pm_output",
    )

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        model: Governor | None = None,
        **parameters: Any,
    ) -> None:
        """
        Initialize the Governor plugin.

        Parameters
        ----------
        model:
            Optional existing frozen Governor model.

        parameters:
            Parameters passed to Governor when an existing model
            is not supplied.

        Notes
        -----
        Either ``model`` or constructor parameters may be used.

        Examples
        --------
        Default model:

            plugin = GovernorPlugin()

        Parameterized model:

            plugin = GovernorPlugin(
                Pref=0.8,
                R=0.05,
                Tg=0.2,
                Pm_min=0.0,
                Pm_max=1.2,
            )

        Existing model:

            governor = Governor(Pref=1.0)
            plugin = GovernorPlugin(model=governor)
        """

        if model is not None and parameters:
            raise ValueError(
                "Provide either an existing Governor model "
                "or constructor parameters, not both."
            )

        if model is not None:

            if not isinstance(model, Governor):
                raise TypeError(
                    "model must be an instance of Governor."
                )

            self.model = model

        else:
            self.model = Governor(
                **parameters,
            )

    # =========================================================
    # METADATA
    # =========================================================

    @property
    def id(self) -> str:
        """
        Return the unique plugin identifier.
        """

        return self.plugin_id

    @property
    def name(self) -> str:
        """
        Return the human-readable plugin name.
        """

        return "Governor"

    # =========================================================
    # STATE DEFINITION
    # =========================================================

    def state_definition(
        self,
    ) -> tuple[dict[str, Any], ...]:
        """
        Describe the dynamic states exposed by this plugin.

        Returns
        -------
        tuple[dict[str, Any], ...]
            Dynamic-state metadata.
        """

        return (
            {
                "name": "Pm",
                "units": "pu",
                "description": (
                    "Governor mechanical-power state."
                ),
            },
        )

    # =========================================================
    # INPUT DEFINITION
    # =========================================================

    def input_definition(
        self,
    ) -> tuple[dict[str, Any], ...]:
        """
        Describe the inputs required by the plugin.

        Returns
        -------
        tuple[dict[str, Any], ...]
            Input metadata.
        """

        return (
            {
                "name": "omega",
                "units": "pu",
                "description": (
                    "Rotor speed deviation."
                ),
            },
        )

    # =========================================================
    # OUTPUT DEFINITION
    # =========================================================

    def output_definition(
        self,
    ) -> tuple[dict[str, Any], ...]:
        """
        Describe the outputs produced by the plugin.

        Returns
        -------
        tuple[dict[str, Any], ...]
            Output metadata.
        """

        return (
            {
                "name": "Pm_output",
                "units": "pu",
                "description": (
                    "Limited mechanical power output."
                ),
            },
        )

    # =========================================================
    # DERIVATIVE
    # =========================================================

    def derivative(
        self,
        state: dict[str, float],
        inputs: dict[str, float],
    ) -> dict[str, float]:
        """
        Evaluate the Governor dynamic derivative.

        Parameters
        ----------
        state:
            Dynamic state supplied by the dynamic solver.

            Required key:

                Pm

        inputs:
            External inputs supplied by the dynamic solver.

            Required key:

                omega

        Returns
        -------
        dict[str, float]
            State derivatives.

        Example
        -------
        {
            "Pm": 0.125
        }

        Notes
        -----
        The plugin does not modify ``state``.
        """

        Pm = float(
            state["Pm"]
        )

        omega = float(
            inputs["omega"]
        )

        dPm_dt = self.model.derivative(
            Pm=Pm,
            omega=omega,
        )

        return {
            "Pm": dPm_dt,
        }

    # =========================================================
    # OUTPUT
    # =========================================================

    def output(
        self,
        state: dict[str, float],
        inputs: dict[str, float],
    ) -> dict[str, float]:
        """
        Evaluate the Governor output.

        Parameters
        ----------
        state:
            Dynamic state supplied by the solver.

        inputs:
            External inputs.

        Returns
        -------
        dict[str, float]
            Limited mechanical-power output.
        """

        Pm = float(
            state["Pm"]
        )

        Pm_output = self.model.output(
            Pm=Pm,
        )

        return {
            "Pm_output": Pm_output,
        }

    # =========================================================
    # COMPLETE EVALUATION
    # =========================================================

    def evaluate(
        self,
        state: dict[str, float],
        inputs: dict[str, float],
    ) -> dict[str, Any]:
        """
        Evaluate derivatives and outputs together.

        Parameters
        ----------
        state:
            Current dynamic state.

        inputs:
            Current dynamic inputs.

        Returns
        -------
        dict
            {
                "derivatives": {
                    "Pm": ...
                },
                "outputs": {
                    "Pm_output": ...
                }
            }

        Notes
        -----
        No integration is performed.
        """

        derivatives = self.derivative(
            state=state,
            inputs=inputs,
        )

        outputs = self.output(
            state=state,
            inputs=inputs,
        )

        return {
            "derivatives": derivatives,
            "outputs": outputs,
        }

    # =========================================================
    # INITIAL STATE
    # =========================================================

    def initial_state(
        self,
        inputs: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """
        Generate the initial Governor dynamic state.

        Parameters
        ----------
        inputs:
            Optional initial input dictionary.

            Supported key:

                omega

        Returns
        -------
        dict[str, float]
            Initial dynamic state.

        Notes
        -----
        The underlying Governor model calculates the steady-state
        mechanical power.

        No state is stored by the plugin.
        """

        if inputs is None:
            inputs = {}

        omega = float(
            inputs.get(
                "omega",
                0.0,
            )
        )

        Pm = self.model.initial_state(
            omega=omega,
        )

        return {
            "Pm": Pm,
        }

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
        inputs: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """
        Generate a fresh initial state.

        This method does not reset internal simulation state
        because the plugin owns no authoritative dynamic state.
        """

        return self.initial_state(
            inputs=inputs,
        )

    # =========================================================
    # PARAMETER ACCESS
    # =========================================================

    def parameters(self) -> dict[str, Any]:
        """
        Return the underlying Governor configuration.
        """

        return dict(
            self.model.summary()
        )

    # =========================================================
    # MODEL ACCESS
    # =========================================================

    @property
    def model_instance(self) -> Governor:
        """
        Return the underlying frozen Governor model.

        This provides controlled access for higher-level GridForge
        infrastructure without duplicating model parameters.
        """

        return self.model

    # =========================================================
    # VALIDATION
    # =========================================================

    def validate(self) -> None:
        """
        Validate the underlying Governor model.

        Raises
        ------
        ValueError
            If the Governor configuration is invalid.
        """

        self.model._validate()

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def diagnostics(self) -> dict[str, Any]:
        """
        Return plugin diagnostics and interface information.
        """

        return {
            "plugin_id": self.plugin_id,
            "plugin_type": self.plugin_type,
            "model_type": self.model_type,
            "version": self.version,
            "state_names": self.state_names,
            "input_names": self.input_names,
            "output_names": self.output_names,
            "state_definition": self.state_definition(),
            "input_definition": self.input_definition(),
            "output_definition": self.output_definition(),
            "parameters": self.parameters(),
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<GovernorPlugin "
            f"id={self.plugin_id!r}, "
            f"version={self.version!r}, "
            f"model={self.model!r}>"
        )
```
