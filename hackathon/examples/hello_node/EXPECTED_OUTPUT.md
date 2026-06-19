# Expected output — hello_node green run

`Node.process()` hides failures (it prints and returns False, and leaves a
mismatched output port as `None`). So "did it work?" must be checked against
known-good numbers, not just "no traceback". Run:

```bash
python workflow.py
```

With the default parameters (`length=100, amplitude=1.0, cycles=2.0`) you should
see exactly:

```
Executing node: Generator
Executing node: Stats

--- results ---
workflow success: True
mean:       -4.501274070443074e-17
std:        0.7071067811865476
n_samples:  100
```

What to confirm:

- `workflow success: True` — every node's `process()` returned True.
- `mean` ≈ `0` (the tiny `-4.5e-17` is floating-point round-off; a full sine
  period averages to zero).
- `std` ≈ `0.7071` (= `1/sqrt(2)`, the RMS of a unit-amplitude sine).
- `n_samples: 100` — and **not `None`**. A `None` here would mean a return-dict
  key did not match the output port name.

Then validate each node on its own with the checker:

```bash
python ../../check_node.py signal_generator.py
python ../../check_node.py signal_statistics.py
```

Both should end with `ALL NODES PASSED`.
