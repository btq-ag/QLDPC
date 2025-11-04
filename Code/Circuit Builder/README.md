# 3D Quantum Circuit Builder
###### Interactive Drag-and-Drop Construction Platform for Quantum LDPC Codes

![Circuit Builder Demo](Figures/circuit_builder_demo.png)

## Objective

This module implements an interactive 3D quantum circuit construction platform using a tkinter-based GUI framework with dark theme styling. The application provides a 2.5D isometric perspective where users can drag and drop quantum circuit components from a toolbox onto a grid-based building area to construct quantum LDPC circuits with real-time computation capabilities.

The platform focuses on quantum Low-Density Parity-Check code construction with support for cavity-mediated non-local gates, parity check measurements, and syndrome extraction circuits. The interface enables practical exploration of quantum error correction architectures through visual circuit building.

**Goal:** Provide an intuitive drag-and-drop interface for constructing quantum LDPC circuits with real-time analysis of code parameters, distance calculations, and syndrome extraction visualization.

## Theoretical Background

### Quantum LDPC Circuit Construction Breakthrough

The 2020-2022 revolution in quantum error correction theory created new challenges in practical circuit implementation. While **Panteleev-Kalachev's lifted product construction** and **Leverrier-Zémor's quantum Tanner codes** achieved the theoretical breakthrough of asymptotically good codes, their non-local stabilizer structure requires sophisticated implementation strategies.

The circuit builder implements these breakthrough constructions through **cavity-mediated non-local gates** as proposed by Brennen et al., enabling practical realization of codes with:

$$\text{Distance: } d \geq c\sqrt{n \log n}, \quad \text{Rate: } R \geq \Theta(1)$$

### Cavity-Mediated Circuit Architecture

The critical innovation lies in implementing the **tri-layer architecture** required by quantum LDPC codes:

1. **Data Layer**: Information qubits arranged in LDPC topology
2. **Ancilla Layer**: Syndrome measurement qubits 
3. **Cavity Layer**: Non-local gate mediation with cooperativity:

$$C = \frac{g^2}{\kappa \gamma} \gtrsim 10^4 - 10^6$$

The circuit builder enables real-time construction of these architectures with **drag-and-drop cavity coupling**, implementing the Mølmer-Sørensen type gates:

$$\hat{U} = e^{i \theta \hat{J}_z^2}, \quad \hat{J}_z = \frac{1}{2}\sum_{j=1}^N Z_j$$

enabling **fault-tolerant multi-qubit stabilizer measurements** with fidelities:

$$F \approx 1 - \frac{1}{C} - \epsilon_{\text{deph}}$$

## Revolutionary Features & Implementation
### Key features

The builder combines a 2.5D isometric renderer with an LDPC-aware placement grid and live analysis backend. It supports placing data and ancilla qubits, adding parity-check elements, and wiring cavity-mediated couplings. Interactive controls allow adjustment of cavity parameters and immediate feedback on how those changes affect estimated gate fidelity and measured syndromes.

Core capabilities include professional isometric rendering for clear topology visualization and depth cues, an LDPC-optimized snap-to-grid placement system that enforces local sparsity constraints and helps keep stabilizer weights bounded, and live code analysis for basic metrics (physical/logical qubit counts, encoding rate, and preliminary distance estimates) with automatic CSS-constraint validation during placement.

The component library contains standard gates (single- and two-qubit), LDPC-specific stabilizers, ancilla blocks for syndrome extraction, and cavity-mode elements for non-local interactions. Syndrome-extraction circuits and common decoding hooks (e.g., BP/OSD stubs) are available for rapid prototyping.

```python
def create_cavity_mediated_gate():
    """
    Construct cavity-mediated multi-qubit gate for LDPC implementation
    """
    # Cavity cooperativity C = g²/(κγ)
    cooperativity = slider_cooperativity.value  # 10^4 to 10^6 range
    
    # Gate fidelity calculation
    epsilon_cavity = 1/cooperativity + epsilon_dephasing
    gate_fidelity = 1 - epsilon_cavity
    
    # Multi-qubit Mølmer-Sørensen gate
    theta = np.pi/2  # For GHZ state preparation
    cavity_gate = exp(1j * theta * J_z_squared)
    
    return CavityGateComponent(
        cooperativity=cooperativity,
        fidelity=gate_fidelity,
        connected_qubits=selected_ancilla_block
    )
```

### Interaction and analysis

Placement is mouse-driven with contextual menus for component configuration. Connections between components are rendered immediately and are updated as you move or reconfigure elements. The system performs background validation (for example, checking that $H_X H_Z^T \equiv 0 \pmod 2$) and annotates any violations in the analysis panel.

