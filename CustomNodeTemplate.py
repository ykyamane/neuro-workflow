"""
Custom Node Template for NeuroWorkflow

This template provides a comprehensive starting point for creating custom nodes
in the NeuroWorkflow system. Follow the comments and examples to build your own
specialized processing nodes.

Author: [Your Name]
Date: [Date]
Version: 1.0
"""

from typing import Dict, Any, List, Optional, Union
import numpy as np  # Common import for numerical operations

# Core NeuroWorkflow imports - REQUIRED for all custom nodes
from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema, 
    PortDefinition, 
    ParameterDefinition, 
    MethodDefinition
)
from neuroworkflow.core.port import PortType

# Add any additional imports your node needs here
# Examples:
# import nest  # For NEST simulator integration
# import matplotlib.pyplot as plt  # For plotting
# import pandas as pd  # For data manipulation
# import scipy.signal  # For signal processing


class CustomNodeTemplate(Node):
    """
    Template for creating custom nodes in NeuroWorkflow.
    
    Replace this docstring with a description of what your node does.
    Be specific about:
    - What type of processing it performs
    - What inputs it expects
    - What outputs it produces
    - Any special requirements or dependencies
    
    Example:
    This node performs spike train analysis on neural simulation data,
    calculating firing rates, inter-spike intervals, and other metrics.
    It requires spike timing data as input and produces statistical summaries.
    """
    
    # NODE_DEFINITION is REQUIRED - this defines your node's interface
    NODE_DEFINITION = NodeDefinitionSchema(
        # REQUIRED: Unique identifier for your node type
        type='custom_node_template',
        
        # REQUIRED: Human-readable description
        description='Template for creating custom NeuroWorkflow nodes',
        
        # OPTIONAL: Parameters that control your node's behavior
        parameters={
            # Example parameter with full specification
            'processing_mode': ParameterDefinition(
                default_value='standard',
                description='Processing mode for the analysis',
                constraints={'allowed_values': ['standard', 'advanced', 'debug']},
                optimizable=False  # Set to True if this should be optimized
            ),
            
            # Example numeric parameter with optimization support
            'threshold': ParameterDefinition(
                default_value=0.5,
                description='Threshold value for processing',
                constraints={'min': 0.0, 'max': 1.0},
                optimizable=True,  # Optional metadata for optimization tools
                optimization_range=[0.1, 0.9],  # Range for optimization
                suggested_values=[
                    {'value': 0.4, 'source': 'literature', 'species': 'human'},
                    {'value': 0.6, 'source': 'allen_brain', 'species': 'mouse'}
                ]
            ),
            
            # Example list parameter
            'filter_frequencies': ParameterDefinition(
                default_value=[1.0, 100.0],
                description='Frequency range for filtering [low, high] in Hz',
                constraints={'min_length': 2, 'max_length': 2}
            ),
            
            # Simple parameter (just default value)
            'enable_plotting': ParameterDefinition(
                default_value=False,
                description='Whether to generate plots'
            ),
        },
        
        # OPTIONAL: Input ports - data your node receives
        inputs={
            # Required input
            'input_data': PortDefinition(
                type=PortType.OBJECT,  # Can be any Python object
                description='Main input data for processing'
            ),
            
            # Optional input with specific type
            'configuration': PortDefinition(
                type=PortType.DICT,
                description='Additional configuration parameters',
                optional=True  # This input is not required
            ),
            
            # Numeric input
            'sampling_rate': PortDefinition(
                type=PortType.FLOAT,
                description='Sampling rate in Hz',
                optional=True
            ),
            
            # File-based input (for I/O operations)
            'data_file': PortDefinition(
                type=PortType.CSV_FILE,
                description='Path to CSV data file',
                optional=True
            ),
        },
        
        # OPTIONAL: Output ports - data your node produces
        outputs={
            # Main results
            'processed_data': PortDefinition(
                type=PortType.OBJECT,
                description='Main processed output data'
            ),
            
            # Statistical summary
            'statistics': PortDefinition(
                type=PortType.DICT,
                description='Statistical summary of processing results'
            ),
            
            # Optional visualization
            'plot_figure': PortDefinition(
                type=PortType.OBJECT,
                description='Matplotlib figure object',
                optional=True
            ),
            
            # File output
            'output_file': PortDefinition(
                type=PortType.CSV_FILE,
                description='Path to output CSV file',
                optional=True
            ),
        },
        
        # OPTIONAL: Method definitions for documentation and process steps
        methods={
            'validate_inputs': MethodDefinition(
                description='Validate input data and parameters',
                inputs=['input_data', 'configuration'],
                outputs=['validation_result']
            ),
            
            'process_data': MethodDefinition(
                description='Main data processing method',
                inputs=['input_data', 'sampling_rate'],
                outputs=['processed_data']
            ),
            
            'calculate_statistics': MethodDefinition(
                description='Calculate statistical summaries',
                inputs=['processed_data'],
                outputs=['statistics']
            ),
            
            'generate_visualization': MethodDefinition(
                description='Generate plots and visualizations',
                inputs=['processed_data', 'statistics'],
                outputs=['plot_figure']
            ),
            
            'save_results': MethodDefinition(
                description='Save results to file',
                inputs=['processed_data', 'statistics'],
                outputs=['output_file']
            ),
        }
    )
    
    def __init__(self, name: str):
        """
        Initialize your custom node.
        
        Args:
            name: Unique name for this node instance
        """
        # REQUIRED: Call parent constructor
        super().__init__(name)
        
        # Initialize any additional instance variables here
        self._processing_cache = {}
        self._validation_status = False
        
        # REQUIRED: Define the processing steps
        self._define_process_steps()
    
    def _define_process_steps(self) -> None:
        """
        Define the sequence of processing steps for this node.
        
        This method is REQUIRED and defines the order in which your
        node's methods will be executed.
        """
        # Add process steps in the order they should be executed
        self.add_process_step(
            "validate_inputs",
            self.validate_inputs,
            method_key="validate_inputs"  # Links to NODE_DEFINITION.methods
        )
        
        self.add_process_step(
            "process_data",
            self.process_data,
            method_key="process_data"
        )
        
        self.add_process_step(
            "calculate_statistics",
            self.calculate_statistics,
            method_key="calculate_statistics"
        )
        
        # Conditional step - only add if plotting is enabled
        if self._parameters.get('enable_plotting', False):
            self.add_process_step(
                "generate_visualization",
                self.generate_visualization,
                method_key="generate_visualization"
            )
        
        self.add_process_step(
            "save_results",
            self.save_results,
            method_key="save_results"
        )
    
    # ========================================================================
    # PROCESSING METHODS
    # Implement your node's functionality in these methods
    # ========================================================================
    
    def validate_inputs(self, input_data: Any, configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate input data and parameters.
        
        This method should check that inputs are valid and compatible
        with your processing requirements.
        
        Args:
            input_data: Main input data to validate
            configuration: Optional configuration parameters
            
        Returns:
            Dictionary containing validation results
            
        Raises:
            ValueError: If inputs are invalid
        """
        print(f"[{self.name}] Validating inputs...")
        
        # Example validation logic
        validation_result = {
            'valid': True,
            'messages': [],
            'warnings': []
        }
        
        # Check if input_data exists
        if input_data is None:
            validation_result['valid'] = False
            validation_result['messages'].append("Input data is None")
        
        # Check parameter constraints
        threshold = self._parameters['threshold']
        if not (0.0 <= threshold <= 1.0):
            validation_result['valid'] = False
            validation_result['messages'].append(f"Threshold {threshold} is out of range [0.0, 1.0]")
        
        # Example: Check data type and structure
        if hasattr(input_data, '__len__') and len(input_data) == 0:
            validation_result['warnings'].append("Input data is empty")
        
        # Store validation status for later use
        self._validation_status = validation_result['valid']
        
        if not validation_result['valid']:
            error_msg = "Validation failed: " + "; ".join(validation_result['messages'])
            raise ValueError(error_msg)
        
        print(f"[{self.name}] Input validation completed successfully")
        return {'validation_result': validation_result}
    
    def process_data(self, input_data: Any, sampling_rate: Optional[float] = None) -> Dict[str, Any]:
        """
        Main data processing method.
        
        Implement your core processing logic here. This is where the main
        work of your node happens.
        
        Args:
            input_data: Input data to process
            sampling_rate: Optional sampling rate
            
        Returns:
            Dictionary containing processed data
        """
        print(f"[{self.name}] Processing data with mode: {self._parameters['processing_mode']}")
        
        # Access parameters
        threshold = self._parameters['threshold']
        processing_mode = self._parameters['processing_mode']
        filter_freqs = self._parameters['filter_frequencies']
        
        # Example processing logic
        if processing_mode == 'standard':
            processed_data = self._standard_processing(input_data, threshold)
        elif processing_mode == 'advanced':
            processed_data = self._advanced_processing(input_data, threshold, filter_freqs)
        elif processing_mode == 'debug':
            processed_data = self._debug_processing(input_data)
        else:
            raise ValueError(f"Unknown processing mode: {processing_mode}")
        
        # Store in cache for potential reuse
        self._processing_cache['last_result'] = processed_data
        
        print(f"[{self.name}] Data processing completed")
        return {'processed_data': processed_data}
    
    def calculate_statistics(self, processed_data: Any) -> Dict[str, Any]:
        """
        Calculate statistical summaries of the processed data.
        
        Args:
            processed_data: Data from the processing step
            
        Returns:
            Dictionary containing statistical summaries
        """
        print(f"[{self.name}] Calculating statistics...")
        
        # Example statistical calculations
        statistics = {}
        
        try:
            # Convert to numpy array if possible for easier statistics
            if hasattr(processed_data, '__iter__') and not isinstance(processed_data, str):
                data_array = np.array(processed_data)
                
                statistics.update({
                    'mean': float(np.mean(data_array)),
                    'std': float(np.std(data_array)),
                    'min': float(np.min(data_array)),
                    'max': float(np.max(data_array)),
                    'count': len(data_array),
                    'shape': data_array.shape if hasattr(data_array, 'shape') else None
                })
            else:
                statistics['type'] = type(processed_data).__name__
                statistics['value'] = str(processed_data)
                
        except Exception as e:
            print(f"[{self.name}] Warning: Could not calculate statistics: {e}")
            statistics = {'error': str(e)}
        
        # Add processing metadata
        statistics['processing_mode'] = self._parameters['processing_mode']
        statistics['threshold_used'] = self._parameters['threshold']
        
        print(f"[{self.name}] Statistics calculation completed")
        return {'statistics': statistics}
    
    def generate_visualization(self, processed_data: Any, statistics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate visualizations of the processed data.
        
        This method is optional and only runs if enable_plotting is True.
        
        Args:
            processed_data: Processed data to visualize
            statistics: Statistical summaries
            
        Returns:
            Dictionary containing plot figure
        """
        print(f"[{self.name}] Generating visualization...")
        
        try:
            import matplotlib.pyplot as plt
            
            # Create a simple plot
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            
            # Plot 1: Data visualization
            if hasattr(processed_data, '__iter__') and not isinstance(processed_data, str):
                ax1.plot(processed_data)
                ax1.set_title(f'Processed Data - {self.name}')
                ax1.set_xlabel('Sample')
                ax1.set_ylabel('Value')
                ax1.grid(True)
            else:
                ax1.text(0.5, 0.5, f'Data: {processed_data}', 
                        ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title('Data Summary')
            
            # Plot 2: Statistics bar chart
            if 'mean' in statistics:
                stats_to_plot = ['mean', 'std', 'min', 'max']
                values = [statistics.get(stat, 0) for stat in stats_to_plot]
                ax2.bar(stats_to_plot, values)
                ax2.set_title('Statistics Summary')
                ax2.set_ylabel('Value')
            else:
                ax2.text(0.5, 0.5, 'No numerical statistics available', 
                        ha='center', va='center', transform=ax2.transAxes)
            
            plt.tight_layout()
            
            print(f"[{self.name}] Visualization generated successfully")
            return {'plot_figure': fig}
            
        except ImportError:
            print(f"[{self.name}] Warning: matplotlib not available, skipping visualization")
            return {'plot_figure': None}
        except Exception as e:
            print(f"[{self.name}] Error generating visualization: {e}")
            return {'plot_figure': None}
    
    def save_results(self, processed_data: Any, statistics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save results to file.
        
        Args:
            processed_data: Processed data to save
            statistics: Statistical summaries to save
            
        Returns:
            Dictionary containing output file path
        """
        print(f"[{self.name}] Saving results...")
        
        # Generate output filename
        output_file = f"{self.name}_results.csv"
        
        try:
            import pandas as pd
            
            # Create a DataFrame with results
            if hasattr(processed_data, '__iter__') and not isinstance(processed_data, str):
                df = pd.DataFrame({'processed_data': processed_data})
            else:
                df = pd.DataFrame({'processed_data': [processed_data]})
            
            # Add statistics as additional columns
            for key, value in statistics.items():
                if isinstance(value, (int, float, str, bool)):
                    df[f'stat_{key}'] = value
            
            # Save to CSV
            df.to_csv(output_file, index=False)
            print(f"[{self.name}] Results saved to {output_file}")
            
        except ImportError:
            print(f"[{self.name}] Warning: pandas not available, saving as text file")
            output_file = f"{self.name}_results.txt"
            with open(output_file, 'w') as f:
                f.write(f"Results from {self.name}\n")
                f.write(f"Processed data: {processed_data}\n")
                f.write(f"Statistics: {statistics}\n")
        except Exception as e:
            print(f"[{self.name}] Error saving results: {e}")
            output_file = None
        
        return {'output_file': output_file}
    
    # ========================================================================
    # HELPER METHODS
    # Add your own helper methods here
    # ========================================================================
    
    def _standard_processing(self, data: Any, threshold: float) -> Any:
        """
        Standard processing implementation.
        
        Args:
            data: Input data
            threshold: Threshold parameter
            
        Returns:
            Processed data
        """
        # Example: Apply threshold to numerical data
        if hasattr(data, '__iter__') and not isinstance(data, str):
            try:
                data_array = np.array(data)
                # Apply threshold
                processed = np.where(data_array > threshold, data_array, 0)
                return processed.tolist()
            except:
                pass
        
        # Fallback for non-numerical data
        return data
    
    def _advanced_processing(self, data: Any, threshold: float, filter_freqs: List[float]) -> Any:
        """
        Advanced processing implementation.
        
        Args:
            data: Input data
            threshold: Threshold parameter
            filter_freqs: Filter frequency range
            
        Returns:
            Processed data
        """
        # Example: More complex processing
        processed = self._standard_processing(data, threshold)
        
        # Add filtering logic here if needed
        # This is just a placeholder
        print(f"[{self.name}] Advanced processing with filter range: {filter_freqs}")
        
        return processed
    
    def _debug_processing(self, data: Any) -> Any:
        """
        Debug processing implementation.
        
        Args:
            data: Input data
            
        Returns:
            Debug information
        """
        debug_info = {
            'original_data': data,
            'data_type': type(data).__name__,
            'parameters': self._parameters.copy(),
            'validation_status': self._validation_status
        }
        
        return debug_info
    
    # ========================================================================
    # CONFIGURATION AND UTILITY METHODS
    # ========================================================================
    
    def configure(self, **kwargs) -> None:
        """
        Configure the node with new parameters.
        
        This is a convenience method for setting multiple parameters at once.
        
        Args:
            **kwargs: Parameter name-value pairs
        """
        for param_name, value in kwargs.items():
            if param_name in self._parameters:
                self._parameters[param_name] = value
                print(f"[{self.name}] Set {param_name} = {value}")
            else:
                print(f"[{self.name}] Warning: Unknown parameter '{param_name}'")
    
    def get_optimizable_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata about parameters that can be optimized.
        
        Returns:
            Dictionary of optimizable parameter metadata
        """
        return self._optimizable_parameters.copy()
    
    def reset_cache(self) -> None:
        """Reset internal processing cache."""
        self._processing_cache.clear()
        print(f"[{self.name}] Processing cache cleared")
    
    def get_processing_info(self) -> Dict[str, Any]:
        """
        Get information about the node's processing state.
        
        Returns:
            Dictionary with processing information
        """
        return {
            'name': self.name,
            'type': self.__class__.NODE_DEFINITION.type,
            'description': self.description,
            'parameters': self._parameters.copy(),
            'validation_status': self._validation_status,
            'cache_size': len(self._processing_cache),
            'input_ports': list(self._input_ports.keys()),
            'output_ports': list(self._output_ports.keys()),
        }

