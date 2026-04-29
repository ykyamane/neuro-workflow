import json
import os
from typing import Dict, Any

import numpy as np
import matplotlib.pyplot as plt

from neuroworkflow.core.node import Node
from neuroworkflow.core.schema import (
    NodeDefinitionSchema,
    PortDefinition,
    ParameterDefinition,
    MethodDefinition,
)
from neuroworkflow.core.port import PortType


_REAL_NUCLEI = ["MSN_d1", "MSN_d2", "FSI", "STN", "GPe", "GPi"]

_TARGET_RATES = {
    "MSN_d1": (0.05, 1.0),
    "MSN_d2": (0.05, 1.0),
    "FSI":    (7.8,  14.0),
    "STN":    (15.2, 22.8),
    "GPe":    (55.7, 74.5),
    "GPi":    (59.1, 79.5),
}

# Inverted-pyramid layout: MSN widest at top (z=9), GPi narrowest at bottom (z=-9)
_POP_CONFIG = {
    "MSN_d1": {"z": 9.0,  "xy": 1.00, "color": "#34d399", "label": "MSN-D1  direct pathway",   "size": 0.10},
    "MSN_d2": {"z": 6.5,  "xy": 1.00, "color": "#fb7185", "label": "MSN-D2  indirect pathway", "size": 0.10},
    "FSI":    {"z": 3.0,  "xy": 0.65, "color": "#f97316", "label": "FSI  fast spiking interneuron", "size": 0.13},
    "STN":    {"z": 0.0,  "xy": 0.40, "color": "#a78bfa", "label": "STN  subthalamic nucleus", "size": 0.16},
    "GPe":    {"z": -4.0, "xy": 0.55, "color": "#fbbf24", "label": "GPe  globus pallidus ext.", "size": 0.14},
    "GPi":    {"z": -8.0, "xy": 0.35, "color": "#22d3ee", "label": "GPi  output nucleus",       "size": 0.18},
}

# Main anatomical pathways: (source, target, color, opacity)
_PATHWAYS = [
    ("MSN_d1", "GPi",    "#34d399", 0.30),   # direct
    ("MSN_d2", "GPe",    "#fb7185", 0.25),   # indirect
    ("GPe",    "STN",    "#fbbf24", 0.25),
    ("GPe",    "GPi",    "#fbbf24", 0.20),
    ("STN",    "GPi",    "#a78bfa", 0.30),   # hyperdirect
    ("FSI",    "MSN_d1", "#f97316", 0.18),
    ("FSI",    "MSN_d2", "#f97316", 0.18),
]


