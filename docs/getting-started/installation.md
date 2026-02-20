# Installation

## Requirements

- Python 3.9+
- tkinter (included with most Python installations)

## Install from Source

```bash
git clone https://github.com/btq-ag/QLDPC.git
cd QLDPC
pip install -e .
```

## Optional Dependencies

### Qiskit (quantum simulation backend)

```bash
pip install -e ".[quantum]"
```

### Development tools

```bash
pip install -e ".[dev]"
```

## Verify Installation

```python
import qldpc
print(qldpc.__version__)  # 1.0.0
```
