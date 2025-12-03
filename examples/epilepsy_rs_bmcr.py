'''
Complete BMCR to Epilepsy workflow using NeuroWorkflow nodes

This workflow demonstrates the complete pipeline from BMCR data download
to epilepsy simulation using the new BMCRDownloadNode and BMCRToTVBNode.

Pipeline:
1. BMCRDownloadNode - Downloads tractography data from AWS and generates connectome
2. BMCRToTVBNode - Converts connectome to TVB format and creates ZIP file
3. TVBConnectivitySetUpNode - Loads the TVB connectome
4. TVBEpileptorNode - Sets up epilepsy model
5. TVBIntegratorNode - Sets up integration scheme
6. TVBMonitorNode - Sets up monitoring
7. TVBSimulatorNode - Runs the simulation
8. TVBVisualizationNode - Visualizes results

Based on: epilepsy_rs_modified.py
'''
import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Add the src directory to the Python path if needed
src_path = os.path.abspath(os.path.join(os.getcwd(), '../src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import NeuroWorkflow components
from neuroworkflow import WorkflowBuilder
from neuroworkflow.nodes.io.BMCR_DTI_to_Connectome import BMCR_DTI_to_Connectome
from neuroworkflow.nodes.io.BMCR_Conn_To_TVB import BMCR_Conn_To_TVB
from neuroworkflow.nodes.network.TVBConnectivitySetUpNode import TVBConnectivitySetUpNode
from neuroworkflow.nodes.network.TVBEpileptorNode import TVBEpileptorNode
from neuroworkflow.nodes.network.TVBIntegratorNode import TVBIntegratorNode
from neuroworkflow.nodes.analysis.TVBVisualizationNode import TVBVisualizationNode
from neuroworkflow.nodes.stimulus.TVBMonitorNode import TVBMonitorNode
from neuroworkflow.nodes.simulation.TVBSimulatorNode import TVBSimulatorNode


# 1. BMCR Download Node - Downloads tractography data and generates connectome
bmcr_download = BMCR_DTI_to_Connectome("BMCRDownload")
# Configure the node - essential parameters
bmcr_download.configure(
    subject='A10-R01_0028-TT21',
    atlas_file='../data/bmcr_data/atlas_segmentation_BM1.nii.gz',
    output_directory='./'#'./bmcr_workflow_data'
)

# 2. BMCR to TVB Conversion Node - Converts connectome to TVB format
bmcr_to_tvb = BMCR_Conn_To_TVB("BMCRToTVB")
# Configure the node
bmcr_to_tvb.configure(
    output_directory='./',#'./bmcr_workflow_data',
    region_prefix='',
    hemisphere_info=True,
    brain_center=[0.0, 0.0, 0.0],
    brain_size=[50.0, 40.0, 30.0],
    tract_length_factor=1.0
)

# 3. Upload and setup connectivity in TVB
load_sc = TVBConnectivitySetUpNode("TVBConnectivity")
# Configure the node (connectivity_file will be overridden by input port)
load_sc.configure(
    #connectivity_file='placeholder.zip'  # This will be replaced by the port connection
)

# 4. Epilepsy model setup
model = TVBEpileptorNode("TVBEpileptor")
# Configure the node
model.configure(
)

# 5. Integration scheme setup
integrator = TVBIntegratorNode("TVBIntegrator")
# Configure the node
integrator.configure(
)

# 6. Monitor setup
monitor = TVBMonitorNode("TVBMonitor")
# Configure the node
monitor.configure(
)

# 7. Simulation setup
simulation = TVBSimulatorNode("TVBSimulator")
# Configure the node
simulation.configure(
    simulation_length='5000'
)

# 8. Visualization setup
plots = TVBVisualizationNode("TVBVisualization")
# Configure the node
plots.configure(
)

# Create a workflow builder
workflow_builder = WorkflowBuilder("BMCR to Epilepsy Pipeline")

# Add nodes to the workflow
workflow_builder.add_node(bmcr_download)
workflow_builder.add_node(bmcr_to_tvb)
workflow_builder.add_node(load_sc)
workflow_builder.add_node(model)
workflow_builder.add_node(integrator)
workflow_builder.add_node(monitor)
workflow_builder.add_node(simulation)
workflow_builder.add_node(plots)

# Connect the BMCR nodes
workflow_builder.connect(
    "BMCRDownload", "connectome_file",
    "BMCRToTVB", "connectome_file"
)
workflow_builder.connect(
    "BMCRDownload", "subject_id",
    "BMCRToTVB", "subject_id"
)
workflow_builder.connect(
    "BMCRDownload", "processing_metadata",
    "BMCRToTVB", "processing_metadata"
)

# Connect BMCRToTVB to TVB pipeline
workflow_builder.connect(
    "BMCRToTVB", "tvb_zip_file",
    "TVBConnectivity", "connectivity_file_path"
)

# Connect the TVB nodes (same as original epilepsy_rs_modified.py)
workflow_builder.connect(
    "TVBConnectivity", "tvb_connectivity", 
    "TVBEpileptor", "tvb_connectivity"
)
workflow_builder.connect(
    "TVBConnectivity", "tvb_connectivity", 
    "TVBSimulator", "tvb_connectivity"
)
workflow_builder.connect(
    "TVBEpileptor", "tvb_model", 
    "TVBSimulator", "tvb_model"
)
workflow_builder.connect(
    "TVBEpileptor", "tvb_coupling", 
    "TVBSimulator", "tvb_coupling"
)
workflow_builder.connect(
    "TVBIntegrator", "tvb_integrator", 
    "TVBSimulator", "tvb_integrator"
)
workflow_builder.connect(
    "TVBMonitor", "tvb_monitor", 
    "TVBSimulator", "tvb_monitor"
)
workflow_builder.connect( 
    "TVBSimulator", "tvb_simdata",
    "TVBVisualization", "data_series",
)
workflow_builder.connect( 
    "TVBSimulator", "tvb_simtime",
    "TVBVisualization", "time_series",
)
workflow_builder.connect( 
    "TVBEpileptor", "tvb_model",
    "TVBVisualization", "tvb_model",
)
workflow_builder.connect( 
    "TVBConnectivity", "tvb_connectivity", 
    "TVBVisualization", "tvb_connectivity",
)

# Build the workflow
workflow = workflow_builder.build()

# Print workflow information
print(workflow)

# Execute the workflow
print("Executing workflow...")
success = workflow.execute()

if success:
    print("\nWorkflow execution completed successfully!")
    print("BMCR connectome has been downloaded, converted to TVB format, and used in epilepsy simulation!")
else:
    print("\nWorkflow execution failed!")