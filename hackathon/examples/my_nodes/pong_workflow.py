"""End-to-end NeuroWorkflow for the NEST R-STDP / dopaminergic Pong example.

Graph:
    NESTKernelNode ──kernel_ready──> LeftPlayer  (NESTPongPlayerNode)
                   └─kernel_ready──> RightPlayer (NESTPongPlayerNode)
    LeftPlayer.player_network  ─> MatchSimulation (PongMatchSimulationNode)
    RightPlayer.player_network ─> MatchSimulation
    MatchSimulation.{game_trace,left_performance,right_performance}
                               ─> RenderGif (PongGifRendererNode)

Run from the my_nodes/ folder:
    /Users/carlosengutierrez/miniforge3/envs/neuroworkflow-hackathon/bin/python pong_workflow.py
"""
import os
import sys

from neuroworkflow import WorkflowBuilder

# Make the node modules + helper modules (pong.py, networks.py) importable
# whether run as a script or inside a Jupyter notebook.
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = os.getcwd()
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from NESTKernelNode import NESTKernelNode
from NESTPongPlayerNode import NESTPongPlayerNode
from PongMatchSimulationNode import PongMatchSimulationNode
from PongGifRendererNode import PongGifRendererNode


def build_workflow():
    kernel = NESTKernelNode("Kernel")
    left_player = NESTPongPlayerNode("LeftPlayer")
    right_player = NESTPongPlayerNode("RightPlayer")
    simulation = PongMatchSimulationNode("MatchSimulation")
    renderer = PongGifRendererNode("RenderGif")

    # --- Configure (defaults from the original pong_simulation: clean R-STDP vs noisy R-STDP) ---
    kernel.configure(random_seed=1, resolution_ms=0.1, reset_kernel=True)
    left_player.configure(learning_rule="rstdp", apply_noise=False, num_neurons=20, player_side="left")
    right_player.configure(learning_rule="rstdp", apply_noise=True, num_neurons=20, player_side="right")
    simulation.configure(max_runs=50, poll_time_ms=200.0, log_interval=10, run_label="pong_demo")
    renderer.configure(gif_name="pong_demo.gif", default_speed=4, frame_duration_ms=150)

    wf = WorkflowBuilder("Pong Training Workflow")
    for node in (kernel, left_player, right_player, simulation, renderer):
        wf.add_node(node)

    wf.connect("Kernel", "kernel_ready", "LeftPlayer", "kernel_ready")
    wf.connect("Kernel", "kernel_ready", "RightPlayer", "kernel_ready")
    wf.connect("LeftPlayer", "player_network", "MatchSimulation", "left_player_network")
    wf.connect("RightPlayer", "player_network", "MatchSimulation", "right_player_network")
    wf.connect("MatchSimulation", "game_trace", "RenderGif", "game_trace")
    wf.connect("MatchSimulation", "left_performance", "RenderGif", "left_performance")
    wf.connect("MatchSimulation", "right_performance", "RenderGif", "right_performance")

    # Set context BEFORE build() — all file-writing nodes read results_path from here.
    wf.context["results_path"] = os.path.join(_HERE, "results")

    workflow = wf.build()
    nodes = {
        "kernel": kernel,
        "left_player": left_player,
        "right_player": right_player,
        "simulation": simulation,
        "renderer": renderer,
    }
    return workflow, nodes


def validate_outputs(workflow):
    """Assert every output port produced a non-None value (errors are swallowed)."""
    all_ok = True
    for name, node in workflow.nodes.items():
        for pname in node.NODE_DEFINITION.outputs:
            value = node.get_output(pname)
            ok = value is not None
            all_ok = all_ok and ok
            print(f"  {name}.{pname}: {'OK' if ok else '*** None ***'}")
    return all_ok


def main() -> int:
    workflow, nodes = build_workflow()

    success = workflow.execute()
    print(f"\nworkflow.execute() -> {success}")
    assert success, "workflow.execute() returned False — a node failed (check printed errors)."

    print("\nOutput port validation:")
    assert validate_outputs(workflow), "A node produced a None output."

    print("\nResults:")
    print("  match output dir:", nodes["simulation"].get_output("output_dir"))
    print("  GIF:", nodes["renderer"].get_output("gif_path"))
    print("  left:", nodes["left_player"].get_output("network_label"),
          "vs right:", nodes["right_player"].get_output("network_label"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
