#!/usr/bin/env python3
"""
Simple simulation example using the NeuroWorkflow library.

This example demonstrates how to create a basic workflow for Virtual Neuromodulation (Group Surrogate model)
using the NeuroWorkflow library.
"""

import sys
import os

# Add the src directory to the Python path to import the library
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from neuroworkflow import WorkflowBuilder
from neuroworkflow.nodes.io.VNMLoadSubjectTimeSeriesNode import VNMLoadSubjectTimeSeriesNode
from neuroworkflow.nodes.io.VNMLoadGroupSurrogateModelNode import VNMLoadGroupSurrogateModelNode
from neuroworkflow.nodes.simulation.VNMSimulatorNode import VNMSimulatorNode
from neuroworkflow.nodes.analysis.VNMGlmAnalysisNode import VNMGlmAnalysisNode


def main():
    """Run a virtual neuromodulation workflow."""
    # Create nodes
    load_subject = VNMLoadSubjectTimeSeriesNode("VNMLoadSubject")
    load_subject.configure(
        cx_file="../data/vnm_data/subjects/ppmi81CXAllenCube2s34gmacomp.mat",
        atlas_file="../data/vnm_data/atlas/allenCube2atlas.nii.gz",
    )

    load_model = VNMLoadGroupSurrogateModelNode("VNMLoadModel")
    load_model.configure(
        model_file="../data/vnm_data/model/ppmi81CXAllenCube2s34gmacomp_gsm_var.mat",
    )

    simulate_vnm = VNMSimulatorNode("VNMSimulation")
    simulate_vnm.configure(
        target_ROI_file="../data/vnm_data/target_roi/allenCube2atlasStn3.nii.gz",
        target_ROI="4525",
        simulation_name="ppmi81CXAllenCube2s34gmacomp",
        subject_perm_path="../data/vnm_data/perm",
        number_of_trials="1"
    )

    analysis_vnm = VNMGlmAnalysisNode("VNMGlmAnalysis")
    analysis_vnm.configure(
        atlas_file="../data/vnm_data/atlas/allenCube2atlas.nii.gz",
    )

    # Create workflow
    workflow = (
        WorkflowBuilder("vnm_simulation_analysis")
            .add_node(load_subject)
            .add_node(load_model)
            .add_node(simulate_vnm)
            .add_node(analysis_vnm)
            .connect("VNMLoadSubject", "CX", "VNMSimulation", "CX")
            .connect("VNMLoadSubject", "atlasV", "VNMSimulation", "atlasV")
            .connect("VNMLoadModel", "model", "VNMSimulation", "model")
            .connect("VNMSimulation", "simulation_name", "VNMGlmAnalysis", "simulation_name")
            .connect("VNMSimulation", "trials", "VNMGlmAnalysis", "trials")
            .connect("VNMSimulation", "Chrf", "VNMGlmAnalysis", "Chrf")
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