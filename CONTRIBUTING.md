# Contributing to QLDPC

Thank you for your interest in contributing to the QLDPC project.

## Development Setup

```bash
git clone https://github.com/btq-ag/QLDPC.git
cd QLDPC
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -e ".[quantum,dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

On headless Linux (CI), prefix with `xvfb-run` since some tests import tkinter:

```bash
xvfb-run pytest tests/ -v
```

## Project Structure

```
qldpc/                  Main package
  builder/              3D circuit builder GUI (tkinter)
  simulation/           LDPC simulation modules (matplotlib)
  tanner/               Tanner graph + threshold visualization
  components.py         Core data types (ViewMode, ComponentType, Component3D)
  config.py             Configuration dataclasses and color palettes
  processor.py          Qiskit-backed circuit processing
tests/                  pytest suite
saved_circuits/         Pre-built circuit JSON files
Plots/                  Generated figures and screenshots
docs/                   Technical documentation
```

## Code Style

- Python 3.9+ syntax (no walrus operators in hot paths)
- Type hints on public APIs
- Docstrings for classes and public methods
- `camelCase` preferred for new local variables (gradual migration)

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Make your changes and add tests if appropriate
4. Run `pytest tests/ -v` to ensure all tests pass
5. Commit with a clear message
6. Open a pull request

## Reporting Issues

Open a GitHub issue with:
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
