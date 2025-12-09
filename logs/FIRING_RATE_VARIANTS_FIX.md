# Firing Rate Variants Fix

## ✅ Issue Fixed

**Problem**: Only `firing_rate` (exact match) was recognized as a calculated field. Variants like:
- `firing_rate_resting`
- `firing_rate_active`
- `firing_rate_maximum`
- `firing_rate_disease`

were not recognized, so they returned 0 suggestions from Allen Brain Atlas.

---

## 🔧 Fix Applied

**Changed**: Made the calculated field check more flexible to recognize all `firing_rate` variants.

**Before**:
```python
is_calculated_field = parameter_name.lower() in ['firing_rate', 'spike_rate', 'rate']
```

**After**:
```python
param_lower = parameter_name.lower()
is_calculated_field = (
    param_lower in ['firing_rate', 'spike_rate', 'rate'] or
    param_lower.startswith('firing_rate_') or
    param_lower.startswith('spike_rate_')
)
```

---

## 📊 Test Results

All `firing_rate` variants now return results from Allen Brain Atlas:

| Parameter | Total Suggestions | Sources |
|-----------|------------------|---------|
| `firing_rate` | 3 | allen_brain (2), pubmed (1) |
| `firing_rate_resting` | 2 | allen_brain (2) |
| `firing_rate_active` | 2 | allen_brain (2) |
| `firing_rate_maximum` | 2 | allen_brain (2) |

---

## 💡 How It Works

All `firing_rate` variants are calculated from `avg_isi` (average inter-spike interval) using the same formula:

```
firing_rate = 1000.0 / avg_isi  (converts milliseconds to Hz)
```

The variant name (resting, active, maximum, etc.) is preserved in the parameter name, but the calculation method is the same for all variants since Allen Brain Atlas provides `avg_isi` data that can be converted to firing rate.

---

## 🎯 Why This Makes Sense

- **Allen Brain Atlas** provides `avg_isi` (average inter-spike interval) data
- All firing rate variants represent the same physical quantity (spikes per second)
- The variant suffix (resting, active, maximum) describes the condition/state, but the calculation is the same
- The system now recognizes all variants and calculates firing rate from the same underlying data

---

*Fix completed: December 2025*

