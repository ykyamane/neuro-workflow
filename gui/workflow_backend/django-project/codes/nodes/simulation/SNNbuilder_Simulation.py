"""
Simulation Node for NeuroWorkflow Model Builder

This node executes neural network simulations using NEST's Simulate() function.
It operates in dual modalities:
1. Direct execution: Runs actual NEST simulation
2. Script generation: Generates Python code for standalone execution

Author: NeuroWorkflow Team
Date: 2025
Version: 1.0
"""

from typing import Dict, Any, List, Optional, Union, Tuple
import time
import json

# Core NeuroWorkflow imports
from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema, 
    PortDefinition, 
    ParameterDefinition, 
    MethodDefinition
)
from neuroworkflow.core.port import PortType

# NEST import (optional - will handle if not available)
try:
    import nest
    NEST_AVAILABLE = True
except ImportError:
    NEST_AVAILABLE = False
    print("Warning: NEST not available. Node will work in script generation mode only.")


class SNNbuilder_Simulation(Node):
    """
    Simulation Builder Node for Neural Network Simulation.
    
    This node executes neural network simulations using NEST's Simulate() function.
    It represents the final step in the neural network construction pipeline.
    
    Simulation Features:
    - **Timed simulation**: Execute simulation for specified duration
    - **Experiment tracking**: Associate simulation with experiments or publications
    - **Performance monitoring**: Track simulation execution time and performance
    - **Script generation**: Generate standalone Python scripts for simulation
    
    The node waits for network construction to complete before executing the simulation.
    """
    
    NODE_DEFINITION = NodeDefinitionSchema(
        type='simulation_builder',
        description='Execute neural network simulation using NEST Simulate function',
        
        parameters={
            # === SIMULATION CONFIGURATION ===
            'simulation_time': ParameterDefinition(
                default_value=1000.0,
                description='Simulation duration in milliseconds',
                constraints={'min': 0.1, 'max': 100000.0}
            ),
            
            'name': ParameterDefinition(
                default_value='Neural_Simulation',
                description='Name/identifier for this simulation run'
            ),
            
            'description': ParameterDefinition(
                default_value='Neural network simulation',
                description='Description of what this simulation represents'
            ),
            
            'experiment_reference': ParameterDefinition(
                default_value='',
                description='Reference to experiment or scientific publication (optional)'
            ),
            
            # === PERFORMANCE MONITORING ===
            'monitor_performance': ParameterDefinition(
                default_value=True,
                description='Monitor and report simulation performance metrics'
            ),
            
            'verbose_output': ParameterDefinition(
                default_value=True,
                description='Enable verbose output during simulation'
            ),
            
            # === SCRIPT GENERATION ===
            'script_format': ParameterDefinition(
                default_value='python',
                description='Format for generated script',
                constraints={'allowed_values': ['python', 'notebook','both']}
            ),
            
            'execution_mode': ParameterDefinition(
                default_value='execution',
                description='Mode of operation',
                constraints={'allowed_values': ['execution', 'script', 'both']}
            ),

            'nest_kernel_settings': ParameterDefinition(
                default_value={'overwrite_files': True},
                description='Dict passed to nest.SetKernelStatus() before simulation. '
                            'Use to set overwrite_files, resolution, rng_seed, local_num_threads, etc.'
            )
        },
        
        inputs={
            'network_ready': PortDefinition(
                type=PortType.BOOL,
                description='Signal that network construction is complete and ready for simulation'
            ),
            
            # Primary recording devices port (backward compatibility)
            'recording_devices': PortDefinition(
                type=PortType.OBJECT,
                description='Recording devices for data collection. Can be a single device, list of devices, or dictionary of devices organized by type/region (optional)',
                optional=True
            ),
            
            # Additional recording device ports for multiple source nodes
            'recording_devices_1': PortDefinition(
                type=PortType.OBJECT,
                description='Additional recording devices from source node 1 (optional)',
                optional=True
            ),
            
            'recording_devices_2': PortDefinition(
                type=PortType.OBJECT,
                description='Additional recording devices from source node 2 (optional)',
                optional=True
            ),
            
            'recording_devices_3': PortDefinition(
                type=PortType.OBJECT,
                description='Additional recording devices from source node 3 (optional)',
                optional=True
            ),
            
            'recording_devices_4': PortDefinition(
                type=PortType.OBJECT,
                description='Additional recording devices from source node 4 (optional)',
                optional=True
            ),
            
            'network_summary': PortDefinition(
                type=PortType.DICT,
                description='Summary of the constructed network (optional)',
                optional=True
            )
        },
        
        outputs={
            # Simulation execution outputs
            'simulation_completed': PortDefinition(
                type=PortType.BOOL,
                description='Signal that simulation completed successfully'
            ),
            
            'simulation_results': PortDefinition(
                type=PortType.DICT,
                description='Simulation results including timing and performance metrics'
            ),
            
            # Script generation outputs
            'python_script': PortDefinition(
                type=PortType.STR,
                description='Generated Python script code'
            ),
            
            'notebook_cell': PortDefinition(
                type=PortType.STR,
                description='Generated Jupyter notebook cell code',
                optional=True
            ),
            
            # Metadata outputs
            'simulation_summary': PortDefinition(
                type=PortType.DICT,
                description='Complete summary of simulation parameters and results'
            )
        },
        
        methods={
            'validate_parameters': MethodDefinition(
                description='Validate simulation parameters and check NEST status',
                inputs=['network_ready', 'network_summary'],
                outputs=['validated_parameters']
            ),
            
            'execute_simulation': MethodDefinition(
                description='Execute the NEST simulation',
                inputs=['validated_parameters'],
                outputs=['simulation_results']
            ),
            
            'generate_python_script': MethodDefinition(
                description='Generate Python script code for simulation',
                inputs=['validated_parameters'],
                outputs=['python_script']
            ),
            
            'generate_notebook_cell': MethodDefinition(
                description='Generate Jupyter notebook cell for simulation',
                inputs=['validated_parameters'],
                outputs=['notebook_cell']
            ),
            
            'compile_summary': MethodDefinition(
                description='Compile complete simulation summary',
                inputs=['validated_parameters', 'simulation_results'],
                outputs=['simulation_summary']
            )
        }
    )
    
    def __init__(self, name: str):
        """Initialize the simulation node."""
        super().__init__(name, self.NODE_DEFINITION)
        
        # Define processing steps
        self._define_process_steps()
        
        # Internal state
        self._validated_parameters = None
        self._simulation_results = None
        self._start_time = None
        self._end_time = None
        
    def _define_process_steps(self):
        """Define the processing steps for the simulation node."""
        # Always validate parameters first
        self.add_process_step(
            "validate_parameters",
            self.validate_parameters,
            method_key="validate_parameters"
        )
        
        self.add_process_step(
            "execute_simulation",
            self.execute_simulation,
            method_key="execute_simulation"
        )
        
        self.add_process_step(
            "generate_python_script",
            self.generate_python_script,
            method_key="generate_python_script"
        )
        
        self.add_process_step(
            "generate_notebook_cell",
            self.generate_notebook_cell,
            method_key="generate_notebook_cell"
        )
        
        self.add_process_step(
            "compile_summary",
            self.compile_summary,
            method_key="compile_summary"
        )
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _process_recording_devices(self, recording_devices) -> Dict[str, Any]:
        """
        Process and organize recording devices from various input formats.
        
        Args:
            recording_devices: Can be single device, list, or dict of devices
            
        Returns:
            Dictionary with organized device information
        """
        if recording_devices is None:
            return {'devices': [], 'count': 0, 'types': [], 'organized': False}
        
        devices = []
        device_types = []
        
        if isinstance(recording_devices, dict):
            # Dictionary of devices (organized by type/region)
            for key, device_group in recording_devices.items():
                if isinstance(device_group, list):
                    devices.extend(device_group)
                    device_types.extend([f"{key}_{i}" for i in range(len(device_group))])
                else:
                    devices.append(device_group)
                    device_types.append(key)
        elif isinstance(recording_devices, list):
            # List of devices
            devices = recording_devices
            device_types = [f"device_{i}" for i in range(len(devices))]
        else:
            # Single device
            devices = [recording_devices]
            device_types = ['device_0']
        
        return {
            'devices': devices,
            'count': len(devices),
            'types': device_types,
            'organized': isinstance(recording_devices, dict)
        }
    
    # ========================================================================
    # PARAMETER VALIDATION
    # ========================================================================
    
    def validate_parameters(self, network_ready=None, network_summary=None) -> Dict[str, Any]:
        """
        Validate simulation parameters and check system readiness.
        
        Args:
            network_ready: Signal that network construction is complete
            network_summary: Summary of the constructed network
        
        Returns:
            Dictionary containing validation results and processed parameters
        """
        print(f"[{self.name}] Validating simulation parameters...")
        
        errors = []
        warnings = []
        
        # Start with current parameters
        validated_params = self._parameters.copy()
        
        # Validate simulation time
        sim_time = validated_params['simulation_time']
        if sim_time <= 0:
            errors.append(f"Simulation time must be positive, got {sim_time}")
        
        if sim_time > 50000.0:  # 50 seconds
            warnings.append(f"Long simulation time ({sim_time} ms) may take significant time to complete")
        
        # Check network readiness
        #network_status = network_ready if network_ready is not None else self._input_ports.get('network_ready', {}).get('value', False)
        #if not network_status:
        #    errors.append("Network is not ready for simulation. Ensure all network construction nodes have completed.")
        
        # Validate NEST availability for execution mode
        execution_mode = validated_params['execution_mode']
        if execution_mode in ['execution', 'both'] and not NEST_AVAILABLE:
            warnings.append("NEST not available. Switching to script generation mode only.")
            validated_params['execution_mode'] = 'script'
        
        # Check experiment reference format if provided
        exp_ref = validated_params['experiment_reference']
        if exp_ref and len(exp_ref.strip()) == 0:
            validated_params['experiment_reference'] = ''
        
        # Collect recording devices from all input ports
        all_recording_devices = []
        device_sources = []
        
        # Check all recording device input ports
        recording_port_names = ['recording_devices', 'recording_devices_1', 'recording_devices_2', 
                               'recording_devices_3', 'recording_devices_4']
        
        for port_name in recording_port_names:
            if port_name in self._input_ports:
                port_value = self._input_ports[port_name].value
                if port_value is not None:
                    all_recording_devices.append(port_value)
                    device_sources.append(port_name)
        
        # Process all collected recording devices
        if all_recording_devices:
            # If multiple sources, combine them into a list
            if len(all_recording_devices) == 1:
                combined_devices = all_recording_devices[0]
            else:
                combined_devices = all_recording_devices
            
            device_info = self._process_recording_devices(combined_devices)
            device_info['source_ports'] = device_sources
            device_info['multiple_sources'] = len(all_recording_devices) > 1
            
            validated_params['recording_device_info'] = device_info
            print(f"[{self.name}] Found {device_info['count']} recording device(s) from {len(device_sources)} source(s)")
            print(f"[{self.name}] Source ports: {', '.join(device_sources)}")
            if device_info['organized']:
                print(f"[{self.name}] Devices organized by: {', '.join(device_info['types'])}")
        else:
            validated_params['recording_device_info'] = {'devices': [], 'count': 0, 'types': [], 'organized': False, 'source_ports': [], 'multiple_sources': False}
        
        # Report validation results
        if errors:
            error_msg = "; ".join(errors)
            raise ValueError(f"Simulation parameter validation failed: {error_msg}")
        
        if warnings:
            for warning in warnings:
                print(f"[{self.name}] Warning: {warning}")
        
        # Store validated parameters
        self._validated_parameters = validated_params
        
        print(f"[{self.name}] Parameter validation completed successfully")
        return {'validated_parameters': validated_params}
    
    # ========================================================================
    # SIMULATION EXECUTION
    # ========================================================================
    
    def execute_simulation(self, validated_parameters=None) -> Dict[str, Any]:
        """
        Execute the NEST simulation.
        
        Args:
            validated_parameters: Validated parameters from validation step
            
        Returns:
            Dictionary containing simulation results and performance metrics
        """
        # Use provided parameters or fall back to stored ones
        validated_params = validated_parameters if validated_parameters is not None else self._validated_parameters
        
        if validated_params is None:
            raise ValueError("No validated parameters available. Run validate_parameters first.")
        
        execution_mode = validated_params.get('execution_mode', 'execution')
        
        # Check if simulation execution is requested
        if execution_mode not in ['execution', 'both']:
            print(f"[{self.name}] Skipping simulation execution (execution_mode: {execution_mode})")
            return {'simulation_results': None}
        
        if not NEST_AVAILABLE:
            raise RuntimeError("NEST is not available for simulation execution")
        
        sim_time = validated_params['simulation_time']
        verbose = validated_params['verbose_output']
        monitor_perf = validated_params['monitor_performance']
        
        print(f"[{self.name}] Starting simulation...")
        print(f"[{self.name}] Simulation name: {validated_params['name']}")
        print(f"[{self.name}] Description: {validated_params['description']}")
        if validated_params['experiment_reference']:
            print(f"[{self.name}] Experiment reference: {validated_params['experiment_reference']}")
        print(f"[{self.name}] Duration: {sim_time} ms")
        
        # Apply kernel settings (e.g. overwrite_files, resolution, rng_seed)
        kernel_settings = validated_params.get('nest_kernel_settings', {})
        if kernel_settings:
            nest.SetKernelStatus(kernel_settings)

        # Record start time
        self._start_time = time.time()

        try:
            # Execute NEST simulation
            if verbose:
                print(f"[{self.name}] Calling nest.Simulate({sim_time})...")
            
            nest.Simulate(sim_time)
            nest.raster_plot.from_device(self.get_input_port("recording_devices").value, hist=True)
            
            # Record end time
            self._end_time = time.time()
            
            # Calculate performance metrics
            wall_time = self._end_time - self._start_time
            simulation_speed = sim_time / (wall_time * 1000.0)  # ms simulated per ms wall time
            
            results = {
                'simulation_completed': True,
                'simulation_time': sim_time,
                'wall_time_seconds': wall_time,
                'simulation_speed': simulation_speed,
                'start_timestamp': self._start_time,
                'end_timestamp': self._end_time
            }
            
            if monitor_perf:
                print(f"[{self.name}] Simulation completed successfully!")
                print(f"[{self.name}] Wall time: {wall_time:.2f} seconds")
                print(f"[{self.name}] Simulation speed: {simulation_speed:.2f}x real-time")
            
            # Store results
            self._simulation_results = results
            
            return {'simulation_results': results}
            
        except Exception as e:
            self._end_time = time.time()
            error_msg = f"Simulation failed: {str(e)}"
            print(f"[{self.name}] {error_msg}")
            
            results = {
                'simulation_completed': False,
                'error': error_msg,
                'simulation_time': sim_time,
                'wall_time_seconds': self._end_time - self._start_time,
                'start_timestamp': self._start_time,
                'end_timestamp': self._end_time
            }
            
            self._simulation_results = results
            return {'simulation_results': results}
    
    # ========================================================================
    # SCRIPT GENERATION
    # ========================================================================
    
    def generate_python_script(self, validated_parameters=None) -> Dict[str, str]:
        """
        Generate Python script for simulation execution.
        
        Args:
            validated_parameters: Validated parameters from validation step
            
        Returns:
            Dictionary containing generated Python script
        """
        # Use provided parameters or fall back to stored ones
        validated_params = validated_parameters if validated_parameters is not None else self._validated_parameters
        
        if validated_params is None:
            raise ValueError("No validated parameters available. Run validate_parameters first.")
        
        execution_mode = validated_params.get('execution_mode', 'execution')
        
        # Check if script generation is requested
        if execution_mode not in ['script', 'both']:
            print(f"[{self.name}] Skipping Python script generation (execution_mode: {execution_mode})")
            return {'python_script': None}
        
        print(f"[{self.name}] Generating Python script for simulation...")
        
        sim_time = validated_params['simulation_time']
        name = validated_params['name']
        description = validated_params['description']
        exp_ref = validated_params['experiment_reference']
        monitor_perf = validated_params['monitor_performance']
        verbose = validated_params['verbose_output']
        
        # Build the script
        script_lines = []
        
        # Header
        script_lines.extend([
            f"# Neural Network Simulation: {name}",
            f"# Generated by NeuroWorkflow SimulationBuilderNode",
            f"# Timestamp: {self._get_timestamp()}",
            "",
            f"# Description: {description}",
        ])
        
        if exp_ref:
            script_lines.append(f"# Experiment Reference: {exp_ref}")
        
        script_lines.extend([
            "",
            "import nest",
            "import time",
            "",
            "# Simulation Configuration",
            f"simulation_time = {sim_time}  # milliseconds",
            f"simulation_name = '{name}'",
            f"monitor_performance = {monitor_perf}",
            f"verbose_output = {verbose}",
            "",
            "# Execute Simulation",
            "print(f'Starting simulation: {simulation_name}')",
            f"print(f'Duration: {{simulation_time}} ms')",
        ])
        
        if exp_ref:
            script_lines.append(f"print(f'Experiment: {exp_ref}')")
        
        script_lines.extend([
            "",
            "# Record start time",
            "start_time = time.time()",
            "",
            "try:",
            "    if verbose_output:",
            "        print(f'Calling nest.Simulate({simulation_time})...')",
            "    ",
            "    # Execute NEST simulation",
            "    nest.Simulate(simulation_time)",
            "    ",
            "    # Record end time",
            "    end_time = time.time()",
            "    ",
            "    # Calculate performance metrics",
            "    wall_time = end_time - start_time",
            "    simulation_speed = simulation_time / (wall_time * 1000.0)",
            "    ",
            "    if monitor_performance:",
            "        print(f'Simulation completed successfully!')",
            "        print(f'Wall time: {wall_time:.2f} seconds')",
            "        print(f'Simulation speed: {simulation_speed:.2f}x real-time')",
            "    ",
            "except Exception as e:",
            "    end_time = time.time()",
            "    print(f'Simulation failed: {str(e)}')",
            "    print(f'Wall time: {end_time - start_time:.2f} seconds')",
            "",
            "print('Simulation script completed.')"
        ])
        
        python_script = '\n'.join(script_lines)
        
        print(f"[{self.name}] Python script generated ({len(script_lines)} lines)")
        return {'python_script': python_script}
    
    def generate_notebook_cell(self, validated_parameters=None) -> Dict[str, str]:
        """
        Generate Jupyter notebook cell for simulation execution.
        
        Args:
            validated_parameters: Validated parameters from validation step
            
        Returns:
            Dictionary containing generated notebook cell
        """
        # Use provided parameters or fall back to stored ones
        validated_params = validated_parameters if validated_parameters is not None else self._validated_parameters
        
        if validated_params is None:
            raise ValueError("No validated parameters available. Run validate_parameters first.")
        
        script_format = validated_params.get('script_format', 'python')
        
        # Check if notebook cell generation is requested
        if script_format != 'notebook':
            print(f"[{self.name}] Skipping notebook cell generation (script_format: {script_format})")
            return {'notebook_cell': None}
        
        print(f"[{self.name}] Generating Jupyter notebook cell for simulation...")
        
        # Get the Python script first
        script_result = self.generate_python_script(validated_params)
        python_script = script_result['python_script']
        
        if python_script is None:
            return {'notebook_cell': None}
        
        # Extract just the code part (remove comments for cleaner notebook)
        script_lines = python_script.split('\n')
        code_lines = []
        
        for line in script_lines:
            if line.strip().startswith('import ') or \
               line.strip().startswith('simulation_') or \
               line.strip().startswith('start_time') or \
               line.strip().startswith('end_time') or \
               line.strip().startswith('wall_time') or \
               line.strip().startswith('nest.Simulate') or \
               line.strip().startswith('try:') or \
               line.strip().startswith('except') or \
               line.strip().startswith('print(') or \
               line.strip() == '' or \
               '    ' in line:  # Indented lines
                code_lines.append(line)
        
        sim_time = validated_params['simulation_time']
        name = validated_params['name']
        description = validated_params['description']
        exp_ref = validated_params['experiment_reference']
        device_info = validated_params.get('recording_device_info', {'count': 0, 'types': []})
        
        # Create notebook cell with markdown header
        header_lines = [
            f"### Neural Network Simulation: {name}\n",
            f"**Description:** {description}  \n",
            f"**Duration:** {sim_time} ms  \n",
        ]
        
        if exp_ref:
            header_lines.append(f"**Experiment Reference:** {exp_ref}  \n")
        
        if device_info['count'] > 0:
            header_lines.append(f"**Recording Devices:** {device_info['count']} device(s)  \n")
        
        header_lines.append("\n")
        
        # Combine header and code
        notebook_cell = ''.join(header_lines) + '\n```python\n' + '\n'.join(code_lines) + '\n```'
        
        print(f"[{self.name}] Notebook cell generated")
        return {'notebook_cell': notebook_cell}
    
    # ========================================================================
    # SUMMARY COMPILATION
    # ========================================================================
    
    def compile_summary(self, validated_parameters=None, simulation_results=None) -> Dict[str, Any]:
        """
        Compile complete simulation summary.
        
        Args:
            validated_parameters: Validated parameters from validation step
            simulation_results: Results from simulation execution
            
        Returns:
            Dictionary containing complete simulation summary
        """
        # Use provided parameters or fall back to stored ones
        validated_params = validated_parameters if validated_parameters is not None else self._validated_parameters
        sim_results = simulation_results if simulation_results is not None else self._simulation_results
        
        if validated_params is None:
            raise ValueError("No validated parameters available. Run validate_parameters first.")
        
        print(f"[{self.name}] Compiling simulation summary...")
        
        summary = {
            'node_name': self.name,
            'node_type': 'simulation_builder',
            'timestamp': self._get_timestamp(),
            
            # Simulation configuration
            'simulation_config': {
                'name': validated_params['name'],
                'description': validated_params['description'],
                'experiment_reference': validated_params['experiment_reference'],
                'simulation_time': validated_params['simulation_time'],
                'execution_mode': validated_params['execution_mode']
            },
            
            # Execution results
            'execution_results': sim_results if sim_results else {
                'simulation_completed': False,
                'reason': 'Simulation not executed'
            },
            
            # Recording devices information
            'recording_devices': validated_params.get('recording_device_info', {'devices': [], 'count': 0, 'types': []}),
            
            # Performance metrics
            'performance': {}
        }
        
        if sim_results and sim_results.get('simulation_completed', False):
            summary['performance'] = {
                'wall_time_seconds': sim_results.get('wall_time_seconds', 0),
                'simulation_speed': sim_results.get('simulation_speed', 0),
                'efficiency_rating': 'excellent' if sim_results.get('simulation_speed', 0) > 1.0 else 'good'
            }
        
        return summary
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")