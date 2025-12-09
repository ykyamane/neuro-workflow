# Web Search Implementation Notes

## Current Status

### ✅ What's Implemented:
- Database adapter framework (ready for API keys)
- Enhanced prompts that guide LLM to use current information
- Hybrid query system (databases + LLM)
- LLM synthesis of multiple sources

### ⚠️ Web Search Limitation:

**OpenAI's `web_search` tool is not available for `gpt-4o-mini`** in the standard API.

The error we encountered:
```
Invalid value: 'web_search'. Supported values are: 'function' and 'custom'.
```

This means:
- The `web_search` tool type is not supported in the current OpenAI API
- It may be available in newer models or different API endpoints
- Or it might require a different approach

---

## Alternative Solutions

### Option 1: Use Models with Built-in Web Access

Some alternatives:
- **Perplexity API**: Has built-in web search
- **Anthropic Claude**: May have web search capabilities
- **OpenAI GPT-4o (newer versions)**: May support web search

### Option 2: Implement Custom Web Search Function

We could implement web search as a function tool:

```python
tools = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current neuroscience information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            }
        }
    }
}]
```

Then implement the function to call:
- Google Search API
- Bing Search API
- Perplexity API
- Or other search services

### Option 3: Enhanced Prompt (Current Approach)

**What we're doing now**:
- Enhanced prompt instructs LLM to base suggestions on current knowledge
- LLM uses its training data (which includes recent information up to training cutoff)
- Prompt emphasizes verified sources and citations

**Benefits**:
- Works with current model
- No additional API costs
- Still provides good suggestions

**Limitations**:
- No real-time web access
- Citations may still be hallucinated (but less likely with better prompt)

---

## Recommended Next Steps

### Short Term (Now):
1. ✅ Use enhanced prompts (already done)
2. ✅ Database adapter framework (already done)
3. ⏳ Get database API keys and implement real queries

### Medium Term:
1. Implement custom web search function tool
2. Use Google/Bing/Perplexity API for web search
3. LLM uses function to search, then synthesizes results

### Long Term:
1. Full database integration (Allen Brain Atlas, NeuroMorpho)
2. Custom web search function
3. Hybrid system: Real DBs + Web Search + LLM Synthesis
4. Verified citations from actual sources

---

## Current Implementation Benefits

Even without real web search, the current implementation:

✅ **Database Framework**: Ready for real API integration
✅ **Enhanced Prompts**: Better guidance for LLM
✅ **Hybrid System**: Can combine multiple sources
✅ **Better Citations**: Prompt asks for verified citations only
✅ **Graceful Fallback**: Works even if databases not configured

---

## Testing Web Search Alternatives

If you want to test web search, consider:

1. **Perplexity API** (has built-in web search):
   ```python
   # Would need to add Perplexity as alternative
   from perplexity import PerplexityClient
   ```

2. **Google Custom Search API**:
   ```python
   # Implement as function tool
   def web_search_function(query):
       # Call Google Custom Search API
       # Return results
   ```

3. **Bing Search API**:
   ```python
   # Similar to Google
   ```

---

*Notes: December 2025*

