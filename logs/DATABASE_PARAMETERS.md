# Database Parameters Reference

This document lists all parameters that can be fetched from the neuroscience databases integrated into the NeuroWorkflow parameter metadata service.

## Overview

The system supports two main databases:
1. **Allen Brain Atlas** - Electrophysiology parameters (56 fields)
2. **NeuroMorpho.org** - Morphological parameters (16 fields)

Additionally, the system uses **AI-powered semantic mapping** to automatically match unmapped parameters to database fields.

---

## 📊 Allen Brain Atlas Parameters

### Manually Mapped Parameters

These parameters have direct mappings to Allen Brain Atlas fields:

| NeuroWorkflow Parameter | Allen Brain Atlas Field | Notes |
|------------------------|------------------------|-------|
| `firing_rate`, `spike_rate`, `rate` | Calculated from `avg_isi` | Special case: `firing_rate = 1000.0 / avg_isi` (ms to Hz) |
| `input_resistance`, `r_input`, `membrane_resistance` | `input_resistance_mohm` | Input resistance in megaohms |
| `rheobase` | `rheobase_sweep_number` | Rheobase sweep number |
| `adaptation` | `adaptation` | Adaptation index |
| `avg_isi`, `isi` | `avg_isi` | Average inter-spike interval (ms) |
| `latency` | `latency` | Latency (ms) |
| `ri` | `ri` | Rebound index |
| `f_i_curve_slope` | `f_i_curve_slope` | F-I curve slope |
| `peak_v_long_square` | `peak_v_long_square` | Peak voltage (long square protocol) |
| `peak_v_short_square` | `peak_v_short_square` | Peak voltage (short square protocol) |
| `fast_trough_v_long_square` | `fast_trough_v_long_square` | Fast trough voltage (long square) |

### All Available Fields (56 total)

The following fields are available in Allen Brain Atlas and can be accessed via AI-powered mapping:

1. `adaptation` - Adaptation index
2. `avg_isi` - Average inter-spike interval (ms)
3. `electrode_0_pa` - Electrode current (pA)
4. `f_i_curve_slope` - F-I curve slope
5. `fast_trough_t_long_square` - Fast trough time (long square)
6. `fast_trough_t_ramp` - Fast trough time (ramp)
7. `fast_trough_t_short_square` - Fast trough time (short square)
8. `fast_trough_v_long_square` - Fast trough voltage (long square)
9. `fast_trough_v_ramp` - Fast trough voltage (ramp)
10. `fast_trough_v_short_square` - Fast trough voltage (short square)
11. `has_burst` - Has burst (boolean)
12. `has_delay` - Has delay (boolean)
13. `has_pause` - Has pause (boolean)
14. `id` - Feature ID
15. `input_resistance_mohm` - Input resistance (MΩ)
16. `latency` - Latency (ms)
17. `peak_t_long_square` - Peak time (long square)
18. `peak_t_ramp` - Peak time (ramp)
19. `peak_t_short_square` - Peak time (short square)
20. `peak_v_long_square` - Peak voltage (long square)
21. `peak_v_ramp` - Peak voltage (ramp)
22. `peak_v_short_square` - Peak voltage (short square)
23. `rheobase_sweep_id` - Rheobase sweep ID
24. `rheobase_sweep_number` - Rheobase sweep number
25. `ri` - Rebound index
26. `sag` - Sag
27. `seal_gohm` - Seal resistance (GΩ)
28. `slow_trough_t_long_square` - Slow trough time (long square)
29. `slow_trough_t_ramp` - Slow trough time (ramp)
30. `slow_trough_t_short_square` - Slow trough time (short square)
31. `slow_trough_v_long_square` - Slow trough voltage (long square)
32. `slow_trough_v_ramp` - Slow trough voltage (ramp)
33. `slow_trough_v_short_square` - Slow trough voltage (short square)
34. `specimen_id` - Specimen ID
35. `tau` - Time constant (ms)
36. `threshold_i_long_square` - Threshold current (long square)
37. `threshold_i_ramp` - Threshold current (ramp)
38. `threshold_i_short_square` - Threshold current (short square)
39. `threshold_t_long_square` - Threshold time (long square)
40. `threshold_t_ramp` - Threshold time (ramp)
41. `threshold_t_short_square` - Threshold time (short square)
42. `threshold_v_long_square` - Threshold voltage (long square)
43. `threshold_v_ramp` - Threshold voltage (ramp)
44. `threshold_v_short_square` - Threshold voltage (short square)
45. `thumbnail_sweep_id` - Thumbnail sweep ID
46. `trough_t_long_square` - Trough time (long square)
47. `trough_t_ramp` - Trough time (ramp)
48. `trough_t_short_square` - Trough time (short square)
49. `trough_v_long_square` - Trough voltage (long square)
50. `trough_v_ramp` - Trough voltage (ramp)
51. `trough_v_short_square` - Trough voltage (short square)
52. `trough_v_ramp` - Trough voltage (ramp)
53. `trough_v_short_square` - Trough voltage (short square)
54. `upstroke_downstroke_ratio_long_square` - Upstroke/downstroke ratio (long square)
55. `upstroke_downstroke_ratio_ramp` - Upstroke/downstroke ratio (ramp)
56. `upstroke_downstroke_ratio_short_square` - Upstroke/downstroke ratio (short square)

