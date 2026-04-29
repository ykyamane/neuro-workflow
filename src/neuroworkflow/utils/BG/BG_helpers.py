"""
NEST 3 Basal Ganglia helpers — adapted from nest_routine.py and ini_all.py
by Girard et al. (top_BG_nest3 model).

Provides three public functions used by the BG nodes:
  - initialize_nest(sim_params)
  - build_bg_network(bg_params, sim_params) -> (bg_layers, detectors)
  - read_spikes(detectors, bg_layers, sim_params) -> (mean_fr, at_fr)
"""

import collections
import math
import os
import random

import nest
import numpy as np


# ---------------------------------------------------------------------------
# NEST kernel
# ---------------------------------------------------------------------------

def initialize_nest(sim_params):
    nest.ResetKernel()
    nest.set_verbosity("M_WARNING")
    nest.SetKernelStatus({"overwrite_files": True})
    nest.SetKernelStatus({"local_num_threads": int(sim_params["nbcpu"])})
    nest.SetKernelStatus({"data_path": sim_params["data_path"]})
    if str(sim_params["dt"]) != "0.1":
        nest.SetKernelStatus({"resolution": float(sim_params["dt"])})
    N_vp = nest.GetKernelStatus("total_num_virtual_procs")
    seed = sim_params["msd"]
    global _pyrngs
    _pyrngs = [np.random.RandomState(s) for s in range(seed, seed + N_vp)]
    nest.SetKernelStatus({"rng_seed": seed})
    print(f"[NEST] kernel ready — {N_vp} virtual procs, seed={seed}")


# ---------------------------------------------------------------------------
# Network build (public entry point)
# ---------------------------------------------------------------------------

def build_bg_network(bg_params, sim_params):
    """Create all BG populations, connect them, attach spike recorders.

    Returns
    -------
    bg_layers : dict  {nucleus: NodeCollection}
    detectors : dict  {nucleus: spike_recorder}
    """
    os.makedirs(sim_params["data_path"], exist_ok=True)

    bg_params = dict(bg_params)  # shallow copy so we can add keys
    _scale_populations(bg_params, sim_params["scalefactor"])

    bg_params["circle_center"] = _get_channel_centers(
        sim_params["data_path"],
        sim_params["channels"],
        sim_params["channels_nb"],
        sim_params["hex_radius"],
    )

    bg_layers = _instantiate_bg(bg_params, sim_params)
    detectors = _attach_detectors(bg_layers, sim_params)
    return bg_layers, detectors


# ---------------------------------------------------------------------------
# Firing-rate analysis
# ---------------------------------------------------------------------------

def read_spikes(detectors, bg_layers, sim_params):
    """Compute mean and instantaneous firing rates from spike recorders.

    Returns
    -------
    mean_fr : dict  {nucleus: float Hz}
    at_fr   : dict  {nucleus: list of 1-ms-binned rates}
    """
    analysis_duration = sim_params["simDuration"] - sim_params["start_time_sp"]
    dt = float(sim_params["dt"])
    mean_fr = {}
    at_fr = {}
    for nucleus, detector in detectors.items():
        if nucleus not in bg_layers:
            continue  # skip combined MSN recorder (no matching layer key)
        n = len(bg_layers[nucleus])
        mean_fr[nucleus] = _average_fr(detector, analysis_duration, n)
        at_fr[nucleus] = list(
            _instantaneous_fr(
                detector,
                sim_params["start_time_sp"],
                sim_params["simDuration"],
                n,
                dt,
            )
        )
    return mean_fr, at_fr


# ---------------------------------------------------------------------------
# Internal helpers — population scaling & channel centres
# ---------------------------------------------------------------------------

_pyrngs = []


def _scale_populations(bg_params, scalefactor):
    for nucleus in ["MSN", "FSI", "STN", "GPe", "GPi", "CSN", "PTN", "CMPf"]:
        bg_params["nb" + nucleus] = (
            bg_params["nb" + nucleus] * scalefactor[0] * scalefactor[1]
        )


