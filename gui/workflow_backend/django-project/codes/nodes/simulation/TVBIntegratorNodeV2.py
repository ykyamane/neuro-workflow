from typing import Dict, Any

import numpy as np

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType

from tvb.simulator.lab import integrators, noise


class TVBIntegratorNodeV2(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type="tvb_integrator",
        stage="simulation",
        tool="TVB",
        model_source="https://github.com/the-virtual-brain/tvb-root",
        description=(
            "Configures a TVB numerical integration scheme (HeunDeterministic or HeunStochastic) "
            "with a user-specified noise profile per state variable, compatible with any TVB neural "
            "mass model by providing the correct nsig vector length."
        ),
        parameters={
            "integrator_type": ParameterDefinition(
                default_value="HeunStochastic",
                description=(
                    "Numerical integration scheme: 'HeunDeterministic' (no noise, for reproducible "
                    "trajectories) or 'HeunStochastic' (additive Gaussian noise, for noisy dynamics). "
                    "Heun is a second-order Runge-Kutta method suitable for most TVB simulations."
                ),
                constraints={"allowed_values": ["HeunDeterministic", "HeunStochastic"]},
            ),
            "dt": ParameterDefinition(
                default_value=0.1,
                description=(
                    "Integration time step in milliseconds. Must be small enough for numerical "
                    "stability; typically 0.1 ms for Generic2dOscillator and EpileptorRestingState."
                ),
                constraints={"min": 0.001, "max": 10.0},
                optimizable=False,
            ),
            "nsig": ParameterDefinition(
                default_value=[0.001, 0.0],
                description=(
                    "List of additive noise standard deviations, one per model state variable. "
                    "Length must match the number of state variables in the chosen model. "
                    "Generic2dOscillator (2 variables V, W): e.g. [0.001, 0.0]. "
                    "EpileptorRestingState (8 variables): e.g. [0., 0., 0., 0.00025, 0.00025, 0., 0.001, 0.]. "
                    "Ignored when integrator_type is HeunDeterministic."
                ),
            ),
        },
        inputs={},
        outputs={
            "tvb_integrator": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Configured TVB integrator object (HeunDeterministic or HeunStochastic) "
                    "with noise profile, ready to be passed to the TVB Simulator."
                ),
            ),
        },
        methods={
            "build_integrator": MethodDefinition(
                description=(
                    "Instantiate the selected Heun integrator with dt and additive Gaussian noise "
                    "defined by the nsig vector."
                ),
                inputs=[],
                outputs=["tvb_integrator"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step(
            "build_integrator", self.build_integrator, method_key="build_integrator"
        )

    def build_integrator(self) -> Dict[str, Any]:
        integrator_type = self._parameters["integrator_type"]
        dt = self._parameters["dt"]
        nsig = np.array(self._parameters["nsig"])

        if integrator_type == "HeunStochastic":
            hiss = noise.Additive(nsig=nsig)
            heunint = integrators.HeunStochastic(dt=dt, noise=hiss)
        elif integrator_type == "HeunDeterministic":
            heunint = integrators.HeunDeterministic(dt=dt)
        else:
            raise ValueError(f"Unknown integrator_type: '{integrator_type}'")

        return {"tvb_integrator": heunint}
