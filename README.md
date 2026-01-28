# Quantum Low-Density Parity-Check (LDPC) Codes
###### Non-Local Resource Implementation for Fault-Tolerant Quantum Computing based on [Brennen and Gopi's work](https://arxiv.org/abs/2409.05818)

![Cavity Cooperativity Analysis](Plots/cavity_cooperativity.png)

## Objective

This repository implements visualizations and analysis of breakthrough quantum Low-Density Parity-Check (qLDPC) codes, focusing on the revolutionary 2020-2022 constructions that achieved asymptotically good codes with linear distance and constant rate. The implementation emphasizes non-local gate implementation, representing a paradigm shift from surface codes toward scalable fault-tolerant quantum computing.

The core breakthrough addresses the fundamental challenge in quantum error correction: achieving **linear distance** $d = \Theta(n)$ and **constant rate** $R = \Theta(1)$ simultaneously, as described by the quantum Singleton bound:

$$k \leq n - 2d + 2$$

where $k$ is the number of logical qubits, $n$ the total physical qubits, and $d$ the code distance.

**Goal:** Demonstrate the practical implementation of asymptotically good qLDPC codes through cavity-mediated non-local gates, visualize the tri-layer architecture, and analyze the error correction process that enables fault-tolerant quantum computing with dramatically reduced overhead.

## Theoretical Background

### Quantum LDPC Breakthrough

The 2020-2022 period witnessed revolutionary advances in quantum error correction theory. Panteleev and Kalachev's **lifted product construction**, followed by Leverrier-Zémor's **quantum Tanner codes**, finally achieved asymptotically good qLDPC codes:

$$\text{Rate: } R \geq 1 - \frac{m}{n} - o(1), \quad \text{Distance: } d \geq c\sqrt{n}$$

These constructions are defined by stabilizer generators with constant weight, forming a sparse parity-check matrix $H$ where each stabilizer $g_i$ has the form:

$$g_i = \bigotimes_{j \in \text{supp}(i)} \sigma_j^{(i)}$$

where $\sigma_j^{(i)} \in \{I, X, Y, Z\}$ and $|\text{supp}(i)| = O(1)$.

### Cavity-Mediated Implementation

The critical challenge lies in implementing the non-local connectivity required by these codes. Brennen et al. propose cavity QED solutions with **cooperativity requirements**:

$$C = \frac{g^2}{\kappa \gamma} \gtrsim 10^4 - 10^6$$

where $g$ is the atom-cavity coupling, $\kappa$ the cavity decay rate, and $\gamma$ the atomic spontaneous emission rate.

The gate fidelity scales as:
$$F \approx 1 - \frac{1}{C} - \epsilon_{\text{deph}}$$

enabling fault-tolerant thresholds around $p_{\text{th}} \approx 10^{-2}$.

## Code Structure and Visualizations

### 1. Live Circuit Builder
This module implements a real-time interactive quantum circuit builder using a custom dark-themed GUI. The application provides a 2.5D isometric perspective, allowing users to drag and drop 3D quantum circuit components (such as Data Qubits, Parity Checks, and CNOT gates) onto a grid-based canvas. It features a real-time quantum computation backend that calculates syndromes and simulates error correction as components are placed. It is optimized for QLDPC codes, taking from Qiskit, PennyLane, as well as homebrewed C++ optimizations.



```python
def create_circuit_builder():
    """
    Launch interactive 3D quantum circuit builder platform
    """
    # Initialize 3D isometric renderer with cavity-aware visualization
    builder = QuantumCircuitBuilder3D()
    builder.setup_toolbox()  # LDPC components, cavity modes, stabilizers
    builder.setup_canvas()   # Grid-based placement with snap-to constraints
    
    # Real-time code analysis during construction
    def analyze_constructed_code():
        H_X, H_Z = extract_stabilizer_matrices(placed_components)
        distance = calculate_code_distance(H_X, H_Z)
        rate = calculate_encoding_rate(H_X, H_Z)
        cooperativity_req = estimate_cavity_requirements(placed_components)
        
        return CodeMetrics(distance=distance, rate=rate, 
                          cooperativity=cooperativity_req)
    
    # Preset circuit templates for breakthrough constructions
    preset_circuits = [
        'error_correction_demo.json',      # Basic LDPC error correction
        'syndrome_extraction.json',        # DiVincenzo-Aliferis protocol  
        'surface_code_syndrome_cycle.json', # Surface code comparison
        'quantum_tanner_linear_decoder.json', # Linear distance breakthrough
        'hypergraph_product_ldpc.json'     # Tensor product construction
    ]
    
    builder.load_presets(preset_circuits)
    builder.run()  # Start interactive session
```

![Circuit Builder Overview](Plots/New/MainTutorial.png)

#### Example Circuits

The circuit builder includes a library of pre-built quantum circuits demonstrating various error correction schemes and quantum algorithms. Users can load circuits including quantum teleportation, GHZ state preparation, Grover's algorithm, Deutsch-Jozsa, and multiple LDPC constructions (hypergraph product, quantum Tanner codes, syndrome extraction). Each circuit can be loaded, modified, and analyzed in real-time through the File menu.

