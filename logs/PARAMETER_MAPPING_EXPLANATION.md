# Parameter Mapping - How It Works

## 🎯 Your Question

> "Do I understand it right that we need to setup every single specific parameter fetching mechanism? Or does the whole system somehow knows which parameters to extract from the databases and how?"

## 📋 Current Answer

**Short answer**: Currently, we need manual mapping for each parameter, BUT we've built a foundation for automatic mapping.

---

## 🔧 How It Works Now

### Current System (Manual + Smart Fallbacks):

1. **Manual Mapping** (Primary):
   - Dictionary of known parameter → database field mappings
   - Fast and reliable
   - Example: `'input_resistance'` → `'input_resistance_mohm'`

2. **Fuzzy Matching** (Fallback):
   - If no manual match, tries fuzzy string matching
   - Looks for similar field names
   - Example: `'membrane_resistance'` might match `'input_resistance_mohm'`

3. **Special Cases**:
   - Some parameters are calculated (like `firing_rate` from `avg_isi`)
   - These have custom logic

### What This Means:

- ✅ **Known parameters**: Work automatically (if in mapping dictionary)
- ⚠️ **New parameters**: May work via fuzzy matching, or need manual addition
- ⚠️ **Complex parameters**: Need custom logic

---

## 💡 What We Can Build (Smart Automatic Mapping)

### Option 1: AI-Powered Semantic Mapping

**How it would work:**
1. System gets parameter name + description (we have this!)
2. System gets list of available database fields
3. AI matches parameter to best database field
4. System uses the match automatically

**Example:**
- Parameter: `"synaptic_weight"` with description `"Strength of synaptic connection"`
- AI sees database fields: `['synaptic_strength', 'connection_weight', 'synapse_amplitude']`
- AI matches: `"synaptic_weight"` → `"connection_weight"` (best semantic match)

### Option 2: Field Discovery + Auto-Mapping

**How it would work:**
1. System queries database to discover all available fields
2. For each new parameter, automatically tries to match
3. Uses parameter description to improve matching
4. Caches successful mappings

---

## 🚀 What We've Built

### Foundation for Smart Mapping:

1. ✅ **Parameter descriptions available**: API receives `parameter_description`
2. ✅ **Fuzzy matching implemented**: Basic automatic matching
3. ✅ **Field discovery method**: `_get_available_fields()`
4. ✅ **AI mapping framework**: Structure ready (needs OpenAI integration)

### Next Steps to Make It Fully Automatic:

1. **Implement AI semantic matching**:
   - Use OpenAI to match parameter descriptions to field names
   - More accurate than fuzzy matching

2. **Add mapping cache**:
   - Store successful mappings
   - Learn from user feedback

3. **Auto-discover on first use**:
   - When new parameter requested, automatically discover and map
   - No manual intervention needed

---

## 📊 Current vs. Future

### Current (Manual + Fuzzy):
- ✅ Works for known parameters
- ⚠️ New parameters may need manual addition
- ✅ Fuzzy matching helps with similar names

### Future (Fully Automatic):
- ✅ Works for ANY parameter automatically
- ✅ Uses AI to understand parameter meaning
- ✅ Learns and improves over time
- ✅ No manual mapping needed

---

## 🎯 Bottom Line

**Right now:**
- We have manual mappings for common parameters
- Fuzzy matching helps with similar names
- New parameters may need to be added manually (or work via fuzzy match)

**Soon (with AI integration):**
- System will automatically map ANY parameter
- Uses parameter descriptions to understand meaning
- No manual setup needed!

---

*Documentation: December 2025*

