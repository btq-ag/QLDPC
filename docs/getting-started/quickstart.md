# Quick Start

## Launch the Circuit Builder

```bash
qldpc-builder
```

Click any gate in the toolbox, then click on the grid to place it. Press `V` to toggle surface code mode, `B` to cycle LDPC visualization modes.

## Launch the LDPC Simulator

```bash
qldpc-simulator
```

Click on qubits to inject errors. Use the control panel to adjust cooperativity, run belief propagation decoding, and explore code parameters.

## Launch the Tanner Graph Visualizer

```bash
qldpc-tanner
```

Adjust graph parameters with sliders, switch code types and layouts, and trigger syndrome propagation to watch error spreading in real time.

## Launch the Threshold Landscape

```bash
qldpc-threshold
```

Switch between code families (Surface, Hypergraph Product, Quantum Tanner) and visualization modes (error threshold, distance scaling). Use the cooperativity slider to explore cavity QED effects.

## Python API

```python
from qldpc.simulation.ldpc_circuit import QuantumLDPCCode

code = QuantumLDPCCode(n_data=20, n_checks=10)
code.inject_error(3, error_type=2)  # X error
code.inject_error(7, error_type=3)  # Z error
code.belief_propagation_step()
print(f"Syndrome: {code.syndrome}")
print(f"Gate fidelity: {code.gate_fidelity:.6f}")
```
