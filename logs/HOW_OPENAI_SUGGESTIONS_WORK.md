# How OpenAI Parameter Suggestions Work - Detailed Explanation

## 🎯 Your Questions Answered

### 1. Are the Citations Real?

**Answer: Likely NOT - they are probably hallucinated.**

You're absolutely correct! Here's why:

- **No Internet Access**: `gpt-4o-mini` does NOT have internet access
- **Training Data Only**: It only knows what was in its training data (up to a cutoff date)
- **Citation Hallucination**: LLMs often generate plausible-sounding citations that don't actually exist
- **Pattern Matching**: It knows citation formats and generates them based on patterns

**What This Means**:
- ✅ **Parameter values** are likely reasonable (based on neuroscience knowledge in training data)
- ✅ **Descriptions** are helpful and contextually relevant  
- ⚠️ **Citations should be VERIFIED** before using in publications
- ⚠️ **Confidence scores** are estimates, not based on actual data analysis

---

## 🔍 How the LLM Makes Suggestions

### Input Provided to OpenAI

For each parameter suggestion request, the LLM receives:

#### **System Message** (Role Definition):
```
"You are a helpful assistant that provides JSON responses for neuroscience parameter suggestions."
```

#### **User Message** (The Actual Prompt):

**What Gets Sent**:
1. **Parameter Name**: e.g., `"firing_rate"`
2. **Parameter Description**: e.g., `"Average firing rate in Hz for cortical neurons"`
3. **Node Type** (if available): e.g., `"BuildSonataNetworkNode"`
4. **Species** (if provided): e.g., `"mouse"`, `"monkey"`, `"human"`
5. **Additional Context** (if provided): e.g., brain region, cell type

**Example Full Prompt**:
```
You are an expert neuroscientist helping to suggest parameter values for brain simulation models.

Parameter Name: firing_rate
Parameter Description: Average firing rate in Hz for cortical neurons
Node type: BuildSonataNetworkNode
Species: mouse

Based on neuroscience literature and databases (Allen Brain Atlas, NeuroMorpho, published papers), 
suggest realistic parameter values for this parameter.

Provide your response as a JSON object with a "suggestions" array:
{
  "suggestions": [
    {
      "value": <numeric value or null>,
      "source": "allen_brain" | "neuromorpho" | "pubmed" | "expert_knowledge",
      "confidence": <0.0 to 1.0>,
      "description": "<explanation of why this value is suggested>",
      "species": "mouse",
      "citation": "<paper or database reference if available>"
    }
  ]
}

Guidelines:
- Provide 1-3 suggestions
- Values should be realistic for neuroscience parameters
- Confidence should reflect how certain you are
- Include units in description if relevant
- IMPORTANT: For citations, only provide them if you are certain they exist

Return ONLY valid JSON, no other text.
```

---

## 🧠 How the LLM Generates Suggestions

### The Process:

1. **Pattern Recognition**:
   - LLM recognizes parameter type from description
   - Matches to neuroscience concepts in its training data
   - Example: "firing rate" → neural activity → typical values learned from training

2. **Knowledge Retrieval**:
   - Draws from neuroscience knowledge in training data
   - Uses patterns learned from scientific literature (up to training cutoff date)
   - Applies general neuroscience principles it learned

3. **Value Estimation**:
   - Generates plausible values based on learned patterns
   - Considers species-specific differences (if provided)
   - Adjusts confidence based on how certain the pattern is

4. **Citation Generation** (The Problematic Part):
   - Generates citations based on learned citation formats
   - May reference real papers it was trained on (if it remembers them)
   - **May hallucinate plausible-sounding citations** ⚠️
   - These should be **verified** before use!

---

## 📊 What the LLM Knows vs. Doesn't Know

### ✅ What It CAN Do:
- Provide reasonable parameter estimates based on training data
- Understand parameter descriptions and context
- Generate multiple suggestions with different confidence levels
- Consider species-specific differences
- Provide helpful explanations

### ❌ What It CANNOT Do:
- Access real-time databases (Allen Brain Atlas, NeuroMorpho APIs)
- Verify citations are real
- Access internet or current research
- Guarantee accuracy of values
- Provide actual confidence based on data analysis
- Know if a citation actually exists

---

## 💡 Recommendations

### For Current Use:

1. **Treat Citations with Caution**:
   - Verify citations before using in publications
   - Consider them as "suggested references" not verified sources
   - Mark as "AI-generated" if using

2. **Use Values as Starting Points**:
   - Treat suggestions as initial estimates
   - Validate against real databases when possible
   - Use domain expert review

3. **Trust Descriptions More Than Citations**:
   - The explanations are usually helpful
   - The values are often reasonable
   - The citations are the most unreliable part

### Future Improvements:

1. **Better Prompt** (Already Updated):
   - Now asks LLM to only provide citations if certain
   - Suggests using "expert_knowledge" if uncertain

2. **Real Database Integration**:
   - Connect to actual Allen Brain Atlas API
   - Connect to NeuroMorpho.org API
   - Use LLM to help query, not replace databases

3. **Hybrid Approach**:
   - LLM helps formulate queries
   - Real databases provide actual data
   - LLM synthesizes and explains results
   - Citations come from actual sources

---

## 🔧 Technical Details

### Model Used:
- **Model**: `gpt-4o-mini`
- **Temperature**: `0.3` (lower = more consistent, factual)
- **Max Tokens**: `500`
- **Response Format**: JSON object (structured output)

### Prompt Location:
- File: `src/neuroworkflow/utils/parameter_metadata_service.py`
- Method: `_suggest_with_openai()`
- Lines: ~165-194

### How to Modify:
You can customize the prompt to:
- Ask for verified citations only
- Request more conservative confidence scores
- Add specific guidelines for your use case
- Remove citation field entirely if preferred

---

## 📝 Summary

**How It Works**:
1. User requests parameter suggestion via API
2. System builds prompt with parameter info + context
3. OpenAI generates suggestions based on training data
4. System parses JSON response
5. Returns suggestions to user

**What to Trust**:
- ✅ Parameter values (usually reasonable)
- ✅ Descriptions (helpful explanations)
- ⚠️ Citations (verify before use!)
- ⚠️ Confidence scores (estimates, not data-driven)

**The Bottom Line**:
The LLM is a helpful assistant that provides educated guesses based on its training. It's great for exploration and getting started, but should be validated with real data sources for production use.

---

*Documentation created: December 2025*