class NESTBGWriterNode(Node):
    """Save BG simulation outputs and display diagnostic plots and 3D viewer."""

    NODE_DEFINITION = NodeDefinitionSchema(
        type="nest_bg_writer",
        stage="output",
        tool="NEST",
        model_source="Girard et al. — top_BG_nest3",
        description=(
            "Persist all NEST BG simulation outputs to disk and display: "
            "mean firing rates bar chart, spike rasters, and an interactive "
            "Three.js 3D network viewer (inverted pyramid, neuron positions)."
        ),
        parameters={
            "output_dir": ParameterDefinition(
                default_value="./results",
                description="Root directory for all outputs.",
            ),
            "raster_max_neurons": ParameterDefinition(
                default_value=200,
                description="Max neurons shown per nucleus in the raster plot.",
                constraints={"min": 10, "max": 2000},
            ),
            "viewer_max_neurons": ParameterDefinition(
                default_value=800,
                description="Max neurons per population shown in the 3D viewer.",
                constraints={"min": 50, "max": 5000},
            ),
        },
        inputs={
            "mean_fr": PortDefinition(type=PortType.OBJECT,
                description="Dict {nucleus: Hz} from NESTBGSimulationNode."),
            "at_fr": PortDefinition(type=PortType.OBJECT,
                description="1-ms-binned rates from NESTBGSimulationNode."),
            "bg_layers": PortDefinition(type=PortType.OBJECT,
                description="Live NEST NodeCollection dict from NESTBGNetworkNode."),
            "sim_params": PortDefinition(type=PortType.OBJECT,
                description="Sim params dict."),
        },
        outputs={
            "results_dir": PortDefinition(type=PortType.STR,
                description="Absolute path to the root output directory."),
        },
        methods={
            "write_results": MethodDefinition(
                description="Save all outputs and display plots + 3D viewer.",
                inputs=["mean_fr", "at_fr", "bg_layers", "sim_params"],
                outputs=["results_dir"],
            ),
        },
    )

    def __init__(self, name: str):
        super().__init__(name)
        self._define_process_steps()

    def _define_process_steps(self) -> None:
        self.add_process_step("write_results", self.write_results, method_key="write_results")

    def write_results(self, mean_fr, at_fr, bg_layers, sim_params) -> Dict[str, Any]:
        root = os.path.abspath(self._parameters["output_dir"])
        os.makedirs(root, exist_ok=True)
        nest_data_path = sim_params.get("data_path", root)

        # ── JSON summaries ───────────────────────────────────────────────
        with open(os.path.join(root, "mean_fr.json"), "w") as f:
            json.dump(mean_fr, f, indent=2)
        with open(os.path.join(root, "At.json"), "w") as f:
            json.dump(at_fr, f)
        print(f"[{self.name}] Saved mean_fr.json and At.json")

        # ── Per-nucleus: GIDs, positions, spike trains ───────────────────
        spike_data = {}
        for nucleus in _REAL_NUCLEI:
            if nucleus not in bg_layers:
                continue
            pop_dir = os.path.join(root, "populations", nucleus)
            os.makedirs(pop_dir, exist_ok=True)

            gids = np.array(bg_layers[nucleus].tolist(), dtype=np.int64)
            np.save(os.path.join(pop_dir, "gids.npy"), gids)

            pos_file = os.path.join(nest_data_path, nucleus + ".txt")
            if os.path.isfile(pos_file):
                pos_data = np.loadtxt(pos_file)
                np.save(os.path.join(pop_dir, "positions.npy"),
                        pos_data[:, 1:3].astype(np.float32))

            times, senders = _collect_spikes(nest_data_path, nucleus)
            np.savez_compressed(os.path.join(pop_dir, "spikes.npz"),
                                times=times, senders=senders)
            spike_data[nucleus] = (times, senders)
            print(f"[{self.name}] {nucleus:10s}  {len(gids):6d} neurons  {len(times):8d} spikes")

        # ── 2D plots ─────────────────────────────────────────────────────
        fig_fr = _plot_mean_fr(mean_fr)
        fig_fr.savefig(os.path.join(root, "mean_firing_rates.png"), dpi=120, bbox_inches="tight")

        fig_raster = _plot_rasters(
            spike_data, sim_params["start_time_sp"], sim_params["simDuration"],
            self._parameters["raster_max_neurons"],
        )
        fig_raster.savefig(os.path.join(root, "spike_rasters.png"), dpi=120, bbox_inches="tight")

        # ── 3D interactive viewer ────────────────────────────────────────
        viewer_path = _generate_3d_viewer(
            mean_fr, nest_data_path, root,
            max_neurons=self._parameters["viewer_max_neurons"],
        )

        # Display everything inline in Jupyter
        try:
            import html as _html
            from IPython.display import display, HTML
            display(fig_fr)
            display(fig_raster)
            with open(viewer_path) as f:
                html_src = f.read()
            display(HTML(f'<iframe srcdoc="{_html.escape(html_src)}" '
                         f'width="100%" height="700px" frameborder="0"></iframe>'))
        except Exception:
            pass

        plt.close(fig_fr)
        plt.close(fig_raster)
        print(f"[{self.name}] All outputs written to: {root}")
        return {"results_dir": root}


