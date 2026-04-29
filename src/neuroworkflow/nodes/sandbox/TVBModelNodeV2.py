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

from tvb.simulator.lab import models


class TVBModelNodeV2(Node):
    NODE_DEFINITION = NodeDefinitionSchema(
        type="tvb_neural_mass_model",
        stage="neuron",
        tool="TVB",
        model_source="https://github.com/the-virtual-brain/tvb-root",
        description=(
            "Instantiates a configurable TVB neural mass model "
            "(Generic2dOscillator, EpileptorRestingState, or other) with "
            "scalar model parameters and optional per-region overrides, "
            "producing the local node dynamics object for any TVB brain network simulation."
        ),
        parameters={
            "model_type": ParameterDefinition(
                default_value="Generic2dOscillator",
                description=(
                    "TVB model class name: 'Generic2dOscillator' (2D oscillatory dynamics, "
                    "resting-state or limit-cycle), 'EpileptorRestingState' (seizure/resting "
                    "hybrid, Jirsa et al. 2014), 'Epileptor', 'WilsonCowan', 'ReducedWongWang'."
                ),
                constraints={
                    "allowed_values": [
                        "Generic2dOscillator",
                        "EpileptorRestingState",
                        "Epileptor",
                        "WilsonCowan",
                        "ReducedWongWang",
                    ]
                },
            ),
            "model_params": ParameterDefinition(
                default_value={"a": 1.74},
                description=(
                    "Dict of scalar model parameters passed to the TVB model constructor as "
                    "numpy arrays. Generic2dOscillator example: {'a': 1.74} (limit-cycle regime). "
                    "EpileptorRestingState example: {'Ks': -1.0, 'K_rs': 1.0, 'tau': 1000, 'r': 0.000015}."
                ),
            ),
            "region_params": ParameterDefinition(
                default_value={},
                description=(
                    "Dict of per-region parameter overrides applied after construction, used for "
                    "epilepsy heatmaps (EZ/PZ zones). Format: "
                    "{'param': {'all': default_val, 'regions': [idx,...], 'values': [val,...]}}. "
                    "Example for EpileptorRestingState x0 epileptogenicity: "
                    "{'x0': {'all': -2.3, 'regions': [40,47,62], 'values': [-1.4,-1.6,-1.6]}}. "
                    "Empty dict skips region-specific setup (use for Generic2dOscillator)."
                ),
            ),
        },
        inputs={
            "tvb_connectivity": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Configured TVB Connectivity object; used to determine number of brain regions "
                    "when applying region_params overrides. Required only when region_params is non-empty."
                ),
                optional=True,
            ),
        },
        outputs={
            "tvb_model": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Configured TVB neural mass model object representing local node dynamics "
                    "for all brain regions, ready to be passed to a TVB Simulator."
                ),
            ),
        },
        methods={
            "build_model": MethodDefinition(
                description=(
                    "Instantiate the selected TVB model class with scalar parameters from "
                    "model_params, then apply per-region overrides from region_params using "
                    "connectivity region count."
                ),
                inputs=["tvb_connectivity"],
                outputs=["tvb_model"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("build_model", self.build_model, method_key="build_model")

    def build_model(self, tvb_connectivity=None) -> Dict[str, Any]:
        model_type = self._parameters["model_type"]
        model_params = self._parameters["model_params"]
        region_params = self._parameters["region_params"]

        model_class = self._resolve_model_class(model_type)
        scalar_kwargs = {k: np.array([v]) for k, v in model_params.items()}
        mod = model_class(**scalar_kwargs)

        if region_params:
            if tvb_connectivity is None:
                raise ValueError(
                    "tvb_connectivity input is required when region_params is non-empty."
                )
            nregions = len(tvb_connectivity.region_labels)
            for param_name, config in region_params.items():
                arr = np.ones(nregions) * config["all"]
                for idx, val in zip(config.get("regions", []), config.get("values", [])):
                    arr[idx] = val
                setattr(mod, param_name, arr)

        return {"tvb_model": mod}

    @staticmethod
    def _resolve_model_class(model_type: str):
        cls = getattr(models, model_type, None)
        if cls is not None:
            return cls
        if model_type == "EpileptorRestingState":
            from tvb.simulator.models.epileptor_rs import EpileptorRestingState
            return EpileptorRestingState
        raise ValueError(
            f"Unknown TVB model type: '{model_type}'. "
            "Supported: Generic2dOscillator, EpileptorRestingState, Epileptor, WilsonCowan, ReducedWongWang."
        )
