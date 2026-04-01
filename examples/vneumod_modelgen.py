#!/usr/bin/env python3
"""
Virtual Neuromodulation (Group Surrogate model) model generation example using the NeuroWorkflow library.

This example demonstrates how to generate whole-brain data-driven model (Group Surrogate model)
using the NeuroWorkflow library.
"""

import sys
import os

# Add the src directory to the Python path to import the library
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from neuroworkflow import WorkflowBuilder
from neuroworkflow.nodes.io.VNMBulkLoadNifti2CxNode import VNMBulkLoadNifti2CxNode
from neuroworkflow.nodes.io.VNMLoadSubjectTimeSeriesNode import VNMLoadSubjectTimeSeriesNode
from neuroworkflow.nodes.network.VNMGenerateGroupSurrogateModelNode import VNMGenerateGroupSurrogateModelNode


def main():
    """Run a virtual neuromodulation workflow."""
    # Create nodes
    load_nifti = VNMBulkLoadNifti2CxNode("VNMLoadNifti2Cx")
    load_nifti.configure(
        nifti_files="../data/vnm_data/subjects/wau*.nii.gz",
        atlas_file="../data/vnm_data/atlas/allenCube10atlas.nii.gz",
        csf_file="../data/vnm_data/atlas/csf.nii.gz",
        white_file = "../data/vnm_data/atlas/white.nii.gz",
        glsig_file = "../data/vnm_data/atlas/itksnap_annotation_full2mmMask.nii.gz",
        cx_file = "ppmi2CXAllenCube10s34gmacomp.mat"  # for DEBUG
    )

    load_subject = VNMLoadSubjectTimeSeriesNode("VNMLoadSubject")
    load_subject.configure(
        cx_file="../data/vnm_data/subjects/ppmi81CXAllenCube2s34gmacomp.mat",
        atlas_file="../data/vnm_data/atlas/allenCube2atlas.nii.gz",
    )

    gen_model = VNMGenerateGroupSurrogateModelNode("VNMGenerateModel")
    gen_model.configure(
        model_file = "ppmi2CXAllenCube10s34gmacomp_gsm_var.mat"  # for DEBUG
    )

    # Create workflow
    workflow = (
        WorkflowBuilder("vnm_model_generation")
            .add_node(load_nifti)
#            .add_node(load_subject)  # this is also possible instead of load_nifti
            .add_node(gen_model)
            .connect("VNMLoadNifti2Cx", "CX", "VNMGenerateModel", "CX")
#            .connect("VNMLoadSubject", "CX", "VNMGenerateModel", "CX")  # this is also possible instead of load_nifti
            .build()
    )
    '''
    .build()
    '''

    # Print workflow information
    print(workflow)
    
    # Execute workflow
    print("\nExecuting workflow...")
    success = workflow.execute()
    
    if success:
        print("Workflow execution completed successfully!")
    else:
        print("Workflow execution failed!")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())