![Loading Example Circuits](Plots/New/Circuits.gif)

#### Interactive Tutorial

The circuit builder includes a comprehensive 10-step interactive tutorial system accessible via the Help menu. The basic tutorial guides users through fundamental quantum computing concepts: qubit placement, single-qubit gates (X, Y, Z, H, S, T), two-qubit gates (CNOT, CZ), controlled gate creation, and the three-qubit repetition code. Each step includes live demonstrations that place example components on the grid.

![Tutorial Step 1](Plots/qldpc_tutorial_1.png)
![Tutorial Step 3](Plots/qldpc_tutorial_3.png)

The advanced Surface Code Tutorial provides deeper coverage of error correction: surface code lattice structure with X/Z stabilizers, error injection and syndrome measurement, LDPC mode with Tanner graph visualization, and comparison between surface codes and qLDPC constructions.

![Advanced Tutorial](Plots/New/AdvancedTutorial.gif)

#### Surface Code Mode

Press `V` to toggle into Surface Code Mode, which renders a 2D top-down lattice view optimized for topological code construction. In this mode, burgundy squares represent X-stabilizers (plaquette operators) and purple squares represent Z-stabilizers (vertex operators). Data qubits are placed on edges between stabilizers. The mode supports error injection (X, Z, Y errors) with visual syndrome highlighting, allowing users to observe how errors propagate through the stabilizer structure.

![Surface Code Mode](Plots/New/Surface.gif)

#### QLDPC Mode

Press `B` to cycle through LDPC visualization modes: Tanner graph view and physical layout view. The Tanner graph mode displays the bipartite graph structure with data qubits (teal), X-check nodes (coral), and Z-check nodes (gold) connected by edges representing the parity-check matrix. The physical layout mode shows the tri-layer architecture with X-ancilla, data qubit, and Z-ancilla rows connected via a cavity bus for non-local gate implementation. Arc connections visualize the sparse LDPC connectivity pattern.

![QLDPC Mode](Plots/New/QLDPC.gif)

#### Resources

The Help menu provides quick access to essential references: a keyboard shortcuts dialog (`?`) listing all hotkeys for navigation, component manipulation, and mode switching; a Quick Reference guide with component descriptions and circuit building tips; and a visual Component Legend showing the 3D isometric representation of all available gates, qubits, and stabilizer elements with their corresponding colors and symbols.

![Resources Panel](Plots/New/Resources.gif)

### 2. Interactive Real-Time LDPC Simulator
Implements a comprehensive interactive quantum LDPC circuit simulation with real-time visualization and control. Users can inject errors into qubits by clicking, watch syndrome extraction in real-time, observe the belief propagation decoding process, adjust code parameters dynamically, and see cavity-mediated gates in action.

```python
def create_interactive_ldpc_simulator():
    """
    Launch real-time interactive LDPC circuit simulator
    """
    # Initialize quantum LDPC code with breakthrough scaling
    ldpc_code = QuantumLDPCCode(n_data=21, n_checks=12)
    ldpc_code.distance = int(np.sqrt(n_data))  # Linear distance scaling
    
    # Setup interactive animation with real-time controls
    simulator = LDPCCircuitAnimation(ldpc_code)
    simulator.setup_controls()  # Sliders, buttons, checkboxes
    
    # Mouse click handler for error injection
    def on_click(event):
        for i in range(ldpc_code.n_data):
            if click_detected(i):
                # Cycle through |0⟩ → |1⟩ → X → Z → Y
                ldpc_code.inject_error(i, next_error_type)
                ldpc_code._update_syndrome()  # Real-time syndrome update
    
    # Belief propagation decoder with live visualization
    def belief_propagation_step():
        for check_idx in range(ldpc_code.n_checks):
            # Message passing with syndrome constraints
            if ldpc_code.syndrome[check_idx] == 0:
                messages[check_idx] = prob_even
            else:
                messages[check_idx] = prob_odd
```

![Interactive LDPC Simulator](Plots/Interactive%20Simulation.png)

### 3. GHZ State Preparation and Analysis
Demonstrates distributed GHZ state preparation protocols and fidelity scaling analysis.

```python
def create_ghz_fidelity_analysis():
    """
    Analyze GHZ preparation fidelity vs system size
    """
    n_qubits = np.arange(3, 21)
    
    # Fidelity model: F = 1 - (n-1)/(2C) - (n-1)*ε_cavity
    for C in cooperativities:
        fidelity = 1 - (n_qubits-1)/(2*C) - (n_qubits-1)*epsilon_cavity
        ax.plot(n_qubits, fidelity, label=f'C = {C:.0e}')
```

The distributed GHZ state preparation achieves:
$$\ket{\text{GHZ}_n} = \frac{1}{\sqrt{2}}(\ket{0}^{\otimes n} + \ket{1}^{\otimes n})$$

