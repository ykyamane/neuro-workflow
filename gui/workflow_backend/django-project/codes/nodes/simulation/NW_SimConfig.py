from typing import Dict, Any

import pandas as pd

# BMTK 1.1.4 reads SONATA node-type tables via pandas. Under pandas >= 3.0 the
# default string dtype became StringDtype(na_value=nan), which BMTK then hands to
# np.empty() (sonata/group.py) and which NumPy cannot interpret as a dtype:
#   "Cannot interpret '<StringDtype(...)>' as a data type"
# Disabling the new string inference keeps those columns as object dtype, exactly
# as pre-3.0. set_option is process-global, so setting it once at import — before
# any BMTK SONATA read in workflow.execute() — covers the whole run.
pd.set_option("future.infer_string", False)

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema, PortDefinition, ParameterDefinition, MethodDefinition,
)
from neuroworkflow.core.port import PortType


class NW_SimConfig(Node):
    """
    BMTK simulation node — builds, configures, and runs.

    Receives the live NetworkBuilder OBJECT from NW_Population (or from the last
    NW_Connectivity in the chain). Follows BMTK's own run sequence:
      net.build() → net.save() → create_environment() → Config → Network → Sim → run()

    For multi-population networks: wire each population (or the last NW_Connectivity
    output for that population) into separate 'populations' and 'extra_populations'
    ports, or collect them in a list via a fan-in node.
    """

    NODE_DEFINITION = NodeDefinitionSchema(
        type="nw_sim_config",
        stage="simulation",
        tool="BMTK",
        model_source="https://alleninstitute.github.io/bmtk/",
        description=(
            "Receives BMTK NetworkBuilder population objects, calls build()+save() "
            "to write SONATA network files, generates the config JSON via create_environment(), "
            "then runs the simulation via PointNet (NEST) or BioNet (NEURON). "
            "Scales from single cell to large networks."
        ),
        parameters={
            "simulator": ParameterDefinition(
                default_value="pointnet",
                description="BMTK simulator backend: 'pointnet' (NEST) or 'bionet' (NEURON).",
            ),
            "config_file": ParameterDefinition(
                default_value="config.json",
                description="Filename for the generated SONATA config JSON (relative to results_path).",
            ),
            "tstop_ms": ParameterDefinition(
                default_value=3000.0,
                description="Simulation end time in milliseconds.",
                constraints={"min": 1.0},
            ),
            "dt_ms": ParameterDefinition(
                default_value=0.1,
                description="Simulation time step in milliseconds.",
                constraints={"min": 0.001},
            ),
            "reports": ParameterDefinition(
                default_value={
                    "v_report": {
                        "variable_name": "V_m",
                        "cells": "all",
                        "module": "membrane_report",
                        "sections": "soma",
                    }
                },
                description=(
                    "SONATA reports dict written to the config 'reports' section. "
                    "Each key is a report name; value is a dict of SONATA report fields. "
                    "Empty dict = spikes only, no membrane recording. "
                    "variable_name: 'V_m' for PointNet/NEST, 'v' for BioNet/NEURON. "
                    "cells: 'all', a population name ('v1'), a filter dict ({'ei_type': 'exc'}), or node id list ([0,1,2]). "
                    "sections: 'soma' (default) or 'all' (all compartments, BioNet only). "
                    "PointNet example: {'exc_Vm': {'variable_name': 'V_m', 'cells': {'ei_type': 'exc'}, 'module': 'membrane_report', 'sections': 'soma'}}. "
                    "BioNet example: {'v_report': {'variable_name': 'v', 'cells': 'all', 'module': 'membrane_report', 'sections': 'soma'}}."
                ),
            ),
            "compile_mechanisms": ParameterDefinition(
                default_value=False,
                description=(
                    "Compile NEURON .mod files before running. "
                    "Required for BioNet on first use; not needed for PointNet."
                ),
            ),
            "overwrite": ParameterDefinition(
                default_value=True,
                description="Overwrite existing config files and network files.",
            ),
        },
        inputs={
            "populations": PortDefinition(
                type=PortType.OBJECT,
                description=(
                    "Single population from NW_Population, or network dict from NW_Connectivity. "
                    "Single pop keys: builder, pop_name, network_dir, optional current_clamp. "
                    "Network dict (multi-pop): keyed by pop_name, each value has the same keys."
                ),
            ),
        },
        outputs={
            "results": PortDefinition(
                type=PortType.DICT,
                description=(
                    "Dict with config_file (str), output_dir (str), simulator (str). "
                    "Consumed by NW_Analysis."
                ),
            ),
        },
        methods={
            "setup": MethodDefinition(
                description=(
                    "Call builder.build() + builder.save(), create directory structure, "
                    "generate SONATA config via create_environment(), inject reports."
                ),
                inputs=["populations"],
                outputs=["config_file", "output_dir", "simulator"],
            ),
            "run": MethodDefinition(
                description="Run the simulation using the generated config (PointNet or BioNet).",
                inputs=["config_file", "output_dir", "simulator"],
                outputs=["results"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("setup", self.setup, method_key="setup")
        self.add_process_step("run",   self.run,   method_key="run")

    def setup(self, populations: Dict) -> Dict[str, Any]:
        import json
        import os
        from bmtk.utils.create_environment import create_environment

        p        = self._parameters
        base_dir = self._context.get("results_path", "results")
        output_dir = os.path.join(base_dir, "output")

        # Single population (direct from NW_Population) or network dict (from NW_Connectivity)
        if "builder" in populations:
            pop_list    = [populations]
            network_dir = populations["network_dir"]
        else:
            pop_list    = list(populations.values())
            network_dir = pop_list[0]["network_dir"]

        for subdir in [
            "components/point_neuron_models",
            "components/biophysical_neuron_models",
            "components/morphologies",
            "components/mechanisms/modfiles",
            "components/synaptic_models",
            "components/templates",
            "inputs",
        ]:
            os.makedirs(os.path.join(base_dir, subdir), exist_ok=True)

        for pop in pop_list:
            pop["builder"].build()
            pop["builder"].save(output_dir=network_dir)

        kwargs: Dict[str, Any] = dict(
            base_dir=base_dir,
            config_file=str(p["config_file"]),
            network_dir=network_dir,
            tstop=float(p["tstop_ms"]),
            dt=float(p["dt_ms"]),
            overwrite=bool(p["overwrite"]),
            compile_mechanisms=bool(p["compile_mechanisms"]),
        )

        # current_clamp lives in the primary pop (single-pop case only)
        primary = pop_list[0]
        if primary.get("current_clamp"):
            kwargs["current_clamp"] = primary["current_clamp"]

        create_environment(str(p["simulator"]), **kwargs)

        reports = dict(p["reports"]) if p["reports"] else {}
        if reports:
            config_path = os.path.join(base_dir, str(p["config_file"]))
            with open(config_path) as f:
                config = json.load(f)
            config["reports"] = reports
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

        return {
            "config_file": os.path.join(base_dir, str(p["config_file"])),
            "output_dir":  output_dir,
            "simulator":   str(p["simulator"]),
        }

    def run(self, config_file: str, output_dir: str, simulator: str) -> Dict[str, Any]:
        if simulator == "pointnet":
            from bmtk.simulator import pointnet
            conf = pointnet.Config.from_json(config_file)
            conf.build_env()
            net = pointnet.PointNetwork.from_config(conf)
            sim = pointnet.PointSimulator.from_config(conf, net)
            sim.run()

        elif simulator == "bionet":
            from bmtk.simulator import bionet
            conf = bionet.Config.from_json(config_file)
            conf.build_env()
            net = bionet.BioNetwork.from_config(conf)
            sim = bionet.BioSimulator.from_config(conf, net)
            sim.run()

        else:
            raise ValueError(f"Unknown simulator '{simulator}'. Use 'pointnet' or 'bionet'.")

        return {
            "results": {
                "config_file": config_file,
                "output_dir":  output_dir,
                "simulator":   simulator,
            }
        }
