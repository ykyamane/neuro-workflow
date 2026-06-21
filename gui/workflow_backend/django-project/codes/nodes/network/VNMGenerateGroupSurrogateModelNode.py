"""
Virtual Neuromodulation (Group Surrogate model) model generation nodes.

This module provides nodes for generating whole brain model of Virtual Neuromodulation.
"""

import os
import json
import numpy as np
import h5py
import hdf5storage
import vneumodpy as vnm

from typing import Dict, Any, List, Tuple
from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition
from neuroworkflow.core.port import PortType


class VNMGenerateGroupSurrogateModelNode(Node):
    """Virtual Neuromodulation (Group Surrogate model) model generator node."""

    NODE_DEFINITION = NodeDefinitionSchema(
        type='model_generator',
        description='Generates whole brain model of Virtual Neuromodulation',
        parameters={
            'var_lag': ParameterDefinition(
                default_value=1,
                description='Vector Auto-Regression model order (lag).',
                constraints = {'min': 1}
            ),
            'use_cache': ParameterDefinition(
                default_value=False,
                description='Save cache file for model generation.'
            ),
            'number_of_threads': ParameterDefinition(
                default_value=1,
                description=(
                    'Number of threads for the Group Surrogate Model computation (int). '
                    'Default is 1 (single-threaded, safe for Jupyter/Docker). '
                    'Set to a higher value only when running outside a Jupyter kernel. '
                ),
                constraints={'min': 1}
            ),
            'model_file': ParameterDefinition(
                default_value='',
                description='(option) save file name of Group Surrogate model file (.mat)'
            ),
        },
        inputs={
            'CX': PortDefinition(
                type=PortType.LIST,
                description='Subject multivariate time-series data'
            ),
        },
        outputs={
            'model': PortDefinition(
                type=PortType.OBJECT,
                description='Group Surrogate model'
            )
        },
        methods={
            'initialize_model': MethodDefinition(
                description='Initialize Group Surrogate model',
                inputs=['CX'],
                outputs=['model']
            )
        }
    )

    def __init__(self, name: str):
        """Initialize Virtual Neuromodulation (Group Surrogate model).

        Args:
            name: Name of the node
        """
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        """Define process steps for this node."""
        # With the new schema, we can use method_key to link directly to NODE_DEFINITION methods
        self.add_process_step(
            "initialize_model",
            self.initialize_model,
            method_key="initialize_model"
        )

    def initialize_model(self, CX: Dict[str, Any]) -> Dict[str, Any]:
        """Generating Group Surrogate model."""
        if CX is None:
            raise ValueError("subject time-series not set")

        number_of_threads = self._parameters["number_of_threads"]
        use_cache = self._parameters["use_cache"]
        var_lag = self._parameters["var_lag"]
        model_file = self._parameters["model_file"]  # (option) output model file (.mat)

        model = vnm.MultivariateVARNetwork()
        model.init_with_cell(CX, lags=var_lag, usecache=use_cache, n_jobs=number_of_threads)

        if len(model_file) > 0:
            gr = vnm.group_range.get(CX)
            model.save_mat(model_file, gRange=gr)

        return {"model": model}