def _get_channel_centers(data_path, channels, channels_nb, hex_radius):
    if not channels:
        return []
    centers = []
    for i in range(channels_nb):
        angle_deg = 60 * i - 30
        angle_rad = math.pi / 180 * angle_deg
        centers.append(
            [hex_radius * math.cos(angle_rad), hex_radius * math.sin(angle_rad)]
        )
    np.savetxt(os.path.join(data_path, "centers.txt"), centers)
    return centers


# ---------------------------------------------------------------------------
# Internal helpers — layer creation
# ---------------------------------------------------------------------------

def _grid_uniform_positions(n):
    return [
        [np.random.uniform(-0.5, 0.5), np.random.uniform(-0.5, 0.5)]
        for _ in range(n)
    ]


def _grid_positions(n, a0, a1, b0, b1):
    n_sq = int(np.ceil(np.sqrt(n)))
    coords = [
        [x / n_sq * a1 - a0, y / n_sq * b1 - b0]
        for x in range(n_sq)
        for y in range(n_sq)
    ]
    if len(coords) > n:
        idx = np.sort(_pyrngs[0].choice(len(coords), size=n, replace=False))
        coords = [coords[i] for i in idx]
    return coords


def _save_positions(data_path, nucleus, layer_gid, positions):
    node_ids = np.array(layer_gid.tolist())
    arr = np.column_stack((node_ids, positions))
    np.savetxt(os.path.join(data_path, nucleus + ".txt"), arr, fmt="%1.3f")
    if nucleus == "MSN":
        half = len(arr) // 2
        np.savetxt(os.path.join(data_path, "MSN_d1.txt"), arr[:half], fmt="%1.3f")
        np.savetxt(os.path.join(data_path, "MSN_d2.txt"), arr[half:], fmt="%1.3f")


def _create_layer(bg_params, nucleus, scalefactor, data_path, fake_rate=0.0):
    sf = scalefactor
    extent = [1.0 * int(sf[0]) + 1.0, 1.0 * int(sf[1]) + 1.0]

    if nucleus == "GPi_fake":
        pop_size = int(bg_params["nbGPi"])
        positions_z = _pyrngs[0].uniform(0.0, 0.5, pop_size).tolist()
        gpi_pos = np.loadtxt(os.path.join(data_path, "GPi.txt"))
        position_nD = [
            [gpi_pos[i, 1], gpi_pos[i, 2], positions_z[i]] for i in range(pop_size)
        ]
        extent = extent + [1.0]
        spatial_pos = nest.spatial.free(position_nD, extent=extent, edge_wrap=True)
        layer_gid = nest.Create("parrot_neuron", positions=spatial_pos)
        _save_positions(data_path, nucleus, layer_gid, np.array(position_nD))
        return layer_gid

    pop_size = int(bg_params["nb" + nucleus])
    print(f"  population size for {nucleus}: {pop_size}")

    if nucleus == "MSN":
        positions = _grid_uniform_positions(pop_size)
        half = pop_size // 2
        nest.SetDefaults("iaf_psc_alpha_multisynapse", bg_params["common_iaf"])
        nest.SetDefaults("iaf_psc_alpha_multisynapse", bg_params["MSN_iaf"])
        nest.SetDefaults("iaf_psc_alpha_multisynapse", {"I_e": bg_params["IeMSN"]})
        nest.CopyModel("iaf_psc_alpha_multisynapse", "msn_d1")
        nest.CopyModel("iaf_psc_alpha_multisynapse", "msn_d2")
        pos_half = positions[:half]
        layer_d1 = nest.Create("msn_d1", positions=nest.spatial.free(pos_half, extent=extent, edge_wrap=True))
        layer_d2 = nest.Create("msn_d2", positions=nest.spatial.free(pos_half, extent=extent, edge_wrap=True))
        _save_positions(data_path, "MSN_d1", layer_d1, np.array(pos_half))
        _save_positions(data_path, "MSN_d2", layer_d2, np.array(pos_half))
        return layer_d1, layer_d2

    # GPi and STN get a tighter grid
    if nucleus in ("GPi", "STN"):
        raw = _grid_positions(pop_size, 0.4 * sf[0], sf[0] - 0.1, 0.4 * sf[1], sf[1] - 0.1)
    else:
        raw = _grid_positions(pop_size, 0.5 * sf[0], sf[0], 0.5 * sf[1], sf[1])
    position_nD = raw

    if fake_rate > 0.0:
        spatial_pos = nest.spatial.free(position_nD, extent=extent, edge_wrap=True)
        layer_gid = nest.Create("parrot_neuron", positions=spatial_pos)
        _save_positions(data_path, nucleus, layer_gid, np.array(position_nD))
        poisson = nest.Create("poisson_generator", 1)
        poisson.set({"rate": fake_rate})
        nest.Connect(poisson, layer_gid, conn_spec={"rule": "all_to_all"})
        return layer_gid

    nest.SetDefaults("iaf_psc_alpha_multisynapse", bg_params["common_iaf"])
    nest.SetDefaults("iaf_psc_alpha_multisynapse", bg_params[nucleus + "_iaf"])
    nest.SetDefaults("iaf_psc_alpha_multisynapse", {"I_e": bg_params["Ie" + nucleus]})
    spatial_pos = nest.spatial.free(position_nD, extent=extent, edge_wrap=True)
    layer_gid = nest.Create("iaf_psc_alpha_multisynapse", positions=spatial_pos)
    _save_positions(data_path, nucleus, layer_gid, np.array(position_nD))
    return layer_gid


