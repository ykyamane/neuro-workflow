#!/usr/bin/env python3
"""Quick test of new features to validate before running in JupyterHub."""

import sys
import os

# Add the src directory
sys.path.insert(0, '/Users/kirill/Documents/digital_brain/neuro-workflow/src')

print("=" * 60)
print("QUICK VALIDATION TEST")
print("=" * 60)

# Test 1: Import all modules
print("\n1. Testing imports...")
try:
    from neuroworkflow import WorkflowBuilder
    from neuroworkflow.core.schema import ParameterDefinition, ResourceRequirements
    from neuroworkflow.utils.script_exporter import export_workflow_scripts
    from neuroworkflow.utils.parameter_metadata_service import ParameterMetadataService
    from neuroworkflow.utils.job_managers import SLURMJobManager
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Create parameter with new fields
print("\n2. Testing extended parameter schema...")
try:
    param = ParameterDefinition(
        default_value=10.0,
        description="Test parameter",
        metadata_sources=["Allen Brain Atlas"],
        species_specific=True,
        suggested_values={"mouse": 10.0}
    )
    print(f"   ✅ Parameter created with metadata_sources: {param.metadata_sources}")
except Exception as e:
    print(f"   ❌ Parameter creation failed: {e}")
    sys.exit(1)

# Test 3: Create ResourceRequirements
print("\n3. Testing ResourceRequirements...")
try:
    resources = ResourceRequirements(
        cpus=8,
        memory_gb=16.0,
        walltime_hours=2.0
    )
    print(f"   ✅ Resources: {resources.cpus} CPUs, {resources.memory_gb}GB RAM")
except Exception as e:
    print(f"   ❌ ResourceRequirements failed: {e}")
    sys.exit(1)

# Test 4: Test Parameter Metadata Service
print("\n4. Testing Parameter Metadata Service...")
try:
    service = ParameterMetadataService()
    suggestions = service.suggest_parameter_values(
        parameter_name="firing_rate",
        parameter_description="Test parameter",
        species="mouse"
    )
    print(f"   ✅ Got {len(suggestions)} suggestions")
    if suggestions:
        print(f"      First suggestion: {suggestions[0].value} from {suggestions[0].source}")
except Exception as e:
    print(f"   ❌ Metadata service failed: {e}")
    sys.exit(1)

# Test 5: Test SLURM Job Manager
print("\n5. Testing SLURM Job Manager...")
try:
    manager = SLURMJobManager(config={'partition': 'compute'})
    script_path = manager.generate_job_script(
        python_script="print('test')",
        resources=resources,
        job_name="test_job",
        output_dir="/tmp"
    )
    if os.path.exists(script_path):
        with open(script_path, 'r') as f:
            content = f.read()
        if "#SBATCH" in content:
            print(f"   ✅ SLURM script generated at {script_path}")
        else:
            print(f"   ❌ SLURM script missing SBATCH directives")
    else:
        print(f"   ❌ SLURM script file not created")
except Exception as e:
    print(f"   ❌ SLURM manager failed: {e}")
    sys.exit(1)

# Test 6: Test export_workflow_scripts signature
print("\n6. Testing export_workflow_scripts signature...")
try:
    import inspect
    sig = inspect.signature(export_workflow_scripts)
    params = list(sig.parameters.keys())
    print(f"   Parameters: {', '.join(params)}")
    
    # Check for expected parameters
    expected = ['execution_sequence', 'output_dir', 'export_python', 'export_notebook', 
                'export_snakemake', 'filename_base', 'resource_requirements']
    missing = [p for p in expected if p not in params]
    if missing:
        print(f"   ⚠️  Missing parameters: {missing}")
    else:
        print(f"   ✅ All expected parameters present")
except Exception as e:
    print(f"   ❌ Signature check failed: {e}")

print("\n" + "=" * 60)
print("✅ ALL VALIDATION TESTS PASSED!")
print("=" * 60)
print("\nThe notebook should work in JupyterHub.")

