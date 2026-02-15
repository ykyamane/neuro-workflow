"""
Node for set the visualization of a TVB simulation. up and run the simulation. The simulator is created as an iterable object, so all we need to do is iterate for some length, which we provide in ms, and collect the output.
"""

import h5py
import numpy as np
import nibabel as nib
import vneumodpy as vnm

from typing import Dict, Any, Optional
from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition
from neuroworkflow.core.port import PortType


class VNMGlmAnalysisNode(Node):
    """Node for GLM analysis of Virtual Neuromodulation (Group Surrogate model)."""
    
    NODE_DEFINITION = NodeDefinitionSchema(
        type='analysis_node',
        description='GLM analysis of the Virtual Neuromodulation',
        
        parameters={
            'atlas_file': ParameterDefinition(
                default_value='',
                description='Cube ROI atlas file (.nii.gz)'
            ),
            'result_nifti_path': ParameterDefinition(
                default_value='.',
                description='2nd level GLM analysis result (NIfTI file) path',
            ),
            'tukey_taper_size': ParameterDefinition(
                default_value='8',
                description='Tukey-taper size for GLM analysis',
            ),
            'number_of_jobs': ParameterDefinition(
                default_value='8',
                description='number of multiprocessing jobs for GLM analysis',
            ),
            'simulation_name': ParameterDefinition(
                default_value='',
                description='(for DEBUG) unique simulation name of virtual neuromodulation',
            ),
            'target_ROI': ParameterDefinition(
                default_value='',
                description='(for DEBUG) Modulation target ROI numbers',
            ),
            'trial_mat_file': ParameterDefinition(
                default_value='',
                description='(for DEBUG) virtual neuromodulation result file (.mat)',
            ),
            'chrf_mat_file': ParameterDefinition(
                default_value='',
                description='(for DEBUG) Chrf file (.mat)',
            ),
        },
        
        inputs={
            'simulation_name': PortDefinition(
                type=PortType.STR,
                description='unique simulation name of virtual neuromodulation'
            ),
            'trials': PortDefinition(
                type=PortType.LIST,
                description='Virtual neuromodulation trial results'
            ),
            'Chrf': PortDefinition(
                type=PortType.OBJECT,
                description='Canonical Hemodynamic Response Function used by GLM analysis'
            )
        },
        
        outputs={
            'glm_volumes': PortDefinition(
                type=PortType.OBJECT,
                description='list of 2nd level GLM analysis result'
            )
        },
        
        methods={
            'glm_analysis': MethodDefinition(
                description='2nd level GLM analysis of the Virtual Neuromodulation',
                inputs=['simulation_name','trials','Chrf'],
                outputs=[]
            ),
        }
    )
    def __init__(self, name: str):
        """Initialize the Virtual Neuromodulation (Group Surrogate model) Node.
        
        Args:
            name: Name of the node
        """
        super().__init__(name)
        self._define_process_steps()
    
    def _define_process_steps(self) -> None:
        """Define the process steps for this node."""
        self.add_process_step(
            "glm_analysis",
            self.glm_analysis,
            method_key="glm_analysis"
        )
        
    def glm_analysis(self, simulation_name: Dict[str, Any], trials: Dict[str, Any],
                 Chrf: Dict[str, Any]) -> Dict[str, Any]:
        """2nd level GLM analysis of the Virtual Neuromodulation.
        Returns:
            List of 2nd level GLM analysis result
        """
        if trials is None:
            trial_mat_file = self._parameters["trial_mat_file"]  # for DEBUG
            target_ROI = int(self._parameters["target_ROI"])  # for DEBUG
            if len(trial_mat_file) == 0:
                raise ValueError("trials input not set")
            print('(DEBUG) loading trial mat file : ' + trial_mat_file)
            S = []
            dic = h5py.File(trial_mat_file, 'r')
            cx = dic['S']
            for j in range(len(cx)):
                hdf5ref = cx[j, 0]
                x = dic[hdf5ref]
                S.append(np.array(np.squeeze(x)).T)  # hmm...we need squeeze here.
            S_rois = [None] * 1
            S_rois[0] = [S, target_ROI]
            trials = [S_rois]
            dic.close()
        if len(trials) == 0:
            raise ValueError("trials input not set")
        if Chrf is None:
            chrf_mat_file = self._parameters["chrf_mat_file"]  # for DEBUG
            if len(chrf_mat_file) == 0:
                raise ValueError("chrf input not set")
            print('(DEBUG) loading Chrf mat file : ' + chrf_mat_file)
            Chrf = []
            dic = h5py.File(chrf_mat_file, 'r')
            cx = dic['Chrf']
            for j in range(len(cx)):
                hdf5ref = cx[j, 0]
                x = dic[hdf5ref]
                Chrf.append(np.array(x).T)
        if simulation_name is None:
            simulation_name = self._parameters["simulation_name"]  # for DEBUG

        result_nifti_path = self._parameters["result_nifti_path"]
        atlas_file = self._parameters["atlas_file"]
        tuM = int(self._parameters["tukey_taper_size"])  # GLM tukey-taper size
        njobs = int(self._parameters["number_of_jobs"])

        print(f"Loading Cube ROI atlas : {atlas_file}")
        atlasDat = nib.load(atlas_file)
        atlasV = atlasDat.get_fdata()
        atlasV = vnm.adjust_volume_dir(atlasV, atlasDat)

        glmVs = []
        for i in range(len(trials)):
            S_rois = trials[i]
            V_rois = []
            for j in range(len(S_rois)):
                S = S_rois[j][0]
                roi = S_rois[j][1]
                surrNum = len(S)

                # calc 1st-level GLM
                print('calc 1st-level GLM. trial=' +str(i)+', target roi=' +str(roi))
                bmatC = [None] * surrNum
                for k in range(surrNum):
                    Xorg = Chrf[k]
                    Xt = np.concatenate([Xorg, np.ones((Xorg.shape[0], 1), dtype=np.float32)], 1)
                    Sk = np.squeeze(S[k])
                    B2, RSS, df, _, _ = vnm.tukey_mp(Sk.T, Xt, tuM=tuM, isOutX2is=False)
                    bmatC[k] = B2

                # calc 2nd-level estimation
                print('calc 2nd-level GLM...')
                B1 = bmatC[0][:, [0, 1]].T
                X2 = np.eye(B1.shape[0])
                for k in range(1, surrNum):
                    # 2nd-level Y vector
                    B2 = bmatC[k][:, [0, 1]].T  # include design and intercept(we need more than 8 length for tukey taper)
                    B1 = np.concatenate([B1, B2], 0)

                    # 2nd-level design matrix
                    X2 = np.concatenate([X2, np.eye(B2.shape[0])], 0)

                B1[np.isnan(B1)] = 0  # there might be nan

                # calc 2nd-level estimation
                B, RSS, df, X2is, tRs = vnm.tukey_mp(B1, X2, tuM=tuM, isOutX2is=True, n_jobs=njobs)

                # GLM contrast images
                contrasts = [np.array([1, 0]).T]  # GLM contrust
                Ts = vnm.contrast_image(contrasts, B, RSS, X2is, tRs)  # this is fast enough
                V2 = vnm.roi_ts_to4dimage(Ts[0], atlasV)  # returns 4D image. this is slow
                V2 = np.squeeze(V2)

                # output nifti file
                V2 = vnm.adjust_volume_dir(V2.astype(np.float32), atlasDat)
                nifti_image = nib.Nifti1Image(V2, atlasDat.affine)
                sessionName = simulation_name + '_' + str(roi) + 'sr' + str(surrNum) + 'pr' + str(i + 1)
                outniiname = result_nifti_path + '/' + sessionName + '_2nd-Tukey' + str(tuM) + '.nii.gz'
                nib.save(nifti_image, outniiname)
                print('save nifti file : ' + outniiname)

                V_rois.append([V2, roi])
            glmVs.append(V_rois)

        return {"glm_volumes": glmVs}
