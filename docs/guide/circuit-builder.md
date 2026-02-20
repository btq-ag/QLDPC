# Circuit Builder

The circuit builder provides interactive drag-and-drop quantum circuit construction with isometric 3D rendering.

## Features

- 10+ gate types: X, Y, Z, H, S, T, CNOT, CZ, SWAP, Measure, Reset
- 30 pre-built example circuits
- Real-time Qiskit-backed computation (when installed)
- Dark-themed tkinter GUI with undo/redo
- Surface code and Tanner graph visualization modes

## Launch

```bash
qldpc-builder
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `V` | Toggle surface code mode |
| `B` | Cycle LDPC visualization modes |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+S` | Save circuit |
| `Ctrl+O` | Load circuit |

## API

```python
from qldpc.builder.app import CircuitBuilder3D

app = CircuitBuilder3D()
app.run()
```