# ---------------------------------------------------------------------------
# Internal helpers — network instantiation
# ---------------------------------------------------------------------------

def _instantiate_bg(bg_params, sim_params):
    sf = sim_params["scalefactor"]
    data_path = sim_params["data_path"]
    bg_layers = {}

    print("--- BG instantiation ---")
    for nucleus in ["GPi", "MSN", "FSI", "STN", "GPe", "GPi_fake"]:
        print(f"Creating {nucleus}...")
        result = _create_layer(bg_params, nucleus, sf, data_path)
        if nucleus == "MSN":
            bg_layers["MSN_d1"], bg_layers["MSN_d2"] = result
        else:
            bg_layers[nucleus] = result

    # GPi 2D → GPi_fake 3D (one-to-one parrot relay)
    nest.SetDefaults("static_synapse", {"receptor_type": 0})
    nest.Connect(bg_layers["GPi"], bg_layers["GPi_fake"], conn_spec={"rule": "one_to_one"})

    # Fake cortical / thalamic inputs (Poisson)
    fake_rates = {
        "CSN": bg_params["normalrate"]["CSN"][0],
        "PTN": bg_params["normalrate"]["PTN"][0],
        "CMPf": bg_params["normalrate"]["CMPf"][0],
    }
    for fake_nucleus, rate in fake_rates.items():
        print(f"Creating fake input {fake_nucleus} @ {rate} Hz...")
        bg_layers[fake_nucleus] = _create_layer(bg_params, fake_nucleus, sf, data_path, fake_rate=rate)

    # Dopamine STDP synapses (needed even in resting state because plastic_syn=True)
    if bg_params["plastic_syn"]:
        bg_params["vt_d1"] = nest.Create("volume_transmitter")
        bg_params["vt_d2"] = nest.Create("volume_transmitter")
        nest.CopyModel("stdp_dopamine_synapse_lbl", "syn_d1")
        nest.SetDefaults("syn_d1", {
            "volume_transmitter": bg_params["vt_d1"],
            "A_plus": 0.013, "A_minus": 0.013 / 4.0,
            "Wmax": 4.0, "b": 0.0, "n": 0.0, "c": 0.0,
            "tau_plus": 20.0, "tau_n": 100.0, "tau_c": 700.0,
        })
        nest.CopyModel("stdp_dopamine_synapse_lbl", "syn_d2")
        nest.SetDefaults("syn_d2", {
            "volume_transmitter": bg_params["vt_d2"],
            "A_plus": 0.013, "A_minus": -0.013,
            "Wmax": 4.0, "b": 0.0, "n": 0.0, "c": 0.0,
            "tau_plus": 20.0, "tau_n": 100.0, "tau_c": 700.0,
        })

    # Wire all 36 projections
    print("--- BG connections ---")
    bg_params["alpha"] = collections.OrderedDict(
        sorted(bg_params["alpha"].items())
    )
    for connection in bg_params["alpha"]:
        src = connection[:3]
        tgt = connection[-3:]
        if src == "CMP":
            src = "CMPf"
        if src in ["MSN", "FSI", "STN", "GPe", "GPi", "CMPf", "CSN", "PTN"]:
            n_type = "in" if src in ["MSN", "FSI", "GPe", "GPi"] else "ex"
            _connect_layers(
                bg_params, n_type, bg_layers, src, tgt,
                proj_type=bg_params["cType" + src + tgt],
                redundancy=bg_params["redundancy" + src + tgt],
                scalefactor=sf,
            )

    return bg_layers


