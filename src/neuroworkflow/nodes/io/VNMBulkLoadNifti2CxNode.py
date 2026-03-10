"""
Virtual Neuromodulation (Group Surrogate model) nifti file to ROI time-series (CX) nodes.

This module provides nodes for loading data of Virtual Neuromodulation.
"""

import os
import numpy as np
import nibabel as nib
import glob
import vneumodpy as vnm
import hdf5storage
from scipy.ndimage import gaussian_filter

from typing import Dict, Any, List, Tuple
from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition
from neuroworkflow.core.port import PortType


class VNMBulkLoadNifti2CxNode(Node):
    """Virtual Neuromodulation (Group Surrogate model) Data loader node."""
    
    NODE_DEFINITION = NodeDefinitionSchema(
        type='4d_nifti_to_cx_bulk_loader',
        description='Loads 4D Nifti files to generate ROI time-series (CX)',
        parameters={
            'nifti_files': ParameterDefinition(
                default_value='',
                description='Nifti file path string (i.e. <path>/*.nii.gz)'
            ),
            'atlas_file': ParameterDefinition(
                default_value='',
                description='Cube ROI atlas file (.nii.gz)'
            ),
            'smooth': ParameterDefinition(
                default_value=3.4,
                description='Spatial smoothing size for each volume'
            ),
            'cut_first_vol': ParameterDefinition(
                default_value=10,
                description='Number of initial cuts in the fMRI volume'
            ),
            'nuisance': ParameterDefinition(
                default_value="gmacomp",
                description='nuisance removal method for fMRI time-series'
            ),
            'csf_file': ParameterDefinition(
                default_value='',
                description='CSF file (.nii.gz) for aCompCor nuisance removal'
            ),
            'white_file': ParameterDefinition(
                default_value='',
                description='White matter file (.nii.gz) for aCompCor nuisance removal'
            ),
            'glsig_file': ParameterDefinition(
                default_value='',
                description='Global signal mask file (.nii.gz) for nuisance regression out'
            ),
            'cx_file': ParameterDefinition(
                default_value='',
                description='(option) save file name of subject multivariate time-series data file (.mat)'
            ),
        },
        outputs={
            'CX': PortDefinition(
                type=PortType.LIST,
                description='Subject multivariate time-series data'
            ),
            'fnames': PortDefinition(
                type=PortType.LIST,
                description='Subject file name list'
            ),
            'atlasV': PortDefinition(
                type=PortType.OBJECT,
                description='Cube ROI atlas'
            )
        },
        methods={
            'initialize_atlas': MethodDefinition(
                description='Load Cube ROI atlas',
                inputs=[],
                outputs=['atlasV']
            ),
            'initialize_cx': MethodDefinition(
                description='Initialize Subject multivariate time-series data',
                inputs=[],
                outputs=['CX', 'fnames']
            )
        }
    )
    
    def __init__(self, name: str):
        """Initialize Virtual Neuromodulation (Group Surrogate model).
        
        Args:
            name: Name of the node
        """
        super().__init__(name)
        self._define_process_steps()
            
        
    def _define_process_steps(self) -> None:
        """Define process steps for this node."""
        # With the new schema, we can use method_key to link directly to NODE_DEFINITION methods
        self.add_process_step(
            "initialize_atlas",
            self.initialize_atlas,
            method_key="initialize_atlas"
        )

        self.add_process_step(
            "initialize_cx",
            self.initialize_cx,
            method_key="initialize_cx"
        )


    def initialize_atlas(self) -> Dict[str, Any]:
        """Initialize Cube ROI atlas."""
        atlas_file = self._parameters["atlas_file"]
        print(f"Loading Cube ROI atlas : {atlas_file}")

        atlasDat = nib.load(atlas_file)
        atlasV = atlasDat.get_fdata()
        atlasV = vnm.adjust_volume_dir(atlasV, atlasDat)

        return {"atlasV": atlasV}

    def initialize_cx(self) -> Dict[str, Any]:
        """Initialize parameters."""
        atlasV = self._output_ports["atlasV"].value
        smooth = self._parameters["smooth"]
        cut_vol = self._parameters["cut_first_vol"]
        nuisance = self._parameters["nuisance"]
        nifti_files = self._parameters["nifti_files"]
        csf_file = self._parameters["csf_file"]
        white_file = self._parameters["white_file"]
        glsig_file = self._parameters["glsig_file"]
        cx_file = self._parameters["cx_file"]
        print(f"Loading nifti files: {nifti_files}")

        # gaussian filter
        FWHM = [smooth, smooth, smooth]  # voxel size
        sigma = np.array(FWHM) / np.sqrt(8 * np.log(2))
        filterSize = 2 * np.ceil(2 * sigma).astype(int) + 1

        # for Nuisance Signal Regression
        dat = nib.load(csf_file)
        csfV = dat.get_fdata() # uint8 is changed to [0 1] range
        csfV = vnm.adjust_volume_dir(csfV, dat)
        dat = nib.load(white_file)
        wmV = dat.get_fdata() # uint8 is changed to [0 1] range
        wmV = vnm.adjust_volume_dir(wmV, dat)
        dat = nib.load(glsig_file)
        gsV = dat.get_fdata() # uint8 is changed to [0 1] range
        gsV = vnm.adjust_volume_dir(gsV, dat)
        gsV[gsV>0] = 1

        CX = []
        fnames = []
        niflist = glob.glob(nifti_files)
        for i in range(len(niflist)):
            name = os.path.basename(niflist[i]).split('.')[0]
            fnames.append(name)

            print(f"loading {niflist[i]} ...")
            dat = nib.load(niflist[i])
            V = dat.get_fdata()
            V = vnm.adjust_volume_dir(V, dat)
            del dat

            # cut first volumes
            if cut_vol > 0:
                print(f"{V.shape[3]} volumes. cut first {cut_vol} volumes.")
                V = V[:, :, :, cut_vol:]

            # gaussian filter
            if smooth > 0:
                print(f'smoothing sz={smooth}, sigma={sigma[0]}, flSz={filterSize[0]}')
                for k in range(V.shape[3]):
                    V[:, :, :, k] = gaussian_filter(V[:, :, :, k], sigma=sigma,
                                                truncate=((filterSize[0] - 1) / 2) / sigma[0])

            # to confirm smoothing compatibility with MATLAB
            # V2 = vnm.adjust_volume_dir(V, dat)
            # nifti_image = nib.Nifti1Image(V2, dat.affine)
            # nib.save(nifti_image, "out"+str(i)+".nii.gz")

            # nuisance regression out
            if len(nuisance) > 0:
                if nuisance == "gmacomp":
                    # get Nuisance time-series (Global Mean, CSF comps, WM comps)
                    Sd = vnm.nuisance_mean_time_series(V)
                    aComp = vnm.nuisance_acompcor(V, csfV, wmV, Sd=Sd)  # this is slightly diff from MATLAB
                    Xn = np.concatenate([Sd, aComp], axis=1)
                    # sio.savemat('xn0.mat', {'Xn': Xn})  # for debug
                V = vnm.nuisance_regression_out(V, Xn, gsV)

            # ROI time-series from rs-fMRI
            X = vnm.roi_ts_from4dimage(V, atlasV, operation='mean')  # this is slow
            del V
            Xm = np.nanmean(X,1)
            X = X - np.tile(np.reshape(Xm,[-1,1]), (1, X.shape[1]))
            # sio.savemat('X'+str(i)+'.mat', {'X': X})  # for debug
            CX.append(X)
            del X, Xm

        if len(cx_file) > 0:
            hdf5storage.savemat(cx_file, {'CX': CX, 'fnames': fnames})

        return {"CX": CX, 'fnames': fnames}
