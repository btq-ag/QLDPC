<p align="center">
  <img src="Plots/MainTutorial.png" alt="QLDPC Circuit Builder" width="720" />
</p>

<h1 align="center">QLDPC</h1>

<p align="center">
  Interactive Python toolkit for quantum LDPC error correction.<br>
  Drag-and-drop 3D circuit builder, real-time belief propagation, surface code & Tanner graph visualization, with Qiskit integration.
</p>

<p align="center">
  <a href="https://www.python.org/"><img alt="Python 3.9+" src="https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white" /></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-green" /></a>
  <a href="#quick-start"><img alt="pip install" src="https://img.shields.io/badge/install-pip%20install%20--e%20.-orange" /></a>
</p>

<p align="center">
  <a href="#overview">Overview</a> |
  <a href="#quick-start">Quick Start</a> |
  <a href="#features">Features</a> |
  <a href="#architecture">Architecture</a> |
  <a href="#theory">Theory</a> |
  <a href="#references">References</a> |
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

<p align="center">
  <img src="./Plots/apple_4x.gif?raw=true" alt="apple" width="28" height="29" />
</p>

---

## Overview

Build and simulate quantum LDPC circuits interactively. The circuit builder supports isometric 3D, surface code, and Tanner graph visualization modes with real-time Qiskit-backed computation. Includes belief propagation decoding, cavity QED parameter exploration, threshold landscape analysis, and 30 pre-built example circuits.

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/btq-ag/QLDPC.git
cd QLDPC
pip install -e .

# Optional: install Qiskit for full quantum simulation
pip install -e ".[quantum]"
```

Launch any tool from the command line:

```bash
qldpc-builder       # Interactive 3D circuit builder
qldpc-simulator     # Real-time LDPC simulator
qldpc-tanner        # 3D Tanner graph visualizer
qldpc-threshold     # 3D threshold landscape
```

Or import directly:

```python
from qldpc.builder import CircuitBuilder3D

app = CircuitBuilder3D()
app.run()
```

---

## Features

### Circuit Builder

Interactive drag-and-drop circuit construction with isometric 3D rendering, dark theme GUI, undo/redo, Qiskit circuit export, and a built-in tutorial system.

- 10+ gate types (X, Y, Z, H, S, T, CNOT, CZ, SWAP, Measure, Reset)
- 30 pre-built example circuits (teleportation, Grover, Deutsch-Jozsa, LDPC schemes)
- Real-time quantum state computation with optional Qiskit backend

![Loading Example Circuits](Plots/Circuits.gif)

### Surface Code Mode

Press `V` to toggle surface code mode. Top-down 2D lattice view with X-stabilizers (burgundy), Z-stabilizers (purple), and data qubits on edges. Inject X/Z/Y errors and watch syndrome propagation.

![Surface Code Mode](Plots/Surface.gif)

### LDPC Visualization Modes

Press `B` to cycle through LDPC views:
- **Tanner graph**: bipartite structure with data qubits, X-checks, Z-checks
- **Physical layout**: tri-layer architecture with cavity bus connections

![QLDPC Mode](Plots/QLDPC.gif)

### Interactive Tutorial System

10-step guided tutorial covering qubit placement, gate operations, controlled gates, repetition codes, and surface code construction. Accessible via Help menu.

![Advanced Tutorial](Plots/AdvancedTutorial.gif)

### Real-Time LDPC Simulator

Matplotlib-based interactive simulator with click-to-inject errors, live belief propagation decoding, and a cooperativity slider for cavity QED parameter exploration.

- Configurable code parameters (data qubits, check nodes)
- Step-through or automatic BP decoding
- Gate fidelity model: $F \approx 1 - 1/C - \epsilon_{\text{deph}}$

![Interactive LDPC Simulator](Plots/Interactive%20Simulation.png)

### 3D Tanner Graph Visualizer

Interactive 3D graph exploration with force-directed layouts, syndrome propagation visualization, and multiple code construction comparisons.

```bash
qldpc-tanner
```

### 3D Threshold Landscape

Rotating 3D surface showing error threshold behavior across code families (surface, hypergraph product, quantum Tanner) with real-time parameter adjustment.

```bash
qldpc-threshold
```

### Static Visualizations

Generate publication-quality plots for cavity cooperativity analysis, GHZ state fidelity, syndrome extraction circuits, and LDPC process animations.

| Plot | Description |
|------|-------------|
| Cavity cooperativity | Gate fidelity vs cooperativity ($C = 10^3 - 10^6$) |
| GHZ fidelity | Multi-qubit entanglement fidelity scaling |
| Syndrome extraction | DiVincenzo-Aliferis fault-tolerant measurement circuit |
| BP animation | Belief propagation message passing convergence |
| Tanner graph | Bipartite graph construction animation |
| Threshold behavior | Code family scaling comparison |

![LDPC Animation](Plots/ldpc_tanner_graph_animation.gif)

### Resources & Shortcuts

Quick access to keyboard shortcuts, component legend, and reference materials via the Help menu.

![Resources Panel](Plots/Resources.gif)

---

## Architecture

```
qldpc/
    __init__.py              # Package root (ComponentType, Config, Processor)
    components.py            # ViewMode, ComponentType, Component3D
    config.py                # GridConfig, UIConfig, ColorPalette, LDPC colors
    processor.py             # QuantumLDPCProcessor (Qiskit backend)
    builder/
        app.py               # CircuitBuilder3D main application (tkinter)
        tutorials.py         # Interactive tutorial screens
        renderers/
            isometric.py     # 2.5D isometric rendering engine
        ui/
            history.py       # Undo/redo command pattern
    simulation/
        ldpc_circuit.py      # QuantumLDPCCode + LDPCCircuitAnimation
        cavity_gates.py      # Cooperativity analysis, tri-layer architecture
        ghz.py               # GHZ state preparation and fidelity
        syndrome.py          # Syndrome extraction visualization
        animations.py        # Tanner graph, BP, threshold animations
        quantum_circuits.py  # Static circuit diagram generation
    tanner/
        graph_3d.py          # 3D Tanner graph visualizer
        threshold_3d.py      # 3D threshold landscape visualizer
