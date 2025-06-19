# Code Documentation
## Quantum LDPC Implementation and Visualization Suite

This directory contains the complete implementation of quantum Low-Density Parity-Check (qLDPC) code visualizations and animations, focusing on Brennen et al.'s cavity-mediated approach and general LDPC processes.

## File Structure

### Core Visualization Scripts

#### `cavity_mediated_gates.py`
**Purpose**: Implements visualizations for cavity-mediated quantum gates and tri-layer architecture analysis.

**Key Functions**:
- `create_cavity_cooperativity_analysis()`: Generates cooperativity threshold analysis
- `create_trilayer_architecture()`: Visualizes the data-ancilla-cavity layer structure  
- `create_error_threshold_analysis()`: Plots error threshold behavior for different code distances

**Dependencies**: `numpy`, `matplotlib`, `seaborn`

**Output Files**: 
- `cavity_cooperativity.png`
- `trilayer_architecture.png` 
- `error_threshold.png`

**Mathematical Models**:
- Cooperativity definition: C = g²/(κγ)
- Gate fidelity scaling: F ≈ 1 - 1/C - ε_deph
- Threshold behavior for distances d = [3, 5, 7, 9]

#### `quantum_circuits.py`
**Purpose**: Creates Qiskit-based quantum circuit visualizations for cavity-mediated protocols.

**Key Functions**:
- `create_cavity_cnot_circuit()`: Generates cavity-mediated CNOT gate implementation
- `create_ghz_preparation_circuit()`: Shows distributed GHZ state preparation protocol
- `create_error_correction_circuit()`: Demonstrates syndrome extraction circuit

**Dependencies**: `qiskit`, `matplotlib`

**Circuit Implementations**:
- **Cavity CNOT**: 4-qubit circuit with 2 data qubits and 2 cavity modes
- **GHZ Preparation**: Sequential cavity-mediated entanglement protocol
- **Syndrome Extraction**: DiVincenzo-Aliferis measurement protocol

**Technical Details**:
- All circuits use standard gate decompositions
- Cavity modes represented as auxiliary qubits
- Measurement outcomes stored in classical registers

#### `ghz_state_preparation.py`
**Purpose**: Analyzes distributed GHZ state preparation protocols and scaling behavior.

**Key Functions**:
- `create_ghz_preparation_protocol()`: Step-by-step GHZ preparation visualization
- `create_ghz_fidelity_analysis()`: Fidelity scaling with system size and cooperativity
- `create_ghz_scaling_analysis()`: Resource requirements vs number of qubits

**Analysis Framework**:
- Fidelity models based on cavity decoherence
- Scaling laws for preparation time and resources
- Comparison across different cooperativity regimes

**Performance Metrics**:
- Preparation fidelity vs system size
- Gate count scaling
- Required cooperativity thresholds

#### `syndrome_extraction.py`
**Purpose**: Implements syndrome extraction circuit analysis and error propagation studies.

**Key Functions**:
- `create_syndrome_extraction_circuit()`: Visualizes measurement protocol
- `create_fault_tolerant_measurement()`: Shows error-corrected syndrome extraction
- `create_syndrome_error_analysis()`: Analyzes measurement error propagation

**Protocol Implementation**:
- Standard DiVincenzo-Aliferis syndrome extraction
- Fault-tolerant measurement with ancilla verification
- Error propagation modeling through measurement circuits

**Error Models**:
- Gate errors during syndrome extraction
- Measurement errors and their correction
- Ancilla preparation and readout fidelity

#### `ldpc_process_animation.py`
**Purpose**: Creates comprehensive animations of LDPC decoding processes and threshold behavior.

**Key Functions**:
- `animate_ldpc_tanner_graph()`: Message-passing algorithm visualization
- `animate_ldpc_error_correction()`: Complete error correction cycle
- `animate_ldpc_threshold_behavior()`: Threshold transition demonstration

**Animation Features**:
- Real-time message passing on Tanner graphs
- Error propagation and correction visualization  
- Threshold behavior across different error rates
- LaTeX equation rendering for mathematical expressions

**Technical Implementation**:
- Frame-by-frame animation using matplotlib.animation
- Dynamic graph layouts for Tanner graph evolution
- Color-coded node states for message passing
- Text overlays with current algorithm state

## Code Quality Standards

### Style Guidelines
- **Function Documentation**: Complete docstrings with parameter descriptions
- **Error Handling**: Try-catch blocks with graceful fallbacks
- **Color Palettes**: Consistent use of specified seaborn palettes
- **File Organization**: Modular functions with single responsibilities

### Visualization Standards
- **Resolution**: All plots saved at 300 DPI minimum
- **Color Schemes**: 
  - Sequential: `sns.color_palette("mako", as_cmap=True)`
  - Diverging: `sns.cubehelix_palette(start=.5, rot=-.5, as_cmap=True)`
  - Light: `sns.cubehelix_palette(start=2, rot=0, dark=0, light=.95, reverse=True, as_cmap=True)`
