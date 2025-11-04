"""
LDPC 3D Error Surface Visualization

This script creates a professional 3D visualization of LDPC error correction performance,
showcasing the error threshold landscape, code distance scaling, and syndrome probability 
distributions. Based on the breakthrough developments in quantum LDPC codes achieving
linear distance and constant rate.

Features:
- 3D error threshold surface
- Code distance scaling visualization
- Syndrome probability landscape
- Fault-tolerant region mapping
- Performance comparison across code families
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.cm as cm
import os

# Set up the color palettes using matplotlib
seqCmap = cm.viridis  # Dark blue to yellow (similar to mako)
divCmap = cm.plasma   # Purple to pink/yellow (similar to cubehelix)
lightCmap = cm.Blues_r  # Light blue palette (similar to light cubehelix)

# Set matplotlib parameters for professional appearance
plt.rcParams['text.usetex'] = False
plt.rcParams['font.family'] = 'serif'
plt.rcParams['mathtext.fontset'] = 'cm'
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3


def create_ldpc_error_threshold_surface():
    """
    Create 3D visualization of LDPC error threshold behavior
    Shows the relationship between physical error rate, code distance, and logical error rate
    """
    print("Creating LDPC 3D error threshold surface...")
    
    # Create figure with 3D subplot
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')
    
    # Define parameter ranges
    n_points = 50
    physical_error_rates = np.linspace(0.001, 0.05, n_points)  # Physical error rate (p)
    code_distances = np.linspace(3, 15, n_points)  # Code distance (d)
    
    # Create meshgrid
    P, D = np.meshgrid(physical_error_rates, code_distances)
    
    # LDPC logical error rate model
    # For LDPC codes: P_L ≈ (p/p_th)^(d+1)/2 for p < p_th, else P_L ≈ 0.5
    p_threshold = 0.018  # Typical LDPC threshold (~1.8%)
    
    # Calculate logical error rates
    P_logical = np.zeros_like(P)
    
    for i in range(len(code_distances)):
        for j in range(len(physical_error_rates)):
            p = P[i, j]
            d = D[i, j]
            
            if p < p_threshold:
                # Below threshold: exponential suppression
                P_logical[i, j] = (p/p_threshold)**((d+1)/2) * p_threshold
            else:
                # Above threshold: logical error rate approaches 0.5
                P_logical[i, j] = 0.5 - 0.4 * np.exp(-2*(p - p_threshold))
    
    # Apply logarithmic scaling for better visualization
    P_logical_log = np.log10(P_logical + 1e-10)
    
    # Create the 3D surface with custom colormap
    surface = ax.plot_surface(P*1000, D, P_logical_log, 
                             cmap=seqCmap, alpha=0.9, 
                             linewidth=0, antialiased=True, shade=True)
    
    # Add threshold plane
    threshold_plane_p = np.full_like(P, p_threshold*1000)
    ax.plot_surface(threshold_plane_p, D, P_logical_log, 
                   alpha=0.3, color='red', linewidth=0)
    
    # Add contour lines at key levels
    contour_levels = [-6, -4, -2, -1]
    for level in contour_levels:
        ax.contour(P*1000, D, P_logical_log, levels=[level], 
                  colors=['white'], alpha=0.7, linewidths=1.5)
    
    # Formatting
    ax.set_xlabel('Physical Error Rate (×10⁻³)', fontsize=14, labelpad=10)
    ax.set_ylabel('Code Distance', fontsize=14, labelpad=10)
    ax.set_zlabel('log₁₀(Logical Error Rate)', fontsize=14, labelpad=10)
    ax.set_title('LDPC Quantum Error Correction: 3D Threshold Landscape\\n' +
                 'Breakthrough: Linear Distance, Constant Rate Codes',
                 fontsize=16, pad=20)
    
    # Add colorbar
    cbar = plt.colorbar(surface, ax=ax, shrink=0.6, aspect=20, pad=0.1)
    cbar.set_label('log₁₀(Logical Error Rate)', fontsize=12)
    
    # Set viewing angle for optimal perspective
    ax.view_init(elev=20, azim=45)
    
    # Add annotations for key regions
    ax.text(5, 12, -1, 'Fault-Tolerant\\nRegion', fontsize=11, 
           bbox=dict(boxstyle='round', facecolor=lightCmap(0.1), alpha=0.8))
    
    ax.text(25, 5, -0.5, 'Above Threshold\\n(No Protection)', fontsize=11,
           bbox=dict(boxstyle='round', facecolor='red', alpha=0.3))
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), 'ldpc_3d_threshold_surface.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"LDPC 3D threshold surface saved to {save_path}")


def create_syndrome_probability_landscape():
    """
    Create 3D visualization of syndrome probability distributions for different error patterns
    """
    print("Creating syndrome probability landscape...")
    
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')
    
    # Define syndrome space (simplified 2D projection of higher-dimensional space)
    n_syndrome_bits = 30
    syndrome_x = np.arange(n_syndrome_bits)
    syndrome_y = np.arange(n_syndrome_bits)
    
    SX, SY = np.meshgrid(syndrome_x, syndrome_y)
    
    # Model syndrome probability based on different error patterns
    # Pattern 1: Single-qubit errors (localized)
    prob_single = np.exp(-((SX-10)**2 + (SY-10)**2)/10) * 0.3
    
    # Pattern 2: Correlated errors (extended)
    prob_correlated = (np.exp(-((SX-20)**2 + (SY-5)**2)/20) * 0.4 +
                      np.exp(-((SX-5)**2 + (SY-20)**2)/15) * 0.3)
    
    # Pattern 3: Random errors (distributed)
    np.random.seed(42)
    prob_random = 0.1 * np.random.random((n_syndrome_bits, n_syndrome_bits))
    for i in range(5):
        center_x, center_y = np.random.randint(0, n_syndrome_bits, 2)
        prob_random += 0.15 * np.exp(-((SX-center_x)**2 + (SY-center_y)**2)/8)
    
    # Combine probability patterns
    total_prob = prob_single + prob_correlated + prob_random
    total_prob = total_prob / np.max(total_prob)  # Normalize
    
    # Create the 3D surface
    surface = ax.plot_surface(SX, SY, total_prob, 
                             cmap=divCmap, alpha=0.8, 
                             linewidth=0, antialiased=True)
    
    # Add wireframe for structure
    ax.plot_wireframe(SX, SY, total_prob, alpha=0.3, color='black', linewidth=0.5)
    
    # Add contour projections
    ax.contour(SX, SY, total_prob, zdir='z', offset=0, cmap=lightCmap, alpha=0.6)
    ax.contour(SX, SY, total_prob, zdir='x', offset=0, cmap=lightCmap, alpha=0.4)
    ax.contour(SX, SY, total_prob, zdir='y', offset=n_syndrome_bits, cmap=lightCmap, alpha=0.4)
    
    # Formatting
    ax.set_xlabel('Syndrome Bit Index (X)', fontsize=14, labelpad=10)
    ax.set_ylabel('Syndrome Bit Index (Y)', fontsize=14, labelpad=10)
    ax.set_zlabel('Error Probability', fontsize=14, labelpad=10)
    ax.set_title('LDPC Syndrome Probability Landscape\\n' +
                 'Error Pattern Recognition for Efficient Decoding',
                 fontsize=16, pad=20)
    
    # Set limits
    ax.set_xlim(0, n_syndrome_bits)
    ax.set_ylim(0, n_syndrome_bits)
    ax.set_zlim(0, np.max(total_prob)*1.1)
    
    # Add colorbar
    cbar = plt.colorbar(surface, ax=ax, shrink=0.6, aspect=20, pad=0.1)
    cbar.set_label('Error Probability', fontsize=12)
    
    # Set viewing angle
    ax.view_init(elev=25, azim=60)
    
    # Add legend for error types
    legend_text = (
        "Error Types:\\n"
        "• Localized: Single-qubit errors\\n"
        "• Correlated: Multi-qubit errors\\n"
        "• Distributed: Random errors"
    )
    ax.text2D(0.02, 0.98, legend_text, transform=ax.transAxes, fontsize=11,
             verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor=lightCmap(0.1), alpha=0.8))
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), 'ldpc_syndrome_landscape.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Syndrome probability landscape saved to {save_path}")


def create_code_family_comparison():
    """
    Create 3D comparison of different LDPC code families performance
    """
    print("Creating LDPC code family comparison...")
    
    fig = plt.figure(figsize=(18, 10))
    
    # Create two subplots for comparison
    ax1 = fig.add_subplot(121, projection='3d')
    ax2 = fig.add_subplot(122, projection='3d')
    
    # Define parameter ranges
    n_points = 40
    code_rates = np.linspace(0.1, 0.9, n_points)  # Code rate R
    block_lengths = np.logspace(2, 4, n_points)   # Block length n
    
    R, N = np.meshgrid(code_rates, block_lengths)
    
    # Model 1: Classical LDPC codes (finite distance)
    distance_classical = np.sqrt(N) * (1 - R)**1.5  # Square-root distance scaling
    
    # Model 2: Quantum LDPC breakthrough codes (linear distance)
    distance_quantum = N * (1 - R) * 0.1  # Linear distance scaling
    
    # Plot classical LDPC codes
    surface1 = ax1.plot_surface(R, np.log10(N), np.log10(distance_classical + 1), 
                               cmap=seqCmap, alpha=0.8, linewidth=0, antialiased=True)
    
    ax1.set_xlabel('Code Rate R', fontsize=12)
    ax1.set_ylabel('log₁₀(Block Length)', fontsize=12)
    ax1.set_zlabel('log₁₀(Distance)', fontsize=12)
    ax1.set_title('Classical LDPC Codes\\n(√n Distance Scaling)', fontsize=14)
    ax1.view_init(elev=20, azim=45)
    
    # Plot quantum LDPC breakthrough codes
    surface2 = ax2.plot_surface(R, np.log10(N), np.log10(distance_quantum + 1), 
                               cmap=divCmap, alpha=0.8, linewidth=0, antialiased=True)
    
    ax2.set_xlabel('Code Rate R', fontsize=12)
    ax2.set_ylabel('log₁₀(Block Length)', fontsize=12)
    ax2.set_zlabel('log₁₀(Distance)', fontsize=12)
    ax2.set_title('Quantum LDPC Breakthrough\\n(Linear Distance Scaling)', fontsize=14)
    ax2.view_init(elev=20, azim=45)
    
    # Add theoretical limits
    # Gilbert-Varshamov bound projection
    for ax in [ax1, ax2]:
        # Add reference planes
        gv_bound = 0.2 * N * (1 - R)  # Simplified GV bound
        ax.plot_wireframe(R, np.log10(N), np.log10(gv_bound + 1), 
                         alpha=0.3, color='red', linewidth=1)
    
    # Add colorbars
    cbar1 = plt.colorbar(surface1, ax=ax1, shrink=0.6, aspect=20)
    cbar1.set_label('log₁₀(Distance)', fontsize=10)
    
    cbar2 = plt.colorbar(surface2, ax=ax2, shrink=0.6, aspect=20)
    cbar2.set_label('log₁₀(Distance)', fontsize=10)
    
    # Add main title
    fig.suptitle('LDPC Code Family Performance Comparison\\n' +
                 'Quantum Breakthrough: Asymptotically Good Codes with Linear Distance',
                 fontsize=16, y=0.95)
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), 'ldpc_code_family_comparison.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"LDPC code family comparison saved to {save_path}")


def create_tanner_graph_3d_structure():
    """
    Create 3D visualization of LDPC Tanner graph structure with node connections
    """
    print("Creating 3D Tanner graph structure...")
    
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')
    
    # Define Tanner graph parameters
    n_var_nodes = 20    # Variable nodes (data qubits)
    n_check_nodes = 10  # Check nodes (parity checks)
    
    # Position variable nodes in a circle at z=0
    theta_var = np.linspace(0, 2*np.pi, n_var_nodes, endpoint=False)
    var_x = 3 * np.cos(theta_var)
    var_y = 3 * np.sin(theta_var)
    var_z = np.zeros(n_var_nodes)
    
    # Position check nodes in a circle at z=2
    theta_check = np.linspace(0, 2*np.pi, n_check_nodes, endpoint=False)
    check_x = 1.5 * np.cos(theta_check)
    check_y = 1.5 * np.sin(theta_check)
    check_z = 2 * np.ones(n_check_nodes)
    
    # Create connection matrix (sparse LDPC structure)
    np.random.seed(42)
    connections = np.zeros((n_check_nodes, n_var_nodes))
    
    # Each variable node connects to exactly 3 check nodes (degree-3)
    for i in range(n_var_nodes):
        check_indices = np.random.choice(n_check_nodes, 3, replace=False)
        connections[check_indices, i] = 1
    
    # Plot variable nodes
    ax.scatter(var_x, var_y, var_z, color=seqCmap(0.8), s=100, alpha=0.8, 
              label='Variable Nodes (Data Qubits)')
    
    # Plot check nodes
    ax.scatter(check_x, check_y, check_z, color=divCmap(0.7), s=150, alpha=0.8, 
              marker='s', label='Check Nodes (Parity Constraints)')
    
    # Draw connections
    connection_colors = []
    for i in range(n_check_nodes):
        for j in range(n_var_nodes):
            if connections[i, j] == 1:
                # Draw line from check node i to variable node j
                ax.plot([check_x[i], var_x[j]], 
                       [check_y[i], var_y[j]], 
                       [check_z[i], var_z[j]], 
                       color=lightCmap(0.3), alpha=0.6, linewidth=1.5)
    
    # Add constraint surface representation
    # Create a mesh between the two layers
    theta_mesh = np.linspace(0, 2*np.pi, 50)
    z_mesh = np.linspace(0, 2, 20)
    THETA, Z = np.meshgrid(theta_mesh, z_mesh)
    
    # Radius varies with height to create a connecting surface
    R = 3 - Z * 0.75  # Shrinks from 3 to 1.5 as z goes from 0 to 2
    X_mesh = R * np.cos(THETA)
    Y_mesh = R * np.sin(THETA)
    
    # Plot constraint surface
    ax.plot_surface(X_mesh, Y_mesh, Z, alpha=0.1, color=lightCmap(0.5), 
                   linewidth=0, antialiased=True)
    
    # Formatting
    ax.set_xlabel('X Coordinate', fontsize=14)
    ax.set_ylabel('Y Coordinate', fontsize=14)
    ax.set_zlabel('Layer (Bipartite Structure)', fontsize=14)
    ax.set_title('3D LDPC Tanner Graph Structure\\n' +
                 'Bipartite Graph: Variable ↔ Check Node Connections',
                 fontsize=16, pad=20)
    
    # Set equal aspect ratio
    max_range = 3.5
    ax.set_xlim(-max_range, max_range)
    ax.set_ylim(-max_range, max_range)
    ax.set_zlim(-0.5, 2.5)
    
    # Add legend
    ax.legend(loc='upper left', bbox_to_anchor=(0, 1))
    
    # Set viewing angle
    ax.view_init(elev=15, azim=45)
    
    # Add text annotations
    performance_text = (
        "Key Properties:\\n"
        f"• Variable Nodes: {n_var_nodes}\\n"
        f"• Check Nodes: {n_check_nodes}\\n"
        f"• Code Rate: R ≈ {1 - n_check_nodes/n_var_nodes:.2f}\\n"
        "• Sparse Connections\\n"
        "• Efficient Decoding"
    )
    ax.text2D(0.02, 0.02, performance_text, transform=ax.transAxes, fontsize=11,
             verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor=lightCmap(0.1), alpha=0.8))
    
    plt.tight_layout()
    
    # Save the plot
    save_path = os.path.join(os.path.dirname(__file__), 'ldpc_tanner_graph_3d.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"3D Tanner graph structure saved to {save_path}")


def main():
    """
    Main function to generate all LDPC 3D visualizations
    """
    print("="*60)
    print("LDPC 3D Visualization Suite")
    print("Professional visualizations for quantum LDPC codes")
    print("="*60)
    
    # Create output directory if it doesn't exist
    plots_dir = os.path.dirname(__file__)
    os.makedirs(plots_dir, exist_ok=True)
    
    # Generate all visualizations
    try:
        create_ldpc_error_threshold_surface()
        create_syndrome_probability_landscape()
        create_code_family_comparison()
        create_tanner_graph_3d_structure()
        
        print("\\n" + "="*60)
        print("All LDPC 3D visualizations completed successfully!")
        print("Files saved in:", plots_dir)
        print("="*60)
        
    except Exception as e:
        print(f"Error generating visualizations: {e}")
        raise


if __name__ == "__main__":
    main()
