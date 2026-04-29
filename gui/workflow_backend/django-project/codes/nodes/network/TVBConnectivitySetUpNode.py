"""
Node for loading and visualizing the structural connectivity matrix that represents 
the set of all existing anatomical connections between brain areas in the virtual brain (TVB)
"""

from typing import Dict, Any, Optional
import os
import numpy as np

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition
from neuroworkflow.core.port import PortType

#%matplotlib inline
# Import a bunch of stuff for TVB
from tvb.simulator.lab import *
from tvb.simulator.models.epileptor_rs import EpileptorRestingState
from tvb.datatypes.time_series import TimeSeriesRegion
import time as tm
import matplotlib.pyplot as plt 
import sys


class TVBConnectivitySetUpNode(Node):
    """Node for loading and visualizing the structural connectivity matrix that represents the set of all existing anatomical connections between brain areas"""
    
    NODE_DEFINITION = NodeDefinitionSchema(
        type='network_builder',
        description='Initialise the Connectivity. TVB structural connectome is read from a zip file.',
        
        parameters={
            'connectivity_file': ParameterDefinition(
                default_value='neuroworkflow/data/tvb_data/connectivity_marmoset.zip',
                description='structural connectivity matrix, from MRI',
                constraints={},
                optimizable=False,
                optimization_range=[]
            ),
        },
        
        inputs={
            'connectivity_file_path': PortDefinition(
                type=PortType.STR,
                description='Path to TVB connectivity ZIP file (overrides connectivity_file parameter)',
                optional=True
            ),
        },
        
        outputs={
            'tvb_connectivity': PortDefinition(
                type=PortType.OBJECT,
                description='Configured connectivity matrix object in TVB'
            ),
        },
        methods={
            'sc_initialization': MethodDefinition(
                description='Initialize the connectivity',
                inputs=['connectivity_file_path'],
                outputs=['tvb_connectivity']
            ),
            'sc_visualization': MethodDefinition(
                description='Visualization of connectivity matrix',
                inputs=['tvb_connectivity'],
                outputs=['visualization completed']
            )
        }
    )
    def __init__(self, name: str):
        """Initialize the TVBConnectivitySetUpNode.
        
        Args:
            name: Name of the node
        """
        super().__init__(name)
        self._define_process_steps()
    
    def _define_process_steps(self) -> None:
        """Define the process steps for this node."""
        self.add_process_step(
            "sc_initialization",
            self.sc_initialization,
            method_key="sc_initialization"
        )
        self.add_process_step(
            "sc_visualization",
            self.sc_visualization,
            method_key="sc_visualization"
        )
        
    def sc_initialization(self, connectivity_file_path: str = None) -> Dict[str, Any]:
        """read a zip file and setup connectivity matrix as TVB object
        
        Args:
            connectivity_file_path: Optional path to connectivity file from input port
            
        Returns:
            connectivity matrix object in TVB format
        """
        # Use input port path if provided, otherwise use parameter
        if connectivity_file_path:
            file_path = connectivity_file_path
            print(f"[{self.name}] Using connectivity file from input port: {file_path}")
        else:
            file_path = self._parameters['connectivity_file']
            print(f"[{self.name}] Using connectivity file from parameter: {file_path}")

        # TVB's from_file resolves relative paths inside the tvb_data package,
        # so convert to absolute using this node file's location as anchor.
        if not os.path.isabs(file_path):
            _node_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.abspath(os.path.join(_node_dir, '../../', file_path))
            print(f"[{self.name}] Resolved absolute path: {file_path}")

        con = connectivity.Connectivity.from_file(file_path)      
        nregions = len(con.region_labels)                               #number of regions
        con.weights = con.weights - con.weights * np.eye((nregions))    #remove self-connection
        con.speed = np.array([sys.float_info.max])                      #set conduction speed (here we neglect it)
        con.configure()
        return {
            'tvb_connectivity': con,
        }

    
    def sc_visualization(self, tvb_connectivity: Dict[str, Any]) -> Dict[str, Any]:
        """Visualize connectivity matrix object in TVB format.
        
        Args:
            tvb_connectivity: connectivity matrix object in TVB format.
            
        Returns:
            a flag indicating the visualization is completed
        """
        
        labels = tvb_connectivity.region_labels
        n = len(labels)

        fig = plt.figure(figsize=(15, 7))
        fig.suptitle('TVB Structural Connectivity', fontsize=20)

        # Weights
        plt.subplot(121)
        plt.imshow(tvb_connectivity.weights, interpolation='nearest', aspect='equal', cmap='jet')
        plt.xticks(range(n), labels, fontsize=7, rotation=90)
        plt.yticks(range(n), labels, fontsize=7)
        cb = plt.colorbar(shrink=0.2)
        cb.set_label('Weights', fontsize=14)

        # Tract lengths
        plt.subplot(122)
        plt.imshow(tvb_connectivity.tract_lengths, interpolation='nearest', aspect='equal', cmap='jet')
        plt.xticks(range(n), labels, fontsize=7, rotation=90)
        plt.yticks(range(n), labels, fontsize=7)
        cb = plt.colorbar(shrink=0.2)
        cb.set_label('Tract lengths', fontsize=14)

        fig.tight_layout()

        try:
            from IPython.display import display as ipy_display
            ipy_display(fig)
        except Exception:
            pass
        plt.close(fig)

        return {
            'visualization completed': True
        }