# ---------------------------------------------------------------------------
# 3D viewer generator
# ---------------------------------------------------------------------------

def _generate_3d_viewer(mean_fr: dict, nest_data_path: str, root: str, max_neurons: int = 800) -> str:
    """Build a self-contained Three.js HTML viewer and save to root/bg_network_viewer.html."""

    populations = {}
    for nucleus, cfg in _POP_CONFIG.items():
        pos_file = os.path.join(nest_data_path, nucleus + ".txt")
        if not os.path.isfile(pos_file):
            continue
        data = np.loadtxt(pos_file)       # columns: gid, x, y
        xy = data[:, 1:3].astype(float)

        if len(xy) > max_neurons:
            idx = np.random.choice(len(xy), max_neurons, replace=False)
            xy = xy[idx]

        # Normalise to [-1,1] then scale to world units
        centre = xy.mean(axis=0)
        xy -= centre
        extent = np.abs(xy).max()
        if extent > 0:
            xy /= extent
        xy *= cfg["xy"] * 7.0            # world-space spread

        z_jitter = np.random.uniform(-0.35, 0.35, len(xy))
        z_col = np.full(len(xy), cfg["z"]) + z_jitter

        # Three.js axes: x=lateral, y=vertical-in-layer, z=depth (layer axis)
        positions = np.column_stack([xy[:, 0], xy[:, 1], z_col]).tolist()

        populations[nucleus] = {
            "positions": positions,
            "color": cfg["color"],
            "mean_fr": float(mean_fr.get(nucleus, 0.0)),
            "label": cfg["label"],
            "size": cfg["size"],
            "z_center": cfg["z"],
        }

    data_json = json.dumps(populations)

    html = _HTML_TEMPLATE.replace("%%BG_DATA%%", data_json)
    out_path = os.path.join(root, "bg_network_viewer.html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"[Writer] 3D viewer saved: {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Three.js HTML template
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>BG Neural Circuit — 3D</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#020617; overflow:hidden; font-family:'JetBrains Mono',monospace; }
  canvas { display:block; }
  #title  { position:fixed; top:18px; left:20px; }
  #title h1 { font-size:0.9rem; font-weight:700; color:#f1f5f9; letter-spacing:-0.01em; }
  #title p  { color:#475569; font-size:0.6rem; margin-top:3px; }
  #legend {
    position:fixed; bottom:18px; left:20px;
    background:rgba(2,6,23,0.88); border:1px solid #1e293b;
    border-radius:8px; padding:11px 15px;
  }
  .lr { display:flex; align-items:center; gap:8px; margin-bottom:5px; color:#94a3b8; font-size:0.62rem; }
  .lr:last-child { margin-bottom:0; }
  .ld { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
  #hint { position:fixed; bottom:18px; right:20px; color:#334155; font-size:0.6rem; text-align:right; line-height:1.7; }
  #info { position:fixed; top:18px; right:20px; color:#64748b; font-size:0.62rem; text-align:right; line-height:1.8; }
</style>
</head>
<body>

<div id="title">
  <h1>BG Neural Circuit — 3D</h1>
  <p>Basal ganglia resting state &nbsp;·&nbsp; real neuron positions</p>
</div>
<div id="legend"></div>
<div id="hint">drag to orbit<br>scroll to zoom<br>auto-rotates</div>
<div id="info"></div>

<script>window.__BG_DATA__ = %%BG_DATA%%;</script>

<script type="importmap">
{
  "imports": {
    "three":         "https://unpkg.com/three@0.160.0/build/three.module.js",
    "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
  }
}
</script>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// ── Renderer ────────────────────────────────────────────────────────────────
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(0x020617, 1);
document.body.appendChild(renderer.domElement);

// ── Scene / Camera ──────────────────────────────────────────────────────────
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x020617, 0.010);

const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 300);
camera.position.set(6, 12, 22);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0, 0);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.4;
controls.minDistance = 6;
controls.maxDistance = 70;
controls.update();

