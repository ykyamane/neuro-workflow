"""
BMCR Download Node for NeuroWorkflow

This node downloads tractography data from AWS S3 and generates connectome matrices
using MRtrix3. It implements the first part of the BMCR connectome generation pipeline.

Based on: BMCR_connectome_dti.ipynb
Author: NeuroWorkflow Team
Date: 2025-11-23
Version: 1.0
"""

import os
import subprocess
import time
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


class BMCR_DTI_to_Connectome(Node):
    """
    Downloads BMCR tractography data from AWS S3 and generates connectome matrices.
    
    This node performs the following operations:
    1. Downloads tractography (.tck) files from AWS S3
    2. Downloads atlas segmentation files if needed
    3. Generates connectome matrices using MRtrix3 tck2connectome
    4. Validates the generated connectome data
    
    The node outputs the path to the generated connectome CSV file and metadata
    about the processing, which can then be used by the BMCRToTVBNode for format conversion.
    """
    
    NODE_DEFINITION = NodeDefinitionSchema(
        type='bmcr_download',
        description='Downloads BMCR tractography data from AWS and generates connectome matrices using MRtrix3',
        
        parameters={
            'subject': ParameterDefinition(
                default_value='A10-R01_0028-TT21',
                description='BMCR subject identifier (e.g., A10-R01_0028-TT21)',
                constraints={},
                optimizable=False
            ),
            
            'atlas_file': ParameterDefinition(
                default_value='./img/atlas_segmentation_BM1.nii.gz',
                description='Path to atlas segmentation file',
                constraints={},
                optimizable=False
            ),
            
            'output_directory': ParameterDefinition(
                default_value='./bmcr_data',
                description='Local directory to store downloaded and processed data',
                constraints={},
                optimizable=False
            ),
        },
        
        inputs={
            # No inputs - this is a data source node
        },
        
        outputs={
            'connectome_file': PortDefinition(
                type=PortType.STR,
                description='Path to the generated connectome CSV file'
            ),
            
            'subject_id': PortDefinition(
                type=PortType.STR,
                description='Subject identifier used for processing'
            ),
            
            'tracks_file': PortDefinition(
                type=PortType.STR,
                description='Path to the downloaded tractography file'
            ),
            
            'processing_metadata': PortDefinition(
                type=PortType.DICT,
                description='Metadata about the processing (file sizes, processing time, etc.)'
            ),
            
            'connectome_matrix': PortDefinition(
                type=PortType.OBJECT,
                description='The connectome matrix as numpy array (for validation)',
                optional=True
            ),
        },
        
        methods={
            'check_dependencies': MethodDefinition(
                description='Check if required tools (AWS CLI, MRtrix3) are available',
                inputs=[],
                outputs=['dependency_status']
            ),
            
            'download_data': MethodDefinition(
                description='Download tractography data from AWS S3',
                inputs=[],
                outputs=['tracks_file', 'download_metadata', 'subject_id']
            ),
            
            'generate_connectome': MethodDefinition(
                description='Generate connectome matrix using MRtrix3',
                inputs=['tracks_file'],
                outputs=['connectome_file', 'connectome_matrix']
            ),
            
            'validate_output': MethodDefinition(
                description='Validate the generated connectome data',
                inputs=['connectome_file', 'connectome_matrix'],
                outputs=['validation_results']
            ),
        }
    )
    
    def __init__(self, name: str):
        """Initialize the BMCR Download Node."""
        super().__init__(name)
        self._processing_start_time = None
        self._download_metadata = {}
        self._define_process_steps()
    
    def _define_process_steps(self) -> None:
        """Define the sequence of processing steps."""
        self.add_process_step(
            "check_dependencies",
            self.check_dependencies,
            method_key="check_dependencies"
        )
        
        self.add_process_step(
            "download_data",
            self.download_data,
            method_key="download_data"
        )
        
        self.add_process_step(
            "generate_connectome",
            self.generate_connectome,
            method_key="generate_connectome"
        )
        
        self.add_process_step(
            "validate_output",
            self.validate_output,
            method_key="validate_output"
        )
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check if required tools are available."""
        print(f"[{self.name}] Checking dependencies...")
        
        dependency_status = {
            'aws_cli': False,
            'mrtrix3': False,
            'all_available': False,
            'missing_tools': []
        }
        
        # Check AWS CLI
        try:
            result = subprocess.run(['aws', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                dependency_status['aws_cli'] = True
                print(f"[{self.name}] AWS CLI available: {result.stdout.strip()}")
            else:
                dependency_status['missing_tools'].append('aws-cli')
                print(f"[{self.name}] AWS CLI not working")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            dependency_status['missing_tools'].append('aws-cli')
            print(f"[{self.name}] AWS CLI not found")
        
        # Check MRtrix3
        try:
            result = subprocess.run(['tck2connectome', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                dependency_status['mrtrix3'] = True
                print(f"[{self.name}] MRtrix3 available")
            else:
                dependency_status['missing_tools'].append('mrtrix3')
                print(f"[{self.name}] MRtrix3 not working")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            dependency_status['missing_tools'].append('mrtrix3')
            print(f"[{self.name}] MRtrix3 not found")
        
        dependency_status['all_available'] = dependency_status['aws_cli'] and dependency_status['mrtrix3']
        
        if not dependency_status['all_available']:
            missing = ', '.join(dependency_status['missing_tools'])
            raise RuntimeError(f"Missing required dependencies: {missing}. "
                             f"Please install AWS CLI and MRtrix3.")
        
        print(f"[{self.name}] All dependencies available")
        return {'dependency_status': dependency_status}
    
    def download_data(self) -> Dict[str, Any]:
        """Download tractography data from AWS S3."""
        
        
        print(f"[{self.name}] Starting data download...")
        self._processing_start_time = time.time()
        
        subject = self._parameters['subject']
        # Use hardcoded defaults for AWS settings (matching original BMCR paths)
        aws_bucket = 'brainminds-marmoset-connectivity'
        aws_prefix = f'BMCR_v02/BMCR_core_data/meta_data/{subject}/meta'
        output_dir = Path(self._parameters['output_directory'])
        force_download = False  # Default to not re-downloading
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define file paths
        tracks_file = output_dir / f"{subject}.tck"
        atlas_file = Path(self._parameters['atlas_file'])
        
        download_metadata = {
            'subject': subject,
            'download_start_time': time.time(),
            'files_downloaded': [],
            'files_skipped': [],
            'download_sizes': {}
        }
        
        # Download tractography file (matching original BMCR path structure)
        s3_tracks_path = f"s3://{aws_bucket}/{aws_prefix}/track.tck"
        
        if not tracks_file.exists() or force_download:
            print(f"[{self.name}] Downloading {subject}.tck from AWS S3...")
            try:
                cmd = ['aws', 's3', 'cp', s3_tracks_path, str(tracks_file), '--no-sign-request']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    file_size = tracks_file.stat().st_size
                    download_metadata['files_downloaded'].append(str(tracks_file))
                    download_metadata['download_sizes'][str(tracks_file)] = file_size
                    print(f"[{self.name}] Downloaded {tracks_file.name} ({file_size:,} bytes)")
                else:
                    raise RuntimeError(f"AWS download failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                raise RuntimeError("AWS download timed out after 5 minutes")
        else:
            print(f"[{self.name}] {tracks_file.name} already exists, skipping download")
            download_metadata['files_skipped'].append(str(tracks_file))
        
        # Check atlas file
        if not atlas_file.exists():
            print(f"[{self.name}] Atlas file not found: {atlas_file}")
            print(f"[{self.name}] Please ensure the atlas file is available")
            # Note: We could download this from S3 too if needed
        else:
            print(f"[{self.name}] Atlas file available: {atlas_file}")
        
        download_metadata['download_end_time'] = time.time()
        download_metadata['download_duration'] = download_metadata['download_end_time'] - download_metadata['download_start_time']
        
        self._download_metadata = download_metadata
        
        print(f"[{self.name}] Data download completed in {download_metadata['download_duration']:.1f} seconds")
        
        return {
            'tracks_file': str(tracks_file),
            'download_metadata': download_metadata,
            'subject_id': subject
        }
    
    def generate_connectome(self, tracks_file: str) -> Dict[str, Any]:
        """Generate connectome matrix using MRtrix3."""
        print(f"[{self.name}] Generating connectome matrix...")
        
        subject = self._parameters['subject']
        atlas_file = self._parameters['atlas_file']
        output_dir = Path(self._parameters['output_directory'])
        connectome_type = 'count'  # Default to count-based connectome
        
        # Define output file
        connectome_file = output_dir / f"{subject}_connectome_{connectome_type}.csv"
        
        # Check if files exist
        if not Path(tracks_file).exists():
            raise FileNotFoundError(f"Tracks file not found: {tracks_file}")
        
        if not Path(atlas_file).exists():
            raise FileNotFoundError(f"Atlas file not found: {atlas_file}")
        
        # Build MRtrix3 command
        cmd = [
            'tck2connectome',
            tracks_file,
            atlas_file,
            str(connectome_file),
            '-assignment_radial_search', '2',
            '-force'  # Overwrite existing file
        ]
        
        # Add connectome type specific options
        if connectome_type == 'length':
            cmd.extend(['-scale_length'])
        elif connectome_type == 'mean_length':
            cmd.extend(['-scale_length', '-stat_edge', 'mean'])
        # 'count' is the default, no additional options needed
        
        print(f"[{self.name}] Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print(f"[{self.name}] Connectome generation completed")
                if result.stdout:
                    print(f"[{self.name}] MRtrix3 output: {result.stdout.strip()}")
            else:
                raise RuntimeError(f"MRtrix3 failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Connectome generation timed out after 10 minutes")
        
        # Load and validate the connectome
        if not connectome_file.exists():
            raise RuntimeError(f"Connectome file was not created: {connectome_file}")
        
        try:
            connectome_matrix = np.loadtxt(connectome_file, delimiter=',')
            print(f"[{self.name}] Connectome matrix loaded: {connectome_matrix.shape}")
            print(f"[{self.name}] Non-zero connections: {np.sum(connectome_matrix > 0)}")
            print(f"[{self.name}] Connection density: {np.sum(connectome_matrix > 0) / (connectome_matrix.shape[0]**2) * 100:.2f}%")
        except Exception as e:
            raise RuntimeError(f"Failed to load connectome matrix: {e}")
        
        return {
            'connectome_file': str(connectome_file),
            'connectome_matrix': connectome_matrix
        }
    
    def validate_output(self, connectome_file: str, connectome_matrix: np.ndarray) -> Dict[str, Any]:
        """Validate the generated connectome data."""
        print(f"[{self.name}] Validating connectome output...")
        
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'statistics': {}
        }
        
        # Check file exists
        if not Path(connectome_file).exists():
            validation_results['valid'] = False
            validation_results['errors'].append(f"Connectome file not found: {connectome_file}")
            return {'validation_results': validation_results}
        
        # Check matrix properties
        if connectome_matrix.ndim != 2:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Matrix is not 2D: {connectome_matrix.ndim}")
        
        if connectome_matrix.shape[0] != connectome_matrix.shape[1]:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Matrix is not square: {connectome_matrix.shape}")
        
        # Check for reasonable number of regions
        n_regions = connectome_matrix.shape[0]
        if n_regions < 10:
            validation_results['warnings'].append(f"Very few regions: {n_regions}")
        elif n_regions > 2000:
            validation_results['warnings'].append(f"Very many regions: {n_regions}")
        
        # Check diagonal (should be zero for connectivity)
        diagonal_sum = np.sum(np.diag(connectome_matrix))
        if diagonal_sum > 0:
            validation_results['warnings'].append(f"Non-zero diagonal elements: {diagonal_sum}")
        
        # Check for negative values
        if np.any(connectome_matrix < 0):
            validation_results['warnings'].append("Matrix contains negative values")
        
        # Calculate statistics
        validation_results['statistics'] = {
            'shape': connectome_matrix.shape,
            'total_connections': int(np.sum(connectome_matrix > 0)),
            'density': float(np.sum(connectome_matrix > 0) / (n_regions**2)),
            'mean_strength': float(np.mean(connectome_matrix[connectome_matrix > 0])) if np.any(connectome_matrix > 0) else 0.0,
            'max_strength': float(np.max(connectome_matrix)),
            'file_size_bytes': Path(connectome_file).stat().st_size
        }
        
        # Compile processing metadata
        processing_metadata = {
            'subject': self._parameters['subject'],
            'connectome_type': 'count',
            'processing_time': time.time() - self._processing_start_time if self._processing_start_time else None,
            'download_metadata': self._download_metadata,
            'validation_results': validation_results
        }
        
        if validation_results['valid']:
            print(f"[{self.name}] Validation passed")
        else:
            print(f"[{self.name}] Validation failed: {validation_results['errors']}")
        
        if validation_results['warnings']:
            print(f"[{self.name}] Warnings: {validation_results['warnings']}")
        
        return {
            'validation_results': validation_results,
            'processing_metadata': processing_metadata
        }


def create_connectome(tracks_file: str, atlas_file: str, output_file: str, connectome_type: str = 'count') -> None:
    """
    Standalone function to create connectome (for backward compatibility).
    
    This function provides the same functionality as the node's generate_connectome method
    but can be used independently.
    """
    cmd = [
        'tck2connectome',
        tracks_file,
        atlas_file,
        output_file,
        '-assignment_radial_search', '2',
        '-force'
    ]
    
    if connectome_type == 'length':
        cmd.extend(['-scale_length'])
    elif connectome_type == 'mean_length':
        cmd.extend(['-scale_length', '-stat_edge', 'mean'])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"MRtrix3 failed: {result.stderr}")
    
    print(f"Connectome created: {output_file}")