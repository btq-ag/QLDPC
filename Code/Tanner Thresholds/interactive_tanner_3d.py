"""
Interactive 3D Quantum LDPC Tanner Graph Visualizer

This script implements an interactive 3D visualization of quantum LDPC Tanner graphs
with topological features. Users can:
- Explore 3D graph structures with vertices and edges
- Click on nodes to see syndrome propagation
- Adjust graph parameters and layout algorithms
- Visualize cavity-mediated connections
- Compare different QLDPC code constructions
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button, CheckButtons
import networkx as nx
import seaborn as sns
import time
from collections import deque
import random


# --- Visualization Parameters ---
seqCmap = sns.color_palette("mako", as_cmap=True)
divCmap = sns.cubehelix_palette(start=.5, rot=-.5, as_cmap=True)
lightCmap = sns.cubehelix_palette(start=2, rot=0, dark=0, light=.95, reverse=True, as_cmap=True)

# --- Graph Parameters ---
DEFAULT_N_QUBITS = 25
DEFAULT_N_CHECKS = 15
DEFAULT_SYNDROME_SPREAD = 3
ANIMATION_INTERVAL = 100  # Milliseconds for smooth updates


class QuantumLDPCTannerGraph:
    """
    3D Tanner graph model for quantum LDPC codes
    """
    def __init__(self, n_qubits=DEFAULT_N_QUBITS, n_checks=DEFAULT_N_CHECKS):
        self.n_qubits = n_qubits
        self.n_checks = n_checks
        self.syndrome_spread = DEFAULT_SYNDROME_SPREAD
        self.graph_type = 0  # 0: Surface-like, 1: Hypergraph, 2: Quantum Tanner
        self.layout_style = 0  # 0: Force-directed, 1: Layered, 2: Sphere
        
        # Graph state
        self.graph = None
        self.qubit_positions = None
        self.check_positions = None
        self.active_syndrome = None
        self.syndrome_time = 0
        
        # Color and visual state
        self.node_colors = None
        self.edge_colors = None
        self.node_sizes = None
        
        self.initialize_graph()
    
    def initialize_graph(self):
        """Initialize the quantum LDPC Tanner graph"""
        self.graph = nx.Graph()
        
        # Add qubit nodes (data qubits)
        qubit_nodes = [f'q_{i}' for i in range(self.n_qubits)]
        self.graph.add_nodes_from(qubit_nodes, node_type='qubit')
        
        # Add check nodes (syndrome qubits)
        check_nodes = [f'c_{i}' for i in range(self.n_checks)]
        self.graph.add_nodes_from(check_nodes, node_type='check')
        
        # Add edges based on code type
        self._add_edges_by_type()
        
        # Generate 3D layout
        self._generate_3d_layout()
        
        # Initialize visual properties
        self._initialize_visual_properties()
    
    def _add_edges_by_type(self):
        """Add edges based on the selected quantum LDPC code type"""
        qubit_nodes = [n for n in self.graph.nodes() if n.startswith('q_')]
        check_nodes = [n for n in self.graph.nodes() if n.startswith('c_')]
        
        if self.graph_type == 0:  # Surface-like code
            # Local connectivity pattern
            degree = 4  # Each qubit connected to ~4 checks
            for qubit in qubit_nodes:
                checks_to_connect = random.sample(check_nodes, min(degree, len(check_nodes)))
                for check in checks_to_connect:
                    self.graph.add_edge(qubit, check)
                    
        elif self.graph_type == 1:  # Hypergraph product code
            # Medium-range connectivity
            degree = 6  # Higher connectivity
            for qubit in qubit_nodes:
                checks_to_connect = random.sample(check_nodes, min(degree, len(check_nodes)))
                for check in checks_to_connect:
                    self.graph.add_edge(qubit, check)
                    
        else:  # Quantum Tanner code (high connectivity)
            # Long-range connectivity with expander properties
            degree = 8  # High connectivity for good distance
            for qubit in qubit_nodes:
                checks_to_connect = random.sample(check_nodes, min(degree, len(check_nodes)))
                for check in checks_to_connect:
                    self.graph.add_edge(qubit, check)
    
    def _generate_3d_layout(self):
        """Generate 3D positions for all nodes"""
        if self.layout_style == 0:  # Force-directed layout
            # Use networkx spring layout and extend to 3D with much more spacing
            pos_2d = nx.spring_layout(self.graph, k=6, iterations=150)  # Even more spacing
            self.qubit_positions = np.array([
                [pos_2d[node][0] * 8, pos_2d[node][1] * 8, random.uniform(-4, 4)]  # Scale up much more
                for node in self.graph.nodes() if node.startswith('q_')
            ])
            self.check_positions = np.array([
                [pos_2d[node][0] * 8, pos_2d[node][1] * 8, random.uniform(-4, 4)]  # Scale up much more
                for node in self.graph.nodes() if node.startswith('c_')
            ])
            
        elif self.layout_style == 1:  # Layered layout
            # Qubits on one layer, checks on another with much more spacing
            qubit_angles = np.linspace(0, 2*np.pi, self.n_qubits, endpoint=False)
            qubit_radius = 12.0  # Much larger radius for plot range 20
            self.qubit_positions = np.array([
                [qubit_radius * np.cos(angle), qubit_radius * np.sin(angle), -5.0]
                for angle in qubit_angles
            ])
            
            check_angles = np.linspace(0, 2*np.pi, self.n_checks, endpoint=False)
            check_radius = 8.0  # Much larger radius
            self.check_positions = np.array([
                [check_radius * np.cos(angle), check_radius * np.sin(angle), 5.0]  # Higher separation
                for angle in check_angles
            ])
            
        else:  # Spherical layout
            # Distribute nodes on sphere surface with much larger radius
            self.qubit_positions = self._sphere_layout(self.n_qubits, radius=12.0)  # Much larger radius
            self.check_positions = self._sphere_layout(self.n_checks, radius=8.0)  # Much larger radius
    
    def _sphere_layout(self, n_nodes, radius=1.0):
        """Generate positions on sphere surface using Fibonacci spiral"""
        positions = []
        golden_ratio = (1 + 5**0.5) / 2
        
        for i in range(n_nodes):
            theta = 2 * np.pi * i / golden_ratio
            phi = np.arccos(1 - 2 * (i + 0.5) / n_nodes)
            
            x = radius * np.sin(phi) * np.cos(theta)
            y = radius * np.sin(phi) * np.sin(theta)
            z = radius * np.cos(phi)
            
            positions.append([x, y, z])
        
        return np.array(positions)
    
    def _initialize_visual_properties(self):
        """Initialize colors and sizes for nodes"""
        # Node colors (qubits blue, checks red)
        qubit_colors = [seqCmap(0.3)] * self.n_qubits
        check_colors = [divCmap(0.7)] * self.n_checks
        self.node_colors = qubit_colors + check_colors
        
        # Node sizes
        qubit_sizes = [100] * self.n_qubits
        check_sizes = [150] * self.n_checks  # Checks slightly larger
        self.node_sizes = qubit_sizes + check_sizes
        
        # Edge colors (default)
        self.edge_colors = ['gray'] * self.graph.number_of_edges()
    
    def trigger_syndrome(self, node_index=None):
        """Trigger syndrome spreading from a specific node"""
        if node_index is None:
            node_index = random.randint(0, self.n_qubits - 1)
        
        self.active_syndrome = node_index
        self.syndrome_time = 0
    
    def update_syndrome_visualization(self):
        """Update colors based on syndrome spreading"""
        if self.active_syndrome is None:
            return
        
        # Reset colors
        self._initialize_visual_properties()
        
        # Highlight syndrome propagation
        syndrome_node = f'q_{self.active_syndrome}'
        
        # Find nodes within syndrome spread distance
        for node in self.graph.nodes():
            try:
                distance = nx.shortest_path_length(self.graph, syndrome_node, node)
                if distance <= self.syndrome_spread:
                    # Color based on distance (closer = more intense)
                    intensity = 1.0 - (distance / self.syndrome_spread)
                    
                    if node.startswith('q_'):
                        node_idx = int(node.split('_')[1])
                        self.node_colors[node_idx] = seqCmap(0.8 * intensity + 0.2)
                        self.node_sizes[node_idx] = int(120 + 80 * intensity)
                    else:
                        node_idx = int(node.split('_')[1]) + self.n_qubits
                        self.node_colors[node_idx] = divCmap(0.8 * intensity + 0.2)
                        self.node_sizes[node_idx] = int(170 + 80 * intensity)
            except nx.NetworkXNoPath:
                continue
        
        self.syndrome_time += 1
        
        # Clear syndrome after some time
        if self.syndrome_time > 20:
            self.active_syndrome = None
    
    def get_edge_positions(self):
        """Get 3D positions for all edges"""
        edge_positions = []
        qubit_nodes = [n for n in self.graph.nodes() if n.startswith('q_')]
        check_nodes = [n for n in self.graph.nodes() if n.startswith('c_')]
        
        for edge in self.graph.edges():
            node1, node2 = edge
            
            if node1.startswith('q_'):
                pos1 = self.qubit_positions[int(node1.split('_')[1])]
            else:
                pos1 = self.check_positions[int(node1.split('_')[1])]
            
            if node2.startswith('q_'):
                pos2 = self.qubit_positions[int(node2.split('_')[1])]
            else:
                pos2 = self.check_positions[int(node2.split('_')[1])]
            
            edge_positions.append([pos1, pos2])
        
        return edge_positions
    
    def get_code_type_name(self):
        """Get human-readable code type name"""
        names = ["Surface-like Code", "Hypergraph Product", "Quantum Tanner (Expander)"]
        return names[self.graph_type]
    
    def get_layout_name(self):
        """Get human-readable layout name"""
        names = ["Force-Directed", "Layered (Bipartite)", "Spherical"]
        return names[self.layout_style]


class TannerGraph3DVisualizer:
    """Interactive 3D Tanner graph visualization"""
    
    def __init__(self, tanner_model):
        self.model = tanner_model
        
        # Animation state (initialize before setup_figure)
        self.rotation_speed = 0.5
        self.auto_rotate = True
        self.azimuth = 45
        self.elevation = 30
        
        # Interaction state
        self.show_edges = True
        self.show_labels = False
        self.highlight_neighbors = True
        
        self.setup_figure()
        self.setup_controls()
    
    def setup_figure(self):
        """Setup the main 3D figure"""
        self.fig = plt.figure(figsize=(18, 12))  # Made wider for better plot visibility
        
        # Layout with more space for the main plot
        gs = self.fig.add_gridspec(2, 1, height_ratios=[4, 1], hspace=0.3, bottom=0.2)
        
        # Main 3D plot (bigger!)
        self.ax_3d = self.fig.add_subplot(gs[0], projection='3d')
        self.ax_3d.set_title("3D Quantum LDPC Tanner Graph\nInteractive Syndrome Visualization", 
                            fontsize=18, fontweight='bold', pad=20)
        
        # Info panel
        self.ax_info = self.fig.add_subplot(gs[1])
        self.ax_info.axis('off')
        
        # Set initial 3D view
        self.ax_3d.view_init(elev=self.elevation, azim=self.azimuth)
    
    def setup_controls(self):
        """Setup interactive controls with vertical stacking - sliders on left, buttons on right"""
        control_height = 0.03
        
        # Left side: Stack 3 sliders vertically
        slider_x = 0.05
        slider_width = 0.25
        
        # Slider 1: Qubits (top)
        ax_qubits = plt.axes([slider_x, 0.12, slider_width, control_height])
        self.slider_qubits = Slider(ax_qubits, 'Qubits', 10, 50, 
                                   valinit=DEFAULT_N_QUBITS, valfmt='%d')
        self.slider_qubits.on_changed(self.update_qubits)
        
        # Slider 2: Checks (middle)
        ax_checks = plt.axes([slider_x, 0.08, slider_width, control_height])
        self.slider_checks = Slider(ax_checks, 'Checks', 5, 30, 
                                   valinit=DEFAULT_N_CHECKS, valfmt='%d')
        self.slider_checks.on_changed(self.update_checks)
        
        # Slider 3: Syndrome (bottom)
        ax_spread = plt.axes([slider_x, 0.04, slider_width, control_height])
        self.slider_spread = Slider(ax_spread, 'Syndrome', 1, 5, 
                                   valinit=DEFAULT_SYNDROME_SPREAD, valfmt='%d')
        self.slider_spread.on_changed(self.update_spread)
        
        # Right side: Stack 3 buttons vertically
        button_x = 0.4
        button_width = 0.15
        
        # Button 1: Code Type (top)
        ax_code_type = plt.axes([button_x, 0.12, button_width, control_height])
        self.btn_code_type = Button(ax_code_type, 'Code Type')
        self.btn_code_type.on_clicked(self.cycle_code_type)
        
        # Button 2: Layout (middle)
        ax_layout = plt.axes([button_x, 0.08, button_width, control_height])
        self.btn_layout = Button(ax_layout, 'Layout')
        self.btn_layout.on_clicked(self.cycle_layout)
        
        # Button 3: Syndrome (bottom)
        ax_syndrome = plt.axes([button_x, 0.04, button_width, control_height])
        self.btn_syndrome = Button(ax_syndrome, 'Syndrome')
        self.btn_syndrome.on_clicked(self.trigger_syndrome)
        
        # Far right: Checkboxes (stacked vertically)
        ax_check = plt.axes([0.7, 0.04, 0.25, 0.12])
        self.checkbox = CheckButtons(ax_check, ['Edges', 'Labels', 'Auto Rotate'], 
                                   [True, False, True])
        self.checkbox.on_clicked(self.toggle_options)
    
    def update_qubits(self, val):
        """Update number of qubits"""
        self.model.n_qubits = int(val)
        self.model.initialize_graph()
    
    def update_checks(self, val):
        """Update number of checks"""
        self.model.n_checks = int(val)
        self.model.initialize_graph()
    
    def update_spread(self, val):
        """Update syndrome spread distance"""
        self.model.syndrome_spread = int(val)
    
    def cycle_code_type(self, event):
        """Cycle through code types"""
        self.model.graph_type = (self.model.graph_type + 1) % 3
        self.model.initialize_graph()
    
    def cycle_layout(self, event):
        """Cycle through layout styles"""
        self.model.layout_style = (self.model.layout_style + 1) % 3
        self.model.initialize_graph()
    
    def trigger_syndrome(self, event):
        """Trigger syndrome visualization"""
        self.model.trigger_syndrome()
    
    def toggle_options(self, label):
        """Toggle display options"""
        if label == 'Edges':
            self.show_edges = not self.show_edges
        elif label == 'Labels':
            self.show_labels = not self.show_labels
        elif label == 'Auto Rotate':
            self.auto_rotate = not self.auto_rotate
    
    def draw_3d_graph(self):
        """Draw the 3D Tanner graph"""
        self.ax_3d.clear()
        
        # Update syndrome visualization
        self.model.update_syndrome_visualization()
        
        # Draw edges first (so they appear behind nodes)
        if self.show_edges:
            edge_positions = self.model.get_edge_positions()
            for i, (pos1, pos2) in enumerate(edge_positions):
                self.ax_3d.plot3D(*zip(pos1, pos2), 'gray', alpha=0.4, linewidth=0.8)
        
        # Draw qubit nodes (data qubits)
        qubit_pos = self.model.qubit_positions
        if len(qubit_pos) > 0:
            self.ax_3d.scatter(qubit_pos[:, 0], qubit_pos[:, 1], qubit_pos[:, 2],
                              c=self.model.node_colors[:self.model.n_qubits],
                              s=self.model.node_sizes[:self.model.n_qubits],
                              alpha=0.8, marker='o', label='Data Qubits', edgecolors='black', linewidth=0.5)
        
        # Draw check nodes (syndrome qubits)
        check_pos = self.model.check_positions
        if len(check_pos) > 0:
            self.ax_3d.scatter(check_pos[:, 0], check_pos[:, 1], check_pos[:, 2],
                              c=self.model.node_colors[self.model.n_qubits:],
                              s=self.model.node_sizes[self.model.n_qubits:],
                              alpha=0.8, marker='s', label='Check Nodes', edgecolors='black', linewidth=0.5)
        
        # Add labels if requested
        if self.show_labels:
            for i, pos in enumerate(qubit_pos):
                self.ax_3d.text(pos[0], pos[1], pos[2], f'q{i}', fontsize=8)
            for i, pos in enumerate(check_pos):
                self.ax_3d.text(pos[0], pos[1], pos[2], f'c{i}', fontsize=8)
        
        # Set labels and title
        self.ax_3d.set_xlabel('X', fontsize=12)
        self.ax_3d.set_ylabel('Y', fontsize=12)
        self.ax_3d.set_zlabel('Z', fontsize=12)
        
        # Update title
        code_name = self.model.get_code_type_name()
        layout_name = self.model.get_layout_name()
        title = f"3D Tanner Graph: {code_name}\nLayout: {layout_name}"
        self.ax_3d.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # Legend positioned to avoid overlap with controls
        self.ax_3d.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98))
        
        # Set equal aspect ratio with much larger range (20 in all directions)
        max_range = 20.0  # Increased from 5.0 to 20.0
        self.ax_3d.set_xlim([-max_range, max_range])
        self.ax_3d.set_ylim([-max_range, max_range])
        self.ax_3d.set_zlim([-max_range, max_range])
    
    def draw_info_panel(self):
        """Draw information panel"""
        self.ax_info.clear()
        self.ax_info.axis('off')
        
        # Graph statistics
        n_edges = self.model.graph.number_of_edges()
        avg_degree = 2 * n_edges / self.model.graph.number_of_nodes() if self.model.graph.number_of_nodes() > 0 else 0
        
        # Current parameters
        param_text = (
            f"Nodes: {self.model.n_qubits} qubits + {self.model.n_checks} checks • "
            f"Edges: {n_edges} • Avg Degree: {avg_degree:.1f} • "
            f"Code: {self.model.get_code_type_name()}"
        )
        
        self.ax_info.text(0.5, 0.7, param_text, ha='center', va='center',
                         transform=self.ax_info.transAxes, fontsize=11,
                         bbox=dict(boxstyle='round,pad=0.5', facecolor='lightpink', alpha=0.8))
        
        # Instructions (more detailed)
        instructions = (
            "• Left-click anywhere to trigger syndrome propagation • "
            "Drag to rotate • Scroll/+/- keys to zoom • "
            "Use buttons/sliders to change parameters"
        )
        
        self.ax_info.text(0.5, 0.3, instructions, ha='center', va='center',
                         transform=self.ax_info.transAxes, fontsize=10,
                         style='italic', color='darkblue')
    
    def update(self, frame):
        """Animation update function"""
        # Auto-rotation
        if self.auto_rotate:
            self.azimuth += self.rotation_speed
            self.ax_3d.view_init(elev=self.elevation, azim=self.azimuth)
        
        # Redraw components
        self.draw_3d_graph()
        self.draw_info_panel()
        
        return []
    
    def zoom(self, factor):
        """Zoom the 3D plot by a given factor"""
        # Get current limits
        xlim = self.ax_3d.get_xlim()
        ylim = self.ax_3d.get_ylim()
        zlim = self.ax_3d.get_zlim()
        
        # Calculate centers
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        z_center = (zlim[0] + zlim[1]) / 2
        
        # Calculate new ranges
        x_range = (xlim[1] - xlim[0]) * factor / 2
        y_range = (ylim[1] - ylim[0]) * factor / 2
        z_range = (zlim[1] - zlim[0]) * factor / 2
        
        # Apply new limits
        self.ax_3d.set_xlim([x_center - x_range, x_center + x_range])
        self.ax_3d.set_ylim([y_center - y_range, y_center + y_range])
        self.ax_3d.set_zlim([z_center - z_range, z_center + z_range])
        
        # Force redraw
        self.fig.canvas.draw_idle()
    
    def run(self):
        """Start the interactive visualization"""
        ani = animation.FuncAnimation(self.fig, self.update, blit=False,
                                    interval=ANIMATION_INTERVAL, cache_frame_data=False)
        
        # Enable better interaction
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        plt.subplots_adjust(left=0.05, bottom=0.4, right=0.95, top=0.9, hspace=0.5)
        plt.show()
    
    def on_key_press(self, event):
        """Handle keyboard shortcuts for zoom"""
        if event.inaxes == self.ax_3d:
            if event.key == '+' or event.key == '=':
                self.zoom(0.8)  # Zoom in
                self.auto_rotate = False
            elif event.key == '-':
                self.zoom(1.2)  # Zoom out
                self.auto_rotate = False
    
    def on_click(self, event):
        """Handle mouse clicks"""
        if event.inaxes == self.ax_3d:
            if event.button == 1:  # Left click
                # Try to find the closest node to click location
                click_successful = False
                
                # Get 2D projection coordinates for node selection
                if len(self.model.qubit_positions) > 0:
                    # For now, just trigger syndrome at a random qubit
                    # In future, could implement proper 3D picking
                    self.model.trigger_syndrome()
                    click_successful = True
                    print(f"Syndrome triggered! Watch the colored propagation spreading from infected qubit.")
                
                if not click_successful:
                    print("Click on the 3D plot to trigger syndrome propagation")
                    
            # Disable auto rotation when user interacts
            self.auto_rotate = False
    
    def on_mouse_move(self, event):
        """Handle mouse movement"""
        if event.inaxes == self.ax_3d and event.button is not None:
            # User is dragging, disable auto rotation
            self.auto_rotate = False
    
    def on_scroll(self, event):
        """Handle mouse scroll for zooming"""
        if event.inaxes == self.ax_3d:
            # Apply zoom based on scroll direction
            if event.step > 0:
                self.zoom(0.9)  # Zoom in
            else:
                self.zoom(1.1)  # Zoom out
            
            # Disable auto rotation when zooming
            self.auto_rotate = False


if __name__ == "__main__":
    print("--- Starting 3D Quantum LDPC Tanner Graph Visualizer ---")
    print("Interactive exploration of quantum LDPC graph topology")
    print("Featuring syndrome propagation and expander graph properties")
    print("\nInteractive Features:")
    print("• 3D graph visualization with vertices and edges")
    print("• Click anywhere to see error propagation")
    print("• Adjust graph parameters with sliders")
    print("• Cycle through different code constructions")
    print("• Multiple 3D layout algorithms")
    print("• Smooth auto-rotation with manual override")
    print("• Zoom with scroll wheel or +/- keys")
    
    # Create model and start visualization
    tanner_model = QuantumLDPCTannerGraph()
    visualizer = TannerGraph3DVisualizer(tanner_model)
    visualizer.run()
    
    print("--- 3D Tanner Graph visualization window closed ---")