// ── Lighting ────────────────────────────────────────────────────────────────
scene.add(new THREE.AmbientLight(0x0f172a, 12));
const pL1 = new THREE.PointLight(0x34d399, 60, 40); pL1.position.set(0, 4,  10); scene.add(pL1);
const pL2 = new THREE.PointLight(0xa78bfa, 40, 40); pL2.position.set(0, 0,  -9); scene.add(pL2);
const pL3 = new THREE.PointLight(0xfbbf24, 25, 30); pL3.position.set(8, 2,   0); scene.add(pL3);

// ── Helpers ──────────────────────────────────────────────────────────────────
function hexToRGB(hex) {
  const r = parseInt(hex.slice(1,3),16)/255;
  const g = parseInt(hex.slice(3,5),16)/255;
  const b = parseInt(hex.slice(5,7),16)/255;
  return new THREE.Color(r,g,b);
}

function mkLayerPlane(zCenter, color, halfW, halfH) {
  const col = hexToRGB(color);
  const geo = new THREE.PlaneGeometry(halfW*2, halfH*2);
  const mesh = new THREE.Mesh(geo,
    new THREE.MeshBasicMaterial({ color: col, transparent:true, opacity:0.04, side:THREE.DoubleSide, depthWrite:false }));
  mesh.position.set(0, 0, zCenter);
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo),
    new THREE.LineBasicMaterial({ color: col, transparent:true, opacity:0.18 }));
  edges.position.set(0, 0, zCenter);
  scene.add(mesh, edges);
}

function mkLabel(text, cssColor, zPos, xPos=0, yPos=0, sx=7, sy=0.7) {
  const canvas = document.createElement('canvas');
  canvas.width = 512; canvas.height = 64;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = cssColor;
  ctx.font = '600 24px "JetBrains Mono", monospace';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 256, 32);
  const sprite = new THREE.Sprite(
    new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(canvas), transparent:true, opacity:0.85 }));
  sprite.scale.set(sx, sy, 1);
  sprite.position.set(xPos, yPos, zPos);
  scene.add(sprite);
}

function mkConnectionBundle(posA, posB, color, opacity, nLines=6, spread=0.6) {
  const col = hexToRGB(color);
  for (let i = 0; i < nLines; i++) {
    const dx = (Math.random()-0.5)*spread;
    const dy = (Math.random()-0.5)*spread;
    const a = new THREE.Vector3(posA.x+dx, posA.y+dy, posA.z);
    const b = new THREE.Vector3(posB.x+dx*0.3, posB.y+dy*0.3, posB.z);
    const geo = new THREE.BufferGeometry().setFromPoints([a, b]);
    scene.add(new THREE.Line(geo,
      new THREE.LineBasicMaterial({ color: col, transparent:true, opacity })));
  }
}

// ── Build populations ────────────────────────────────────────────────────────
const data      = window.__BG_DATA__;
const popKeys   = Object.keys(data);
const pointClouds = {};   // nucleus → THREE.Points
const centroids   = {};   // nucleus → THREE.Vector3

for (const key of popKeys) {
  const pop = data[key];
  const pts = pop.positions;
  const N   = pts.length;
  const col = hexToRGB(pop.color);

  const posArr = new Float32Array(N * 3);
  let cx=0, cy=0, cz=0;
  for (let i = 0; i < N; i++) {
    posArr[i*3]   = pts[i][0];
    posArr[i*3+1] = pts[i][1];
    posArr[i*3+2] = pts[i][2];
    cx += pts[i][0]; cy += pts[i][1]; cz += pts[i][2];
  }
  centroids[key] = new THREE.Vector3(cx/N, cy/N, cz/N);

  const geo  = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
  const mat  = new THREE.PointsMaterial({
    color: col, size: pop.size, sizeAttenuation: true,
    transparent: true, opacity: 0.92, depthWrite: false,
  });
  const cloud = new THREE.Points(geo, mat);
  scene.add(cloud);
  pointClouds[key] = { cloud, mat, color: col, mean_fr: pop.mean_fr };

  // Layer plane sized to the population's XY spread
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const hw = (Math.max(...xs) - Math.min(...xs)) / 2 + 0.8;
  const hh = (Math.max(...ys) - Math.min(...ys)) / 2 + 0.8;
  mkLayerPlane(pop.z_center, pop.color, hw, hh);

  // Label
  mkLabel(pop.label, pop.color, pop.z_center, 0, Math.max(...ys) + 1.4, 7.5, 0.65);
}

