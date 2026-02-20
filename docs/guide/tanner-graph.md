# 3D Tanner Graph Visualizer

Dark-themed tkinter GUI with interactive 3D Tanner graph exploration and syndrome propagation.

## Features

- 3D scatter plot with edges connecting data qubits, X-checks, and Z-checks
- Force-directed layouts (spring, shell, spectral)
- Multiple code constructions (cycle, random, product)
- Real-time syndrome propagation animation
- Auto-rotation with adjustable speed

## Launch

```bash
qldpc-tanner
```

## Controls

| Control | Action |
|---------|--------|
| Qubits / X-Checks / Z-Checks sliders | Adjust graph size |
| Spread slider | Control node spacing |
| Code Type buttons | Switch construction method |
| Layout buttons | Switch graph layout algorithm |
| Trigger Syndrome | Inject and propagate errors |

## API

```python
from qldpc.tanner.graph_3d import QuantumLDPCTannerGraph

graph = QuantumLDPCTannerGraph(n_qubits=15, n_checks=10)
graph.trigger_syndrome(0)
graph.update_syndrome_visualization()
```