For analysis, the builder provides quick decoders and probes (belief-propagation stubs, simple MWPM/heuristic fallbacks) suitable for interactive exploration. These are intended for prototyping and visual intuition; high-throughput simulations should be run with dedicated decoding toolchains.

```python
def analyze_constructed_code():
    """
    Analyze breakthrough LDPC code properties in real-time
    """
    # Extract parity check matrices from placed components
    H_X, H_Z = extract_stabilizer_matrices(circuit_components)
    
    # Verify quantum CSS constraint
    constraint_satisfied = np.allclose(H_X @ H_Z.T % 2, 0)
    
    # Calculate breakthrough parameters
    n_physical = len(data_qubits)
    n_logical = n_physical - rank(H_X) - rank(H_Z)
    distance = min(calculate_X_distance(H_X), calculate_Z_distance(H_Z))
    
    # Rate scaling analysis
    encoding_rate = n_logical / n_physical
    distance_scaling = distance / np.sqrt(n_physical * np.log(n_physical))
    
    # Cavity cooperativity requirements
    required_cooperativity = estimate_cooperativity_needs(distance, cavity_gates)
    
    return CodeAnalysis(
        physical_qubits=n_physical,
        logical_qubits=n_logical, 
        distance=distance,
        rate=encoding_rate,
        is_asymptotically_good=(distance_scaling > threshold),
        cooperativity_requirement=required_cooperativity
    )
```

## Advanced GUI Framework & Architecture

**Framework**: tkinter with custom quantum-optimized theming for LDPC visualization  
**Theme**: Professional dark theme emphasizing cavity-mediated connections  
**Architecture**: Quantum circuit entity system with real-time stabilizer analysis

The application implements an architecture tailored for LDPC circuit construction: an object-oriented Quantum Component Entity System, a cavity-aware isometric renderer for non-local gate display, a real-time stabilizer analysis backend, and a professional dark-themed scientific interface optimized for circuit visualization.

## Installation & Breakthrough Dependencies

### Required Packages for Quantum LDPC Analysis
```python
# Core quantum LDPC dependencies
import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx  # For LDPC Tanner graph analysis

# Advanced quantum computing features
# pip install qiskit qiskit-aer  
# pip install ldpc  # For BP+OSD decoding
# pip install networkx  # For graph analysis
```

### Breakthrough Color Palette Standards
Following project visualization standards, the README uses a small set of seaborn palettes tuned for cavity physics: sequential palettes for cavity modes (e.g. `sns.color_palette("mako", as_cmap=True)`), a diverging cubehelix for error-syndrome overlays (e.g. `sns.cubehelix_palette(start=.5, rot=-.5, as_cmap=True)`), and a light cubehelix variant for background areas (e.g. `sns.cubehelix_palette(start=2, rot=0, dark=0, light=.95, reverse=True, as_cmap=True)`).

## Construction Guide for Breakthrough Codes

### Building Asymptotically Good LDPC Codes
1. **Initialize Canvas**: Launch `python quantum_circuit_builder_3d.py` 
2. **Select Code Type**: Choose from Lifted Product, Quantum Tanner, or Hypergraph Product templates
3. **Place Data Qubits**: Arrange in sparse topology with automatic LDPC constraint checking
4. **Add Cavity Modes**: Implement non-local connectivity for breakthrough distance scaling
5. **Real-Time Analysis**: Monitor distance, rate, and threshold parameters during construction

### Cavity-Mediated Gate Construction
Placement and coupling are direct: click to position cavity modes (with automatic cooperativity estimation), drag to connect ancilla qubits (fidelity updates occur in real time), right-click to access advanced cavity parameters (typical cooperativity C ~ 10^4–10^6), and rely on background validation to flag any fault-tolerance violations.

### Breakthrough Circuit Operations
The builder supports common LDPC operations such as DiVincenzo–Aliferis syndrome extraction via cavity gates, configurable error injection for testing with realistic noise models, interactive belief-propagation (BP+OSD) decoding for prototyping, and live performance analysis for threshold and scaling behavior.

