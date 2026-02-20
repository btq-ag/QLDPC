# QLDPC

Interactive Python toolkit for quantum LDPC error correction.

## Overview

Build and simulate quantum LDPC circuits interactively. The toolkit includes:

- **Circuit Builder** — Drag-and-drop 3D circuit construction with isometric rendering
- **LDPC Simulator** — Real-time belief propagation with cavity QED parameters
- **Tanner Graph 3D** — Interactive 3D topology explorer
- **Threshold Landscape** — 3D error threshold surfaces across code families

## Quick Install

```bash
git clone https://github.com/btq-ag/QLDPC.git
cd QLDPC
pip install -e .
```

## Launch

```bash
qldpc-builder       # Interactive 3D circuit builder
qldpc-simulator     # Real-time LDPC simulator
qldpc-tanner        # 3D Tanner graph visualizer
qldpc-threshold     # 3D threshold landscape
```

## Navigation

- [Getting Started](getting-started/installation.md) — Installation and first steps
- [User Guide](guide/circuit-builder.md) — Tool-by-tool walkthroughs
- [API Reference](api/qldpc.md) — Full module documentation