# ---------------------------------------------------------------------------
# Internal helpers — spike recorders
# ---------------------------------------------------------------------------

def _attach_detectors(bg_layers, sim_params):
    ignore_time = sim_params["start_time_sp"]
    detectors = {}
    for nucleus, layer in bg_layers.items():
        params = {"record_to": "ascii", "label": nucleus, "start": float(ignore_time)}
        det = nest.Create("spike_recorder", params=params)
        nest.Connect(layer, det)
        detectors[nucleus] = det
    # Combined MSN recorder (d1 + d2 together)
    msn_params = {"record_to": "ascii", "label": "MSN", "start": float(ignore_time)}
    detectors["MSN"] = nest.Create("spike_recorder", params=msn_params)
    nest.Connect(bg_layers["MSN_d1"], detectors["MSN"])
    nest.Connect(bg_layers["MSN_d2"], detectors["MSN"])
    return detectors


def _average_fr(detector, duration_ms, n_neurons):
    return detector.get("n_events") / (float(duration_ms) * float(n_neurons) / 1000.0)


def _instantaneous_fr(detector, sim_start, sim_end, n_neurons, dt=0.1):
    filenames = detector.get("filenames")
    if isinstance(filenames, str):
        filenames = [filenames]
    spike_times = []
    for fname in (filenames or []):
        if fname and os.path.isfile(fname):
            with open(fname) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            spike_times.append(float(parts[1]))
                        except ValueError:
                            pass
    spike_times = np.array(spike_times)
    at = []
    for t in np.arange(int(sim_start), int(sim_end), dt):
        count = ((t <= spike_times) & (spike_times < (t + 1))).sum()
        at.append(count)
    return np.array(at) / float(n_neurons) * 1000.0


# ---------------------------------------------------------------------------
# Internal helpers — synaptic weight calculation
# ---------------------------------------------------------------------------

def _get_input_range(bg_params, src, tgt):
    cnt_src = bg_params["count" + src]
    cnt_tgt = bg_params["count" + tgt]
    if src in ("CSN", "PTN"):
        nu = bg_params["alpha"][src + "->" + tgt]
        return [0, nu]
    nu = cnt_src / float(cnt_tgt) * bg_params["ProjPercent"][src + "->" + tgt] * bg_params["alpha"][src + "->" + tgt]
    nu0 = cnt_src / float(cnt_tgt) * bg_params["ProjPercent"][src + "->" + tgt]
    return [nu0, nu]


def _compute_weight(bg_params, rec_types, src, tgt, in_degree, gain=1.0):
    nu = _get_input_range(bg_params, src, tgt)[1]
    lx_tgt = bg_params["lx"][tgt] if tgt in bg_params["lx"] else bg_params["lx"].get(tgt, 0.001)
    if tgt not in bg_params["lx"]:
        return {r: 0.0 for r in rec_types}
    LX = lx_tgt * math.sqrt(4.0 * bg_params["Ri"] / (bg_params["dx"][tgt] * bg_params["Rm"]))
    attenuation = math.cosh(LX * (1 - bg_params["distcontact"][src + "->" + tgt])) / math.cosh(LX)
    rec_idx = {"AMPA": 0, "NMDA": 1, "GABA": 2}
    w = {}
    for r in rec_types:
        w[r] = nu / float(in_degree) * attenuation * bg_params["wPSP"][rec_idx[r]] * gain
    return w


