"""
Generic interactive NIfTI viewer node using ipywidgets + matplotlib.

Accepts a list of NIfTI file paths and displays them as overlaid slices
in an interactive Jupyter widget (axis selector + slice slider).
An optional background image (e.g. atlas) can be set via parameter.

Requires: %matplotlib inline in the notebook.
"""

import os
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets

from typing import Dict, Any, List

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition
from neuroworkflow.core.port import PortType


class NiftiViewerNode(Node):
    """Interactive NIfTI viewer: overlays N files with axis/slice controls."""

    NODE_DEFINITION = NodeDefinitionSchema(
        type='nifti_viewer',
        description='Interactively visualize one or more NIfTI files as overlaid slices in a Jupyter cell',

        parameters={
            'file_path': ParameterDefinition(
                default_value='',
                description='Fallback NIfTI file path+name used when no input port is connected'
            ),
            'bg_img': ParameterDefinition(
                default_value='',
                description=(
                    'Optional background image path+name (e.g. atlas or T1 MRI .nii.gz) '
                    'displayed in grayscale beneath the overlays.'
                )
            ),
            'cal_min': ParameterDefinition(
                default_value=0.0,
                description=(
                    'Minimum intensity value shown in the viewer (float). '
                    'Voxels below this value are clipped to transparent in the slice display. '
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
                description='True when the viewer has been displayed successfully'
            )
        },

        methods={
            'visualize': MethodDefinition(
                description='Display NIfTI files as interactive overlaid slices',
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
        """Load and display NIfTI files as interactive overlaid slices.

        Priority for overlay files:
            1. nifti_files input port
            2. file_path parameter (single file fallback)

        Background image (optional):
            Set bg_img parameter to a NIfTI path. Rendered in grayscale
            beneath all overlays.

        Args:
            nifti_files: list of NIfTI file paths from input port, or None

        Returns:
            visualization_completed flag
        """
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

        # --- Load background image (optional) ---
        volumes = []   # list of (numpy_array, label, cmap, alpha)
        bg_path = self._parameters['bg_img']
        if bg_path:
            print(f"[{self.name}] Loading background image: {bg_path}")
            bg_vol = nib.load(bg_path).get_fdata()
            volumes.append((bg_vol, os.path.basename(bg_path), 'gray', 1.0))

        # --- Read display parameters (0.0 = auto-scale sentinel) ---
        cal_min_raw = self._parameters['cal_min']
        cal_max_raw = self._parameters['cal_max']
        cal_min = cal_min_raw if cal_min_raw > 0.0 else None
        cal_max = cal_max_raw if cal_max_raw > 0.0 else None
        show_colorbar = self._parameters['show_colorbar']  # bool

        # --- Load overlay volumes ---
        overlay_cmaps = ['hot', 'cool', 'spring', 'summer', 'winter', 'plasma']
        for i, path in enumerate(overlay_paths):
            print(f"[{self.name}] Loading overlay: {path}")
            vol = nib.load(path).get_fdata()
            cmap = overlay_cmaps[i % len(overlay_cmaps)]
            # First overlay is fully opaque if no background, translucent otherwise
            alpha = 0.6 if bg_path or i > 0 else 1.0
            volumes.append((vol, os.path.basename(path), cmap, alpha))

        if not volumes:
            raise ValueError(f"[{self.name}] No volumes loaded.")

        # --- Determine slider range (max across all volumes and all axes) ---
        max_dim = max(max(v[0].shape) for v in volumes) - 1
        init_slice = max_dim // 2

        # --- Ensure inline backend so plots render inside the notebook cell ---
        from IPython import get_ipython
        ip = get_ipython()
        if ip is not None:
            ip.run_line_magic('matplotlib', 'inline')

        print(f"[{self.name}] Displaying interactive viewer...")

        # --- Build controls ---
        axis_w = widgets.Dropdown(
            options=['axial', 'sagittal', 'coronal'],
            value='axial',
            description='Axis:'
        )
        slice_w = widgets.IntSlider(
            min=0, max=max_dim, value=init_slice,
            description='Slice:',
            continuous_update=False
        )
        # One checkbox per volume for visibility toggle
        check_widgets = [
            widgets.Checkbox(value=True, description=label, indent=False)
            for (_, label, _, _) in volumes
        ]

        out = widgets.Output()

        def _update(*args):
            with out:
                out.clear_output(wait=True)
                fig, ax = plt.subplots(figsize=(7, 6))
                ax.set_facecolor('black')

                axis = axis_w.value
                slice_idx = slice_w.value

                for i, (vol, label, cmap, alpha) in enumerate(volumes):
                    if not check_widgets[i].value:
                        continue
                    if axis == 'axial':
                        idx = min(slice_idx, vol.shape[2] - 1)
                        slc = vol[:, :, idx].T
                    elif axis == 'sagittal':
                        idx = min(slice_idx, vol.shape[0] - 1)
                        slc = vol[idx, :, :].T
                    else:  # coronal
                        idx = min(slice_idx, vol.shape[1] - 1)
                        slc = vol[:, idx, :].T

                    # Background always auto-scales; overlays use cal_min/cal_max
                    # (None = auto when user left defaults at 0.0)
                    is_bg = (bg_path and i == 0)
                    vmin = None if is_bg else cal_min
                    vmax = None if is_bg else cal_max

                    # Mask voxels below cal_min so they are truly transparent
                    # (without masking, sub-threshold voxels render as the darkest
                    # colormap color and obscure the background)
                    if vmin is not None and not is_bg:
                        slc = np.ma.masked_where(slc < vmin, slc)

                    im = ax.imshow(slc, cmap=cmap, alpha=alpha, origin='lower',
                                   aspect='auto', vmin=vmin, vmax=vmax)

                    if show_colorbar and not is_bg:
                        fig.colorbar(im, ax=ax, fraction=0.03, pad=0.01, label=label)

                ax.set_title(f'{axis.capitalize()} — slice {slice_idx}', color='white')
                ax.axis('off')
                fig.patch.set_facecolor('black')
                plt.tight_layout()
                plt.show()
                plt.close(fig)

        # Attach observers
        axis_w.observe(_update, names='value')
        slice_w.observe(_update, names='value')
        for w in check_widgets:
            w.observe(_update, names='value')

        # Layout: controls on left, checkboxes on right
        layers_box = widgets.VBox(
            [widgets.Label(value='Layers:')] + check_widgets
        )
        controls_box = widgets.HBox([
            widgets.VBox([axis_w, slice_w]),
            layers_box
        ])

        from IPython.display import display as ipy_display
        ipy_display(widgets.VBox([controls_box, out]))

        # Trigger initial render
        _update()

        return {"visualization_completed": True}
