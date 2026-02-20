# LDPC Simulator

Dark-themed tkinter GUI with embedded matplotlib panels for real-time quantum LDPC error correction simulation.

## Features

- Click-to-inject X, Z, and Y errors
- Live belief propagation decoding with step-through or auto mode
- Cooperativity slider for cavity QED parameter exploration
- Three-panel display: circuit view, syndrome vector, belief bars

## Launch

```bash
qldpc-simulator
```

## Controls

| Control | Action |
|---------|--------|
| Cooperativity slider | Adjust cavity QED cooperativity (10³–10⁶) |
| Random Errors | Inject random errors at 10% rate |
| BP Step | Single belief propagation iteration |
| Full Decode | Run BP to convergence |
| Reset | Clear all errors |

## Model

Gate fidelity follows the cavity QED model:

$$F \approx 1 - \frac{1}{C} - \epsilon_{\text{deph}}$$

where $C$ is cooperativity and $\epsilon_{\text{deph}}$ is dephasing noise.

## API

```python
from qldpc.simulation.ldpc_circuit import QuantumLDPCCode

code = QuantumLDPCCode(n_data=20, n_checks=10, cooperativity=1e5)
code.inject_error(3, "X")
code.compute_syndrome()
code.bp_step()
```