---

## 📐 NeuroMorpho.org Parameters

### Manually Mapped Parameters

These parameters have direct mappings to NeuroMorpho fields:

| NeuroWorkflow Parameter | NeuroMorpho Field | Notes |
|------------------------|------------------|-------|
| `soma_surface` | `surface` | Soma surface area |
| `soma_volume` | `volume` | Soma volume |
| `total_length` | `pathDistance` | Total path length (or `eucDistance` for euclidean) |
| `total_volume` | `volume` | Total volume |
| `number_stems` | `n_stems` | Number of stems |
| `number_bifurcations` | `n_bifs` | Number of bifurcations |
| `width` | `width` | Width |
| `height` | `height` | Height |
| `depth` | `depth` | Depth |
| `diameter`, `dendrite_diameter`, `axon_diameter` | `diameter` | Diameter |
| `path_length` | `pathDistance` | Path distance |
| `euclidean_distance` | `eucDistance` | Euclidean distance |
| `branch_order` | `branch_Order` | Branch order |
| `contraction` | `contraction` | Contraction |
| `fragmentation` | `fragmentation` | Fragmentation |
| `partition_asymmetry` | `partition_asymmetry` | Partition asymmetry |
| `fractal_dimension` | `fractal_Dim` | Fractal dimension |

### All Available Fields (16 total)

1. `surface` - Surface area
2. `volume` - Volume
3. `n_stems` - Number of stems
4. `n_bifs` - Number of bifurcations
5. `n_branch` - Number of branches
6. `width` - Width
7. `height` - Height
8. `depth` - Depth
9. `diameter` - Diameter
10. `eucDistance` - Euclidean distance
11. `pathDistance` - Path distance
12. `branch_Order` - Branch order
13. `contraction` - Contraction
14. `fragmentation` - Fragmentation
15. `partition_asymmetry` - Partition asymmetry
16. `fractal_Dim` - Fractal dimension

---

## 🤖 AI-Powered Automatic Mapping

For parameters **not** in the manual mappings above, the system uses **AI semantic matching** to automatically find the best matching field from the available database fields.

### How It Works

1. **Manual Mapping** (fastest) - Checks if parameter is in the manual mapping table
2. **AI Semantic Matching** (if enabled) - Uses OpenAI to semantically match parameter name + description to database fields
3. **Fuzzy String Matching** (fallback) - Uses fuzzy string matching to find similar field names

### Example

If you request `membrane_time_constant`:
- Not in manual mappings
- AI analyzes: "membrane time constant" → matches to `tau` in Allen Brain Atlas
- Returns real database values for `tau`

---

## 📝 Notes

### Calculated Parameters

- **`firing_rate`**: Calculated from `avg_isi` using formula: `firing_rate = 1000.0 / avg_isi` (converts ms to Hz)

### Species Support

Both databases support filtering by species:
- **Allen Brain Atlas**: `mouse`, `human`, `rat`, `monkey` (mapped to scientific names)
- **NeuroMorpho**: `mouse`, `rat`, `human`, `monkey`, `cat`

### Data Quality

- **Allen Brain Atlas**: ~1,800+ cells with electrophysiology data
- **NeuroMorpho**: ~50,000+ neurons with morphological data
- Both databases provide real, verified neuroscience data with proper citations

### Limitations

- Some parameters (e.g., `psp_amplitudes`) may not exist in these databases
- In such cases, the system falls back to AI-generated estimates (clearly marked as `expert_knowledge` or `openai` source, with `null` citations)

---

## 🔄 Adding New Mappings

To add new manual mappings, edit:
- `src/neuroworkflow/utils/database_adapters/allen_brain.py` → `_get_manual_mapping()`
- `src/neuroworkflow/utils/database_adapters/neuromorpho.py` → `_get_manual_mapping()`

The AI-powered mapping will automatically handle many more parameters without manual configuration!

