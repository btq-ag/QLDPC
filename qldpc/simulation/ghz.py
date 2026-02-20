"""
GHZ State Preparation Visualization

This script creates visualizations for GHZ state preparation protocols as described in 
Brennen et al.'s paper, focusing on the cavity-mediated approach and fidelity analysis.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch
import os

# Set up the color palettes
seqCmap = sns.color_palette("mako", as_cmap=True)
divCmap = sns.cubehelix_palette(start=.5, rot=-.5, as_cmap=True)
lightCmap = sns.cubehelix_palette(start=2, rot=0, dark=0, light=.95, reverse=True, as_cmap=True)

def create_ghz_fidelity_analysis():
    """
    Create visualization of GHZ state preparation fidelity vs system parameters
    """
    print("Creating GHZ state fidelity analysis...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Left plot: Fidelity vs number of qubits
    n_qubits = np.arange(3, 21)
    
    # Different cavity cooperativity values
    C_values = [1e3, 1e4, 1e5, 1e6]
    colors = [seqCmap(i/len(C_values)) for i in range(len(C_values))]
    
    for i, C in enumerate(C_values):
        # GHZ fidelity model: F = exp(-n*ε) where ε ~ 1/C
        epsilon = 1/C + 0.001  # Base error rate
        fidelity = np.exp(-n_qubits * epsilon)
        
        ax1.plot(n_qubits, fidelity, 'o-', color=colors[i], linewidth=2.5, 
                markersize=6, label=f'$C = 10^{{{int(np.log10(C))}}}$')
    
    # Add threshold line
    ax1.axhline(y=0.9, color='red', linestyle='--', linewidth=2, alpha=0.7,
                label='Target Fidelity (90%)')
    
    ax1.set_xlabel('Number of Qubits in GHZ State', fontsize=14)
    ax1.set_ylabel('State Preparation Fidelity', fontsize=14)
    ax1.set_title('GHZ State Fidelity vs System Size', fontsize=16)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=12)
    ax1.set_ylim(0, 1.05)
    
    # Right plot: Preparation time vs cooperativity
    C_range = np.logspace(3, 6, 100)
    
    # Gate time scaling with cooperativity: t_gate ~ 1/sqrt(C)
    base_gate_time = 1.0  # microseconds
    gate_times = base_gate_time / np.sqrt(C_range/1e3)
    
    # Total preparation time for n-qubit GHZ (scales logarithmically with n)
    n_values = [5, 10, 15, 20]
    prep_colors = [divCmap(i/len(n_values)) for i in range(len(n_values))]
    
    for i, n in enumerate(n_values):
        # Preparation requires ~log(n) parallel steps
        prep_times = gate_times * np.log2(n)
        ax2.loglog(C_range, prep_times, linewidth=2.5, color=prep_colors[i],
                  label=f'{n}-qubit GHZ')
    
    # Add practical time constraints
    ax2.axhline(y=100, color='orange', linestyle=':', linewidth=2, alpha=0.7,
                label='Decoherence Limit (~100 μs)')
    
    ax2.set_xlabel('Cavity Cooperativity $C$', fontsize=14)
    ax2.set_ylabel('Preparation Time (μs)', fontsize=14)
    ax2.set_title('GHZ Preparation Time vs Cooperativity', fontsize=16)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=12)
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Plots', 'ghz_fidelity_analysis.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"GHZ fidelity analysis saved to {save_path}")


def create_ghz_preparation_protocol():
    """
    Create step-by-step visualization of GHZ state preparation protocol
    """
    print("Creating GHZ preparation protocol visualization...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    steps = [
        "Step 1: Initialize Atoms in Ground State",
        "Step 2: Cavity-Mediated Entangling Gates", 
        "Step 3: Measurement and Post-Selection",
        "Step 4: Final GHZ State Verification"
    ]
    
    # Step 1: Initial state
    ax = axes[0]
    ax.set_title(steps[0], fontsize=14, fontweight='bold')
    
    # Draw 5 atoms in ground state
    n_atoms = 5
    atom_positions = np.linspace(1, 9, n_atoms)
    
    for i, x in enumerate(atom_positions):
        # Ground state atoms
        circle = Circle((x, 3), 0.4, color=lightCmap(0.3), alpha=0.8)
        ax.add_patch(circle)
        ax.text(x, 3, '|0⟩', ha='center', va='center', fontsize=12, fontweight='bold')
        ax.text(x, 2, f'Atom {i+1}', ha='center', va='center', fontsize=10)
    
    # Draw cavity
    cavity_rect = Rectangle((0.5, 1), 9, 4, fill=False, edgecolor='black', 
                           linewidth=2, linestyle='--')
    ax.add_patch(cavity_rect)
    ax.text(5, 0.5, 'Optical Cavity', ha='center', va='center', fontsize=12)
    
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Step 2: Entangling gates
    ax = axes[1]
    ax.set_title(steps[1], fontsize=14, fontweight='bold')
    
    # Show atoms in superposition
    for i, x in enumerate(atom_positions):
        if i == 0:  # First atom remains in |0⟩
            circle = Circle((x, 3), 0.4, color=lightCmap(0.3), alpha=0.8)
            ax.add_patch(circle)
            ax.text(x, 3, '|0⟩', ha='center', va='center', fontsize=12, fontweight='bold')
        else:  # Others in superposition
            circle = Circle((x, 3), 0.4, color=seqCmap(0.6), alpha=0.8)
            ax.add_patch(circle)
            ax.text(x, 3, '|+⟩', ha='center', va='center', fontsize=12, fontweight='bold')
        ax.text(x, 2, f'Atom {i+1}', ha='center', va='center', fontsize=10)
    
    # Draw entangling connections
    for i in range(1, n_atoms):
        ax.plot([atom_positions[0], atom_positions[i]], [3.4, 3.4], 
               'r-', linewidth=2, alpha=0.7)
        ax.text((atom_positions[0] + atom_positions[i])/2, 3.8, 'CNOT', 
               ha='center', fontsize=10, color='red')
    
    # Cavity
    cavity_rect = Rectangle((0.5, 1), 9, 4, fill=False, edgecolor='black', 
                           linewidth=2, linestyle='--')
    ax.add_patch(cavity_rect)
    ax.text(5, 0.5, 'Cavity Mediates Non-Local Gates', ha='center', va='center', fontsize=12)
    
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Step 3: Measurement
    ax = axes[2]
    ax.set_title(steps[2], fontsize=14, fontweight='bold')
    
    # Show measurement apparatus
    for i, x in enumerate(atom_positions):
        circle = Circle((x, 3), 0.4, color=divCmap(0.5), alpha=0.8)
        ax.add_patch(circle)
        ax.text(x, 3, '?', ha='center', va='center', fontsize=12, fontweight='bold')
        
        # Measurement detectors
        detector = Rectangle((x-0.2, 1.5), 0.4, 0.8, color='gray', alpha=0.6)
        ax.add_patch(detector)
        ax.plot([x, x], [2.6, 2.3], 'k-', linewidth=2)
        ax.text(x, 1, f'Det {i+1}', ha='center', va='center', fontsize=10)
    
    ax.text(5, 4.5, 'Simultaneous Z-basis Measurements', ha='center', va='center', 
           fontsize=12, fontweight='bold', color='blue')
    
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Step 4: GHZ state
    ax = axes[3]
    ax.set_title(steps[3], fontsize=14, fontweight='bold')
    
    # Show final GHZ state
    for i, x in enumerate(atom_positions):
        circle = Circle((x, 3), 0.4, color=seqCmap(0.8), alpha=0.8)
        ax.add_patch(circle)
        ax.text(x, 3, 'GHZ', ha='center', va='center', fontsize=10, fontweight='bold')
        ax.text(x, 2, f'Atom {i+1}', ha='center', va='center', fontsize=10)
    
    # Show entanglement
    for i in range(n_atoms-1):
        for j in range(i+1, n_atoms):
            ax.plot([atom_positions[i], atom_positions[j]], [3.8, 3.8], 
                   'g-', linewidth=1, alpha=0.4)
    
    # State equation
    ax.text(5, 4.5, r'$|\psi_{GHZ}\rangle = \frac{1}{\sqrt{2}}(|00000\rangle + |11111\rangle)$', 
           ha='center', va='center', fontsize=14, fontweight='bold')
    
    ax.text(5, 0.5, f'Fidelity: F = {0.95:.2f}', ha='center', va='center', 
           fontsize=12, color='green', fontweight='bold')
    
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Plots', 'ghz_preparation_protocol.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"GHZ preparation protocol saved to {save_path}")


def create_ghz_scaling_analysis():
    """
    Create visualization of GHZ state scaling properties and resource requirements
    """
    print("Creating GHZ scaling analysis...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Left plot: Resource scaling
    n_qubits = np.arange(3, 51)
    
    # Gate count scaling (logarithmic for tree-based protocol)
    gate_count = np.log2(n_qubits) * 2  # Two-qubit gates
    
    # Cavity mode requirements (assuming distributed approach)
    cavity_modes = np.ceil(n_qubits / 4)  # 4 qubits per cavity
    
    # Plot gate scaling
    ax1_twin = ax1.twinx()
    
    line1 = ax1.plot(n_qubits, gate_count, 'o-', color=seqCmap(0.8), linewidth=2.5, 
                    markersize=4, label='Two-Qubit Gates')
    line2 = ax1_twin.plot(n_qubits, cavity_modes, 's-', color=divCmap(0.6), linewidth=2.5, 
                         markersize=4, label='Cavity Modes Required')
    
    ax1.set_xlabel('Number of Qubits in GHZ State', fontsize=14)
    ax1.set_ylabel('Number of Two-Qubit Gates', fontsize=14, color=seqCmap(0.8))
    ax1_twin.set_ylabel('Number of Cavity Modes', fontsize=14, color=divCmap(0.6))
    ax1.set_title('Resource Scaling for GHZ State Preparation', fontsize=16)
    ax1.grid(True, alpha=0.3)
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', fontsize=12)
    
    # Color the y-axis labels
    ax1.tick_params(axis='y', labelcolor=seqCmap(0.8))
    ax1_twin.tick_params(axis='y', labelcolor=divCmap(0.6))
    
    # Right plot: Success probability vs system size
    success_prob_ideal = np.ones_like(n_qubits)  # Ideal case
    
    # Realistic success probability with decoherence
    T1 = 100e-6  # 100 microseconds coherence time
    gate_time = 1e-6  # 1 microsecond per gate
    
    total_time = gate_count * gate_time
    success_prob_real = np.exp(-total_time / T1)
    
    # With error correction
    success_prob_ec = 1 - (1 - success_prob_real) * 0.1  # 90% error correction efficiency
    
    ax2.plot(n_qubits, success_prob_ideal, '--', color='gray', linewidth=2, 
            alpha=0.5, label='Ideal (No Decoherence)')
    ax2.plot(n_qubits, success_prob_real, 'o-', color=seqCmap(0.3), linewidth=2.5, 
            markersize=4, label='With Decoherence')
    ax2.plot(n_qubits, success_prob_ec, 's-', color=seqCmap(0.8), linewidth=2.5, 
            markersize=4, label='With Error Correction')
    
    ax2.set_xlabel('Number of Qubits in GHZ State', fontsize=14)
    ax2.set_ylabel('Success Probability', fontsize=14)
    ax2.set_title('GHZ Preparation Success Rate', fontsize=16)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=12)
    ax2.set_ylim(0, 1.05)
    
    # Add annotations
    ax2.annotate('Decoherence Limit', 
                xy=(30, success_prob_real[27]), xytext=(35, 0.3),
                arrowprops=dict(arrowstyle='->', color=seqCmap(0.3)),
                fontsize=12, color=seqCmap(0.3))
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Plots', 'ghz_scaling_analysis.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"GHZ scaling analysis saved to {save_path}")


def main():
    print("Generating GHZ state preparation visualizations...")
    
    # Create output directory if it doesn't exist
    plots_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Plots')
    os.makedirs(plots_dir, exist_ok=True)
    
    try:
        create_ghz_fidelity_analysis()
        create_ghz_preparation_protocol()
        create_ghz_scaling_analysis()
        print("All GHZ state preparation visualizations completed successfully!")
        
    except Exception as e:
        print(f"Error in visualization generation: {e}")


if __name__ == "__main__":
    main()
