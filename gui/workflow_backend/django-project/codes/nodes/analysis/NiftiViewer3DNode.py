"""
Generic interactive 3D NIfTI viewer node using ipyniivue (WebGL).

Accepts a list of NIfTI file paths and displays them in an interactive
3D WebGL viewer embedded in the Jupyter notebook cell.
An optional background image (e.g. atlas) can be set via parameter.

Requires: pip install ipyniivue
"""

import os
from IPython.display import display
from typing import Dict, Any, List

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition
from neuroworkflow.core.port import PortType


class NiftiViewer3DNode(Node):
    """Interactive 3D NIfTI viewer using ipyniivue (WebGL, no extension needed)."""

    NODE_DEFINITION = NodeDefinitionSchema(
        type='nifti_viewer_3d',
        description='Interactively visualize one or more NIfTI files in a 3D WebGL viewer embedded in a Jupyter cell',

        parameters={
            'file_path': ParameterDefinition(
                default_value='',
                description='Fallback NIfTI file path+name used when no input port is connected'
            ),
            'bg_img': ParameterDefinition(
                default_value='',
                description=(
                    'Optional background image path+name (e.g. a T1 MRI .nii.gz) displayed '
                    'in grayscale beneath the overlay. For best 3D rendering use an anatomical '
                    'MRI, not a discrete ROI atlas (which renders as a solid cube).'
                )
            ),
            'cal_min': ParameterDefinition(
                default_value=0.0,
                description=(
                    'Minimum intensity value shown in the viewer (float). '
                    'Voxels below this value are fully transparent in the 3D render and slices. '
                    '0.0 (default) = auto-scale: shows all values, works for any NIfTI file. '
                    'Set above 0 to threshold. Examples by data type:\n'
                    '  GLM t-statistic map: 1.5 (weak-to-strong), 2.0 (moderate, ~p<0.05), 3.0 (strong only)\n'
                    '  Structural MRI (T1/T2): 0.0 (show all) or a small noise floor value e.g. 50.0\n'
                    '  Probability / FA map (0-1 range): 0.0 (show all) or 0.2 to hide near-zero noise\n'
                    '  Raw BOLD fMRI: 0.0 (auto) — values are in thousands, do not threshold'
                ),
                constraints={'min': 0.0}
            ),
            'cal_max': ParameterDefinition(
                default_value=0.0,
                description=(
                    'Maximum intensity value shown in the viewer (float). '
                    'Values above this are clamped to the brightest colormap color. '
                    '0.0 (default) = auto-scale: uses the data maximum, works for any NIfTI file. '
                    'Set above 0 to fix the color scale upper bound. Examples by data type:\n'
                    '  GLM t-statistic map: 8.0 (typical upper bound for t-values)\n'
                    '  Structural MRI (T1): 1200.0 (typical white matter peak in HU-like units)\n'
                    '  Probability / FA map (0-1 range): 1.0\n'
                    '  Raw BOLD fMRI: 0.0 (auto) — let the viewer scale to the data'
                ),
                constraints={'min': 0.0}
            ),
            'show_colorbar': ParameterDefinition(
                default_value=True,
                description='Show colorbar legend mapping colors to intensity values'
            ),
            'show_3d_render': ParameterDefinition(
                default_value=True,
                description=(
                    'Show the 3D volume render panel alongside the orthogonal slices. '
                    'Set to False to show only the axial/sagittal/coronal slice panels, '
                    'which is useful when no anatomical background is available.'
                )
            ),
        },

        inputs={
            'nifti_files': PortDefinition(
                type=PortType.LIST,
                description='List of NIfTI file paths (full path + filename) to overlay. Optional — falls back to file_path parameter.',
                optional=True
            )
        },

        outputs={
            'visualization_completed': PortDefinition(
                type=PortType.BOOL,
                description='True when the 3D viewer has been displayed successfully'
            )
        },

        methods={
            'visualize': MethodDefinition(
                description='Display NIfTI files in an interactive 3D WebGL viewer using ipyniivue',
                inputs=['nifti_files'],
                outputs=['visualization_completed']
            )
        }
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step(
            "visualize",
            self.visualize,
            method_key="visualize"
        )

    def visualize(self, nifti_files: List[str] = None) -> Dict[str, Any]:
        """Load and display NIfTI files in an interactive 3D WebGL viewer.

        Priority for overlay files:
            1. nifti_files input port
            2. file_path parameter (single file fallback)

        Background image (optional):
            Set bg_img parameter to a NIfTI path (ideally a T1 MRI, not a
            discrete atlas). Rendered in grayscale beneath all overlays.

        Intensity windowing (cal_min / cal_max):
            Controls which voxel values are visible. In the 3D render, voxels
            below cal_min are transparent — useful for thresholding GLM maps
            so only significant activations appear in 3D. Leave empty for auto.

        Args:
            nifti_files: list of NIfTI file paths from input port, or None

        Returns:
            visualization_completed flag
        """
        try:
            from ipyniivue import NiiVue
        except ImportError:
            raise ImportError(
                f"[{self.name}] ipyniivue is not installed. Run: pip install ipyniivue"
            )

        # --- Resolve overlay paths ---
        if nifti_files is not None and len(nifti_files) > 0:
            overlay_paths = nifti_files
            print(f"[{self.name}] Using nifti_files input port ({len(overlay_paths)} file(s))")
        else:
            file_path = self._parameters['file_path']
            if not file_path:
                raise ValueError(
                    f"[{self.name}] No input provided: connect the nifti_files port "
                    "or set the file_path parameter"
                )
            overlay_paths = [file_path]
            print(f"[{self.name}] Using file_path parameter: {file_path}")

        # --- Read parameters (0.0 = auto-scale sentinel) ---
        cal_min_raw = self._parameters['cal_min']    # float, 0.0 = auto
        cal_max_raw = self._parameters['cal_max']    # float, 0.0 = auto
        cal_min = cal_min_raw if cal_min_raw > 0.0 else None
        cal_max = cal_max_raw if cal_max_raw > 0.0 else None
        show_colorbar = self._parameters['show_colorbar']    # bool
        show_3d_render = self._parameters['show_3d_render']  # bool

        # --- Build volumes list ---
        volumes = []
        bg_path = self._parameters['bg_img'].strip()

        if bg_path:
            print(f"[{self.name}] Loading background: {bg_path}")
            volumes.append({
                "path": bg_path,
                "colormap": "gray",
                "opacity": 1.0
            })

        overlay_cmaps = ["hot", "cool", "spring", "summer", "winter", "plasma"]
        for i, path in enumerate(overlay_paths):
            print(f"[{self.name}] Loading overlay: {path}")
            vol_entry = {
                "path": path,
                "colormap": overlay_cmaps[i % len(overlay_cmaps)],
                "opacity": 0.7 if (bg_path or i > 0) else 1.0
            }
            if cal_min is not None:
                vol_entry["cal_min"] = cal_min
            if cal_max is not None:
                vol_entry["cal_max"] = cal_max
            volumes.append(vol_entry)

        if not volumes:
            raise ValueError(f"[{self.name}] No volumes loaded.")

        # --- Display 3D viewer ---
        print(f"[{self.name}] Displaying 3D viewer...")
        nv = NiiVue(is_colorbar=show_colorbar)

        if not show_3d_render:
            # MULTIPLANAR without render panel: slice_type 3 = multiplanar,
            # hide the 3D panel by disabling it
            nv.opts.multiplanar_show_render = False

        nv.load_volumes(volumes)
        display(nv)

        return {"visualization_completed": True}
