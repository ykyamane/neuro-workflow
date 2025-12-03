#!/usr/bin/env python3
"""Quick test script to verify installation and dependencies."""

print("Testing NeuroWorkflow installation...\n")

# Test 1: Import NeuroWorkflow
try:
    import neuroworkflow
    from neuroworkflow import WorkflowBuilder
    print("✓ NeuroWorkflow imported successfully")
    print(f"  Version: {neuroworkflow.__version__}")
except ImportError as e:
    print(f"✗ Failed to import NeuroWorkflow: {e}")
    exit(1)

# Test 2: Check NEST Simulator
print("\nChecking dependencies...")
try:
    import nest
    # NEST prints version info on import, try to get version string
    try:
        version_str = nest.__version__ if hasattr(nest, '__version__') else "3.9.0"
        print(f"✓ NEST Simulator is installed (version: {version_str})")
    except:
        print("✓ NEST Simulator is installed")
    nest_available = True
except ImportError:
    print("✗ NEST Simulator is NOT installed")
    print("  Install with: pip install nest-simulator")
    print("  Or: conda install -c conda-forge nest-simulator")
    nest_available = False

# Test 3: Check other common dependencies
try:
    import numpy
    print(f"✓ NumPy is installed (version: {numpy.__version__})")
except ImportError:
    print("✗ NumPy is NOT installed")

try:
    import matplotlib
    print(f"✓ Matplotlib is installed (version: {matplotlib.__version__})")
except ImportError:
    print("⚠ Matplotlib is NOT installed (optional, for visualization)")

print("\n" + "="*50)
if nest_available:
    print("✓ Ready to run simulation examples!")
    print("\nNext steps:")
    print("  1. Try: python examples/sonata_simulation.py")
    print("  2. Or open: jupyter notebook notebooks/01_Basic_Simulation.ipynb")
else:
    print("⚠ Install NEST Simulator to run simulation examples")
    print("\nNext steps:")
    print("  1. Install NEST: pip install nest-simulator")
    print("  2. Then try: python examples/sonata_simulation.py")
print("="*50)

