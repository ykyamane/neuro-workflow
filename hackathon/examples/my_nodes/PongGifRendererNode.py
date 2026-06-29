from typing import Dict, Any
import os
from copy import copy
from glob import glob

import numpy as np
import matplotlib

matplotlib.use("Agg")  # headless rendering, safe inside workflows/notebooks
import matplotlib.pyplot as plt
import imageio.v2 as imageio

from pong import GameOfPong as Pong

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType


# --- Rendering constants (from the original generate_gif visualisation) ---
GRIDSIZE = (12, 16)
LEFT_COLOR = np.array((204, 0, 153))
RIGHT_COLOR = np.array((255, 128, 0))
LEFT_COLOR_HEX = "#cc0099"
RIGHT_COLOR_HEX = "#ff8000"
WHITE = np.array((255, 255, 255))

GAME_GRID = np.array([Pong.x_grid, Pong.y_grid])
GRID_SCALE = 24
GAME_GRID_SCALED = GAME_GRID * GRID_SCALE

BALL_RAD = 6
PADDLE_LEN = int(0.1 * GAME_GRID_SCALED[1])
PADDLE_WID = 18

FIELD_PADDING = PADDLE_WID * 2
FIELD_SIZE = copy(GAME_GRID_SCALED)
FIELD_SIZE[0] += 2 * FIELD_PADDING


def scale_coordinates(coordinates: np.ndarray) -> np.ndarray:
    """Scale (x,y) coordinate tuples from simulation units to output pixels."""
    coordinates[:, 0] = coordinates[:, 0] * GAME_GRID_SCALED[0] / Pong.x_length + FIELD_PADDING
    coordinates[:, 1] = coordinates[:, 1] * GAME_GRID_SCALED[1] / Pong.y_length
    return coordinates.astype(int)


def grayscale_to_heatmap(in_image, min_val, max_val, base_color):
    """Map a 2D weight matrix to an RGB heatmap (low=base_color, high=white)."""
    x_len, y_len = in_image.shape
    out_image = np.ones((x_len, y_len, 3), dtype=np.uint8)
    span = max_val - min_val
    if span == 0:
        return out_image * base_color
    for x in range(x_len):
        for y in range(y_len):
            color_scaled = (in_image[x, y] - min_val) / span
            out_image[x, y, :] = base_color + (WHITE - base_color) * color_scaled
    return out_image