// ── Connection bundles ───────────────────────────────────────────────────────
const PATHWAYS = [
  ["MSN_d1","GPi",  "#34d399", 0.28],
  ["MSN_d2","GPe",  "#fb7185", 0.22],
  ["GPe",   "STN",  "#fbbf24", 0.22],
  ["GPe",   "GPi",  "#fbbf24", 0.18],
  ["STN",   "GPi",  "#a78bfa", 0.28],
  ["FSI",   "MSN_d1","#f97316",0.16],
  ["FSI",   "MSN_d2","#f97316",0.16],
];
for (const [src, tgt, col, op] of PATHWAYS) {
  if (centroids[src] && centroids[tgt])
    mkConnectionBundle(centroids[src], centroids[tgt], col, op, 8, 0.7);
}

// ── Legend ──────────────────────────────────────────────────────────────────
const legend = document.getElementById('legend');
for (const key of popKeys) {
  const pop = data[key];
  const fr  = pop.mean_fr.toFixed(2);
  legend.innerHTML +=
    `<div class="lr"><div class="ld" style="background:${pop.color}"></div>` +
    `${pop.label} &nbsp; <span style="color:${pop.color}">${fr} Hz</span></div>`;
}

// ── Info panel ───────────────────────────────────────────────────────────────
const infoEl = document.getElementById('info');
const totalN = popKeys.reduce((s,k) => s + data[k].positions.length, 0);
infoEl.innerHTML = `${totalN} neurons shown<br>${popKeys.length} populations<br>resting state`;

// ── Grid ────────────────────────────────────────────────────────────────────
const grid = new THREE.GridHelper(50, 50, 0x0c1222, 0x0c1222);
grid.position.set(0, -5, 0);
scene.add(grid);

// ── Resize ───────────────────────────────────────────────────────────────────
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ── Animation ────────────────────────────────────────────────────────────────
// Each population pulses at a frequency proportional to its mean firing rate.
// Base reference: 60 Hz → pulse period ~1.5 s; 1 Hz → very slow.
let t = 0;
function animate() {
  requestAnimationFrame(animate);
  t += 0.016;

  for (const key of popKeys) {
    const { mat, mean_fr } = pointClouds[key];
    const freq  = Math.max(mean_fr / 40.0, 0.05);   // pulse frequency in rad/s
    const pulse = 0.75 + 0.25 * Math.sin(t * freq * Math.PI * 2);
    mat.opacity = 0.65 + 0.35 * pulse;
    mat.size    = data[key].size * (0.85 + 0.15 * pulse);
    mat.needsUpdate = true;
  }

  controls.update();
  renderer.render(scene, camera);
}
animate();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------