```python
def construct_quantum_tanner_code():
    """
    Build quantum Tanner code with linear distance scaling
    """
    # Initialize breakthrough code template
    tanner_template = QuantumTannerTemplate(
        base_dimension=dimension_slider.value,
        expander_degree=degree_slider.value
    )
    
    # Generate LDPC structure with constant rate
    for vertex in tanner_template.left_vertices:
        data_qubit = DataQubit(position=vertex.coordinates)
        data_qubit.cavity_coupling = cavity_cooperativity.value
        canvas.place_component(data_qubit)
    
    # Add parity check nodes with sparse connectivity
    for check in tanner_template.parity_checks:
        parity_node = ParityCheck(
            connected_qubits=check.neighbors,
            syndrome_weight=check.weight  # Constant for LDPC
        )
        canvas.place_component(parity_node)
    
    # Verify breakthrough scaling
    distance = tanner_template.calculate_distance()  # d = Θ(n)
    rate = tanner_template.calculate_rate()  # R = Θ(1)
    
    return QuantumTannerCircuit(distance=distance, rate=rate)
```

### Breakthrough Component Categories

#### Quantum LDPC Stabilizers
Stabilizer support includes lifted-product generators (group-algebra multi-qubit stabilizers), quantum-Tanner-style expander checks (linear distance constructions), hypergraph-product nodes (tensor-product stabilizers with √n scaling), and cavity-mediated measurement primitives for non-local syndrome extraction.

#### Revolutionary Gate Components
Gate primitives include Mølmer–Sørensen multi-qubit gates ($e^{i\theta J_z^2}$), DiVincenzo–Aliferis syndrome measurement circuits, cavity-mediated GHZ-preparation routines for ancilla blocks, and integration points for belief-propagation decoders.

#### Advanced LDPC Elements
Other elements include sparse-connectivity nodes to enforce constant-degree LDPC structure, cavity-based distance-amplifier components, rate-optimizers that trade structure for encoding efficiency, and threshold-analyzer utilities for real-time fault-tolerance estimation.

## Technical Implementation & Breakthrough Architecture

### Core Class Hierarchy
```
QuantumCircuitBuilder3D (Main Controller)
├── CavityIsometricRenderer (3D Cavity Visualization)  
├── BreakthroughLDPCProcessor (Quantum Code Analysis)
├── CavityComponent3D (Non-Local Gate Elements)
└── LDPCCodeType (Breakthrough Construction Types)
```

### Revolutionary Classes

#### `QuantumCircuitBuilder3D`
Main application implementing cavity-mediated circuit construction with real-time breakthrough code analysis.

#### `CavityIsometricRenderer`  
Advanced 2.5D projection system optimized for cavity-qubit coupling visualization with cooperativity-dependent rendering.

#### `BreakthroughLDPCProcessor`
Quantum computation backend implementing:
- **Panteleev-Kalachev Analysis**: Lifted product code parameter calculation
- **Quantum Tanner Metrics**: Expander-based distance and rate computation  
- **Cavity Error Modeling**: Realistic noise simulation with cooperativity dependence

#### `CavityComponent3D`
Enhanced component structure supporting cavity-mediated non-local gates with:
- Real-time cooperativity calculation: $C = g^2/(\kappa\gamma)$
- Fidelity estimation: $F = 1 - 1/C - \epsilon_{\text{deph}}$  
- Multi-qubit coupling topology for breakthrough stabilizer weights

### Advanced Rendering Engine
The cavity-aware isometric renderer converts 3D cavity-qubit coordinates to 2D visualization using enhanced projection:
```python
def render_cavity_coupling(cavity_pos, qubit_positions, cooperativity):
    """
    Render cavity-mediated non-local coupling with cooperativity-dependent styling
    """
    # Enhanced isometric projection for cavity physics
    iso_x = (x - y) * cos(30°) * scale + offset_x  
    iso_y = (x + y) * sin(30°) * scale - z * scale + offset_y
    
    # Cooperativity-dependent visual effects
    coupling_strength = min(cooperativity / 1e6, 1.0)  # Normalize to C_max
    line_alpha = 0.3 + 0.7 * coupling_strength
    line_width = 1 + 3 * coupling_strength
    
    # Non-local connection rendering with quantum interference visualization
    for qubit_pos in qubit_positions:
        draw_quantum_coupling(cavity_pos, qubit_pos, 
                            alpha=line_alpha, width=line_width,
                            color=cavity_coupling_colormap(coupling_strength))
```

### Breakthrough Quantum Computations

#### Real-Time Distance Calculation
Implements linear distance verification for breakthrough codes:
```python
def calculate_breakthrough_distance(H_X, H_Z):
    """
    Verify linear distance scaling d = Θ(n) for breakthrough LDPC codes
    """
    # X-distance: minimum weight of Z-type logical operators
    Z_logicals = find_logical_operators(H_X)
    d_X = min(hamming_weight(op) for op in Z_logicals)
    
    # Z-distance: minimum weight of X-type logical operators  
    X_logicals = find_logical_operators(H_Z)
    d_Z = min(hamming_weight(op) for op in X_logicals)
    
    distance = min(d_X, d_Z)
    n_physical = H_X.shape[1]
    
    # Verify breakthrough scaling d = Θ(n)
    is_breakthrough = distance >= breakthrough_threshold * n_physical
    
    return distance, is_breakthrough
```