class PongGifRendererNode(Node):
    """Renders an animated GIF of a simulated Pong match.

    Consumes the in-memory game trace and both networks' reward/weight
    histories (as produced by the match-simulation node) and draws, per frame,
    the playing field with ball and paddles, each network's synaptic-weight
    heatmap, and the running mean-reward curves. Frames are assembled into a
    single GIF written under `results_path`.
    """

    NODE_DEFINITION = NodeDefinitionSchema(
        type="pong_gif_renderer",
        stage="analysis",
        tool="custom",
        model_source="https://github.com/electronicvisions/model-sw-pong",
        description="Visualises a Pong match as an animated GIF showing ball/paddle motion, per-network synaptic-weight heatmaps, and mean-reward learning curves over training iterations.",
        parameters={
            "gif_name": ParameterDefinition(
                default_value="pong_sim.gif",
                description="File name of the output GIF, written inside results_path.",
            ),
            "default_speed": ParameterDefinition(
                default_value=4,
                description="Number of simulation iterations skipped between rendered frames during slow segments (lower = smoother, more frames).",
                constraints={"min": 1, "max": 100},
            ),
            "frame_duration_ms": ParameterDefinition(
                default_value=150,
                description="Display duration of each GIF frame in milliseconds.",
                constraints={"min": 10, "max": 2000},
            ),
            "keep_temp_frames": ParameterDefinition(
                default_value=False,
                description="If True, keep the intermediate per-frame PNGs on disk after the GIF is assembled.",
            ),
        },
        inputs={
            "game_trace": PortDefinition(
                type=PortType.DICT,
                description="Per-iteration game state with keys 'ball_pos', 'left_paddle', 'right_paddle' (arrays of (x,y) in game units) and 'score' (array of (left,right) tuples).",
            ),
            "left_performance": PortDefinition(
                type=PortType.DICT,
                description="Left network history with keys 'network_type', 'rewards' (mean-reward arrays per iteration) and 'weights' (input->motor weight matrices per iteration).",
            ),
            "right_performance": PortDefinition(
                type=PortType.DICT,
                description="Right network history with the same schema as left_performance.",
            ),
        },
        outputs={
            "gif_path": PortDefinition(
                type=PortType.STR,
                description="Absolute path of the generated animated GIF file.",
            ),
        },
        methods={
            "render": MethodDefinition(
                description="Render per-iteration frames and assemble them into an animated GIF.",
                inputs=["game_trace", "left_performance", "right_performance"],
                outputs=["gif_path"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("render", self.render, method_key="render")

    def render(self, game_trace, left_performance, right_performance) -> Dict[str, Any]:
        gif_name = str(self._parameters["gif_name"])
        default_speed = int(self._parameters["default_speed"])
        frame_duration = int(self._parameters["frame_duration_ms"])
        keep_temps = bool(self._parameters["keep_temp_frames"])

        data_path = self._context.get("results_path", "results/")
        out_dir = os.path.abspath(data_path)
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, gif_name)
        temp_dir = os.path.join(out_dir, "temp_frames")
        os.makedirs(temp_dir, exist_ok=True)

        # Game geometry (copy arrays so scaling does not mutate the inputs)
        ball_positions = scale_coordinates(np.array(game_trace["ball_pos"], dtype=float))
        l_paddle_positions = scale_coordinates(np.array(game_trace["left_paddle"], dtype=float))
        l_paddle_positions[:, 0] -= PADDLE_WID  # shift left paddle outwards for symmetry
        r_paddle_positions = scale_coordinates(np.array(game_trace["right_paddle"], dtype=float))
        score = np.array(game_trace["score"]).astype(int)

        rewards_left = [np.mean(x) for x in left_performance["rewards"]]
        weights_left = left_performance["weights"]
        name_left = left_performance["network_type"]
        rewards_right = [np.mean(x) for x in right_performance["rewards"]]
        weights_right = right_performance["weights"]
        name_right = right_performance["network_type"]

        min_r, max_r = np.min(weights_right), np.max(weights_right)
        min_l, max_l = np.min(weights_left), np.max(weights_left)

        n_iterations = score.shape[0]
        i = 0
        output_speed = default_speed

        while i < n_iterations:
            px = 1 / plt.rcParams["figure.dpi"]
            fig, ax = plt.subplots(figsize=(400 * px, 300 * px))
            ax.set_axis_off()
            plt.rcParams.update({"font.size": 6})

            title = plt.subplot2grid(GRIDSIZE, (0, 0), 1, 16)
            l_info = plt.subplot2grid(GRIDSIZE, (1, 0), 7, 2)
            r_info = plt.subplot2grid(GRIDSIZE, (1, 14), 7, 2)
            field = plt.subplot2grid(GRIDSIZE, (1, 2), 7, 12)
            l_hm = plt.subplot2grid(GRIDSIZE, (8, 0), 4, 4)
            reward_plot = plt.subplot2grid(GRIDSIZE, (8, 6), 4, 6)
            r_hm = plt.subplot2grid(GRIDSIZE, (8, 12), 4, 4)

            for axis in [title, l_info, r_info, field, l_hm, r_hm]:
                axis.axis("off")

            playing_field = np.zeros((FIELD_SIZE[0], FIELD_SIZE[1], 3), dtype=np.uint8)

            x, y = ball_positions[i]
            playing_field[x - BALL_RAD : x + BALL_RAD, y - BALL_RAD : y + BALL_RAD] = WHITE
            for (x, y), color in zip([l_paddle_positions[i], r_paddle_positions[i]], [LEFT_COLOR, RIGHT_COLOR]):
                y = max(PADDLE_LEN, y)
                y = min(FIELD_SIZE[1] - PADDLE_LEN, y)
                playing_field[x : x + PADDLE_WID, y - PADDLE_LEN : y + PADDLE_LEN] = color

            field.imshow(np.transpose(playing_field, [1, 0, 2]))

            heatmap_l = grayscale_to_heatmap(weights_left[i], min_l, max_l, LEFT_COLOR)
            l_hm.imshow(heatmap_l)
            l_hm.set_xlabel("output")
            l_hm.set_ylabel("input")
            l_hm.set_title("weights", y=-0.3)

            heatmap_r = grayscale_to_heatmap(weights_right[i], min_r, max_r, RIGHT_COLOR)
            r_hm.imshow(heatmap_r)
            r_hm.set_xlabel("output")
            r_hm.set_ylabel("input")
            r_hm.set_title("weights", y=-0.3)

            reward_plot.plot([0, i], [-1, -1])
            reward_plot.plot(rewards_right[: i + 1], color=RIGHT_COLOR / 255)
            reward_plot.plot(rewards_left[: i + 1], color=LEFT_COLOR / 255)

            if i < 1600:
                x_min = 0
                reward_plot.set_xticks(np.arange(0, n_iterations, 250))
            else:
                x_min = i - 1600
                reward_plot.set_xticks(np.arange(0, n_iterations, 500))

            reward_plot.set_ylabel("mean reward")
            reward_plot.set_yticks([0, 0.5, 1])
            reward_plot.set_ylim(0, 1.0)
            reward_plot.set_xlim(x_min, i + 10)

            title.text(0.4, 0.75, name_left, ha="right", fontsize=15, c=LEFT_COLOR_HEX)
            title.text(0.5, 0.75, "VS", ha="center", fontsize=17)
            title.text(0.6, 0.75, name_right, ha="left", fontsize=15, c=RIGHT_COLOR_HEX)

            l_score, r_score = score[i]
            l_info.text(0, 0.9, "run:", fontsize=14)
            l_info.text(0, 0.75, str(i), fontsize=14)
            l_info.text(1, 0.5, l_score, ha="right", va="center", fontsize=26, c=LEFT_COLOR_HEX)
            r_info.text(0, 0.9, "speed:", fontsize=14)
            r_info.text(0, 0.75, str(output_speed) + "x", fontsize=14)
            r_info.text(0, 0.5, r_score, ha="left", va="center", fontsize=26, c=RIGHT_COLOR_HEX)

            plt.subplots_adjust(left=0.05, right=0.95, bottom=0.1, top=0.9, wspace=0.35, hspace=0.35)
            plt.savefig(os.path.join(temp_dir, f"img_{str(i).zfill(6)}.png"))

            if 75 <= i < 100 or n_iterations - 400 <= i < n_iterations - 350:
                output_speed = 10
            elif 100 <= i < n_iterations - 350:
                output_speed = 50
            else:
                output_speed = default_speed

            i += output_speed
            plt.close()

        filenames = sorted(glob(os.path.join(temp_dir, "*.png")))
        with imageio.get_writer(out_file, mode="I", duration=frame_duration) as writer:
            for filename in filenames:
                writer.append_data(imageio.imread(filename))

        if not keep_temps:
            for in_file in filenames:
                os.unlink(in_file)
            if not os.listdir(temp_dir):
                os.rmdir(temp_dir)

        return {"gif_path": out_file}
