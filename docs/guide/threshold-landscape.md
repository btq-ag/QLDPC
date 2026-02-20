# 3D Threshold Landscape

Dark-themed tkinter GUI with rotating 3D surface for error threshold analysis across quantum LDPC code families.

## Features

- Error threshold landscape: logical error rate vs physical error rate and code distance
- Distance scaling analysis: distance vs code length and code rate
- Three code families: Surface, Hypergraph Product, Quantum Tanner
- Cooperativity slider for cavity QED effects
- Wireframe / surface toggle, colorbar, auto-rotation

## Launch

```bash
qldpc-threshold
```

## Controls

| Control | Action |
|---------|--------|
| Cooperativity slider | Adjust cavity QED cooperativity |
| Code Family radios | Switch between Surface / Hypergraph / Quantum Tanner |
| View Mode radios | Switch between Error Threshold and Distance Scaling |
| Wireframe checkbox | Toggle wireframe rendering |
| Auto Rotate checkbox | Toggle automatic rotation |
| Rotation Speed slider | Control rotation speed |

## Code Families

| Family | Distance | Rate | Threshold |
|--------|----------|------|-----------|
| Surface | $O(\sqrt{n})$ | $O(1/n)$ | ~0.5% |
| Hypergraph Product | $O(\sqrt{n \log n})$ | $O(1)$ | ~1% |
| Quantum Tanner | $O(n)$ | $O(1)$ | ~3% |

## API

```python
from qldpc.tanner.threshold_3d import QuantumLDPCThresholdModel

model = QuantumLDPCThresholdModel()
model.code_family = 2  # Quantum Tanner
P, D, Z = model.calculate_threshold_surface()
```