# ---------------------------------------------------------------------------
# Internal helpers — connectivity
# ---------------------------------------------------------------------------

def _compute_indegree(bg_params, src, tgt, redundancy):
    return _get_input_range(bg_params, src, tgt)[1] / float(redundancy)


def _connect_layers(bg_params, n_type, bg_layers, src, tgt,
                    proj_type, redundancy, scalefactor):
    in_degree = _compute_indegree(bg_params, src, tgt, redundancy)
    if in_degree == 0.0:
        return

    rec_map = {"AMPA": 1, "NMDA": 2, "GABA": 3}

    if n_type == "ex":
        rec_types = ["AMPA", "NMDA"]
        lbl = _next_ampa_label()
    elif n_type == "in":
        rec_types = ["GABA"]
        lbl = 0
    else:
        raise ValueError(f"Unknown n_type: {n_type}")

    # Gain overrides for specific pathways
    if src == "GPe" and tgt == "STN":
        gain = bg_params["GGPe_STN"]
    elif src == "STN" and tgt == "GPi":
        gain = bg_params["GSTN_GPi"]
    elif src == "MSN" and tgt == "MSN":
        gain = bg_params["GMSN_MSN"]
    elif src == "MSN" and tgt in ("GPi", "GPe") and bg_params["plastic_syn"]:
        gain = bg_params["GMSN_GPx"]
    else:
        gain = 1.0

    W = _compute_weight(bg_params, rec_types, src, tgt, in_degree, gain)
    delay = bg_params["tau"][src + "->" + tgt]
    spread = (
        bg_params["spread_focused"] if proj_type == "focused"
        else bg_params["spread_diffuse"] * max(scalefactor)
    )

    ampa_spec = {
        "synapse_model": "static_synapse_lbl",
        "synapse_label": lbl,
        "receptor_type": rec_map["AMPA"],
        "weight": W["AMPA"] if "AMPA" in W else W["GABA"],
        "delay": delay,
    }
    if n_type == "ex":
        nmda_spec = {
            "synapse_model": "static_synapse_lbl",
            "synapse_label": lbl,
            "receptor_type": rec_map["NMDA"],
            "weight": W["NMDA"],
            "delay": delay,
        }
        syn_spec = nest.CollocatedSynapses(ampa_spec, nmda_spec)
    else:
        syn_spec = ampa_spec

    _mass_connect(bg_params, bg_layers, src, tgt, lbl, in_degree,
                  rec_map["AMPA"] if n_type == "ex" else rec_map["GABA"],
                  W["AMPA"] if "AMPA" in W else W["GABA"],
                  delay, spread, ampa_spec, syn_spec, n_type,
                  nmda_spec=(nmda_spec if n_type == "ex" else None),
                  nmda_weight=(W.get("NMDA") if n_type == "ex" else None))


_ampa_counter = 0


def _next_ampa_label():
    global _ampa_counter
    _ampa_counter += 1
    return _ampa_counter