#### Cavity-Enhanced Error Correction
Implementation of belief propagation with cavity noise modeling:
```python
def cavity_enhanced_belief_propagation(syndrome, H, cooperativity_map):
    """
    BP decoder with cavity-mediated gate error modeling
    """
    # Initialize beliefs with cavity error probabilities
    for qubit_idx in range(len(qubits)):
        cavity_fidelity = 1 - 1/cooperativity_map[qubit_idx]
        initial_error_prob = 1 - cavity_fidelity
        variable_beliefs[qubit_idx] = [1-initial_error_prob, initial_error_prob]
    
    # Iterative message passing with cavity constraints
    for iteration in range(max_iterations):
        # Check-to-variable messages with syndrome constraints
        for check_idx, syndrome_bit in enumerate(syndrome):
            connected_qubits = get_connected_qubits(H, check_idx)
            update_check_messages(check_idx, connected_qubits, syndrome_bit)
        
        # Variable-to-check messages with cavity coupling
        for var_idx in range(len(qubits)):
            cavity_coupling = cooperativity_map[var_idx]
            update_variable_messages(var_idx, cavity_coupling)
    
    return decode_beliefs(variable_beliefs)
```

## File Structure

```
Circuit Builder/
├── quantum_circuit_builder_3d.py    # Main application
├── README.md                         # This documentation
└── saved_circuits/                   # Directory for saved circuit files
    ├── example_ldpc_code.json       # Example LDPC circuit
    └── syndrome_extraction.json      # Syndrome measurement example
```

## Examples & Use Cases

### Building a Simple LDPC Code
1. Place **Data Qubits** in a grid pattern
2. Add **Parity Check** nodes around data qubits
3. Use **Syndrome Extraction** components for measurements
4. Connect components by proximity (automatic connection detection)
5. Run **Calculate Syndrome** to verify code structure

### Error Correction Demonstration
1. Build LDPC code as above
2. Add **X Gates** to simulate bit flip errors
3. Run **Error Correction** to see belief propagation in action
4. Observe correction suggestions and success probability

### Quantum State Analysis
1. Create circuit with **Hadamard** gates for superposition
2. Add **CNOT** gates for entanglement
3. Include **Measurement** operations
4. Run **Simulate Evolution** to see quantum state probabilities

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Left Click` | Place component / Select component |
| `Right Click` | Component context menu |
| `Drag` | Move component |
| `Delete` | Remove selected component |
| `Ctrl+C` | Copy selected component |
| `Ctrl+V` | Paste component |
| `Ctrl+S` | Save circuit |
| `Ctrl+O` | Load circuit |

## Troubleshooting

### Common Issues

**Components not appearing**: Check that you've selected a component type from the toolbox before clicking.

**Quantum computations failing**: Ensure Qiskit is installed for advanced quantum features. The application will fall back to classical simulation otherwise.

**Performance issues**: For large circuits (>50 components), consider using smaller grid areas or reducing component count.

**Grid alignment problems**: Components automatically snap to grid intersections. Use drag to fine-tune positioning.

### Error Messages

**"Position occupied"**: Attempting to place component where another exists. Move or delete existing component first.

**"No syndrome available"**: Need parity check components and data qubits for syndrome calculation.

**"Circuit build failed"**: Invalid component configuration. Check component types and connections.

## Advanced Features

### Custom Component Properties
Right-click any component and select "Properties" to view:
- Component type and position
- Rotation angle and size
- Connection information
- Custom properties dictionary

### Circuit Export/Import
Save circuits as JSON files containing:
- Component positions and types
- Rotation and size information
- Connection mappings
- Custom properties

### Real-Time Analysis
Status panel provides live feedback on:
- Circuit construction progress
- Quantum computation results
- Error correction statistics
- Performance metrics

## Contributing

This application follows the project's coding standards:
- Comprehensive docstrings for all functions and classes
- Type hints for function parameters and returns
- Professional error handling with user feedback
- Consistent color scheme using project seaborn palettes
- Modular design for easy extension and maintenance

## Version History

- **v1.0**: Initial release with core 3D circuit building functionality
- Real-time syndrome calculation and error correction
- Professional dark theme GUI with tkinter
- Comprehensive component library for LDPC circuits

---

*Part of the Quantum LDPC Visualization Project*
*Built with quantum error correction breakthroughs from 2020-2022 research*