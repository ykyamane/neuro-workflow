# Database Search Limits - Explanation

## What Are These Limits?

When you request parameter suggestions, the system queries multiple neuroscience databases. To avoid overwhelming the databases or taking too long, we set **limits** on how many records to process.

## What Changed

### Before (Too Restrictive):
- **Allen Brain Atlas**: Processed only the first **100 cells** from the database
- **NeuroMorpho**: Processed only the first **50 neurons** from the database  
- **PubMed**: Fetched only **5 abstracts** and searched only **10 papers** maximum

### After (More Comprehensive):
- **Allen Brain Atlas**: Now processes **200 cells** (2x more)
- **NeuroMorpho**: Now processes **100 neurons** (2x more)
- **PubMed**: Now fetches **10 abstracts** and searches **20 papers** maximum (2x more)

## What This Means

### Example: Querying "firing_rate" for mouse neurons

**Before**:
- Allen Brain Atlas: Looked at 100 mouse cells → Found maybe 50 with firing rate data → Generated 1-2 suggestions
- NeuroMorpho: Looked at 50 neurons → Found maybe 20 with relevant data → Generated 1 suggestion
- PubMed: Searched 10 papers → Found 2-3 relevant → Generated 1 suggestion
- **Total: 3-4 suggestions**

**After**:
- Allen Brain Atlas: Looks at 200 mouse cells → Finds maybe 100 with firing rate data → Generates 2-3 suggestions
- NeuroMorpho: Looks at 100 neurons → Finds maybe 40 with relevant data → Generates 2 suggestions
- PubMed: Searches 20 papers → Finds 5-6 relevant → Generates 2-3 suggestions
- **Total: 6-8 suggestions** (roughly 2x more!)

## Why These Limits Exist

1. **Performance**: Processing more records takes more time
2. **API Rate Limits**: Some databases limit how many requests you can make
3. **Relevance**: After a certain point, more data doesn't always mean better suggestions

## The Trade-off

- **More data** = More suggestions, but slower response
- **Less data** = Fewer suggestions, but faster response

We chose a middle ground: **2x more data** for **roughly 2x more suggestions**, while still keeping response times reasonable.

---

## Visual Example

```
Query: "firing_rate" for mouse

Allen Brain Atlas:
  Before: [100 cells] → 1-2 suggestions
  After:  [200 cells] → 2-3 suggestions ⬆️

NeuroMorpho:
  Before: [50 neurons] → 1 suggestion
  After:  [100 neurons] → 2 suggestions ⬆️

PubMed:
  Before: [10 papers, 5 abstracts] → 1 suggestion
  After:  [20 papers, 10 abstracts] → 2-3 suggestions ⬆️

Total Results:
  Before: ~3-4 suggestions
  After:  ~6-8 suggestions (2x more!)
```

---

*Updated: December 2025*