def _mass_connect(bg_params, bg_layers, src, tgt, lbl, in_degree,
                  receptor_type, weight, delay, spread,
                  ampa_spec, syn_spec, n_type,
                  nmda_spec=None, nmda_weight=None):
    int_deg = int(math.floor(in_degree))
    base_conn = {
        "rule": "fixed_indegree",
        "indegree": int_deg,
        "mask": {"circular": {"radius": spread}},
        "allow_oversized_mask": True,
        "allow_multapses": True,
    }

    if int_deg > 0:
        if (src, tgt) in (("CSN", "MSN"), ("PTN", "MSN")) and bg_params["plastic_syn"]:
            w_p = weight * bg_params["plast_gain"]
            d1_spec = dict(ampa_spec, synapse_model="syn_d1", weight=w_p)
            d2_spec = dict(ampa_spec, synapse_model="syn_d2",
                           synapse_label=lbl + 1000, weight=w_p)
            if nmda_spec is not None:
                w_p_n = nmda_weight * bg_params["plast_gain"]
                nd1 = dict(nmda_spec, synapse_model="syn_d1", weight=w_p_n)
                nd2 = dict(nmda_spec, synapse_model="syn_d2",
                           synapse_label=lbl + 1000, weight=w_p_n)
                syn_d1 = nest.CollocatedSynapses(d1_spec, nd1)
                syn_d2 = nest.CollocatedSynapses(d2_spec, nd2)
            else:
                syn_d1, syn_d2 = d1_spec, d2_spec
            nest.Connect(bg_layers[src], bg_layers["MSN_d1"], conn_spec=base_conn, syn_spec=syn_d1)
            nest.Connect(bg_layers[src], bg_layers["MSN_d2"], conn_spec=base_conn, syn_spec=syn_d2)

        elif src == "MSN" and tgt in ("GPe", "GPi"):
            if tgt == "GPi":
                n_d1 = int(int_deg * (1.0 - bg_params["overlap_d1d2"]))
                n_d2 = int(int_deg * bg_params["overlap_d1d2"])
            else:
                n_d1 = int(int_deg * bg_params["overlap_d1d2"])
                n_d2 = int(int_deg * (1.0 - bg_params["overlap_d1d2"]))
            nest.Connect(bg_layers["MSN_d1"], bg_layers[tgt],
                         conn_spec=dict(base_conn, indegree=n_d1), syn_spec=syn_spec)
            nest.Connect(bg_layers["MSN_d2"], bg_layers[tgt],
                         conn_spec=dict(base_conn, indegree=n_d2), syn_spec=syn_spec)

        elif src == "MSN" and tgt == "MSN":
            n_a1 = int(int_deg * bg_params["asymmetry_1"])
            n_a2 = int(int_deg * bg_params["asymmetry_2"])
            asym_syn = dict(ampa_spec, weight=weight * bg_params["syn_asymm"])
            nest.Connect(bg_layers["MSN_d2"], bg_layers["MSN_d2"],
                         conn_spec=dict(base_conn, indegree=n_a1), syn_spec=asym_syn)
            nest.Connect(bg_layers["MSN_d2"], bg_layers["MSN_d1"],
                         conn_spec=dict(base_conn, indegree=n_a1), syn_spec=asym_syn)
            nest.Connect(bg_layers["MSN_d1"], bg_layers["MSN_d1"],
                         conn_spec=dict(base_conn, indegree=n_a1), syn_spec=ampa_spec)
            nest.Connect(bg_layers["MSN_d1"], bg_layers["MSN_d2"],
                         conn_spec=dict(base_conn, indegree=n_a2), syn_spec=ampa_spec)

        elif tgt == "MSN":
            nest.Connect(bg_layers[src], bg_layers["MSN_d1"], conn_spec=base_conn, syn_spec=syn_spec)
            nest.Connect(bg_layers[src], bg_layers["MSN_d2"], conn_spec=base_conn, syn_spec=syn_spec)

        else:
            nest.Connect(bg_layers[src], bg_layers[tgt], conn_spec=base_conn, syn_spec=syn_spec)

    # Fractional remainder via pairwise_bernoulli
    frac = in_degree - math.floor(in_degree)
    remaining = round(frac * bg_params["nb" + tgt])
    if remaining > 0:
        p = 1.0 / (bg_params["nb" + src] * float(remaining))
        fconn = {
            "rule": "pairwise_bernoulli", "p": p,
            "mask": {"circular": {"radius": spread}},
            "allow_oversized_mask": True, "allow_multapses": True,
        }
        if tgt == "MSN":
            nest.Connect(bg_layers[src], bg_layers["MSN_d1"], conn_spec=fconn, syn_spec=syn_spec)
            nest.Connect(bg_layers[src], bg_layers["MSN_d2"], conn_spec=fconn, syn_spec=syn_spec)
        elif src == "MSN":
            nest.Connect(bg_layers["MSN_d1"], bg_layers[tgt], conn_spec=fconn, syn_spec=syn_spec)
            nest.Connect(bg_layers["MSN_d2"], bg_layers[tgt], conn_spec=fconn, syn_spec=syn_spec)
        else:
            nest.Connect(bg_layers[src], bg_layers[tgt], conn_spec=fconn, syn_spec=syn_spec)
