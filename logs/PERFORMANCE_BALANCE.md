# Performance Balance - Database Search Limits

## ⚖️ The Trade-off

**Comprehensive Search** (no limits) = Very slow (30+ seconds)
**Too Limited** (50-100 records) = Fast but inaccurate averages

**Solution**: Balanced limits that give good statistics while staying fast.

---

## 📊 Current Balanced Limits

### Allen Brain Atlas
- **Limit**: 500 cells (2.5x more than before)
- **Reason**: Processing all cells can be thousands - 500 gives good statistics
- **Performance**: ~2-5 seconds
- **Statistics Quality**: Very good (500+ data points)

### NeuroMorpho
- **Neuron Fetching**: 200 neurons (2x more than before)
- **Morphometry Processing**: 200 neurons (each requires separate API call)
- **Reason**: Each morphometry fetch is a separate HTTP request - 200 is reasonable
- **Performance**: ~5-10 seconds (depends on API response time)
- **Statistics Quality**: Good (200+ data points)

### PubMed
- **Paper Search**: 50 papers
- **Abstract Fetching**: 20 abstracts
- **Reason**: Each abstract fetch is a separate API call - 20 is reasonable
- **Performance**: ~3-5 seconds
- **Statistics Quality**: Good (values from 20 papers)

### NeuroML-DB
- **Model Search**: 10 models (unchanged)
- **Performance**: ~2-3 seconds
- **Reason**: Model details can be large, 10 is reasonable

---

## ⏱️ Expected Performance

**Total Time**: ~10-20 seconds for all databases
- Allen Brain: 2-5s
- NeuroMorpho: 5-10s
- PubMed: 3-5s
- NeuroML-DB: 2-3s

**If taking longer than 30 seconds**: There may be a network issue or API slowdown.

---

## 🎯 Why These Limits?

### Statistics Theory
- **30+ samples**: Good for mean estimation
- **100+ samples**: Very good for mean and median
- **200+ samples**: Excellent for mean, median, and standard deviation
- **500+ samples**: Diminishing returns for most use cases

### Our Limits
- **Allen Brain**: 500 cells → Excellent statistics
- **NeuroMorpho**: 200 neurons → Very good statistics
- **PubMed**: 20 abstracts → Good coverage
- **Total**: Much better than before, still fast enough

---

## 🔧 Adjusting Limits

If you want to change the limits, edit these files:

### Allen Brain Atlas
`src/neuroworkflow/utils/database_adapters/allen_brain.py`
```python
max_cells = 500  # Change this value
```

### NeuroMorpho
`src/neuroworkflow/utils/database_adapters/neuromorpho.py`
```python
max_neurons = 200  # Change this value
processed >= 200  # Change this value (morphometry processing)
```

### PubMed
`src/neuroworkflow/utils/database_adapters/pubmed.py`
```python
self.max_results = 50  # Change this value (paper search)
max_abstracts = 20  # Change this value (abstract fetching)
```

---

## 💡 Future Improvements

1. **Async Processing**: Process databases in parallel
2. **Caching**: Cache results for common parameters
3. **Progressive Loading**: Return results as they come in
4. **User Configurable**: Let users choose speed vs. comprehensiveness

---

*Balanced for performance: December 2025*

