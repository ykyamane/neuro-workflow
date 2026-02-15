"""
Virtual Neuromodulation (Group Surrogate model) simulation nodes.

This module provides nodes for simulating Virtual Neuromodulation (Group Surrogate model).
"""

from typing import Dict, Any, List, Tuple, Optional
import time
import os
import numpy as np
import h5py
import hdf5storage
import nibabel as nib
import vneumodpy as vnm

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition
from neuroworkflow.core.port import PortType


class VNMSimulatorNode(Node):
    """Simulation of a Virtual Neuromodulation (Group Surrogate model)."""
    
    NODE_DEFINITION = NodeDefinitionSchema(
        type='simulation_node',
        description='Simulates a Virtual Neuromodulation (Group Surrogate model)',
        parameters={
            'target_ROI_file': ParameterDefinition(
                default_value='',
                description='Modulation target ROI atlas file (.nii.gz)'
            ),
            'target_ROI': ParameterDefinition(
                default_value='',
                description='Modulation target ROI numbers (list)',
            ),
            'subject_perm_path': ParameterDefinition(
                default_value='.',
                description='Subject permutation file path',
            ),
            'simulation_name':ParameterDefinition(
                default_value='vnmSimName',
                description='unique simulation name of virtual neuromodulation'
            ),
            'number_of_trials':ParameterDefinition(
                default_value='1',
                description='Number of trials (Each trial generates a permutation of the subjects)',
            ),
            'number_of_surrogate':ParameterDefinition(
                default_value='40',
                description='Number of surrogates time-series in each trial (Fixed value)',
            ),
            'modulation_params': ParameterDefinition(
                default_value='28,22,160,0.15',
                description='Virtual neuromodulation params: on/off/total duration (sec), and modulation power (Fixed value)',
            ),
            'fmri_tr': ParameterDefinition(
                default_value='1',
                description='fMRI TR (sec) (Fixed value)',
            ),
            'hrf_params': ParameterDefinition(
                default_value='16,8',
                description='Canonical Hemodynamic Response Function (HRF) params (Fixed value)',
            ),
        },
        inputs={
            'CX': PortDefinition(
                type=PortType.LIST,
                description='Subject multivariate time-series data'
            ),
            'model': PortDefinition(
                type=PortType.OBJECT,
                description='Group Surrogate model'
            ),
            'atlasV': PortDefinition(
                type=PortType.OBJECT,
                description='Cube ROI atlas'
            )
        },
        outputs={
            'simulation_name':PortDefinition(
                type=PortType.STR,
                description='unique simulation name of virtual neuromodulation'
            ),
            'trials': PortDefinition(
                type=PortType.LIST,
                description='Virtual neuromodulation trial results'
            ),
            'Chrf': PortDefinition(
                type=PortType.OBJECT,
                description='Canonical Hemodynamic Response Function (will be used by GLM analysis)'
            )
        },
        methods={
            'initialize_modulation': MethodDefinition(
                description='Setup modulation time-series',
                inputs=['CX', 'atlasV'],
                outputs=['CAs', 'Chrf', 'CMs']
            ),
            'simulate_modulation': MethodDefinition(
                description='Run virtual neuromodulation simulation',
                inputs=['CX', 'model', 'atlasV', 'CAs', 'Chrf', 'CMs'],
                outputs=['simulation_name', 'trials', 'Chrf']
            )
        }
    )
    
    def __init__(self, name: str):
        """Initialize a SimulateSonataNetworkNode.
        
        Args:
            name: Name of the node
        """
        super().__init__(name)
        self._define_process_steps()
    
    
    def _define_process_steps(self) -> None:
        """Define process steps for this node."""
        self.add_process_step(
            "initialize_modulation",
            self.initialize_modulation,
            method_key="initialize_modulation"
        )
        
        self.add_process_step(
            "simulate_modulation",
            self.simulate_modulation,
            method_key="simulate_modulation"
        )
    
        
    def str2numlist(self, str_data, ctype):
        slist = str_data.split(',')
        clist = []
        for i in range(len(slist)):
            clist.append(ctype(slist[i]))
        return clist


    def initialize_modulation(self, CX: Dict[str, Any], atlasV: Dict[str, Any]) -> Dict[str, Any]:
        """Setup HRF and neuromodulation."""
        if CX is None:
            raise ValueError("subject time-series not set")
        if atlasV is None:
            raise ValueError("atlas not set")

        target_ROI_file = self._parameters["target_ROI_file"]
        target_ROI = self._parameters['target_ROI']
        if len(target_ROI_file) == 0:
            raise ValueError("target ROI file not set")
        if len(target_ROI) == 0:
            raise ValueError("target ROI (numbers) not set")

        print(f"Loading target ROI nifti file: {target_ROI_file}")
        targetDat = nib.load(target_ROI_file)
        targetV = targetDat.get_fdata()
        targetV = vnm.adjust_volume_dir(targetV, targetDat)

        # init param string to list
        trois = self.str2numlist(target_ROI, int)
        vnpm = self.str2numlist(self._parameters['modulation_params'], float)
        hrfpm = self.str2numlist(self._parameters['hrf_params'], int)
        tr = float(self._parameters['fmri_tr'])
        n_surr = int(self._parameters['number_of_surrogate'])

        dbsidxs = []
        for i in range(len(trois)):
            dbsidx = np.unique(atlasV[targetV == trois[i]])
            dbsidxs.append(dbsidx.astype(np.int32))
        if len(dbsidxs) == 0:
            raise ValueError("error: empty modulation target. bad ROI numbers.")

        roilen = len(trois)
        CAs = [None] * roilen
        CMs = [None] * roilen
        for j in range(roilen):
            roi = trois[j]
            dbsidx = dbsidxs[j]

            # get modulation (add & mul) time-series for vertual neuromodulation
            print('generate modulation (add & mul) time-series, target roi=' + str(roi) + ', srframes=' +str(vnpm[2])+ ', dbsoffsec=' +str(vnpm[0])+ ', dbsonsec=' +str(vnpm[1])+ ', dbspw=' +str(vnpm[3]))
            print('convolution params tr=' +str(tr)+ ', res=' +str(hrfpm[0])+ ', sp=' +str(hrfpm[1]))
            CAs[j], Chrf, CMs[j] = vnm.vnm_addmul_signals(CX, dbsidx, n_surr, int(vnpm[2]), int(vnpm[0]), int(vnpm[1]), vnpm[3], tr, hrfpm[0], hrfpm[1])

        return {"CAs": CAs, "Chrf": Chrf, "CMs": CMs}


    def simulate_modulation(self, CX: Dict[str, Any], model: Dict[str, Any], atlasV: Dict[str, Any],
                              CAs: Dict[str, Any], Chrf: Dict[str, Any], CMs: Dict[str, Any],
                              ) -> Dict[str, Any]:
        """Simulate Virtual Neuromodulation."""
        # Validate inputs
        if CX is None:
            raise ValueError("CX (Subject multivariate time-series) not set")
        if model is None:
            raise ValueError("Group Surrogate model not set")
        if atlasV is None:
            raise ValueError("Atlas volume not set")
        if CAs is None:
            raise ValueError("Modulation add not set")
        if CMs is None:
            raise ValueError("Modulation multi not set")

        simulation_name = self._parameters['simulation_name']
        subject_perm_path = self._parameters['subject_perm_path']
        n_trials = int(self._parameters['number_of_trials'])
        n_surr = int(self._parameters['number_of_surrogate'])
        vnpm = self.str2numlist(self._parameters['modulation_params'], float)
        trois = self.str2numlist(self._parameters['target_ROI'], int)
        srframes = int(vnpm[2])

        trials = [None] * n_trials

        # process each file
        for i in range(n_trials):
            perm = []
            permf = subject_perm_path + '/perm' + str(i + 1) + '_' + simulation_name + '.mat'
            if os.path.isfile(permf):
                print('loading subject permutation : ' + permf)
                dic = h5py.File(permf, 'r')
                perm = np.array(dic['perm']).T[0]  # Dataset to single array 1xlength
                perm = perm.astype(np.int32)
                dic.close()

            if len(perm) == 0 or perm is None:
                # generate subject permutation
                permf = subject_perm_path + '/perm' + str(i + 1) + '_' + simulation_name + '.mat'
                perm, uxtime = vnm.vnm_subject_perm(CX)
                matdata = {}
                matdata['perm'] = perm
                matdata['uxtime'] = uxtime
                hdf5storage.write(matdata, filename=permf, matlab_compatible=True)
                print('save perm file : ' + permf)

            # loop for neuromodulation target rois
            S_rois = [None] * len(trois)
            for j in range(len(trois)):
                roi = trois[j]
                sessionName = simulation_name+ '_' +str(roi)+ 'sr' +str(n_surr)+ 'pr' +str(i+1)

                # calc virtual neuromodulation VAR surrogate
                print('calc virtual neuromodulation surrogate. roi=' +str(roi)+ ', n_surr=' +str(n_surr))
                S = vnm.vnm_var_surrogate(model, CX, CAs[j], CMs[j], perm, n_surr, srframes)
                S_rois[j] = [S, roi]

            trials[i] = S_rois

        return {"simulation_name": simulation_name, "trials": trials, "Chrf": Chrf}
    
