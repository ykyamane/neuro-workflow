# How OpenAI Parameter Suggestions Work

## 🎯 Your Questions Answered

### 1. Are the Citations Real?

**Short Answer**: **No, they are likely hallucinated.**

You're absolutely correct! `gpt-4o-mini` does NOT have internet access. The citations it provides are:
- **Based on training data** (knowledge up to the model's training cutoff date)
- **Potentially hallucinated** - The model may generate plausible-sounding citations that don't actually exist
- **Pattern-based** - It knows the format of citations and generates them based on patterns it learned

**What This Means**:
- ✅ The **parameter values** are likely reasonable (based on neuroscience knowledge in training data)
- ✅ The **descriptions** are helpful and contextually relevant
- ⚠️ The **citations** should be **verified** before using in publications
- ⚠️ The **confidence scores** are estimates, not based on actual data analysis

---

## 🔍 How the LLM Makes Suggestions

### Input/Context Provided to OpenAI

For each parameter suggestion request, the LLM receives:

#### 1. **System Prompt** (Context Setting)
```
"You are a helpful assistant that provides JSON responses for neuroscience parameter suggestions."
```

#### 2. **User Prompt** (Detailed Context)

The prompt includes:

**Parameter Information**:
- Parameter name (e.g., "firing_rate")
- Parameter description (e.g., "Average firing rate in Hz for cortical neurons")

**Context Information** (if available):
- Node type (e.g., "BuildSonataNetworkNode")
- Species (e.g., "mouse", "monkey", "human")
- Additional context (brain region, cell type, etc.)

**Output Format Instructions**:
- JSON structure with specific fields
- Guidelines for confidence scores
- Instructions for realistic values

**Example Full Prompt**:
```
You are an expert neuroscientist helping to suggest parameter values for brain simulation models.

Parameter Name: firing_rate
Parameter Description: Average firing rate in Hz for cortical neurons
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
- Confidence should reflect how certain you are (0.6-0.9 for typical values, 0.4-0.6 for estimates)
- Include units in description if relevant
- If the parameter description is unclear, provide general suggestions with lower confidence

Return ONLY valid JSON, no other text.
```

---

## 🧠 How the LLM Generates Suggestions

### Process:

1. **Pattern Recognition**:
   - LLM recognizes parameter type from description (e.g., "firing rate" → neural activity)
   - Matches to neuroscience concepts in training data

2. **Knowledge Retrieval**:
   - Draws from neuroscience knowledge in training data
   - Uses patterns learned from scientific literature (up to training cutoff)
   - Applies general neuroscience principles

3. **Value Estimation**:
   - Generates plausible values based on learned patterns
   - Considers species-specific differences (if provided)
   - Adjusts confidence based on how certain the pattern is

4. **Citation Generation**:
   - Generates citations based on learned citation formats
   - May reference real papers it was trained on
   - May hallucinate plausible-sounding citations
   - **These should be verified!**

---

## ⚠️ Limitations & Considerations

### What the LLM CAN Do:
- ✅ Provide reasonable parameter estimates based on training data
- ✅ Understand parameter descriptions and context
- ✅ Generate multiple suggestions with different confidence levels
- ✅ Consider species-specific differences
- ✅ Provide helpful explanations

### What the LLM CANNOT Do:
- ❌ Access real-time databases (Allen Brain Atlas, NeuroMorpho APIs)
- ❌ Verify citations are real
- ❌ Access internet or current research
- ❌ Guarantee accuracy of values
- ❌ Provide actual confidence based on data analysis

---

## 💡 Recommendations

### For Production Use:

1. **Verify Citations**:
   - Check if citations are real before using in publications
   - Consider removing citation field or marking as "AI-generated"

2. **Use as Starting Point**:
   - Treat suggestions as initial estimates
   - Validate against real databases when possible
   - Use domain expert review

3. **Improve Prompt**:
   - Could add: "Only provide citations if you are certain they exist"
   - Could add: "Mark citations as 'estimated' if uncertain"

4. **Future Enhancement**:
   - Connect to real databases (Allen Brain Atlas API, NeuroMorpho API)
   - Use LLM to help query databases, not replace them
   - Combine LLM suggestions with real database queries

---

## 🔄 Current vs. Future Vision

### Current Implementation (What We Have):
- LLM generates suggestions based on training data
- Provides helpful starting values
- Citations may be hallucinated
- Good for exploration and initial estimates

### Future Vision (What Could Be):
- LLM helps formulate database queries
- Real databases provide actual data
- LLM synthesizes and explains results
- Citations come from actual database sources
- Hybrid approach: LLM + Real Data

---

## 📝 Code Location

The prompt is generated in:
- File: `src/neuroworkflow/utils/parameter_metadata_service.py`
- Method: `_suggest_with_openai()`
- Lines: ~140-190

You can modify the prompt there to:
- Ask for verified citations only
- Request more conservative confidence scores
- Add specific guidelines for your use case

---

*Documentation created: December 2025*

