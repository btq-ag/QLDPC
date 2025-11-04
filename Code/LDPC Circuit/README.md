# Code+ Directory
## Real-Time Interactive Quantum LDPC Simulations

This directory contains enhanced, interactive implementations of quantum LDPC code visualizations that go beyond the static plots in the main `Code/` directory.

## Files

### `realtime_ldpc_circuit.py`
**Interactive Quantum LDPC Circuit Simulator**

A comprehensive real-time interactive visualization of quantum LDPC codes with breakthrough linear distance scaling, implementing Brennen et al.'s cavity-mediated approach.

#### Features:
- **Real-time error injection**: Click on qubits to cycle through different error states (|0⟩ → |1⟩ → X-error → Z-error → Y-error)
- **Live belief propagation**: Watch the BP decoding algorithm converge in real-time
- **Cavity QED integration**: Adjust cooperativity and observe gate fidelity effects
- **Interactive controls**: Manual/automatic decoding, parameter adjustment, error clearing
- **Multi-panel visualization**: 
  - Main circuit with qubits, parity checks, and cavity representation
  - Real-time syndrome vector display
  - Belief propagation probability tracking
  - Code parameter dashboard

#### Controls:
- **Mouse clicks**: Inject errors into qubits by clicking on them
- **Cooperativity slider**: Adjust cavity cooperativity (10³ to 10⁶)
- **Decode Step**: Manually advance belief propagation by one iteration
- **Auto Decode**: Enable/disable automatic continuous decoding
- **Clear Errors**: Remove all errors from the circuit
- **Reset Code**: Generate a new random LDPC code
- **Checkboxes**: Toggle display of BP messages and cavity visualization

#### Theoretical Foundation:
Implements the breakthrough 2020-2022 quantum LDPC constructions:
- **Linear distance scaling**: d = Θ(√n) improving to d = Θ(n)
- **Constant rate**: R = k/n = Θ(1)
- **LDPC property**: Constant-weight stabilizers and bounded qubit degree
- **Cavity-mediated gates**: Non-local gate implementation with cooperativity C ~ 10⁴-10⁶

#### Technical Implementation:
- **Sparse parity check matrix**: Each check connects to ~6 qubits (LDPC property)
- **Belief propagation decoder**: Iterative message-passing algorithm
- **Cavity QED model**: Gate fidelity F ≈ 1 - 1/C - ε_deph
- **Real-time animation**: 60 FPS performance monitoring
- **Interactive matplotlib GUI**: Sliders, buttons, and mouse interaction

#### Usage:
```python
python realtime_ldpc_circuit.py
```

This creates an interactive window where you can:
1. Explore quantum LDPC codes hands-on
2. Understand belief propagation decoding visually
3. See the impact of cavity cooperativity on gate fidelity
4. Experience the breakthrough linear distance scaling
5. Observe how non-local gates enable these powerful codes

#### Educational Value:
- **Visual learning**: See abstract quantum error correction concepts in action
- **Parameter exploration**: Understand the role of cooperativity and code parameters
- **Algorithm understanding**: Watch belief propagation converge step-by-step
- **Breakthrough appreciation**: Experience the significance of linear distance scaling
- **Implementation insight**: Connect theory (Brennen et al.) to practice

#### Future Extensions:
- Multi-user collaborative error injection
- Real-time threshold analysis
- Advanced decoding algorithms (BP+OSD, BP+LSD)
- Hardware noise models
- Comparison with surface codes
- Integration with quantum computing platforms

### Examples Directory
Contains the reference implementation (`realtime_simulation.py`) that demonstrates the GUI framework used for the LDPC simulator.

## Requirements
- numpy
- matplotlib
- seaborn
- Interactive matplotlib backend (e.g., Qt5Agg, TkAgg)

## Installation
Ensure you have an interactive matplotlib backend:
```bash
pip install matplotlib[qt5] seaborn numpy
# or
pip install matplotlib[tk] seaborn numpy
```

## Performance Notes
The interactive simulations are optimized for real-time performance:
- 60 FPS target with performance monitoring
- Efficient belief propagation implementation
- Optimized drawing routines
- Minimal memory allocation in animation loops

## Contributing
When adding new interactive simulations:
1. Follow the pattern established in `realtime_ldpc_circuit.py`
2. Include comprehensive docstrings and comments
3. Implement performance monitoring
4. Add interactive controls for key parameters
5. Provide educational context in the interface
