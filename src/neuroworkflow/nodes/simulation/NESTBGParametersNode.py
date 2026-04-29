from typing import Dict, Any

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType


class NESTBGParametersNode(Node):
    """Configure Basal Ganglia model parameters.

    Exposes the key tunable values as node parameters (DC drives, pathway
    overlap, synaptic asymmetry, simulation duration, etc.).  All other
    anatomical constants (in-degrees, delays, distcontact, …) keep the
    Girard et al. defaults and are embedded in the output dicts.
    """

    NODE_DEFINITION = NodeDefinitionSchema(
        type="nest_bg_parameters",
        stage="setup",
        tool="NEST",
        model_source="Girard et al. — top_BG_nest3",
        description=(
            "Build bg_params and sim_params dicts for the NEST 3 Basal Ganglia model "
            "(Girard et al.).  Key biological parameters are exposed for GUI tuning; "
            "anatomical constants use published defaults."
        ),
        parameters={
            # ── Simulation timing ───────────────────────────────────────────
            "sim_duration_ms": ParameterDefinition(
                default_value=3000.0,
                description="Total simulation duration in milliseconds.",
                constraints={"min": 500.0, "max": 300000.0},
            ),
            "warmup_ms": ParameterDefinition(
                default_value=1000.0,
                description=(
                    "Discard spikes in the first N ms (network settling). "
                    "Firing-rate analysis starts after this period."
                ),
                constraints={"min": 0.0},
            ),
            "dt_ms": ParameterDefinition(
                default_value=0.1,
                description="Simulation timestep in milliseconds.",
                constraints={"min": 0.01, "max": 1.0},
            ),
            # ── NEST kernel ─────────────────────────────────────────────────
            "n_threads": ParameterDefinition(
                default_value=10,
                description="Number of parallel threads for the NEST kernel.",
                constraints={"min": 1, "max": 64},
            ),
            "rng_seed": ParameterDefinition(
                default_value=42,
                description="Random seed for reproducibility.",
            ),
            # ── Population scaling ──────────────────────────────────────────
            "scale_factor": ParameterDefinition(
                default_value=1.0,
                description=(
                    "Direct multiplier on every population count: "
                    "0.5 → N/2 neurons, 0.25 → N/4, etc. "
                    "Connectivity in-degrees are anatomical ratios so they scale correctly. "
                    "1.0 = published 1:834 scale."
                ),
                constraints={"min": 0.1, "max": 4.0},
            ),
            # ── DC drive currents [pA] ───────────────────────────────────────
            "ie_msn_pa": ParameterDefinition(
                default_value=24.5,
                description=(
                    "DC current injected into MSN neurons (pA). "
                    "Controls MSN resting firing rate (~0.05–1 Hz target)."
                ),
            ),
            "ie_fsi_pa": ParameterDefinition(
                default_value=8.0,
                description="DC current injected into FSI neurons (pA). Target: 7.8–14 Hz.",
            ),
            "ie_gpe_pa": ParameterDefinition(
                default_value=11.0,
                description="DC current injected into GPe neurons (pA). Target: 55.7–74.5 Hz.",
            ),
            "ie_gpi_pa": ParameterDefinition(
                default_value=8.5,
                description="DC current injected into GPi neurons (pA). Target: 59.1–79.5 Hz.",
            ),
            "ie_stn_pa": ParameterDefinition(
                default_value=9.0,
                description="DC current injected into STN neurons (pA). Target: 15.2–22.8 Hz.",
            ),
            # ── Striatal pathway parameters ─────────────────────────────────
            "overlap_d1d2": ParameterDefinition(
                default_value=0.1,
                description=(
                    "D1/D2 pathway overlap fraction λ (0 = full segregation, 0.5 = 50 %% overlap). "
                    "Higher λ degrades action selection but accelerates discrimination learning."
                ),
                constraints={"min": 0.0, "max": 0.5},
            ),
            "syn_asymm": ParameterDefinition(
                default_value=2.0,
                description=(
                    "Synaptic strength asymmetry κ: scales MSN-D2→MSN weights. "
                    "Based on Taverna et al. 2008 (MSN-D2 PSPs 2×–4× larger than D1). "
                    "Explored between 2.0 and 4.0."
                ),
                constraints={"min": 1.0, "max": 5.0},
            ),
            # ── Output ──────────────────────────────────────────────────────
            "output_dir": ParameterDefinition(
                default_value="./results/nest_bg",
                description="Directory where NEST spike files and position logs are written.",
            ),
        },
        inputs={},
        outputs={
            "bg_params": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Full bgParams dict for the BG network: neuron models, in-degrees, delays, "
                    "synaptic weights, connectivity types, and all anatomical constants."
                ),
            ),
            "sim_params": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Simulation control dict: duration, timestep, thread count, seed, "
                    "scalefactor, warmup period, and output path."
                ),
            ),
        },
        methods={
            "build_params": MethodDefinition(
                description="Assemble bg_params and sim_params from node parameter values.",
                inputs=[],
                outputs=["bg_params", "sim_params"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("build_params", self.build_params, method_key="build_params")

    def build_params(self) -> Dict[str, Any]:
        p = self._parameters

        bg_params = {
            # ── Neuron models (Girard et al.) ────────────────────────────────
            "common_iaf": {
                "E_L": 0.0, "I_e": 0.0, "V_m": 0.0, "V_min": -20.0,
                "V_reset": 0.0, "V_th": 10.0, "t_ref": 2.0,
                "tau_syn": [1.8393972058572117, 36.787944117144235, 1.8393972058572117],
            },
            "MSN_iaf": {"C_m": 13.0, "V_th": 30.0, "tau_m": 13.0},
            "FSI_iaf": {"C_m": 3.1,  "V_th": 16.0, "tau_m": 3.1},
            "GPe_iaf": {"C_m": 14.0, "V_th": 11.0, "tau_m": 14.0},
            "GPi_iaf": {"C_m": 14.0, "V_th": 6.0,  "tau_m": 14.0},
            "STN_iaf": {"C_m": 6.0,  "V_th": 26.0, "tau_m": 6.0},
            # ── DC drives (from node parameters) ────────────────────────────
            "IeMSN": p["ie_msn_pa"],
            "IeFSI": p["ie_fsi_pa"],
            "IeGPe": p["ie_gpe_pa"],
            "IeGPi": p["ie_gpi_pa"],
            "IeSTN": p["ie_stn_pa"],
            # ── Synaptic gain factors ────────────────────────────────────────
            "GFSI": 1.0, "GGPe": 1.0, "GGPe_STN": 1.0, "GGPi": 1.0,
            "GMSN": 1.0, "GMSN_MSN": 1.0, "GMSN_GPx": 0.3, "GSTN": 1.0, "GSTN_GPi": 1.0,
            # ── Pathway parameters (from node parameters) ────────────────────
            "overlap_d1d2": p["overlap_d1d2"],
            "syn_asymm":    p["syn_asymm"],
            "asymmetry_1":  0.5,
            "asymmetry_2":  0.1,
            "MSND2_mod":    1.0,
            "plast_gain":   0.65,
            "plastic_syn":  True,
            # ── Population sizes at 1:834 scale ─────────────────────────────
            "nbMSN": 31728.0, "nbFSI": 636.0, "nbSTN": 96.0,
            "nbGPe": 300.0,   "nbGPi": 168.0,
            "nbCSN": 36000.0, "nbPTN": 36000.0, "nbCMPf": 36000.0,
            # ── Real macaque counts (for weight normalisation) ───────────────
            "countMSN": 26448000.0, "countFSI": 532000.0, "countSTN": 77000.0,
            "countGPe": 251000.0,   "countGPi": 143000.0, "countCMPf": 86000.0,
            "countCSN": None, "countPTN": None,
            # ── Cable equation parameters ────────────────────────────────────
            "Ri": 2.0, "Rm": 2.0,
            "lx":  {"MSN": 0.000619, "FSI": 0.000961, "GPe": 0.000865, "GPi": 0.001132, "STN": 0.00075},
            "dx":  {"MSN": 1e-6, "FSI": 1.5e-6, "GPe": 1.7e-6, "GPi": 1.2e-6, "STN": 1.5e-6},
            "wPSP": [1.0, 0.025, -0.25],
            # ── In-degrees per projection (Girard et al.) ────────────────────
            "alpha": {
                "CMPf->FSI": 1053, "CMPf->GPe": 79,   "CMPf->GPi": 131,
                "CMPf->MSN": 4965, "CMPf->STN": 76,
                "CSN->FSI":  250,  "CSN->MSN":  342,
                "FSI->FSI":  116,  "FSI->MSN":  4362,
                "GPe->FSI":  353,  "GPe->GPe":  38,   "GPe->GPi": 16,
                "GPe->MSN":  0,    "GPe->STN":  19,
                "MSN->GPe":  171,  "MSN->GPi":  210,  "MSN->MSN": 210,
                "PTN->FSI":  5,    "PTN->MSN":  5,    "PTN->STN": 259,
                "STN->FSI":  91,   "STN->GPe":  428,  "STN->GPi": 233, "STN->MSN": 0,
            },
            # ── Axonal delays [ms] ───────────────────────────────────────────
            "tau": {
                "CMPf->FSI": 7.0, "CMPf->GPe": 7.0, "CMPf->GPi": 7.0,
                "CMPf->MSN": 7.0, "CMPf->STN": 7.0,
                "CSN->FSI":  7.0, "CSN->MSN":  7.0,
                "FSI->FSI":  1.0, "FSI->MSN":  1.0,
                "GPe->FSI":  3.0, "GPe->GPe":  1.0, "GPe->GPi": 3.0,
                "GPe->MSN":  3.0, "GPe->STN":  10.0,
                "MSN->GPe":  7.0, "MSN->GPi":  11.0, "MSN->MSN": 1.0,
                "PTN->FSI":  3.0, "PTN->MSN":  3.0,  "PTN->STN": 3.0,
                "STN->FSI":  3.0, "STN->GPe":  3.0,  "STN->GPi": 3.0, "STN->MSN": 3.0,
            },
            # ── Projection-target fractions ──────────────────────────────────
            "ProjPercent": {
                "CMPf->FSI": 1.0, "CMPf->GPe": 1.0, "CMPf->GPi": 1.0,
                "CMPf->MSN": 1.0, "CMPf->STN": 1.0,
                "CSN->FSI":  1.0, "CSN->MSN":  1.0,
                "FSI->FSI":  1.0, "FSI->MSN":  1.0,
                "GPe->FSI":  0.16,"GPe->GPe":  0.84, "GPe->GPi": 0.84,
                "GPe->MSN":  0.16,"GPe->STN":  1.0,
                "MSN->GPe":  1.0, "MSN->GPi":  0.82, "MSN->MSN": 1.0,
                "PTN->FSI":  1.0, "PTN->MSN":  1.0,  "PTN->STN": 1.0,
                "STN->FSI":  0.17,"STN->GPe":  0.83, "STN->GPi": 0.72, "STN->MSN": 0.17,
            },
            # ── Axonal contact fractions (cable attenuation) ─────────────────
            "distcontact": {
                "CMPf->FSI": 0.06, "CMPf->GPe": 0.0,  "CMPf->GPi": 0.48,
                "CMPf->MSN": 0.27, "CMPf->STN": 0.46,
                "CSN->FSI":  0.82, "CSN->MSN":  0.95,
                "FSI->FSI":  0.16, "FSI->MSN":  0.19,
                "GPe->FSI":  0.58, "GPe->GPe":  0.01, "GPe->GPi": 0.13,
                "GPe->MSN":  0.06, "GPe->STN":  0.58,
                "MSN->GPe":  0.48, "MSN->GPi":  0.59, "MSN->MSN": 0.77,
                "PTN->FSI":  0.7,  "PTN->MSN":  0.98, "PTN->STN": 0.97,
                "STN->FSI":  0.41, "STN->GPe":  0.3,  "STN->GPi": 0.59, "STN->MSN": 0.16,
            },
            # ── Connectivity types: focused vs diffuse ───────────────────────
            "cTypeCMPfFSI": "diffuse", "cTypeCMPfGPe": "diffuse", "cTypeCMPfGPi": "diffuse",
            "cTypeCMPfMSN": "diffuse", "cTypeCMPfSTN": "diffuse",
            "cTypeCSNFSI":  "focused", "cTypeCSNMSN":  "focused",
            "cTypeFSIFSI":  "diffuse", "cTypeFSIMSN":  "diffuse",
            "cTypeGPeFSI":  "diffuse", "cTypeGPeGPe":  "diffuse", "cTypeGPeGPi": "focused",
            "cTypeGPeMSN":  "diffuse", "cTypeGPeSTN":  "focused",
            "cTypeMSNGPe":  "focused", "cTypeMSNGPi":  "focused", "cTypeMSNMSN": "focused",
            "cTypePTNFSI":  "focused", "cTypePTNMSN":  "focused", "cTypePTNSTN": "focused",
            "cTypeSTNFSI":  "diffuse", "cTypeSTNGPe":  "diffuse",
            "cTypeSTNGPi":  "diffuse", "cTypeSTNMSN":  "diffuse",
            # ── Redundancy factors ───────────────────────────────────────────
            **{f"redundancy{k}": 3 for k in [
                "CMPfFSI","CMPfGPe","CMPfGPi","CMPfMSN","CMPfSTN",
                "CSNFSI","CSNMSN","FSIFSI","FSIMSN",
                "GPeFSI","GPeGPe","GPeGPi","GPeMSN","GPeSTN",
                "MSNGPe","MSNGPi","MSNMSN",
                "PTNFSI","PTNMSN","PTNSTN",
                "STNFSI","STNGPe","STNGPi","STNMSN",
            ]},
            "RedundancyType": "outDegreeAbs",
            # ── Spatial spread ───────────────────────────────────────────────
            "spread_focused": 0.15,
            "spread_diffuse": 2.0,
            "stochastic_delays": None,
            # ── Channel geometry ─────────────────────────────────────────────
            "channels": True,
            "circle_center": [],
            # ── Validation target rates [Hz] ─────────────────────────────────
            "normalrate": {
                "MSN":  [0.05, 1.0],  "FSI":  [7.8, 14.0],
                "STN":  [15.2, 22.8], "GPe":  [55.7, 74.5],
                "GPi":  [59.1, 79.5], "CSN":  [2.0, 19.7],
                "PTN":  [15.0, 46.3], "CMPf": [4.0, 34.0],
            },
        }

        sim_params = {
            "simDuration":    p["sim_duration_ms"],
            "start_time_sp":  p["warmup_ms"],
            "initial_ignore": 0.0,
            "dt":             str(p["dt_ms"]),
            "nbcpu":          p["n_threads"],
            "msd":            p["rng_seed"],
            "scalefactor":    [p["scale_factor"] ** 0.5, p["scale_factor"] ** 0.5],
            "overwrite_files": True,
            "channels":       True,
            "channels_nb":    6,
            "channels_radius": 0.12,
            "hex_radius":     0.24,
            "data_path":      p["output_dir"],
        }

        print(f"[{self.name}] bg_params and sim_params ready.")
        return {"bg_params": bg_params, "sim_params": sim_params}
