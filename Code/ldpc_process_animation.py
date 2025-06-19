"""
LDPC Process Animation

This script creates comprehensive animations showing the quantum LDPC process based on the
breakthrough developments in quantum LDPC codes, particularly focusing on the revolutionary
2020-2022 breakthroughs that achieved asymptotically good LDPC codes with linear distance
and constant rate.

Features:
- Tanner graph construction and evolution
- Parity check matrix visualization
- Error syndrome detection and correction
- Threshold behavior demonstration
- Quantum Tanner codes and lifted product codes
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import seaborn as sns
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch, Polygon
from matplotlib.collections import LineCollection
import networkx as nx
import os

# Set up the color palettes as specified
seqCmap = sns.color_palette("mako", as_cmap=True)
divCmap = sns.cubehelix_palette(start=.5, rot=-.5, as_cmap=True)
lightCmap = sns.cubehelix_palette(start=2, rot=0, dark=0, light=.95, reverse=True, as_cmap=True)

# Set matplotlib to use LaTeX for text rendering
plt.rcParams['text.usetex'] = False  # Set to True if LaTeX is available
plt.rcParams['font.family'] = 'serif'
plt.rcParams['mathtext.fontset'] = 'cm'

def create_ldpc_tanner_graph_animation():
    """
    Create animation showing LDPC Tanner graph construction and evolution
    """
    print("Creating LDPC Tanner graph animation...")
    
    # Set up the figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Parameters for LDPC code
    n = 12  # Number of variable nodes (data qubits)
    m = 6   # Number of check nodes (parity checks)
    
    # Generate a sparse parity check matrix
    np.random.seed(42)  # For reproducibility
    H = np.zeros((m, n), dtype=int)
    
    # Create a regular LDPC code with degree-3 variable nodes and degree-6 check nodes
    for i in range(n):
        # Each variable node connects to 3 check nodes
        checks = np.random.choice(m, 3, replace=False)
        H[checks, i] = 1
    
    # Ensure each check node has at least 2 connections
    for j in range(m):
        if np.sum(H[j, :]) < 2:
            vars_to_add = np.random.choice(n, 2, replace=False)
            H[j, vars_to_add] = 1
    
    # Position nodes for visualization
    var_positions = {}
    check_positions = {}
    
    # Variable nodes on the left
    for i in range(n):
        var_positions[f'v{i}'] = (0, i * 0.8 - (n-1)*0.4)
    
    # Check nodes on the right
    for j in range(m):
        check_positions[f'c{j}'] = (4, j * 1.2 - (m-1)*0.6)
    
    def init():
        ax1.clear()
        ax2.clear()
        
        # Setup ax1 - Tanner Graph
        ax1.set_title('LDPC Tanner Graph Construction\nBreakthrough: Linear Distance Codes', 
                     fontsize=14, fontweight='bold')
        ax1.set_xlim(-1, 5)
        ax1.set_ylim(-6, 6)
        ax1.axis('off')
        
        # Setup ax2 - Parity Check Matrix
        ax2.set_title('Parity Check Matrix $\\mathbf{H}$\nSparse Structure for Efficient Decoding', 
                     fontsize=14, fontweight='bold')
        ax2.set_xlim(-0.5, n-0.5)
        ax2.set_ylim(-0.5, m-0.5)
        
        return []
    
    def animate(frame):
        ax1.clear()
        ax2.clear()
        
        # Determine what to show based on frame
        max_connections = min(frame + 1, np.sum(H))
        
        # Setup ax1 - Tanner Graph
        ax1.set_title('LDPC Tanner Graph Construction\nBreakthrough: Linear Distance Codes', 
                     fontsize=14, fontweight='bold')
        ax1.set_xlim(-1, 5)
        ax1.set_ylim(-6, 6)
        ax1.axis('off')
        
        # Draw variable nodes
        for i, (node, pos) in enumerate(var_positions.items()):
            color = seqCmap(0.8) if i < frame else seqCmap(0.3)
            circle = Circle(pos, 0.15, color=color, alpha=0.8)
            ax1.add_patch(circle)
            ax1.text(pos[0], pos[1], f'$q_{{{i}}}$', ha='center', va='center', 
                    fontsize=10, fontweight='bold')
        
        # Draw check nodes
        for j, (node, pos) in enumerate(check_positions.items()):
            color = divCmap(0.7) if j < frame else divCmap(0.3)
            square = Rectangle((pos[0]-0.15, pos[1]-0.15), 0.3, 0.3, 
                             facecolor=color, alpha=0.8)
            ax1.add_patch(square)
            ax1.text(pos[0], pos[1], f'$s_{{{j}}}$', ha='center', va='center', 
                    fontsize=10, fontweight='bold')
        
        # Draw edges gradually
        edge_count = 0
        for j in range(m):
            for i in range(n):
                if H[j, i] == 1:
                    if edge_count < max_connections:
                        var_pos = var_positions[f'v{i}']
                        check_pos = check_positions[f'c{j}']
                        
                        # Add some curvature to edges
                        mid_x = (var_pos[0] + check_pos[0]) / 2
                        mid_y = (var_pos[1] + check_pos[1]) / 2 + 0.2 * np.sin(edge_count)
                        
                        ax1.plot([var_pos[0], mid_x, check_pos[0]], 
                               [var_pos[1], mid_y, check_pos[1]], 
                               color=lightCmap(0.2), linewidth=2, alpha=0.7)
                    edge_count += 1
        
        # Add labels
        ax1.text(-0.5, -5.5, 'Variable Nodes\n(Data Qubits)', 
                fontsize=12, ha='center', 
                bbox=dict(boxstyle='round', facecolor=seqCmap(0.2), alpha=0.3))
        
        ax1.text(4.5, -5.5, 'Check Nodes\n(Parity Constraints)', 
                fontsize=12, ha='center',
                bbox=dict(boxstyle='round', facecolor=divCmap(0.2), alpha=0.3))
        
        # Setup ax2 - Parity Check Matrix
        ax2.set_title('Parity Check Matrix $\\mathbf{H}$\nSparse Structure for Efficient Decoding', 
                     fontsize=14, fontweight='bold')
        ax2.set_xlim(-0.5, n-0.5)
        ax2.set_ylim(m-0.5, -0.5)  # Flip y-axis for matrix convention
        
        # Draw matrix elements
        for j in range(m):
            for i in range(n):
                if H[j, i] == 1 and edge_count >= np.sum(H[:j+1, :i+1]):
                    color = seqCmap(0.8)
                    alpha = 0.9
                else:
                    color = 'lightgray'
                    alpha = 0.3
                
                rect = Rectangle((i-0.4, j-0.4), 0.8, 0.8, 
                               facecolor=color, alpha=alpha, edgecolor='black')
                ax2.add_patch(rect)
                
                if H[j, i] == 1:
                    ax2.text(i, j, '1', ha='center', va='center', 
                           fontsize=12, fontweight='bold')
        
        # Add matrix labels
        ax2.set_xlabel('Variable Nodes (Qubits)', fontsize=12)
        ax2.set_ylabel('Check Nodes (Constraints)', fontsize=12)
        
        # Add progress text
        progress_text = f"Connections: {min(edge_count, max_connections)}/{np.sum(H)}"
        ax1.text(2, 5.5, progress_text, fontsize=12, ha='center',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Add theoretical context
        if frame > 20:
            theory_text = (
                "Key Breakthroughs (2020-2022):\n"
                "• Panteleev-Kalachev: Lifted Product Codes\n"
                "• Quantum Tanner Codes: Linear Distance\n"
                "• Rate: $R = \\Omega(1)$, Distance: $d = \\Omega(n)$"
            )
            ax2.text(0.02, 0.98, theory_text, transform=ax2.transAxes,
                    fontsize=10, va='top',
                    bbox=dict(boxstyle='round', facecolor=lightCmap(0.1), alpha=0.8))
        
        return []
    
    # Create animation
    frames = 60
    anim = animation.FuncAnimation(fig, animate, init_func=init,
                                  frames=frames, interval=150, blit=False, repeat=True)
    
    # Save animation
    plt.tight_layout()
    save_path = os.path.join(os.path.dirname(__file__), '..', 'Plots', 'ldpc_tanner_graph_animation.gif')
    print(f"Saving LDPC Tanner graph animation to {save_path}")
    anim.save(save_path, writer='pillow', fps=8, dpi=100)
    plt.close()
    
    print("LDPC Tanner graph animation completed")


def create_error_correction_process_animation():
    """
    Create animation showing the LDPC error correction process
    """
    print("Creating LDPC error correction process animation...")
    
    # Set up the figure
    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1], width_ratios=[1, 1, 1])
    
    ax1 = fig.add_subplot(gs[0, :2])  # Quantum state and errors
    ax2 = fig.add_subplot(gs[0, 2])   # Syndrome measurement
    ax3 = fig.add_subplot(gs[1, :])   # Decoding process
    
    # LDPC code parameters
    n = 15  # Number of qubits
    k = 9   # Number of logical qubits
    m = n - k  # Number of parity checks
    
    # Generate error patterns
    np.random.seed(123)
    error_probability = 0.1
    num_frames = 80
    
    def init():
        for ax in [ax1, ax2, ax3]:
            ax.clear()
        return []
    
    def animate(frame):
        ax1.clear()
        ax2.clear() 
        ax3.clear()
        
        # Phase of animation
        phase = frame // 20
        subframe = frame % 20
        
        # Quantum state visualization
        ax1.set_title('Quantum LDPC Error Correction Process\n'
                     'Revolutionary Asymptotically Good Codes', 
                     fontsize=16, fontweight='bold')
        ax1.set_xlim(-1, 16)
        ax1.set_ylim(-2, 3)
        ax1.axis('off')
        
        # Draw qubits
        qubit_positions = np.linspace(0, 14, n)
        for i, pos in enumerate(qubit_positions):
            # Determine if qubit has error
            has_error = np.random.random() < error_probability if phase >= 1 else False
            
            if has_error and phase >= 1:
                color = 'red'
                alpha = 0.8
                error_type = np.random.choice(['X', 'Z', 'Y'])
            else:
                color = seqCmap(0.7)
                alpha = 0.6
                error_type = None
            
            # Draw qubit
            circle = Circle((pos, 1), 0.3, color=color, alpha=alpha)
            ax1.add_patch(circle)
            ax1.text(pos, 1, f'$q_{{{i}}}$', ha='center', va='center', 
                    fontsize=10, fontweight='bold')
            
            # Draw error if present
            if error_type and phase >= 1:
                ax1.text(pos, 1.8, f'${error_type}$', ha='center', va='center',
                        fontsize=14, color='red', fontweight='bold')
        
        # Add logical qubit indication
        ax1.text(7, -1, f'Logical Qubits: $k = {k}$, Physical Qubits: $n = {n}$\n'
                       f'Code Rate: $R = k/n = {k/n:.2f}$',
                ha='center', fontsize=12,
                bbox=dict(boxstyle='round', facecolor=lightCmap(0.1), alpha=0.8))
        
        # Syndrome measurement
        ax2.set_title('Syndrome\nMeasurement', fontsize=14, fontweight='bold')
        ax2.set_xlim(-0.5, 2.5)
        ax2.set_ylim(-0.5, m-0.5)
        ax2.axis('off')
        
        # Generate syndromes
        for j in range(m):
            # Syndrome bit (0 or 1)
            syndrome_bit = np.random.choice([0, 1], p=[0.7, 0.3]) if phase >= 2 else 0
            
            color = seqCmap(0.8) if syndrome_bit == 0 else 'red'
            
            # Draw syndrome bit
            rect = Rectangle((0.5, j), 1, 0.8, facecolor=color, alpha=0.8)
            ax2.add_patch(rect)
            ax2.text(1, j+0.4, f'$s_{{{j}}} = {syndrome_bit}$', 
                    ha='center', va='center', fontsize=12, fontweight='bold')
        
        # Syndrome equation
        if phase >= 2:
            ax2.text(1, -0.3, '$\\mathbf{s} = \\mathbf{H} \\mathbf{e}$', 
                    ha='center', va='top', fontsize=14,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Decoding process
        ax3.set_title('LDPC Decoding: Belief Propagation Algorithm', 
                     fontsize=14, fontweight='bold')
        ax3.set_xlim(-1, 15)
        ax3.set_ylim(-3, 4)
        ax3.axis('off')
        
        if phase >= 3:
            # Show belief propagation iterations
            iteration = min(subframe // 4, 4)
            
            # Draw variable and check nodes
            var_y = 2
            check_y = -1
            
            for i in range(min(8, n)):  # Show subset for clarity
                pos_x = i * 2
                
                # Variable node
                color = seqCmap(0.7 + 0.2 * iteration / 4)
                circle = Circle((pos_x, var_y), 0.25, color=color, alpha=0.8)
                ax3.add_patch(circle)
                ax3.text(pos_x, var_y, f'$v_{{{i}}}$', ha='center', va='center', 
                        fontsize=9, fontweight='bold')
                
                # Check node (every other position)
                if i < 4:
                    check_x = i * 4 + 1
                    color = divCmap(0.5 + 0.3 * iteration / 4)
                    square = Rectangle((check_x-0.25, check_y-0.25), 0.5, 0.5, 
                                     facecolor=color, alpha=0.8)
                    ax3.add_patch(square)
                    ax3.text(check_x, check_y, f'$c_{{{i}}}$', ha='center', va='center', 
                            fontsize=9, fontweight='bold')
                    
                    # Draw message passing edges
                    for j in range(2):
                        var_x = check_x - 1 + j * 2
                        if var_x >= 0 and var_x <= 14:
                            # Message from variable to check
                            ax3.annotate('', xy=(check_x, check_y + 0.25), 
                                       xytext=(var_x, var_y - 0.25),
                                       arrowprops=dict(arrowstyle='->', 
                                                     color=lightCmap(0.3), 
                                                     alpha=0.6, lw=1.5))
                            
                            # Message from check to variable
                            ax3.annotate('', xy=(var_x, var_y - 0.25), 
                                       xytext=(check_x, check_y + 0.25),
                                       arrowprops=dict(arrowstyle='->', 
                                                     color=lightCmap(0.7), 
                                                     alpha=0.6, lw=1.5))
            
            # Add iteration counter and convergence info
            ax3.text(7, 3.5, f'Belief Propagation Iteration: {iteration}/4', 
                    ha='center', fontsize=12, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            if iteration >= 4:
                ax3.text(7, -2.5, 'Decoding Complete!\nError Pattern Estimated', 
                        ha='center', fontsize=12, color='green', fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
        
        # Add phase indicators
        phases = ['Encoding', 'Error Introduction', 'Syndrome Measurement', 'Decoding']
        current_phase = min(phase, 3)
        
        phase_text = f"Phase {current_phase + 1}/4: {phases[current_phase]}"
        fig.text(0.5, 0.02, phase_text, ha='center', fontsize=14, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor=seqCmap(0.2), alpha=0.8))
        
        # Add theoretical context
        if frame > 60:
            theory_text = (
                "Quantum LDPC Breakthroughs:\n"
                "• Distance: $d = \\Theta(\\sqrt{n \\log n})$ → $d = \\Theta(n)$\n"
                "• Rate: $R = \\Omega(1)$ with linear distance\n"
                "• Efficient classical decoding algorithms\n"
                "• Fault-tolerant implementations possible"
            )
            fig.text(0.98, 0.98, theory_text, ha='right', va='top', fontsize=10,
                    transform=fig.transFigure,
                    bbox=dict(boxstyle='round', facecolor=lightCmap(0.1), alpha=0.9))
        
        return []
    
    # Create animation
    anim = animation.FuncAnimation(fig, animate, init_func=init,
                                  frames=num_frames, interval=200, blit=False, repeat=True)
    
    # Save animation
    plt.tight_layout()
    save_path = os.path.join(os.path.dirname(__file__), '..', 'Plots', 'ldpc_error_correction_animation.gif')
    print(f"Saving LDPC error correction animation to {save_path}")
    anim.save(save_path, writer='pillow', fps=6, dpi=100)
    plt.close()
    
    print("LDPC error correction animation completed")


def create_threshold_behavior_animation():
    """
    Create animation showing LDPC threshold behavior and scaling
    """
    print("Creating LDPC threshold behavior animation...")
    
    # Set up the figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Parameters
    p_range = np.logspace(-3, -0.5, 100)
    distances = [3, 5, 7, 11, 21, 51]
    threshold = 0.05  # Approximate threshold for quantum LDPC
    
    def init():
        ax1.clear()
        ax2.clear()
        return []
    
    def animate(frame):
        ax1.clear()
        ax2.clear()
        
        # Show curves progressively
        max_distance_idx = min(frame // 10, len(distances))
        
        # Plot 1: Threshold behavior
        ax1.set_title('LDPC Threshold Behavior\nAsymptotically Good Performance', 
                     fontsize=14, fontweight='bold')
        ax1.set_xlabel('Physical Error Rate $p$', fontsize=12)
        ax1.set_ylabel('Logical Error Rate $p_L$', fontsize=12)
        ax1.set_xscale('log')
        ax1.set_yscale('log')
        ax1.grid(True, alpha=0.3)
        
        colors = [seqCmap(i/len(distances)) for i in range(len(distances))]
        
        for i in range(max_distance_idx):
            d = distances[i]
            
            # Simplified threshold behavior model
            p_logical = np.zeros_like(p_range)
            
            # Below threshold: exponential suppression
            below_threshold = p_range < threshold
            p_logical[below_threshold] = (p_range[below_threshold] / threshold) ** ((d+1)/2)
            
            # Above threshold: polynomial scaling  
            above_threshold = p_range >= threshold
            p_logical[above_threshold] = p_range[above_threshold] ** (1/2)
            
            ax1.loglog(p_range, p_logical, color=colors[i], linewidth=2.5, 
                      label=f'Distance $d = {d}$', alpha=0.8)
        
        # Add threshold line
        if max_distance_idx > 0:
            ax1.axvline(x=threshold, color='red', linestyle='--', linewidth=2, 
                       alpha=0.8, label=f'Threshold $p_{{th}} \\approx {threshold}$')
        
        # Reference line (no error correction)
        ax1.loglog(p_range, p_range, 'k:', alpha=0.5, linewidth=1.5, 
                  label='No Error Correction')
        
        ax1.set_xlim(1e-3, 10**(-0.5))
        ax1.set_ylim(1e-6, 1e0)
        ax1.legend(fontsize=10)
        
        # Add annotations
        if max_distance_idx >= 3:
            ax1.annotate('Error Suppression\n(Below Threshold)', 
                        xy=(1e-3, 1e-5), xytext=(5e-3, 1e-4),
                        arrowprops=dict(arrowstyle='->', color=seqCmap(0.8)),
                        fontsize=11, color=seqCmap(0.8))
            
            ax1.annotate('Error Proliferation\n(Above Threshold)', 
                        xy=(2e-1, 5e-1), xytext=(1e-1, 2e-1),
                        arrowprops=dict(arrowstyle='->', color='red'),
                        fontsize=11, color='red')
        
        # Plot 2: Code scaling and distance growth
        ax2.set_title('LDPC Code Scaling\nLinear Distance Achievement', 
                     fontsize=14, fontweight='bold')
        ax2.set_xlabel('Code Length $n$', fontsize=12)
        ax2.set_ylabel('Code Distance $d$', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Code lengths
        n_values = np.logspace(2, 6, 50)
        
        # Show different scaling regimes
        regime = min(frame // 15, 3)
        
        if regime >= 0:
            # Classical LDPC: d ~ sqrt(n)
            d_classical = 2 * np.sqrt(n_values)
            ax2.loglog(n_values, d_classical, color=divCmap(0.3), linewidth=3,
                      alpha=0.7, label='Classical LDPC: $d \\sim \\sqrt{n}$')
        
        if regime >= 1:
            # Hypergraph product codes: d ~ sqrt(n log n)
            d_hypergraph = 3 * np.sqrt(n_values * np.log(n_values))
            ax2.loglog(n_values, d_hypergraph, color=divCmap(0.6), linewidth=3,
                      alpha=0.7, label='Hypergraph Product: $d \\sim \\sqrt{n \\log n}$')
        
        if regime >= 2:
            # Quantum Tanner codes: d ~ n (breakthrough!)
            d_tanner = 0.1 * n_values
            ax2.loglog(n_values, d_tanner, color=seqCmap(0.8), linewidth=4,
                      alpha=0.9, label='Quantum Tanner: $d \\sim n$ (Breakthrough!)')
        
        ax2.set_xlim(1e2, 1e6)
        ax2.set_ylim(1e1, 1e5)
        ax2.legend(fontsize=11)
        
        # Add breakthrough timeline
        if regime >= 3:
            timeline_text = (
                "Timeline of Breakthroughs:\n"
                "2020: Panteleev-Kalachev (Lifted Products)\n"
                "2021: Leverrier-Tillich-Zémor (Quantum Tanner)\n"
                "2022: Breuckmann-Eberhardt (Balanced Products)\n"
                "\n"
                "Achievement: $R = \\Omega(1)$, $d = \\Omega(n)$"
            )
            ax2.text(0.02, 0.98, timeline_text, transform=ax2.transAxes,
                    fontsize=10, va='top',
                    bbox=dict(boxstyle='round', facecolor=lightCmap(0.1), alpha=0.9))
        
        # Frame counter
        frame_text = f"Frame: {frame}/{100}"
        fig.text(0.02, 0.02, frame_text, fontsize=10, alpha=0.7)
        
        return []
    
    # Create animation
    frames = 100
    anim = animation.FuncAnimation(fig, animate, init_func=init,
                                  frames=frames, interval=150, blit=False, repeat=True)
    
    # Save animation
    plt.tight_layout()
    save_path = os.path.join(os.path.dirname(__file__), '..', 'Plots', 'ldpc_threshold_behavior_animation.gif')
    print(f"Saving LDPC threshold behavior animation to {save_path}")
    anim.save(save_path, writer='pillow', fps=8, dpi=100)
    plt.close()
    
    print("LDPC threshold behavior animation completed")


if __name__ == "__main__":
    print("Generating comprehensive LDPC process animations...")
    print("Based on revolutionary 2020-2022 breakthroughs in quantum LDPC codes")
    
    # Create output directory if it doesn't exist
    plots_dir = os.path.join(os.path.dirname(__file__), '..', 'Plots')
    os.makedirs(plots_dir, exist_ok=True)
    
    try:
        # Generate all animations
        create_ldpc_tanner_graph_animation()
        create_error_correction_process_animation()
        create_threshold_behavior_animation()
        
        print("\n" + "="*60)
        print("All LDPC process animations completed successfully!")
        print("Animations showcase:")
        print("• Tanner graph construction and structure")
        print("• Complete error correction process")
        print("• Threshold behavior and code scaling")
        print("• Revolutionary linear distance achievements")
        print("="*60)
        
    except Exception as e:
        print(f"Error in animation generation: {e}")
        import traceback
        traceback.print_exc()
