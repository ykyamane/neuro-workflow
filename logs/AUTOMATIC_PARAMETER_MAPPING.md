# Automatic Parameter Mapping - Current vs. Smart Approach

## 🔍 Current Approach (Manual Mapping)

**How it works now:**
- Each database adapter has a `_map_parameter_name()` method
- Contains a hardcoded dictionary mapping parameter names to database fields
- Example:
  ```python
  mapping = {
      'firing_rate': None,  # Special case
      'input_resistance': 'input_resistance_mohm',
      'rheobase': 'rheobase_sweep_number',
      # ... need to add each one manually
  }
  ```

**Limitations:**
- ❌ Need to manually add each parameter
- ❌ Doesn't use parameter descriptions
- ❌ Doesn't discover available fields automatically
- ❌ Can't handle new parameters without code changes

---

## 💡 Smart Approach (What We Can Build)

### Option 1: AI-Powered Semantic Mapping

Use AI to map parameters based on:
- Parameter name
- Parameter description (we have this!)
- Available database fields

**How it would work:**
1. Get list of available database fields
2. Use AI to match parameter name/description to database fields
3. AI suggests the best field match
4. System uses the match automatically

### Option 2: Auto-Discovery with Fuzzy Matching

1. Get all available database fields
2. Use fuzzy string matching to find similar field names
3. Rank matches by similarity
4. Use best match if confidence is high enough

### Option 3: Hybrid Approach (Best!)

Combine both:
1. **First**: Try manual mapping (fast, reliable)
2. **If no match**: Use AI semantic matching
3. **Fallback**: Fuzzy string matching
4. **Cache results** for future use

---

## 🚀 Implementation Plan

### Step 1: Get Available Fields

Query databases to discover available fields:
- Allen Brain Atlas: Get all ephys_features field names
- NeuroMorpho: Get all morphometry field names

### Step 2: AI Semantic Matching

Use AI to match:
- Input: Parameter name + description
- Input: List of available database fields
- Output: Best matching field(s) with confidence

### Step 3: Cache Mappings

Store successful mappings for reuse:
- Avoid repeated AI calls
- Learn from user corrections
- Build knowledge base over time

---

## 📋 Current Status

**What we have:**
- ✅ Parameter descriptions available in API calls
- ✅ Manual mapping dictionaries
- ✅ Database adapters that can query fields

**What we need:**
- ⏳ AI-powered mapping function
- ⏳ Field discovery mechanism
- ⏳ Caching system

---

## 🎯 Benefits of Smart Mapping

### Before (Manual):
- Need to add each parameter manually
- Can't handle new parameters
- Time-consuming maintenance

### After (Smart):
- ✅ Automatically handles new parameters
- ✅ Uses parameter descriptions
- ✅ Learns and improves over time
- ✅ Works for any parameter

---

*Documentation: December 2025*

