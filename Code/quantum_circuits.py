"""
Quantum Circuit Visualizations

This script creates quantum circuit diagrams using Qiskit to visualize the key concepts
from Brennen et al.'s paper on non-local resources for quantum LDPC codes.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Import Qiskit components
try:
    from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
    from qiskit.visualization import circuit_drawer
    from qiskit.circuit.library import TwoLocal, RealAmplitudes
    QISKIT_AVAILABLE = True
except ImportError:
    print("Qiskit not available. Creating alternative circuit visualizations.")
    QISKIT_AVAILABLE = False

# Set up the color palettes
seqCmap = sns.color_palette("mako", as_cmap=True)
divCmap = sns.cubehelix_palette(start=.5, rot=-.5, as_cmap=True)
lightCmap = sns.cubehelix_palette(start=2, rot=0, dark=0, light=.95, reverse=True, as_cmap=True)

def create_cavity_mediated_cnot():
    """
    Create Qiskit circuit for cavity-mediated CNOT gate
    """
    print("Creating cavity-mediated CNOT circuit...")
    
    if QISKIT_AVAILABLE:
        # Create quantum circuit with 2 atoms + 1 cavity mode
        qreg_atoms = QuantumRegister(2, 'atom')
        qreg_cavity = QuantumRegister(1, 'cavity')
        circuit = QuantumCircuit(qreg_atoms, qreg_cavity)
        
        # Cavity-mediated CNOT implementation
        # Step 1: Entangle control atom with cavity
        circuit.h(qreg_cavity[0])  # Put cavity in superposition
        circuit.cx(qreg_atoms[0], qreg_cavity[0])  # Control atom - cavity
        
        # Step 2: Controlled rotation on target
        circuit.cry(np.pi, qreg_cavity[0], qreg_atoms[1])  # Cavity controls target
        
        # Step 3: Disentangle cavity
        circuit.cx(qreg_atoms[0], qreg_cavity[0])
        circuit.h(qreg_cavity[0])
        
        # Add measurement (optional)
        creg = ClassicalRegister(2, 'result')
        circuit.add_register(creg)
        circuit.measure(qreg_atoms, creg)
        
        # Draw circuit
        circuit_fig = circuit_drawer(circuit, output='mpl', style='iqx', fold=100)
        
        # Save the circuit
        save_path = os.path.join(os.path.dirname(__file__), '..', 'Plots', 'cavity_cnot_circuit.png')
        circuit_fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(circuit_fig)
        
        print(f"Cavity-mediated CNOT circuit saved to {save_path}")
    
    else:
        create_manual_circuit_cnot()


def create_manual_circuit_cnot():
    """
    Create manual circuit visualization for cavity-mediated CNOT
    """
    print("Creating manual cavity-mediated CNOT circuit...")
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    
    # Circuit parameters
    n_qubits = 3  # 2 atoms + 1 cavity
    n_steps = 8
    
    qubit_labels = ['Control Atom', 'Target Atom', 'Cavity Mode']
    colors = [seqCmap(0.8), seqCmap(0.6), lightCmap(0.3)]
    
    # Draw horizontal lines for qubits
    for i in range(n_qubits):
        ax.plot([0, n_steps], [i, i], color=colors[i], linewidth=3, alpha=0.8)
        ax.text(-0.5, i, qubit_labels[i], ha='right', va='center', fontsize=12, fontweight='bold')
    
    # Gate positions
    gates = [
        (1, 2, 'H'),      # Hadamard on cavity
        (2, [0, 2], 'CNOT'),  # Control-cavity CNOT
        (4, [2, 1], 'CRY'),   # Cavity-controlled rotation
        (6, [0, 2], 'CNOT'),  # Control-cavity CNOT
        (7, 2, 'H'),      # Hadamard on cavity
    ]
    
    for gate in gates:
        time, qubits, gate_type = gate
        
        if gate_type == 'H':
            # Hadamard gate
            rect = plt.Rectangle((time-0.15, qubits-0.15), 0.3, 0.3, 
                               facecolor=lightCmap(0.3), edgecolor='black', linewidth=2)
            ax.add_patch(rect)
            ax.text(time, qubits, 'H', ha='center', va='center', fontsize=12, fontweight='bold')
            
        elif gate_type == 'CNOT':
            # CNOT gate
            control, target = qubits
            # Control dot
            ax.add_patch(plt.Circle((time, control), 0.1, color='black'))
            # Target circle
            ax.add_patch(plt.Circle((time, target), 0.15, fill=False, edgecolor='black', linewidth=2))
            ax.plot([time-0.1, time+0.1], [target, target], 'k-', linewidth=2)
            ax.plot([time, time], [target-0.1, target+0.1], 'k-', linewidth=2)
            # Connection line
            ax.plot([time, time], [min(control, target)+0.1, max(control, target)-0.1], 'k-', linewidth=1)
            
        elif gate_type == 'CRY':
            # Controlled rotation
            control, target = qubits
            # Control dot
            ax.add_patch(plt.Circle((time, control), 0.1, color='black'))
            # Target rotation gate
            rect = plt.Rectangle((time-0.15, target-0.15), 0.3, 0.3, 
                               facecolor=divCmap(0.5), edgecolor='black', linewidth=2)
            ax.add_patch(rect)
            ax.text(time, target, 'RY', ha='center', va='center', fontsize=10, fontweight='bold')
            # Connection line
            ax.plot([time, time], [min(control, target)+0.1, max(control, target)-0.1], 'k-', linewidth=1)
    
    # Add step labels
    step_labels = ['Init', 'H', 'CNOT₁', '', 'CRY', '', 'CNOT₂', 'H']
    for i, label in enumerate(step_labels):
        if label:
            ax.text(i, -0.7, label, ha='center', va='center', fontsize=11, 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    # Formatting
    ax.set_xlim(-1, n_steps)
    ax.set_ylim(-1, n_qubits)
    ax.set_title('Cavity-Mediated CNOT Gate Implementation\n' +
                 'Non-Local Quantum Gate via Optical Cavity', fontsize=16)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Add explanation
    explanation = ("1. Initialize cavity in superposition (H)\n"
                  "2. Entangle control atom with cavity (CNOT₁)\n" 
                  "3. Cavity-controlled rotation on target (CRY)\n"
                  "4. Disentangle control from cavity (CNOT₂)\n"
                  "5. Return cavity to ground state (H)")
    
    ax.text(0.02, 0.02, explanation, transform=ax.transAxes, fontsize=11,
           bbox=dict(boxstyle='round', facecolor=lightCmap(0.1), alpha=0.8),
           verticalalignment='bottom')
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), '..', 'Plots', 'cavity_cnot_circuit.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Manual cavity-mediated CNOT circuit saved to {save_path}")


def create_ghz_preparation_circuit():
    """
    Create quantum circuit for GHZ state preparation
    """
    print("Creating GHZ preparation circuit...")
    
    if QISKIT_AVAILABLE:
        n_qubits = 5
        qreg = QuantumRegister(n_qubits, 'q')
        creg = ClassicalRegister(n_qubits, 'c')
        circuit = QuantumCircuit(qreg, creg)
        
        # GHZ state preparation: |00000⟩ + |11111⟩
        circuit.h(qreg[0])  # Put first qubit in superposition
        
        # Entangle all other qubits with the first
        for i in range(1, n_qubits):
            circuit.cx(qreg[0], qreg[i])
        
        # Add measurement
        circuit.measure(qreg, creg)
        
        # Draw circuit
        circuit_fig = circuit_drawer(circuit, output='mpl', style='iqx', fold=100)
        
        # Save the circuit
        save_path = os.path.join(os.path.dirname(__file__), '..', 'Plots', 'ghz_preparation_circuit.png')
        circuit_fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(circuit_fig)
        
        print(f"GHZ preparation circuit saved to {save_path}")
    
    else:
        create_manual_ghz_circuit()


def create_manual_ghz_circuit():
    """
    Create manual GHZ preparation circuit visualization
    """
    print("Creating manual GHZ preparation circuit...")
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    
    n_qubits = 5
    n_steps = 7
    
    # Draw qubit lines
    for i in range(n_qubits):
        ax.plot([0, n_steps], [i, i], color=seqCmap(0.8), linewidth=3, alpha=0.8)
        ax.text(-0.3, i, f'$|q_{i}\\rangle$', ha='right', va='center', fontsize=12, fontweight='bold')
    
    # Initial state labels
    for i in range(n_qubits):
        ax.text(0.5, i, '|0⟩', ha='center', va='center', fontsize=11,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Hadamard gate on first qubit
    h_rect = plt.Rectangle((1-0.15, 0-0.15), 0.3, 0.3, 
                          facecolor=lightCmap(0.3), edgecolor='black', linewidth=2)
    ax.add_patch(h_rect)
    ax.text(1, 0, 'H', ha='center', va='center', fontsize=12, fontweight='bold')
    
    # CNOT gates
    cnot_positions = [2, 3, 4, 5]
    for i, time in enumerate(cnot_positions):
        target_qubit = i + 1
        
        # Control dot on qubit 0
        ax.add_patch(plt.Circle((time, 0), 0.1, color='black'))
        
        # Target on other qubits
        ax.add_patch(plt.Circle((time, target_qubit), 0.15, fill=False, edgecolor='black', linewidth=2))
        ax.plot([time-0.1, time+0.1], [target_qubit, target_qubit], 'k-', linewidth=2)
        ax.plot([time, time], [target_qubit-0.1, target_qubit+0.1], 'k-', linewidth=2)
        
        # Connection line
        ax.plot([time, time], [0.1, target_qubit-0.1], 'k-', linewidth=1)
    
    # Final state annotation
    final_time = 6
    ax.text(final_time, n_qubits/2, r'$|\psi_{GHZ}\rangle = \frac{1}{\sqrt{2}}(|00000\rangle + |11111\rangle)$', 
           ha='center', va='center', fontsize=14, fontweight='bold',
           bbox=dict(boxstyle='round', facecolor=seqCmap(0.2), alpha=0.3))
    
    # Formatting
    ax.set_xlim(-0.5, n_steps)
    ax.set_ylim(-0.5, n_qubits + 0.5)
    ax.set_title('5-Qubit GHZ State Preparation Circuit\n' +
                 'Essential Building Block for Quantum LDPC Codes', fontsize=16)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Add step annotations
    steps = ['Init', 'H', 'CNOT₁', 'CNOT₂', 'CNOT₃', 'CNOT₄', 'GHZ']
    for i, step in enumerate(steps):
        ax.text(i, -0.8, step, ha='center', va='center', fontsize=11,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), '..', 'Plots', 'ghz_preparation_circuit.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Manual GHZ preparation circuit saved to {save_path}")


def create_error_correction_circuit():
    """
    Create quantum circuit for basic error correction
    """
    print("Creating error correction circuit...")
    
    if QISKIT_AVAILABLE:
        # 3-qubit bit flip code
        qreg_data = QuantumRegister(3, 'data')
        qreg_ancilla = QuantumRegister(2, 'ancilla')
        creg_syndrome = ClassicalRegister(2, 'syndrome')
        circuit = QuantumCircuit(qreg_data, qreg_ancilla, creg_syndrome)
        
        # Encode logical |0⟩ -> |000⟩
        # (Initial state is already |000⟩)
        
        # Syndrome extraction
        circuit.cx(qreg_data[0], qreg_ancilla[0])
        circuit.cx(qreg_data[1], qreg_ancilla[0])
        circuit.cx(qreg_data[1], qreg_ancilla[1])
        circuit.cx(qreg_data[2], qreg_ancilla[1])
        
        # Measure syndrome
        circuit.measure(qreg_ancilla, creg_syndrome)
        
        # Draw circuit
        circuit_fig = circuit_drawer(circuit, output='mpl', style='iqx', fold=100)
        
        # Save the circuit
        save_path = os.path.join(os.path.dirname(__file__), '..', 'Plots', 'error_correction_circuit.png')
        circuit_fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(circuit_fig)
        
        print(f"Error correction circuit saved to {save_path}")
    
    else:
        create_manual_error_correction_circuit()


def create_manual_error_correction_circuit():
    """
    Create manual error correction circuit visualization
    """
    print("Creating manual error correction circuit...")
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    
    n_data_qubits = 3
    n_ancilla_qubits = 2
    n_steps = 6
    
    # Draw data qubit lines
    for i in range(n_data_qubits):
        ax.plot([0, n_steps], [i, i], color=seqCmap(0.8), linewidth=3, alpha=0.8)
        ax.text(-0.3, i, f'$d_{i}$', ha='right', va='center', fontsize=12, fontweight='bold')
    
    # Draw ancilla qubit lines
    for i in range(n_ancilla_qubits):
        y_pos = n_data_qubits + i
        ax.plot([0, n_steps], [y_pos, y_pos], color=divCmap(0.6), linewidth=3, alpha=0.8)
        ax.text(-0.3, y_pos, f'$a_{i}$', ha='right', va='center', fontsize=12, fontweight='bold')
    
    # Syndrome extraction gates
    # Parity check 1: d0 ⊕ d1
    time1 = 2
    ax.add_patch(plt.Circle((time1, 0), 0.1, color='black'))  # Control on d0
    ax.add_patch(plt.Circle((time1, 3), 0.15, fill=False, edgecolor='black', linewidth=2))  # Target on a0
    ax.plot([time1-0.1, time1+0.1], [3, 3], 'k-', linewidth=2)
    ax.plot([time1, time1], [2.9, 3.1], 'k-', linewidth=2)
    ax.plot([time1, time1], [0.1, 2.9], 'k-', linewidth=1)
    
    ax.add_patch(plt.Circle((time1+0.5, 1), 0.1, color='black'))  # Control on d1
    ax.add_patch(plt.Circle((time1+0.5, 3), 0.15, fill=False, edgecolor='black', linewidth=2))  # Target on a0
    ax.plot([time1+0.5-0.1, time1+0.5+0.1], [3, 3], 'k-', linewidth=2)
    ax.plot([time1+0.5, time1+0.5], [2.9, 3.1], 'k-', linewidth=2)
    ax.plot([time1+0.5, time1+0.5], [1.1, 2.9], 'k-', linewidth=1)
    
    # Parity check 2: d1 ⊕ d2
    time2 = 4
    ax.add_patch(plt.Circle((time2, 1), 0.1, color='black'))  # Control on d1
    ax.add_patch(plt.Circle((time2, 4), 0.15, fill=False, edgecolor='black', linewidth=2))  # Target on a1
    ax.plot([time2-0.1, time2+0.1], [4, 4], 'k-', linewidth=2)
    ax.plot([time2, time2], [3.9, 4.1], 'k-', linewidth=2)
    ax.plot([time2, time2], [1.1, 3.9], 'k-', linewidth=1)
    
    ax.add_patch(plt.Circle((time2+0.5, 2), 0.1, color='black'))  # Control on d2
    ax.add_patch(plt.Circle((time2+0.5, 4), 0.15, fill=False, edgecolor='black', linewidth=2))  # Target on a1
    ax.plot([time2+0.5-0.1, time2+0.5+0.1], [4, 4], 'k-', linewidth=2)
    ax.plot([time2+0.5, time2+0.5], [3.9, 4.1], 'k-', linewidth=2)
    ax.plot([time2+0.5, time2+0.5], [2.1, 3.9], 'k-', linewidth=1)
    
    # Measurements
    meas_time = 5.5
    for i in range(n_ancilla_qubits):
        y_pos = n_data_qubits + i
        meas_rect = plt.Rectangle((meas_time-0.15, y_pos-0.15), 0.3, 0.3, 
                                 facecolor=divCmap(0.5), edgecolor='black', linewidth=2)
        ax.add_patch(meas_rect)
        ax.text(meas_time, y_pos, 'M', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Formatting
    ax.set_xlim(-0.5, n_steps + 0.5)
    ax.set_ylim(-0.5, n_data_qubits + n_ancilla_qubits)
    ax.set_title('3-Qubit Error Correction Circuit\n' +
                 'Syndrome Extraction for Bit-Flip Code', fontsize=16)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Add syndrome lookup table
    syndrome_table = ("Syndrome Lookup:\n"
                     "00 → No error\n"
                     "10 → Error on d₀\n" 
                     "11 → Error on d₁\n"
                     "01 → Error on d₂")
    
    ax.text(0.02, 0.98, syndrome_table, transform=ax.transAxes, fontsize=11,
           bbox=dict(boxstyle='round', facecolor=lightCmap(0.1), alpha=0.8),
           verticalalignment='top')
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), '..', 'Plots', 'error_correction_circuit.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Manual error correction circuit saved to {save_path}")


if __name__ == "__main__":
    print("Generating quantum circuit visualizations...")
    
    # Create output directory if it doesn't exist
    plots_dir = os.path.join(os.path.dirname(__file__), '..', 'Plots')
    os.makedirs(plots_dir, exist_ok=True)
    
    try:
        create_cavity_mediated_cnot()
        create_ghz_preparation_circuit()
        create_error_correction_circuit()
        print("All quantum circuit visualizations completed successfully!")
        
    except Exception as e:
        print(f"Error in visualization generation: {e}")
