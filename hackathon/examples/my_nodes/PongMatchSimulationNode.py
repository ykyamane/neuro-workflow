from typing import Dict, Any
import os
import gzip
import pickle
import logging

import numpy as np
import nest

from pong import GameOfPong, LEFT_SCORE, RIGHT_SCORE

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType


class PongMatchSimulationNode(Node):
    """Runs a Pong match between two spiking networks and trains them online.

    Each iteration: the ball's vertical cell drives an input spike train into
    both players, NEST simulates one poll window, each network applies its
    plasticity rule and moves its paddle toward its most-active motor neuron,
    then the game advances. The per-step game state and each network's reward
    and weight histories are returned in memory (for downstream visualisation)
    and also written to pickle files under `results_path` for the server step.
    """

    NODE_DEFINITION = NodeDefinitionSchema(
        type="pong_match_simulation",
        stage="simulation",
        tool="NEST",
        model_source="https://github.com/electronicvisions/model-sw-pong",
        description="Simulates a competitive Pong match between two spiking networks over many poll windows, applying online reward-based plasticity each step and recording game state, rewards, and synaptic weight trajectories.",
        parameters={
            "max_runs": ParameterDefinition(
                default_value=50,
                description="Number of game iterations (poll windows) to simulate and train over.",
                constraints={"min": 1, "max": 100000},
                optimizable=True,
                optimization_range=[50, 5000],
            ),
            "poll_time_ms": ParameterDefinition(
                default_value=200.0,
                description="Biological simulation time per iteration in milliseconds (nest.Simulate duration per game step).",
                constraints={"min": 1.0, "max": 1000.0},
            ),
            "log_interval": ParameterDefinition(
                default_value=100,
                description="Emit a progress log line every this many iterations (score and mean rewards).",
                constraints={"min": 1},
            ),
            "run_label": ParameterDefinition(
                default_value="pong_run",
                description="Sub-folder name created under results_path to hold this match's pickle outputs.",
            ),
        },
        inputs={
            "left_player_network": PortDefinition(
                type=PortType.OBJECT,
                description="Live PongNet instance for the left paddle, produced by a network node in the same NEST kernel.",
            ),
            "right_player_network": PortDefinition(
                type=PortType.OBJECT,
                description="Live PongNet instance for the right paddle, produced by a network node in the same NEST kernel.",
            ),
        },
        outputs={
            "game_trace": PortDefinition(
                type=PortType.DICT,
                description="Per-iteration game state with keys 'ball_pos', 'left_paddle', 'right_paddle' (each an array of (x,y) in game units) and 'score' (array of (left,right) score tuples).",
            ),
            "left_performance": PortDefinition(
                type=PortType.DICT,
                description="Left network history: keys 'network_type' (str), 'with_noise' (bool), 'rewards' (list of mean-reward arrays per iteration), 'weights' (list of input->motor weight matrices per iteration).",
            ),
            "right_performance": PortDefinition(
                type=PortType.DICT,
                description="Right network history with the same schema as left_performance.",
            ),
            "output_dir": PortDefinition(
                type=PortType.STR,
                description="Absolute path of the folder containing gamestate.pkl, data_left.pkl.gz and data_right.pkl.gz for this match.",
            ),
        },
        methods={
            "run": MethodDefinition(
                description="Run the training loop for max_runs iterations and persist/return the results.",
                inputs=["left_player_network", "right_player_network"],
                outputs=["game_trace", "left_performance", "right_performance", "output_dir"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("run", self.run, method_key="run")

    def run(self, left_player_network, right_player_network) -> Dict[str, Any]:
        max_runs = int(self._parameters["max_runs"])
        poll_time = float(self._parameters["poll_time_ms"])
        log_interval = int(self._parameters["log_interval"])
        run_label = str(self._parameters["run_label"])

        data_path = self._context.get("results_path", "results/")
        out_dir = os.path.abspath(os.path.join(data_path, run_label))
        os.makedirs(out_dir, exist_ok=True)

        game = GameOfPong()
        player1, player2 = left_player_network, right_player_network

        game_data = []
        l_score, r_score = 0, 0
        run = 0
        biological_time = 0

        logging.info(f"Starting Pong match: {max_runs} iterations of {poll_time}ms each.")
        while run < max_runs:
            input_index = game.ball.get_cell()[1]
            player1.set_input_spiketrain(input_index, biological_time)
            player2.set_input_spiketrain(input_index, biological_time)

            if run % log_interval == 0:
                logging.info(
                    f"Run {run}, score: {(l_score, r_score)}, mean rewards: "
                    f"{round(np.mean(player1.mean_reward), 3)}, "
                    f"{round(np.mean(player2.mean_reward), 3)}"
                )

            nest.Simulate(poll_time)
            biological_time = nest.GetKernelStatus("biological_time")

            for network, paddle in zip([player1, player2], [game.l_paddle, game.r_paddle]):
                network.apply_synaptic_plasticity(biological_time)
                network.reset()

                position_diff = network.winning_neuron - paddle.get_cell()[1]
                if position_diff > 0:
                    paddle.move_up()
                elif position_diff == 0:
                    paddle.dont_move()
                else:
                    paddle.move_down()

            game.step()
            run += 1
            game_data.append(
                [
                    game.ball.get_pos(),
                    game.l_paddle.get_pos(),
                    game.r_paddle.get_pos(),
                    (l_score, r_score),
                ]
            )

            if game.result == RIGHT_SCORE:
                game.reset_ball(False)
                r_score += 1
            elif game.result == LEFT_SCORE:
                game.reset_ball(True)
                l_score += 1

        game_data = np.array(game_data)
        out_data = {
            "ball_pos": game_data[:, 0],
            "left_paddle": game_data[:, 1],
            "right_paddle": game_data[:, 2],
            "score": game_data[:, 3],
        }

        with open(os.path.join(out_dir, "gamestate.pkl"), "wb") as file:
            pickle.dump(out_data, file)

        performances = []
        for net, filename in zip([player1, player2], ["data_left.pkl.gz", "data_right.pkl.gz"]):
            reward_history, weight_history = net.get_performance_data()
            perf = {
                "network_type": repr(net),
                "with_noise": net.apply_noise,
                "rewards": reward_history,
                "weights": weight_history,
            }
            with gzip.open(os.path.join(out_dir, filename), "w") as file:
                pickle.dump(perf, file)
            performances.append(perf)

        logging.info(f"Match complete. Final score (L,R): {(l_score, r_score)}. Outputs in {out_dir}")

        return {
            "game_trace": out_data,
            "left_performance": performances[0],
            "right_performance": performances[1],
            "output_dir": out_dir,
        }
