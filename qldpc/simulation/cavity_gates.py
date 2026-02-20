"""
Cavity-Mediated Gates Visualization

This script creates visualizations for cavity-mediated quantum gates as described in 
Brennen et al.'s paper on non-local resources for quantum LDPC codes.
Focuses on the cavity cooperativity requirements and gate fidelity analysis.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch
import os

# Set up the color palettes as specified
seqCmap = sns.color_palette("mako", as_cmap=True)
divCmap = sns.cubehelix_palette(start=.5, rot=-.5, as_cmap=True)
lightCmap = sns.cubehelix_palette(start=2, rot=0, dark=0, light=.95, reverse=True, as_cmap=True)

def create_cavity_cooperativity_analysis():
    """
    Create visualization of cavity cooperativity requirements for non-local gates
    """
    print("Creating cavity cooperativity analysis...")
    
    # Set up the figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Define cooperativity range (C values from 10^3 to 10^6)
    C_values = np.logspace(3, 6, 100)
    
    # Gate fidelity model based on cavity cooperativity
    # F = 1 - ε where ε ~ 1/C for high cooperativity
    gate_fidelity = 1 - 1/C_values - 0.01*np.exp(-C_values/1e4)
    
    # Error threshold for fault-tolerant quantum computing
    threshold_fidelity = 0.99  # 99% fidelity threshold
    
    # Plot the main curve
    ax.semilogx(C_values, gate_fidelity, linewidth=3, color=seqCmap(0.8), 
                label='Gate Fidelity')
    
    # Add threshold line
    ax.axhline(y=threshold_fidelity, color=seqCmap(0.3), linestyle='--', 
               linewidth=2, label=f'Fault-Tolerant Threshold ({threshold_fidelity})')
    
    # Highlight the required cooperativity region
    C_min = 1e4  # Minimum cooperativity for fault tolerance
    C_max = 1e6  # Practical upper limit
    
    ax.axvspan(C_min, C_max, alpha=0.2, color=seqCmap(0.5), 
               label=f'Required Range: $C \\sim 10^4 - 10^6$')
    
    # Add annotations for key points
    ax.annotate('Fault-Tolerant Region', 
                xy=(3e4, 0.995), xytext=(1e5, 0.985),
                arrowprops=dict(arrowstyle='->', color=seqCmap(0.7)),
                fontsize=12, color=seqCmap(0.7))
    
    ax.annotate('Sub-threshold\nPerformance', 
                xy=(5e3, 0.985), xytext=(2e3, 0.975),
                arrowprops=dict(arrowstyle='->', color=seqCmap(0.3)),
                fontsize=12, color=seqCmap(0.3))
    
    # Formatting
    ax.set_xlabel('Cavity Cooperativity $C$', fontsize=14)
    ax.set_ylabel('Gate Fidelity', fontsize=14)
    ax.set_title('Cavity Cooperativity Requirements for Non-Local Gates\n' +
                 'Quantum LDPC Error Correction', fontsize=16)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=12)
    ax.set_ylim(0.95, 1.0)
    
    # Add text box with key parameters
    textstr = r'$C = \frac{g^2}{\kappa \gamma}$' + '\n\n' + \
              r'$g$: atom-cavity coupling' + '\n' + \
              r'$\kappa$: cavity decay rate' + '\n' + \
              r'$\gamma$: atomic decay rate'
    
    props = dict(boxstyle='round', facecolor=lightCmap(0.1), alpha=0.8)
    ax.text(0.02, 0.02, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='bottom', bbox=props)
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Plots', 'cavity_cooperativity.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Cavity cooperativity analysis saved to {save_path}")


def create_trilayer_architecture():
    """
    Create visualization of the tri-layer architecture for quantum LDPC codes
    """
    print("Creating tri-layer architecture visualization...")
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    
    # Define layer positions
    layer_height = 2.5
    layer_spacing = 1.0
    
    # Layer 1: Data qubits (bottom)
    data_y = 0
    data_qubits = 12
    data_x = np.linspace(1, 13, data_qubits)
    
    # Layer 2: Ancilla qubits (middle) 
    ancilla_y = data_y + layer_height + layer_spacing
    ancilla_qubits = 6
    ancilla_x = np.linspace(2.5, 11.5, ancilla_qubits)
    
    # Layer 3: Cavity modes (top)
    cavity_y = ancilla_y + layer_height + layer_spacing
    cavity_modes = 3
    cavity_x = np.linspace(4, 10, cavity_modes)
    
    # Draw data qubits
    for i, x in enumerate(data_x):
        color = seqCmap(0.8) if i % 2 == 0 else seqCmap(0.6)
        circle = Circle((x, data_y), 0.3, color=color, alpha=0.8)
        ax.add_patch(circle)
        ax.text(x, data_y, f'D{i+1}', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Draw ancilla qubits
    for i, x in enumerate(ancilla_x):
        color = divCmap(0.7)
        circle = Circle((x, ancilla_y), 0.3, color=color, alpha=0.8)
        ax.add_patch(circle)
        ax.text(x, ancilla_y, f'A{i+1}', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Draw cavity modes
    for i, x in enumerate(cavity_x):
        color = lightCmap(0.3)
        rect = FancyBboxPatch((x-0.5, cavity_y-0.3), 1.0, 0.6, 
                             boxstyle="round,pad=0.1", 
                             facecolor=color, alpha=0.8, edgecolor='black')
        ax.add_patch(rect)
        ax.text(x, cavity_y, f'C{i+1}', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Draw connections (simplified parity checks)
    # Data to ancilla connections
    for i in range(ancilla_qubits):
        # Each ancilla connects to 4 data qubits
        start_data = i * 2
        for j in range(4):
            if start_data + j < data_qubits:
                ax.plot([data_x[start_data + j], ancilla_x[i]], 
                       [data_y + 0.3, ancilla_y - 0.3], 
                       'k-', alpha=0.4, linewidth=1)
    
    # Ancilla to cavity connections (non-local gates)
    for i in range(cavity_modes):
        # Each cavity connects to 2 ancilla qubits
        start_ancilla = i * 2
        for j in range(2):
            if start_ancilla + j < ancilla_qubits:
                ax.plot([ancilla_x[start_ancilla + j], cavity_x[i]], 
                       [ancilla_y + 0.3, cavity_y - 0.3], 
                       'r-', alpha=0.7, linewidth=2)
    
    # Add layer labels
    ax.text(0.5, data_y, 'Data Qubits\n(Logical Information)', 
            ha='center', va='center', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=seqCmap(0.2), alpha=0.3))
    
    ax.text(0.5, ancilla_y, 'Ancilla Qubits\n(Parity Checks)', 
            ha='center', va='center', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=divCmap(0.2), alpha=0.3))
    
    ax.text(0.5, cavity_y, 'Cavity Modes\n(Non-local Gates)', 
            ha='center', va='center', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=lightCmap(0.8), alpha=0.3))
    
    # Add title and formatting
    ax.set_title('Tri-Layer Architecture for Quantum LDPC Codes\n' +
                 'Cavity-Mediated Non-Local Error Correction', fontsize=16)
    ax.set_xlim(-0.5, 14.5)
    ax.set_ylim(-1, cavity_y + 1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], color='k', alpha=0.4, linewidth=1, label='Local Parity Checks'),
        plt.Line2D([0], [0], color='r', alpha=0.7, linewidth=2, label='Non-Local Cavity Gates'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=12)
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Plots', 'trilayer_architecture.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Tri-layer architecture saved to {save_path}")


def create_error_threshold_analysis():
    """
    Create visualization of error threshold analysis for cavity-mediated LDPC codes
    """
    print("Creating error threshold analysis...")
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Physical error rates
    p_phys = np.logspace(-4, -1, 100)
    
    # Logical error rates for different code distances
    distances = [3, 5, 7, 9]
    colors = [seqCmap(i/len(distances)) for i in range(len(distances))]
    
    # Error threshold (approximate)
    p_th = 0.01  # 1% threshold for cavity-mediated codes
    
    for i, d in enumerate(distances):
        # Simplified threshold behavior: p_L ~ (p/p_th)^((d+1)/2)
        p_logical = (p_phys / p_th)**((d+1)/2)
        
        # Below threshold: exponential suppression
        # Above threshold: polynomial growth
        mask_below = p_phys < p_th
        mask_above = p_phys >= p_th
        
        p_logical[mask_below] = p_phys[mask_below]**((d+1)/2) * 10
        p_logical[mask_above] = p_phys[mask_above] * (p_th)**(-(d-1)/2)
        
        ax.loglog(p_phys, p_logical, color=colors[i], linewidth=2.5, 
                 label=f'Distance d = {d}')
    
    # Add threshold line
    ax.axvline(x=p_th, color='red', linestyle='--', linewidth=2, 
               label=f'Error Threshold $p_{{th}} = {p_th}$')
    
    # Add diagonal reference line (no error correction)
    ax.loglog(p_phys, p_phys, 'k:', alpha=0.5, linewidth=1, 
              label='No Error Correction')
    
    # Annotations
    ax.annotate('Error Suppression\n(Below Threshold)', 
                xy=(1e-4, 1e-8), xytext=(5e-4, 1e-6),
                arrowprops=dict(arrowstyle='->', color=seqCmap(0.8)),
                fontsize=11, color=seqCmap(0.8))
    
    ax.annotate('Error Proliferation\n(Above Threshold)', 
                xy=(5e-2, 1e-2), xytext=(2e-2, 5e-3),
                arrowprops=dict(arrowstyle='->', color='red'),
                fontsize=11, color='red')
    
    # Formatting
    ax.set_xlabel('Physical Error Rate $p$', fontsize=14)
    ax.set_ylabel('Logical Error Rate $p_L$', fontsize=14)
    ax.set_title('Error Threshold Analysis for Cavity-Mediated Quantum LDPC Codes', fontsize=16)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=12)
    ax.set_xlim(1e-4, 1e-1)
    ax.set_ylim(1e-10, 1e-1)
    
    # Add text box with threshold information
    textstr = 'Cavity Requirements:\n' + \
              r'$C \gtrsim 10^4$' + '\n' + \
              r'$\kappa t_{gate} \ll 1$' + '\n' + \
              r'$\gamma t_{gate} \ll 1$'
    
    props = dict(boxstyle='round', facecolor=lightCmap(0.1), alpha=0.8)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Plots', 'error_threshold.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Error threshold analysis saved to {save_path}")


def main():
    print("Generating cavity-mediated gates visualizations...")
    
    # Create output directory if it doesn't exist
    plots_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Plots')
    os.makedirs(plots_dir, exist_ok=True)
    
    try:
        create_cavity_cooperativity_analysis()
        create_trilayer_architecture()
        create_error_threshold_analysis()
        print("All cavity-mediated gates visualizations completed successfully!")
        
    except Exception as e:
        print(f"Error in visualization generation: {e}")


if __name__ == "__main__":
    main()
