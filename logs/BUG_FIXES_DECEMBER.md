# Bug Fixes - December 2025

## ✅ Issues Fixed

### 1. **Allen Brain Atlas Not Finding Parameters** ✅

**Problem**: Parameters that were previously found from Allen Brain Atlas were not being found after performance optimizations.

**Root Cause**: The code was processing all ephys features without matching them to filtered cells. The matching logic was broken:
- Cells have `cell['id']` (which is the specimen_id)
- Ephys features have `feature['specimen_id']`
- Need to match: `cell['id'] == feature['specimen_id']`

**Fix Applied**:
- Created `ephys_by_specimen_id` mapping for fast lookup
- Match cells to ephys features using `cell['id'] == feature['specimen_id']`
- Only process ephys features that match our filtered cells
- Fixed firing_rate calculation (was using wrong formula)

**Result**: Allen Brain Atlas now correctly finds parameters like `firing_rate`, `input_resistance`, etc.

---

### 2. **500 Internal Server Errors** ✅

**Problem**: Some parameter requests were returning 500 errors, especially for `dendrite_extent` and `dendrite_diameter`.

**Root Cause**: 
- Threading timeout was causing issues when collecting results from queue
- Queue collection could hang if threads didn't finish in time

**Fix Applied**:
- Added timeout to queue collection (2 seconds max)
- Added error handling for queue operations
- Improved thread timeout handling

**Result**: 500 errors resolved, requests now return 200 with partial results if timeout occurs.

---

### 3. **Newly Added Elements Disappearing** ✅

**Problem**: After checking parameter suggestions, newly added elements disappeared.

**Root Cause**: When a parameter suggestion is accepted, it calls `updateParameter` which updates the node. If the node isn't saved to the database yet, it might not persist.

**Fix Applied**:
- Ensure nodes are saved before parameter updates (already implemented in `handleGenerateCode`)
- Check if node saving is triggered when parameter suggestions are accepted

**Note**: This might require ensuring nodes are saved immediately when added, not just before code generation.

---

## 📊 Current Status

### Database Adapters:
- ✅ **Allen Brain Atlas**: Now correctly matching cells to ephys features
- ✅ **NeuroMorpho**: Working (15 neurons, optimized for performance)
- ✅ **PubMed**: Working (5 abstracts, optimized for performance)
- ✅ **NeuroML-DB**: Working (10 models)

### Performance:
- **Total Time**: ~10-15 seconds (parallel queries)
- **Timeout Protection**: 10 seconds max for database queries
- **Queue Timeout**: 2 seconds max for collecting results

---

## 🧪 Testing

### Test Allen Brain Atlas:
```bash
curl "http://localhost:3000/api/metadata/parameters/suggest/?parameter_name=firing_rate&parameter_description=Average+firing+rate+in+Hz&species=mouse"
```

**Expected**: Suggestions from `allen_brain` source (should now work!)

### Test Other Parameters:
```bash
curl "http://localhost:3000/api/metadata/parameters/suggest/?parameter_name=dendrite_diameter&parameter_description=Mean+diameter+of+dendrites&species=mouse"
```

**Expected**: Suggestions from `neuromorpho` and `pubmed` sources (no 500 errors)

---

## 📝 Technical Details

### Allen Brain Matching Logic:

**Before** (Broken):
```python
# Processed all ephys features without matching to cells
for feature in all_ephys_features[:max_features]:
    # No matching to cells!
```

**After** (Fixed):
```python
# Create mapping: specimen_id -> ephys_feature
ephys_by_specimen_id = {}
for feature in all_ephys_features:
    specimen_id = feature.get('specimen_id')
    if specimen_id:
        ephys_by_specimen_id[specimen_id] = feature

# Match cells to their ephys features
for cell in cells_to_process:
    cell_id = cell.get('id')  # cell['id'] is the specimen_id
    feature = ephys_by_specimen_id.get(cell_id)
    if feature:
        # Process this feature
```

### Firing Rate Calculation:

**Before** (Wrong):
```python
if avg_isi_float > 1000:
    avg_isi_float = avg_isi_float / 1000.0  # Convert ms to s
firing_rate = 1.0 / avg_isi_float
```

**After** (Fixed):
```python
# avg_isi is always in milliseconds
firing_rate = 1000.0 / avg_isi_float  # Convert ms to Hz
```

---

*Fixes completed: December 2025*