saved_circuits/
    circuits/                # 22 pre-built quantum circuits
    surface/                 # 8 surface code configurations
tests/                       # pytest suite (64 tests)
docs/                        # Technical documentation
Plots/                       # Generated figures and screenshots
```

| Module | Entry Point | Description |
|--------|-------------|-------------|
| `qldpc.builder.app` | `qldpc-builder` | Interactive 3D circuit builder with 4 view modes |
| `qldpc.simulation.ldpc_circuit` | `qldpc-simulator` | Real-time LDPC error injection and BP decoding |
| `qldpc.tanner.graph_3d` | `qldpc-tanner` | 3D Tanner graph topology explorer |
| `qldpc.tanner.threshold_3d` | `qldpc-threshold` | 3D error threshold landscape |

### Tech Stack

| Technology | Role |
|------------|------|
| Python 3.9+ | Core language |
| tkinter | Circuit builder GUI framework |
| matplotlib | Simulation GUIs, static plots, animations |
| NumPy | Numerical computation, parity matrices |
| Seaborn | Color palettes, statistical visualization |
| NetworkX | Graph structures for Tanner graphs |
| Qiskit (optional) | Quantum circuit simulation and export |

---

## Theory

<details>
<summary><strong>Quantum LDPC Background</strong> (click to expand)</summary>

### Asymptotically Good Codes

The 2020-2022 breakthrough in quantum error correction achieved codes with linear distance $d = \Theta(n)$ and constant rate $R = \Theta(1)$ simultaneously, bounded by the quantum Singleton bound:

$$k \leq n - 2d + 2$$

Panteleev-Kalachev's lifted product construction and Leverrier-Zemor's quantum Tanner codes achieve:

$$\text{Rate: } R \geq 1 - \frac{m}{n} - o(1), \quad \text{Distance: } d \geq c\sqrt{n}$$

### Cavity-Mediated Non-Local Gates

The non-local connectivity required by these codes is implemented via cavity QED with cooperativity:

$$C = \frac{g^2}{\kappa \gamma} \gtrsim 10^4 - 10^6$$

Gate fidelity: $F \approx 1 - 1/C - \epsilon_{\text{deph}}$, enabling thresholds around $p_{\text{th}} \approx 10^{-2}$.

### Scaling Comparison

| Code Family | Rate | Distance | Qubits/Logical | Threshold |
|------------|------|----------|----------------|-----------|
| Surface | $O(1/n)$ | $O(\sqrt{n})$ | ~$10^6$ | ~$10^{-3}$ |
| Hypergraph Product | $O(1)$ | $O(\sqrt{n})$ | ~$10^4$ | ~$10^{-2}$ |
| Lifted Product | $\Theta(1)$ | $\Theta(\sqrt{n}\log n)$ | ~$10^3$ | ~$10^{-2}$ |
| Quantum Tanner | $\Theta(1)$ | $\Theta(n)$ | ~$10^3$ | ~$10^{-2}$ |

</details>

---

## References

1. Panteleev & Kalachev (2021) - "Asymptotically Good Quantum and Locally Testable Classical LDPC Codes"
2. Leverrier & Zemor (2022) - "Quantum Tanner Codes"
3. Brennen et al. (2023) - "Non-local resources for error correction in quantum LDPC codes" ([arXiv:2409.05818](https://arxiv.org/abs/2409.05818))
4. Breuckmann & Eberhardt (2021) - "Quantum Low-Density Parity-Check Codes"

### BibTeX

```bibtex
@software{morais2025qldpc,
    title  = {QLDPC: Interactive Quantum LDPC Error Correction Toolkit},
    author = {Morais, Jeffrey},
    year   = {2025},
    url    = {https://github.com/btq-ag/QLDPC}
}
```

---

## See Also

| Project | Description |
|---------|-------------|
| [TQNN](https://github.com/IsolatedSingularity/Topological-Quantum-Neural-Networks) | Topological Quantum Neural Networks - interactive visualization toolkit |

---

## License

[MIT](LICENSE)