def _plot_mean_fr(mean_fr: dict) -> plt.Figure:
    nuclei = [n for n in _REAL_NUCLEI if n in mean_fr]
    rates  = [mean_fr[n] for n in nuclei]
    colors = []
    for n, r in zip(nuclei, rates):
        if n in _TARGET_RATES:
            lo, hi = _TARGET_RATES[n]
            colors.append("#2ecc71" if lo <= r <= hi else "#e74c3c")
        else:
            colors.append("#3498db")

    fig, ax = plt.subplots(figsize=(9, 4))
    x = np.arange(len(nuclei))
    bars = ax.bar(x, rates, color=colors, width=0.6, zorder=3)

    for i, n in enumerate(nuclei):
        if n in _TARGET_RATES:
            lo, hi = _TARGET_RATES[n]
            ax.plot([i-0.3, i+0.3], [lo, lo], color="black", lw=1.5, zorder=4)
            ax.plot([i-0.3, i+0.3], [hi, hi], color="black", lw=1.5, zorder=4)
            ax.plot([i, i], [lo, hi], color="black", lw=1.0, ls="--", zorder=4)

    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+0.3,
                f"{rate:.2f}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(nuclei, fontsize=10)
    ax.set_ylabel("Firing rate (Hz)")
    ax.set_title("BG Resting State — Mean Firing Rates\n"
                 "green = within target range, red = outside")
    ax.grid(axis="y", alpha=0.3, zorder=0)
    fig.tight_layout()
    return fig


def _plot_rasters(spike_data, t_start, t_end, max_neurons) -> plt.Figure:
    nuclei   = [n for n in _REAL_NUCLEI if n in spike_data]
    n_panels = len(nuclei)
    fig, axes = plt.subplots(n_panels, 1, figsize=(12, 2.0*n_panels), sharex=True)
    if n_panels == 1:
        axes = [axes]

    colors = {
        "MSN_d1": "#1565c0", "MSN_d2": "#0d47a1",
        "FSI":    "#e65100", "STN":    "#6a1b9a",
        "GPe":    "#2e7d32", "GPi":    "#c62828",
    }

    for ax, nucleus in zip(axes, nuclei):
        times, senders = spike_data[nucleus]
        if len(times) == 0:
            ax.text(0.5, 0.5, "no spikes", transform=ax.transAxes,
                    ha="center", va="center", color="gray")
            ax.set_ylabel(nucleus, fontsize=9)
            continue

        unique_gids = np.unique(senders)
        if len(unique_gids) > max_neurons:
            chosen = np.random.choice(unique_gids, size=max_neurons, replace=False)
            mask   = np.isin(senders, chosen)
            times_plot   = times[mask]
            senders_plot = senders[mask]
        else:
            times_plot, senders_plot = times, senders

        gid_map = {g: i for i, g in enumerate(np.unique(senders_plot))}
        y = np.array([gid_map[g] for g in senders_plot], dtype=float)

        ax.vlines(times_plot, y-0.45, y+0.45,
                  colors=colors.get(nucleus, "#333333"),
                  linewidth=1.2, alpha=1.0, rasterized=True)
        ax.set_ylabel(nucleus, fontsize=9)
        ax.set_xlim(t_start, t_end)
        ax.set_ylim(-1, len(gid_map))
        ax.tick_params(axis="y", labelsize=7)
        n_shown = len(gid_map)
        n_total = len(np.unique(spike_data[nucleus][1]))
        ax.text(0.99, 0.95, f"{n_shown}/{n_total} neurons shown",
                transform=ax.transAxes, ha="right", va="top", fontsize=7, color="gray")

    axes[-1].set_xlabel("Time (ms)")
    fig.suptitle("BG Resting State — Spike Rasters", fontsize=12, y=1.01)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Spike file aggregator
# ---------------------------------------------------------------------------

def _collect_spikes(data_path: str, nucleus: str):
    times_list, senders_list = [], []
    if not os.path.isdir(data_path):
        return np.array([], dtype=np.float64), np.array([], dtype=np.int64)
    for fname in sorted(os.listdir(data_path)):
        if not (fname.startswith(nucleus + "-") and fname.endswith(".dat")):
            continue
        with open(os.path.join(data_path, fname)) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        senders_list.append(int(float(parts[0])))
                        times_list.append(float(parts[1]))
                    except ValueError:
                        pass
    times   = np.array(times_list,   dtype=np.float64)
    senders = np.array(senders_list, dtype=np.int64)
    if len(times) > 0:
        order   = np.argsort(times)
        times   = times[order]
        senders = senders[order]
    return times, senders
