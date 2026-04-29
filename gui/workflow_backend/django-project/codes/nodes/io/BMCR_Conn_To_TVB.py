"""
BMCR to TVB Conversion Node for NeuroWorkflow

This node converts BMCR connectome matrices to TVB format and creates ZIP packages
ready for use in TVB simulations. It implements the TVB conversion part of the 
BMCR connectome generation pipeline.

Based on: BMCR_connectome_dti.ipynb
Author: NeuroWorkflow Team
Date: 2025-11-23
Version: 1.0
"""

import os
import zipfile
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema, 
    PortDefinition, 
    ParameterDefinition, 
    MethodDefinition
)
from neuroworkflow.core.port import PortType


class BMCR_Conn_To_TVB(Node):
    """
    Converts BMCR connectome matrices to TVB format and creates ZIP packages.
    
    This node performs the following operations:
    1. Loads connectome matrix from CSV file
    2. Generates all required TVB format files (weights, tract_lengths, centres, etc.)
    3. Creates a ZIP package compatible with TVB
    4. Validates the TVB format
    5. Signals completion for downstream TVB nodes
    
    The node outputs a TVB-compatible ZIP file that can be directly used by
    TVBConnectivitySetUpNode and other TVB workflow components.
    """
    
    NODE_DEFINITION = NodeDefinitionSchema(
        type='bmcr_to_tvb',
        description='Converts BMCR connectome matrices to TVB format and creates ZIP packages',
        
        parameters={
            'output_directory': ParameterDefinition(
                default_value='./',
                description='Directory to store TVB format files and ZIP package',
                constraints={},
                optimizable=False
            ),
            
            'region_prefix': ParameterDefinition(
                default_value='region',
                description='Prefix for region labels (e.g., "region" -> "region_001")',
                constraints={},
                optimizable=False
            ),
            
            'hemisphere_info': ParameterDefinition(
                default_value=True,
                description='Include hemisphere information in region labels',
                constraints={},
                optimizable=False
            ),
            
            'brain_center': ParameterDefinition(
                default_value=[0.0, 0.0, 0.0],
                description='Center coordinates for brain positioning [x, y, z] in mm',
                constraints={'min_length': 3, 'max_length': 3},
                optimizable=False
            ),
            
            'brain_size': ParameterDefinition(
                default_value=[50.0, 40.0, 30.0],
                description='Brain size dimensions [width, height, depth] in mm',
                constraints={'min_length': 3, 'max_length': 3},
                optimizable=False
            ),
            
            'tract_length_factor': ParameterDefinition(
                default_value=1.0,
                description='Scaling factor for tract lengths (default assumes mm)',
                constraints={'min': 0.1, 'max': 100.0},
                optimizable=False
            ),
        },
        
        inputs={
            'connectome_file': PortDefinition(
                type=PortType.STR,
                description='Path to the connectome CSV file from BMCRDownloadNode'
            ),
            
            'subject_id': PortDefinition(
                type=PortType.STR,
                description='Subject identifier for naming the output files'
            ),
            
            'processing_metadata': PortDefinition(
                type=PortType.DICT,
                description='Metadata from the download/generation process',
                optional=True
            ),
        },
        
        outputs={
            'tvb_zip_file': PortDefinition(
                type=PortType.STR,
                description='Path to the TVB-compatible ZIP file'
            ),
            
            'tvb_connectivity': PortDefinition(
                type=PortType.OBJECT,
                description='TVB Connectivity object (for direct use)',
                optional=True
            ),
            
            'conversion_metadata': PortDefinition(
                type=PortType.DICT,
                description='Metadata about the TVB conversion process'
            ),
            
            'tvb_files': PortDefinition(
                type=PortType.DICT,
                description='Dictionary of paths to individual TVB format files'
            ),
            
            'completion_signal': PortDefinition(
                type=PortType.BOOL,
                description='Signal indicating successful completion for downstream nodes'
            ),
        },
        
        methods={
            'load_connectome': MethodDefinition(
                description='Load connectome matrix from CSV file',
                inputs=['connectome_file'],
                outputs=['connectome_matrix', 'matrix_info']
            ),
            
            'generate_tvb_files': MethodDefinition(
                description='Generate all required TVB format files',
                inputs=['connectome_matrix', 'subject_id'],
                outputs=['tvb_files']
            ),
            
            'create_tvb_zip': MethodDefinition(
                description='Create TVB-compatible ZIP package',
                inputs=['tvb_files', 'subject_id'],
                outputs=['tvb_zip_file']
            ),
            
            'validate_tvb_format': MethodDefinition(
                description='Validate TVB format compatibility',
                inputs=['tvb_zip_file'],
                outputs=['validation_results', 'tvb_connectivity']
            ),
            
            'finalize_output': MethodDefinition(
                description='Finalize output and signal completion',
                inputs=['tvb_zip_file', 'validation_results'],
                outputs=['completion_signal', 'conversion_metadata', 'tvb_zip_file']
            ),
        }
    )
    
    def __init__(self, name: str):
        """Initialize the BMCR to TVB Conversion Node."""
        super().__init__(name)
        self._conversion_start_time = None
        self._connectome_matrix = None
        self._n_regions = 0
        self._define_process_steps()
    
    def _define_process_steps(self) -> None:
        """Define the sequence of processing steps."""
        self.add_process_step(
            "load_connectome",
            self.load_connectome,
            method_key="load_connectome"
        )
        
        self.add_process_step(
            "generate_tvb_files",
            self.generate_tvb_files,
            method_key="generate_tvb_files"
        )
        
        self.add_process_step(
            "create_tvb_zip",
            self.create_tvb_zip,
            method_key="create_tvb_zip"
        )
        
        # Always validate TVB format
        self.add_process_step(
            "validate_tvb_format",
            self.validate_tvb_format,
            method_key="validate_tvb_format"
        )
        
        self.add_process_step(
            "finalize_output",
            self.finalize_output,
            method_key="finalize_output"
        )
    
    def load_connectome(self, connectome_file: str) -> Dict[str, Any]:
        """Load connectome matrix from CSV file."""
        import time
        
        print(f"[{self.name}] Loading connectome from {connectome_file}...")
        self._conversion_start_time = time.time()
        
        if not Path(connectome_file).exists():
            raise FileNotFoundError(f"Connectome file not found: {connectome_file}")
        
        try:
            # Load the connectome matrix
            connectome_matrix = np.loadtxt(connectome_file, delimiter=',')
            
            if connectome_matrix.ndim != 2:
                raise ValueError(f"Expected 2D matrix, got {connectome_matrix.ndim}D")
            
            if connectome_matrix.shape[0] != connectome_matrix.shape[1]:
                raise ValueError(f"Expected square matrix, got shape {connectome_matrix.shape}")
            
            self._connectome_matrix = connectome_matrix
            self._n_regions = connectome_matrix.shape[0]
            
            matrix_info = {
                'shape': connectome_matrix.shape,
                'n_regions': self._n_regions,
                'total_connections': int(np.sum(connectome_matrix > 0)),
                'density': float(np.sum(connectome_matrix > 0) / (self._n_regions**2)),
                'mean_strength': float(np.mean(connectome_matrix[connectome_matrix > 0])) if np.any(connectome_matrix > 0) else 0.0,
                'max_strength': float(np.max(connectome_matrix)),
                'file_size_bytes': Path(connectome_file).stat().st_size
            }
            
            print(f"[{self.name}] Connectome loaded: {connectome_matrix.shape}")
            print(f"[{self.name}] Regions: {self._n_regions}, Connections: {matrix_info['total_connections']}")
            print(f"[{self.name}] Density: {matrix_info['density']*100:.2f}%")
            
            return {
                'connectome_matrix': connectome_matrix,
                'matrix_info': matrix_info
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to load connectome matrix: {e}")
    
    def generate_tvb_files(self, connectome_matrix: np.ndarray, subject_id: str) -> Dict[str, Any]:
        """Generate all required TVB format files."""
        print(f"[{self.name}] Generating TVB format files...")
        
        output_dir = Path(self._parameters['output_directory'])
        subject_output_dir = output_dir / f"tvb_output_{subject_id}"
        subject_output_dir.mkdir(parents=True, exist_ok=True)
        
        tvb_files = {}
        
        # 1. Weights matrix (connectivity strengths)
        weights_file = subject_output_dir / 'weights.txt'
        np.savetxt(weights_file, connectome_matrix, fmt='%.6e', delimiter=' ')
        tvb_files['weights'] = str(weights_file)
        print(f"[{self.name}] Saved weights: {weights_file}")
        
        # 2. Tract lengths matrix
        tract_lengths_file = subject_output_dir / 'tract_lengths.txt'
        tract_lengths = self._generate_tract_lengths(connectome_matrix)
        np.savetxt(tract_lengths_file, tract_lengths, fmt='%.6e', delimiter=' ')
        tvb_files['tract_lengths'] = str(tract_lengths_file)
        print(f"[{self.name}] Saved tract lengths: {tract_lengths_file}")
        
        # 3. Region centres (3D coordinates)
        centres_file = subject_output_dir / 'centres.txt'
        centres = self._generate_centres()
        self._save_centres(centres_file, centres, subject_id)
        tvb_files['centres'] = str(centres_file)
        print(f"[{self.name}] Saved centres: {centres_file}")
        
        # 4. Region areas
        areas_file = subject_output_dir / 'areas.txt'
        areas = self._generate_areas()
        np.savetxt(areas_file, areas, fmt='%.6e')
        tvb_files['areas'] = str(areas_file)
        print(f"[{self.name}] Saved areas: {areas_file}")
        
        # 5. Cortical labels
        cortical_file = subject_output_dir / 'cortical.txt'
        cortical = self._generate_cortical_labels()
        np.savetxt(cortical_file, cortical, fmt='%d')
        tvb_files['cortical'] = str(cortical_file)
        print(f"[{self.name}] Saved cortical: {cortical_file}")
        
        # 6. Average orientations
        orientations_file = subject_output_dir / 'average_orientations.txt'
        orientations = self._generate_orientations()
        np.savetxt(orientations_file, orientations, fmt='%.6e', delimiter=' ')
        tvb_files['orientations'] = str(orientations_file)
        print(f"[{self.name}] Saved orientations: {orientations_file}")
        
        # 7. Info file
        info_file = subject_output_dir / 'info.txt'
        self._save_info_file(info_file, subject_id)
        tvb_files['info'] = str(info_file)
        print(f"[{self.name}] Saved info: {info_file}")
        
        return {'tvb_files': tvb_files}
    
    def create_tvb_zip(self, tvb_files: Dict[str, str], subject_id: str) -> Dict[str, Any]:
        """Create TVB-compatible ZIP package."""
        print(f"[{self.name}] Creating TVB ZIP package...")
        
        output_dir = Path(self._parameters['output_directory'])
        subject_output_dir = output_dir / f"tvb_output_{subject_id}"
        zip_file = subject_output_dir / f'connectivity_{subject_id}.zip'
        
        # Create ZIP file with all TVB format files
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(tvb_files['weights'], 'weights.txt')
            zf.write(tvb_files['tract_lengths'], 'tract_lengths.txt')
            zf.write(tvb_files['centres'], 'centres.txt')
            zf.write(tvb_files['areas'], 'areas.txt')
            zf.write(tvb_files['cortical'], 'cortical.txt')
            zf.write(tvb_files['orientations'], 'average_orientations.txt')
            zf.write(tvb_files['info'], 'info.txt')
        
        zip_size = zip_file.stat().st_size
        print(f"[{self.name}] TVB ZIP created: {zip_file} ({zip_size:,} bytes)")
        
        # Verify ZIP contents
        with zipfile.ZipFile(zip_file, 'r') as zf:
            zip_contents = zf.namelist()
            expected_files = ['weights.txt', 'tract_lengths.txt', 'centres.txt', 
                            'areas.txt', 'cortical.txt', 'average_orientations.txt', 'info.txt']
            
            missing_files = [f for f in expected_files if f not in zip_contents]
            if missing_files:
                raise RuntimeError(f"ZIP package missing files: {missing_files}")
        
        print(f"[{self.name}] ZIP validation passed: {len(zip_contents)} files")
        
        return {'tvb_zip_file': str(zip_file.resolve())} #provide absolute path
    
    def validate_tvb_format(self, tvb_zip_file: str) -> Dict[str, Any]:
        """Validate TVB format compatibility."""
        print(f"[{self.name}] Validating TVB format...")
        
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'tvb_compatible': False
        }
        
        tvb_connectivity = None
        
        try:
            # Try to create TVB Connectivity object
            import tempfile
            from tvb.datatypes.connectivity import Connectivity
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract ZIP to temp directory
                with zipfile.ZipFile(tvb_zip_file, 'r') as zf:
                    zf.extractall(temp_dir)
                
                # Load all TVB files
                weights = np.loadtxt(Path(temp_dir) / 'weights.txt')
                tract_lengths = np.loadtxt(Path(temp_dir) / 'tract_lengths.txt')
                areas = np.loadtxt(Path(temp_dir) / 'areas.txt')
                cortical = np.loadtxt(Path(temp_dir) / 'cortical.txt')
                orientations = np.loadtxt(Path(temp_dir) / 'average_orientations.txt')
                
                # Load centres
                centres_data = []
                region_labels = []
                with open(Path(temp_dir) / 'centres.txt', 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            region_labels.append(parts[0])
                            centres_data.append([float(parts[1]), float(parts[2]), float(parts[3])])
                
                centres = np.array(centres_data)
                region_labels = np.array(region_labels)
                
                # Create TVB Connectivity object
                tvb_connectivity = Connectivity(
                    weights=weights,
                    tract_lengths=tract_lengths,
                    centres=centres,
                    region_labels=region_labels,
                    areas=areas,
                    cortical=cortical.astype(bool),
                    orientations=orientations
                )
                
                validation_results['tvb_compatible'] = True
                print(f"[{self.name}] TVB Connectivity object created successfully")
                print(f"[{self.name}] TVB regions: {tvb_connectivity.number_of_regions}")
                
        except Exception as e:
            validation_results['valid'] = False
            validation_results['errors'].append(f"TVB compatibility test failed: {e}")
            print(f"[{self.name}] TVB validation failed: {e}")
        
        return {
            'validation_results': validation_results,
            'tvb_connectivity': tvb_connectivity
        }
    
    def finalize_output(self, tvb_zip_file: str, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize output and signal completion."""
        import time
        
        processing_time = time.time() - self._conversion_start_time if self._conversion_start_time else None
        
        conversion_metadata = {
            'subject_id': self._parameters.get('subject_id', 'unknown'),
            'n_regions': self._n_regions,
            'tvb_zip_file': tvb_zip_file,
            'processing_time': processing_time,
            'validation_results': validation_results,
            'tvb_compatible': validation_results.get('tvb_compatible', False),
            'conversion_timestamp': time.time()
        }
        
        completion_signal = validation_results.get('valid', False)
        
        if completion_signal:
            print(f"[{self.name}] 🎉 TVB conversion completed successfully!")
            print(f"[{self.name}] Output: {tvb_zip_file}")
            print(f"[{self.name}] Processing time: {processing_time:.1f} seconds")
            print(f"[{self.name}] Ready for TVB simulations!")
        else:
            print(f"[{self.name}] TVB conversion failed")
            print(f"[{self.name}] Errors: {validation_results.get('errors', [])}")
        
        return {
            'completion_signal': completion_signal,
            'conversion_metadata': conversion_metadata,
            'tvb_zip_file': tvb_zip_file
        }
    
    # ========================================================================
    # HELPER METHODS FOR TVB FORMAT GENERATION
    # ========================================================================
    
    def _generate_tract_lengths(self, weights: np.ndarray) -> np.ndarray:
        """Generate tract length matrix based on connectivity weights."""
        tract_length_factor = self._parameters['tract_length_factor']
        
        # Create tract lengths proportional to weights (with some randomness)
        np.random.seed(42)  # For reproducibility
        tract_lengths = np.zeros_like(weights)
        
        # For connected regions, generate realistic tract lengths
        connected = weights > 0
        if np.any(connected):
            # Base lengths between 5-50mm, scaled by weight
            base_lengths = np.random.uniform(5.0, 50.0, size=weights.shape)
            weight_factor = weights / np.max(weights) if np.max(weights) > 0 else 1.0
            tract_lengths[connected] = base_lengths[connected] * (0.5 + 0.5 * weight_factor[connected])
            tract_lengths *= tract_length_factor
        
        return tract_lengths
    
    def _generate_centres(self) -> np.ndarray:
        """Generate 3D coordinates for brain regions."""
        brain_center = self._parameters['brain_center']
        brain_size = self._parameters['brain_size']
        hemisphere_info = self._parameters['hemisphere_info']
        
        np.random.seed(42)  # For reproducibility
        centres = []
        
        for i in range(self._n_regions):
            # Generate points roughly in a brain-like ellipsoid
            if hemisphere_info and i < self._n_regions // 2:
                # Left hemisphere (negative x)
                x = brain_center[0] - np.random.uniform(0, brain_size[0]/2)
            else:
                # Right hemisphere (positive x)
                x = brain_center[0] + np.random.uniform(0, brain_size[0]/2)
            
            y = brain_center[1] + np.random.uniform(-brain_size[1]/2, brain_size[1]/2)
            z = brain_center[2] + np.random.uniform(-brain_size[2]/2, brain_size[2]/2)
            
            centres.append([x, y, z])
        
        return np.array(centres)
    
    def _save_centres(self, centres_file: Path, centres: np.ndarray, subject_id: str) -> None:
        """Save centres file in TVB format with region labels."""
        region_prefix = self._parameters['region_prefix']
        
        with open(centres_file, 'w') as f:
            for i, (x, y, z) in enumerate(centres):
                region_label = f"{region_prefix}_{i+1:03d}"
                f.write(f"{region_label} {x:.6f} {y:.6f} {z:.6f}\n")
    
    def _generate_areas(self) -> np.ndarray:
        """Generate region areas."""
        np.random.seed(42)  # For reproducibility
        # Generate realistic brain region areas (in mm²)
        areas = np.random.uniform(50.0, 500.0, self._n_regions)
        return areas
    
    def _generate_cortical_labels(self) -> np.ndarray:
        """Generate cortical/subcortical labels."""
        # Assume most regions are cortical (1), some subcortical (0)
        cortical = np.ones(self._n_regions, dtype=int)
        
        # Make some regions subcortical (roughly 10%)
        n_subcortical = max(1, self._n_regions // 10)
        subcortical_indices = np.random.choice(self._n_regions, n_subcortical, replace=False)
        cortical[subcortical_indices] = 0
        
        return cortical
    
    def _generate_orientations(self) -> np.ndarray:
        """Generate average orientation vectors for regions."""
        np.random.seed(42)  # For reproducibility
        
        # Generate random unit vectors
        orientations = np.random.randn(self._n_regions, 3)
        
        # Normalize to unit vectors
        norms = np.linalg.norm(orientations, axis=1, keepdims=True)
        orientations = orientations / np.maximum(norms, 1e-10)
        
        return orientations
    
    def _save_info_file(self, info_file: Path, subject_id: str) -> None:
        """Save info file with metadata."""
        with open(info_file, 'w') as f:
            f.write(f'# TVB Connectivity Info File\n')
            f.write(f'# Generated from BMCR data for subject: {subject_id}\n')
            f.write(f'# Number of regions: {self._n_regions}\n')
            f.write(f'# Generated by: BMCRToTVBNode\n')
            f.write(f'# \n')
            f.write(f'connectivity_type = "BMCR_DTI"\n')
            f.write(f'subject_id = "{subject_id}"\n')
            f.write(f'number_of_regions = {self._n_regions}\n')
            f.write(f'coordinate_system = "mm"\n')
            f.write(f'area_unit = "mm^2"\n')


# Standalone conversion function for backward compatibility
def convert_to_tvb_format(connectome_csv_path: str, subject_id: str, output_dir: str, 
                         atlas_info: Optional[Dict[str, Any]] = None) -> Path:
    """
    Standalone function to convert connectome to TVB format.
    
    This function provides the same functionality as the node but can be used independently.
    """
    # Create a temporary node instance to use its methods
    temp_node = BMCRToTVBNode("temp_conversion_node")
    temp_node._parameters.update({
        'output_directory': output_dir
    })
    
    # Load connectome
    result = temp_node.load_connectome(connectome_csv_path)
    connectome_matrix = result['connectome_matrix']
    
    # Generate TVB files
    result = temp_node.generate_tvb_files(connectome_matrix, subject_id)
    tvb_files = result['tvb_files']
    
    # Create ZIP
    result = temp_node.create_tvb_zip(tvb_files, subject_id)
    tvb_zip_file = result['tvb_zip_file']
    
    return Path(tvb_zip_file)