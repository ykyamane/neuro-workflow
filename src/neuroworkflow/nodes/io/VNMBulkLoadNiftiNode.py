"""
Virtual Neuromodulation (Group Surrogate model) nifti load nodes.

This module provides nodes for loading data of Virtual Neuromodulation.
"""

import os
import nibabel as nib
import glob
import vneumodpy as vnm

from typing import Dict, Any, List, Tuple
from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition
from neuroworkflow.core.port import PortType


class VNMBulkLoadNiftiNode(Node):
    """Virtual Neuromodulation (Group Surrogate model) Data loader node."""
    
    NODE_DEFINITION = NodeDefinitionSchema(
        type='nifti_bulk_loader',
        description='Loads Nifti files',
        parameters={
            'nifti_files': ParameterDefinition(
                default_value='',
                description='Nifti file path string (i.e. <path>/*.nii.gz)'
            ),
        },
        outputs={
            'volumes': PortDefinition(
                type=PortType.OBJECT,
                description='list of nifti volumes'
            )
        },
        methods={
            'initialize_nifti': MethodDefinition(
                description='Loading nifti files',
                inputs=[],
                outputs=['Vs']
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
            "initialize_nifti",
            self.initialize_nifti,
            method_key="initialize_nifti"
        )

    def initialize_nifti(self) -> Dict[str, Any]:
        """Loading nifti files."""
        nifti_files = self._parameters["nifti_files"]
        print(f"Loading nifti files: {nifti_files}")

        Vs = []
        niflist = glob.glob(nifti_files)
        for i in range(len(niflist)):
            dat = nib.load(niflist[i])
            V = dat.get_fdata()
            V = vnm.adjust_volume_dir(V, dat)
            Vs.append(V)

        return {"Vs": Vs}