- **Typography**: LaTeX rendering for all mathematical expressions
- **Layout**: Professional subplot arrangements with proper spacing

### Animation Requirements
- **Frame Rate**: 10 FPS for smooth playback
- **Duration**: 5-10 seconds for complete cycles
- **Text Rendering**: All equations properly formatted with LaTeX
- **Compression**: Optimized GIF output with PIL writer

## Dependencies and Installation

### Required Packages
```python
# Core scientific computing
numpy >= 1.21.0
matplotlib >= 3.5.0
seaborn >= 0.11.0

# Quantum computing frameworks
qiskit >= 0.39.0
qiskit-aer >= 0.11.0

# Animation and visualization
pillow >= 8.3.0
scipy >= 1.7.0
```

### Installation Commands
```bash
pip install numpy matplotlib seaborn
pip install qiskit qiskit-aer
pip install pillow scipy
```

### Environment Setup
- **Python Version**: 3.8+ required for Qiskit compatibility
- **Memory Requirements**: 4GB+ RAM for large Tanner graph animations
- **Display**: High-resolution monitor recommended for detailed visualizations

## Usage Instructions

### Running Individual Scripts
Each script can be executed independently:

```bash
cd Code/
python cavity_mediated_gates.py
python quantum_circuits.py
python ghz_state_preparation.py
python syndrome_extraction.py
python ldpc_process_animation.py
```

### Output Management
- All plots automatically saved to `../Plots/` directory
- Filenames follow consistent naming convention
- Existing files are overwritten without warning
- Directory creation handled automatically if needed

### Customization Options

#### Color Palette Modification
```python
# Modify at script header
seqCmap = sns.color_palette("viridis", as_cmap=True)  # Alternative sequential
divCmap = sns.color_palette("RdBu", as_cmap=True)    # Alternative diverging
```

#### Animation Parameters
```python
# In animation functions
fps = 10          # Frames per second
duration = 8.0    # Total animation time
interval = 100    # Milliseconds between frames
```

#### Plot Resolution
```python
# In save commands
plt.savefig(save_path, dpi=300, bbox_inches='tight')  # High resolution
plt.savefig(save_path, dpi=150, bbox_inches='tight')  # Medium resolution
```

## Algorithm Implementations

### LDPC Decoding
The animations implement several key algorithms:

#### Belief Propagation
- **Variable-to-Check Messages**: Probability distributions over bit values
- **Check-to-Variable Messages**: Parity constraint enforcement
- **Convergence Criteria**: Maximum iterations or probability threshold
- **Scheduling**: Simultaneous vs sequential message updates

#### Syndrome Decoding
- **Syndrome Calculation**: Parity check evaluation
- **Error Localization**: Maximum likelihood estimation
- **Correction Application**: Bit flip or phase flip operations
- **Verification**: Syndrome recalculation after correction

### Cavity Gate Protocols
Implementation of theoretical protocols from Brennen et al.:

#### Distributed CNOT
1. **Cavity Preparation**: Initialize cavity in |+⟩ state
2. **Control Coupling**: Conditional coupling to cavity mode
3. **Target Interaction**: Cavity-mediated phase accumulation
4. **Decoupling**: Return cavity to ground state
5. **Verification**: Optional process tomography

#### GHZ State Preparation
1. **Initialization**: All qubits in |0⟩ state
2. **Superposition**: Hadamard on first qubit
3. **Sequential Entanglement**: Cavity-mediated CNOT gates
4. **State Verification**: Stabilizer measurements
5. **Fidelity Assessment**: Process tomography results

## Error Handling and Debugging

### Common Issues
- **Import Errors**: Ensure all dependencies installed correctly
- **Memory Errors**: Reduce animation resolution or frame count
- **Display Issues**: Check matplotlib backend configuration
- **File Permissions**: Verify write access to Plots directory

### Debug Mode
Enable verbose output by modifying script headers:
```python
DEBUG = True  # Set to False for production runs

if DEBUG:
    print(f"Processing frame {i}/{total_frames}")
    print(f"Current state: {current_algorithm_state}")
```

### Performance Optimization
- **Large Graphs**: Use sparse matrix representations
- **Memory Management**: Clear figure objects after saving
- **Parallel Processing**: Consider multiprocessing for batch generation
- **Caching**: Store intermediate results for repeated calculations

## Testing and Validation

### Verification Methods
- **Visual Inspection**: Manual review of generated plots
- **Mathematical Consistency**: Verify equations and scaling laws
- **Reference Comparison**: Match literature values where possible
- **Cross-Platform Testing**: Validate on different operating systems

### Quality Assurance
- **Code Review**: All functions documented and tested
- **Output Validation**: Automated checks for file generation
- **Consistency Checks**: Color schemes and formatting standards
- **Performance Benchmarks**: Execution time monitoring

This documentation provides comprehensive guidance for understanding, using, and modifying the quantum LDPC visualization codebase. The implementations follow best practices for scientific computing and visualization while maintaining the theoretical rigor required for quantum error correction research.
