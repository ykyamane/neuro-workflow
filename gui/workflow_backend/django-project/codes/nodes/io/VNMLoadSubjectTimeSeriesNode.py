"""
Virtual Neuromodulation (Group Surrogate model) building nodes.

This module provides nodes for loading data of Virtual Neuromodulation.
"""

import os
import json
import numpy as np
import h5py
import hdf5storage
import nibabel as nib
import vneumodpy as vnm

from typing import Dict, Any, List, Tuple
from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition
from neuroworkflow.core.port import PortType


class VNMLoadSubjectTimeSeriesNode(Node):
    """Virtual Neuromodulation (Group Surrogate model) Data loader node."""
    
    NODE_DEFINITION = NodeDefinitionSchema(
        type='subject_data_loader',
        description='Loads Virtual Neuromodulation (Group Surrogate model) subject data',
        parameters={
            'cx_file': ParameterDefinition(
                default_value='',
                description='Subject multivariate time-series data file (.mat)'
            ),
            'atlas_file': ParameterDefinition(
                default_value='',
                description='Cube ROI atlas file (.nii.gz)'
            ),
        },
        outputs={
            'CX': PortDefinition(
                type=PortType.LIST,
                description='Subject multivariate time-series data'
            ),
            'atlasV': PortDefinition(
                type=PortType.OBJECT,
                description='Cube ROI atlas'
            )
        },
        methods={
            'initialize_cx': MethodDefinition(
                description='Initialize Subject multivariate time-series data',
                inputs=[],
                outputs=['CX']
            ),
            'initialize_atlas': MethodDefinition(
                description='Initialize Cube ROI atlas',
                inputs=[],
                outputs=['atlasV']
            ),
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
            "initialize_cx",
            self.initialize_cx,
            method_key="initialize_cx"
        )

        self.add_process_step(
            "initialize_atlas",
            self.initialize_atlas,
            method_key="initialize_atlas"
        )

    def initialize_cx(self) -> Dict[str, Any]:
        """Initialize Subject multivariate time-series data."""
        cx_file = self._parameters["cx_file"]
        print(f"Loading Subject multivariate time-series : {cx_file}")

        dic = h5py.File(cx_file, 'r')
        if dic.get('CX') is None:
            raise FileNotFoundError(f"no cells of subject time-series (CX) file. please specify .mat file.: {cx_file}")

        CX = []
        cx = dic['CX']
        for j in range(len(cx)):
            hdf5ref = cx[j, 0]
            x = dic[hdf5ref]
            CX.append(np.array(x).T)
        dic.close()

        return {"CX": CX}

    def initialize_atlas(self) -> Dict[str, Any]:
        """Initialize Cube ROI atlas."""
        atlas_file = self._parameters["atlas_file"]
        print(f"Loading Cube ROI atlas : {atlas_file}")

        atlasDat = nib.load(atlas_file)
        atlasV = atlasDat.get_fdata()
        atlasV = vnm.adjust_volume_dir(atlasV, atlasDat)

        return {"atlasV": atlasV}