with fidelity: $F_{\text{GHZ}} = 1 - \frac{n-1}{2C} - (n-1)\epsilon_{\text{cavity}}$

![GHZ Fidelity Analysis](Plots/ghz_fidelity_analysis.png)

### 4. Syndrome Extraction and Error Correction
Implements the DiVincenzo-Aliferis syndrome extraction protocol for qLDPC codes.

```python
def create_syndrome_extraction_circuit():
    """
    Generate syndrome extraction circuit for 4-qubit stabilizer
    """
    qc = QuantumCircuit(5, 1)  # 4 data + 1 ancilla
    
    # Syndrome measurement sequence
    qc.h(4)  # Prepare ancilla in |+⟩
    for i, pauli in enumerate(['Z', 'Z', 'X', 'X']):
        if pauli == 'Z':
            qc.cz(i, 4)
        elif pauli == 'X':
            qc.cx(i, 4)
    qc.h(4)
    qc.measure(4, 0)
```

![Syndrome Extraction](Plots/syndrome_extraction_circuit.png)

### 5. LDPC Process Animations
Comprehensive animations demonstrating Tanner graph evolution, error correction dynamics, and threshold behavior.

```python
def animate_ldpc_tanner_graph():
    """
    Animate LDPC Tanner graph message passing algorithm
    """
    # Initialize bipartite graph: variable nodes ↔ check nodes
    for iteration in range(max_iter):
        # Variable-to-check messages
        for v_node in variable_nodes:
            send_message(v_node, connected_checks[v_node])
        
        # Check-to-variable messages  
        for c_node in check_nodes:
            send_message(c_node, connected_variables[c_node])
```

![LDPC Animation](Plots/ldpc_tanner_graph_animation.gif)

## Performance Analysis

### Scaling Advantages

The asymptotically good qLDPC codes offer dramatic improvements over surface codes:

| Code Type | Rate | Distance | Physical Qubits per Logical | Error Threshold |
|-----------|------|----------|----------------------------|-----------------|
| Surface Codes | $O(1/n)$ | $O(\sqrt{n})$ | $\sim 10^6$ | $\sim 10^{-3}$ |
| Hypergraph Product | $O(1)$ | $O(\sqrt{n})$ | $\sim 10^4$ | $\sim 10^{-2}$ |
| Lifted Product | $\Theta(1)$ | $\Theta(\sqrt{n}\log n)$ | $\sim 10^3$ | $\sim 10^{-2}$ |
| Quantum Tanner | $\Theta(1)$ | $\Theta(n)$ | $\sim 10^3$ | $\sim 10^{-2}$ |
| qLDPC Codes | $\Theta(1)$ | $\Theta(n)$ | $\sim 10^3$ | $\sim 10^{-2}$ |

### Cavity Implementation Requirements

- **Cooperativity**: $C \sim 10^4 - 10^6$
- **Gate Time**: $t_{\text{gate}} \ll 1/\kappa, 1/\gamma$
- **Connectivity**: Non-local via cavity modes
- **Fidelity**: $F > 99\%$ for fault tolerance

## Key Contributions

This implementation demonstrates cavity-mediated non-local gates for qLDPC codes using the tri-layer qubit-ancilla-cavity architecture. The visualizations cover DiVincenzo-Aliferis syndrome extraction, belief propagation decoding, and comparative analysis of code families (surface, hypergraph product, lifted product, quantum Tanner). The theoretical overhead reduction from $\sim 10^6$ to $\sim 10^3$ physical qubits per logical qubit motivates continued experimental development toward the required cooperativity regime ($C \sim 10^4 - 10^6$).

## Future Directions

- **Experimental Realization**: Implementing $C \sim 10^6$ cavity systems
- **Decoding Algorithms**: Efficient decoders for hypergraph product codes  
- **Noise Modeling**: Realistic cavity decoherence and gate errors
- **Scalability Studies**: Performance analysis for $n > 1000$ qubit systems

## Caveats and Challenges

- **Technical Requirements**: Extremely high cavity cooperativity ($C \sim 10^6$)
- **Connectivity Complexity**: Non-local gates require sophisticated cavity networks
- **Decoding Overhead**: Classical decoding algorithms may become bottleneck
- **Experimental Validation**: Current cavity QED systems approach but don't reach required cooperativities

## References

This implementation is based on:

1. **Panteleev & Kalachev** (2021): "Asymptotically Good Quantum and Locally Testable Classical LDPC Codes"
2. **Leverrier & Zémor** (2022): "Quantum Tanner Codes" 
3. **Brennen et al.** (2023): "Non-local resources for error correction in quantum LDPC codes"
4. **Breuckmann & Eberhardt** (2021): "Quantum Low-Density Parity-Check Codes"

> [!IMPORTANT]
> This represents one of the most significant advances in quantum error correction since the discovery of the threshold theorem, potentially enabling practical fault-tolerant quantum computing with dramatically reduced overhead.

> [!NOTE]  
> The visualizations demonstrate theoretical constructions and may require significant experimental advances to achieve the cavity cooperativities needed for practical implementation.



