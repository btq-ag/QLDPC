"""
Real-Time 3D Quantum LDPC Threshold Landscape Visualizer

This script implements an interactive 3D visualization of quantum LDPC threshold behavior
and scaling analysis. Users can:
- Rotate and zoom the 3D landscape in real-time
- Adjust code parameters with interactive sliders
- Visualize the breakthrough linear distance scaling
- Explore error threshold surfaces across different code families
- Compare scaling behaviors between surface codes and QLDPC codes
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button, CheckButtons
from matplotlib.patches import Rectangle
import seaborn as sns
import time
from collections import deque

# --- Visualization Parameters ---
seqCmap = sns.color_palette("mako", as_cmap=True)
divCmap = sns.cubehelix_palette(start=.5, rot=-.5, as_cmap=True)
lightCmap = sns.cubehelix_palette(start=2, rot=0, dark=0, light=.95, reverse=True, as_cmap=True)

# --- Simulation Parameters ---
ANIMATION_INTERVAL = 50  # Milliseconds between frames for 60 FPS target
DEFAULT_COOPERATIVITY = 1e5
SURFACE_RESOLUTION = 50  # Resolution of 3D surface mesh


class QuantumLDPCThresholdModel:
    """
    Model for quantum LDPC threshold behavior and scaling analysis
    """
    def __init__(self):
        # Code parameter ranges with safe positive values for log scaling
        self.code_lengths = np.logspace(2, 4, SURFACE_RESOLUTION)  # 100 to 10,000 qubits
        self.physical_error_rates = np.logspace(-4, -1, SURFACE_RESOLUTION)  # 0.01% to 10%
        self.distances = np.logspace(1, 3, SURFACE_RESOLUTION)  # Distance 10 to 1000
        
        # Model parameters
        self.cooperativity = DEFAULT_COOPERATIVITY
        self.code_family = 0  # 0: Surface, 1: Hypergraph Product, 2: Quantum Tanner
        self.visualization_mode = 0  # 0: Threshold Surface, 1: Scaling Analysis
        
        # Performance tracking
        self.frame_times = deque(maxlen=30)
        
    def calculate_threshold_surface(self):
        """Calculate 3D threshold surface: (physical_error, distance) -> logical_error"""
        # Create meshgrids with better spacing for 3D visualization
        p_range = np.linspace(0.001, 0.1, SURFACE_RESOLUTION)  # 0.1% to 10% error rates
        d_range = np.linspace(10, 100, SURFACE_RESOLUTION)      # Distance 10 to 100
        P, D = np.meshgrid(p_range, d_range)
        
        if self.code_family == 0:  # Surface codes
            # Surface code: distance ~ sqrt(n), threshold ~ 0.5%
            threshold = 0.005
            scaling_exponent = (D + 1) / 2
            
        elif self.code_family == 1:  # Hypergraph product codes
            # Hypergraph: distance ~ sqrt(n log n), threshold ~ 1%
            threshold = 0.01
            scaling_exponent = (D * np.log(D + 1) + 1) / 2
            
        else:  # Quantum Tanner codes (breakthrough!)
            # Quantum Tanner: distance ~ n, threshold ~ 3%
            threshold = 0.03
            scaling_exponent = D  # Linear scaling breakthrough!
        
        # Threshold behavior model with better 3D structure
        Z = np.zeros_like(P)
        
        # Below threshold: exponential suppression
        below_threshold = P < threshold
        Z[below_threshold] = np.exp(-scaling_exponent[below_threshold] * (threshold - P[below_threshold]) / threshold)
        
        # Above threshold: polynomial growth
        above_threshold = P >= threshold
        Z[above_threshold] = (P[above_threshold] / threshold) ** 0.5
        
        # Add cooperativity effects for cavity-mediated implementation
        cavity_factor = max(0.1, 1 - 1/self.cooperativity)  # Ensure reasonable range
        Z *= cavity_factor
        
        # Scale Z to have good 3D visibility (not too flat)
        Z = Z * 10 + 0.01  # Scale up and add offset
        
        return P, D, Z
    
    def calculate_scaling_surface(self):
        """Calculate 3D scaling surface: (code_length, rate) -> distance"""
        # Use linear ranges for better 3D visualization
        n_range = np.linspace(100, 1000, SURFACE_RESOLUTION)    # Code lengths
        r_range = np.linspace(0.1, 0.9, SURFACE_RESOLUTION)    # Code rates
        N, R = np.meshgrid(n_range, r_range)
        
        if self.code_family == 0:  # Surface codes
            # Surface: d ~ sqrt(n), rate ~ 1/n
            Z = np.sqrt(N) * (1.1 - R) * 0.5  # Scale for better visibility
            
        elif self.code_family == 1:  # Hypergraph product codes
            # Hypergraph: d ~ sqrt(n log n), moderate rate
            Z = np.sqrt(N * np.log(N + 1)) * (1.1 - R) * 0.3
            
        else:  # Quantum Tanner codes (breakthrough!)
            # Quantum Tanner: d ~ n (linear!), constant rate
            Z = N * 0.15 * (1.2 - R)  # Linear distance with good rate
        
        # Ensure all values are positive and have good range
        Z = np.maximum(Z, 5.0)  # Minimum distance of 5
        
        return N, R, Z
    
    def get_code_family_name(self):
        """Get human-readable code family name"""
        names = ["Surface Codes", "Hypergraph Product", "Quantum Tanner (Breakthrough)"]
        return names[self.code_family]
    
    def get_visualization_mode_name(self):
        """Get human-readable visualization mode name"""
        modes = ["Error Threshold Landscape", "Distance Scaling Analysis"]
        return modes[self.visualization_mode]


class ThresholdLandscape3D:
    """Interactive 3D threshold landscape visualization"""
    
    def __init__(self, threshold_model):
        self.model = threshold_model
        
        # Animation state (initialize before setup_figure)
        self.rotation_speed = 1.0
        self.auto_rotate = True
        self.azimuth = 45
        self.elevation = 30
        
        # Track when redraw is needed
        self.need_redraw = True
        self.last_parameters = None
        self.surface_object = None  # Store the surface object
        
        self.setup_figure()
        self.setup_controls()
        
        # Performance tracking
        self.frame_count = 0
        self.start_time = time.time()
        
        # Initial drawing
        self.draw_3d_surface()
        self.draw_info_panel()
        
    def setup_figure(self):
        """Setup the main 3D figure and axis"""
        self.fig = plt.figure(figsize=(16, 12))
        
        # Create layout with more space for 3D plot and controls at bottom
        gs = self.fig.add_gridspec(2, 1, height_ratios=[4, 1], hspace=0.3, bottom=0.15)
        
        # Main 3D plot
        self.ax_3d = self.fig.add_subplot(gs[0], projection='3d')
        self.ax_3d.set_title("3D Quantum LDPC Threshold Landscape\nBreakthrough Linear Distance Scaling", 
                            fontsize=16, fontweight='bold', pad=20)
        
        # Info panel
        self.ax_info = self.fig.add_subplot(gs[1])
        self.ax_info.axis('off')
        
        # Set initial 3D view
        self.ax_3d.view_init(elev=self.elevation, azim=self.azimuth)
        
    def setup_controls(self):
        """Setup interactive controls"""
        control_y = 0.02
        control_height = 0.03
        
        # Sliders
        ax_coop = plt.axes([0.1, control_y + 0.04, 0.15, control_height])
        self.slider_coop = Slider(ax_coop, 'Cooperativity', 1e3, 1e6, 
                                 valinit=DEFAULT_COOPERATIVITY, valstep=1e3,
                                 valfmt='%.0e')
        self.slider_coop.on_changed(self.update_cooperativity)
        
        ax_rotation = plt.axes([0.3, control_y + 0.04, 0.15, control_height])
        self.slider_rotation = Slider(ax_rotation, 'Rotation Speed', 0, 5, 
                                     valinit=1.0, valfmt='%.1f')
        self.slider_rotation.on_changed(self.update_rotation_speed)
        
        # Buttons
        button_width = 0.08
        button_spacing = 0.01
        start_x = 0.5
        
        ax_family = plt.axes([start_x, control_y + 0.04, button_width, control_height])
        self.btn_family = Button(ax_family, 'Code Family')
        self.btn_family.on_clicked(self.cycle_code_family)
        
        ax_mode = plt.axes([start_x + button_width + button_spacing, control_y + 0.04, button_width, control_height])
        self.btn_mode = Button(ax_mode, 'View Mode')
        self.btn_mode.on_clicked(self.cycle_view_mode)
        
        ax_rotate = plt.axes([start_x + 2*(button_width + button_spacing), control_y + 0.04, button_width, control_height])
        self.btn_rotate = Button(ax_rotate, 'Auto Rotate')
        self.btn_rotate.on_clicked(self.toggle_auto_rotate)
        
        # Checkboxes
        ax_check = plt.axes([0.8, control_y, 0.15, 0.08])
        self.checkbox = CheckButtons(ax_check, ['Wireframe', 'Colorbar', 'Grid'], [False, True, True])
        self.checkbox.on_clicked(self.on_checkbox_toggle)
    
    def on_checkbox_toggle(self, label):
        """Handle checkbox toggles"""
        self.need_redraw = True
        
    def update_cooperativity(self, val):
        """Update cavity cooperativity"""
        self.model.cooperativity = val
        self.need_redraw = True
    
    def update_rotation_speed(self, val):
        """Update rotation speed"""
        self.rotation_speed = val
    
    def cycle_code_family(self, event):
        """Cycle through different code families"""
        self.model.code_family = (self.model.code_family + 1) % 3
        self.need_redraw = True
    
    def cycle_view_mode(self, event):
        """Cycle through visualization modes"""
        self.model.visualization_mode = (self.model.visualization_mode + 1) % 2
        self.need_redraw = True
    
    def toggle_auto_rotate(self, event):
        """Toggle automatic rotation"""
        self.auto_rotate = not self.auto_rotate
        self.btn_rotate.label.set_text('Stop Rotate' if self.auto_rotate else 'Auto Rotate')
    
    def draw_3d_surface(self):
        """Draw the main 3D surface without destroying the view"""
        # Calculate surface data based on current mode
        if self.model.visualization_mode == 0:
            X, Y, Z = self.model.calculate_threshold_surface()
            xlabel = 'Physical Error Rate'
            ylabel = 'Code Distance'
            zlabel = 'Logical Error Rate'
        else:
            X, Y, Z = self.model.calculate_scaling_surface()
            xlabel = 'Code Length (n)'
            ylabel = 'Code Rate (k/n)'
            zlabel = 'Distance (d)'
        
        # Get checkbox states
        wireframe = self.checkbox.get_status()[0] if hasattr(self, 'checkbox') else False
        show_colorbar = self.checkbox.get_status()[1] if hasattr(self, 'checkbox') else True
        show_grid = self.checkbox.get_status()[2] if hasattr(self, 'checkbox') else True
        
        # Choose colormap based on code family
        if self.model.code_family == 0:
            cmap = lightCmap
        elif self.model.code_family == 1:
            cmap = divCmap
        else:
            cmap = seqCmap
        
        # Only clear the axes if we need to redraw (parameters changed)
        # This prevents the view from jumping around
        if self.need_redraw or not hasattr(self, 'surface_object') or self.surface_object is None:
            # Store current view if axes exist and have been used
            if hasattr(self.ax_3d, 'elev') and hasattr(self.ax_3d, 'azim'):
                stored_elev = self.ax_3d.elev
                stored_azim = self.ax_3d.azim
            else:
                stored_elev = self.elevation
                stored_azim = self.azimuth
            
            # Clear the axes only when necessary
            self.ax_3d.clear()
            
            # Draw surface with proper 3D settings
            if wireframe:
                self.surface_object = self.ax_3d.plot_wireframe(X, Y, Z, cmap=cmap, alpha=0.7, linewidth=1)
            else:
                self.surface_object = self.ax_3d.plot_surface(X, Y, Z, cmap=cmap, alpha=0.8, 
                                                linewidth=0, antialiased=True, shade=True)
            
            # Add colorbar (with proper error handling)
            if show_colorbar and not wireframe:
                # Remove existing colorbar safely
                if hasattr(self, 'colorbar') and self.colorbar is not None:
                    try:
                        self.colorbar.remove()
                    except (AttributeError, ValueError):
                        pass  # Ignore removal errors
                
                # Create new colorbar
                try:
                    self.colorbar = self.fig.colorbar(self.surface_object, ax=self.ax_3d, shrink=0.5, aspect=30)
                    self.colorbar.set_label(zlabel, fontsize=12)
                except Exception:
                    # If colorbar creation fails, skip it
                    pass
            
            # Set labels and title
            self.ax_3d.set_xlabel(xlabel, fontsize=12, labelpad=10)
            self.ax_3d.set_ylabel(ylabel, fontsize=12, labelpad=10)
            self.ax_3d.set_zlabel(zlabel, fontsize=12, labelpad=10)
            
            # Update title with current settings
            family_name = self.model.get_code_family_name()
            mode_name = self.model.get_visualization_mode_name()
            title = f"3D {mode_name}\n{family_name}"
            self.ax_3d.set_title(title, fontsize=14, fontweight='bold', pad=20)
            
            # Grid
            self.ax_3d.grid(show_grid, alpha=0.3)
            
            # Set proper 3D aspect ratio and limits to prevent collapse
            x_min, x_max = np.min(X), np.max(X)
            y_min, y_max = np.min(Y), np.max(Y) 
            z_min, z_max = np.min(Z), np.max(Z)
            
            # Add some padding to prevent edge clipping
            x_pad = (x_max - x_min) * 0.1
            y_pad = (y_max - y_min) * 0.1
            z_pad = (z_max - z_min) * 0.1
            
            self.ax_3d.set_xlim([x_min - x_pad, x_max + x_pad])
            self.ax_3d.set_ylim([y_min - y_pad, y_max + y_pad])
            self.ax_3d.set_zlim([z_min - z_pad, z_max + z_pad])
            
            # Set equal aspect ratio for all axes
            self.ax_3d.set_box_aspect([1, 1, 0.8])  # Slightly flatten Z for better viewing
            
            # Restore the view
            self.ax_3d.view_init(elev=stored_elev, azim=stored_azim)
            
            # Reset the redraw flag
            self.need_redraw = False
    
    def draw_info_panel(self):
        """Draw information panel with clean, refined text"""
        self.ax_info.clear()
        self.ax_info.axis('off')
        
        # Performance info
        current_time = time.time()
        if hasattr(self, 'start_time') and current_time > self.start_time:
            fps = self.frame_count / (current_time - self.start_time)
            self.model.frame_times.append(current_time)
        else:
            fps = 0
        
        # Current parameters display (compact and clean)
        family_name = self.model.get_code_family_name()
        mode_name = self.model.get_visualization_mode_name()
        
        param_text = (
            f"Mode: {mode_name} • Family: {family_name} • "
            f"Cooperativity: C = {self.model.cooperativity:.0e} • "
            f"Performance: {fps:.1f} FPS"
        )
        
        self.ax_info.text(0.5, 0.7, param_text, ha='center', va='center',
                         transform=self.ax_info.transAxes, fontsize=11,
                         bbox=dict(boxstyle='round,pad=0.5', facecolor=lightCmap(0.05), alpha=0.8))
        
        # Instructions (compact)
        instructions = (
            "Drag to rotate • Scroll to zoom • Sliders adjust parameters • "
            "Buttons cycle through families/modes • Auto Rotate for smooth animation"
        )
        
        self.ax_info.text(0.5, 0.3, instructions, ha='center', va='center',
                         transform=self.ax_info.transAxes, fontsize=10,
                         style='italic', color='darkblue')
        
        # Key insights for current family (very compact)
        if self.model.code_family == 0:
            insight = "Surface: d ∼ √n, R ∼ 1/n (Traditional)"
        elif self.model.code_family == 1:
            insight = "Hypergraph: d ∼ √(n log n), R = const (Improved)"
        else:
            insight = "Quantum Tanner: d ∼ n, R = const (BREAKTHROUGH!)"
        
        color = 'darkgreen' if self.model.code_family == 2 else 'darkblue'
        self.ax_info.text(0.02, 0.1, insight, ha='left', va='center',
                         transform=self.ax_info.transAxes, fontsize=10,
                         color=color, fontweight='bold')
    
    def update(self, frame):
        """Animation update function - only redraws when necessary"""
        # Check if parameters have changed and redraw is needed
        current_parameters = (
            self.model.code_family,
            self.model.visualization_mode,
            self.model.cooperativity
        )
        
        if self.need_redraw or current_parameters != self.last_parameters:
            # Only redraw the surface when parameters change
            self.draw_3d_surface()
            self.last_parameters = current_parameters
        
        # Auto-rotation (this doesn't require redrawing the surface)
        if self.auto_rotate:
            self.azimuth += self.rotation_speed
            self.ax_3d.view_init(elev=self.elevation, azim=self.azimuth)
        
        # Update info panel every frame (lightweight)
        self.draw_info_panel()
        
        # Update frame counter
        self.frame_count += 1
        
        return []
    
    def run(self):
        """Start the interactive 3D visualization"""
        ani = animation.FuncAnimation(self.fig, self.update, blit=False, 
                                    interval=ANIMATION_INTERVAL, cache_frame_data=False)
        
        # Enable 3D interaction
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        
        plt.subplots_adjust(left=0.05, bottom=0.15, right=0.95, top=0.9, hspace=0.3)
        plt.show()
    
    def on_mouse_move(self, event):
        """Handle mouse movement for manual rotation"""
        if event.inaxes == self.ax_3d and event.button == 1:  # Left mouse button
            # Disable auto-rotation when manually rotating
            self.auto_rotate = False
            self.btn_rotate.label.set_text('Auto Rotate')
    
    def on_scroll(self, event):
        """Handle mouse scroll for zooming"""
        if event.inaxes == self.ax_3d:
            # Let matplotlib handle the zoom
            pass


if __name__ == "__main__":
    print("--- Starting 3D Quantum LDPC Threshold Landscape Visualizer ---")
    print("Revolutionary linear distance scaling visualization in 3D")
    print("Based on breakthrough 2020-2022 quantum LDPC constructions")
    print("\nInteractive Features:")
    print("• Drag to rotate the 3D landscape")
    print("• Scroll to zoom in/out")
    print("• Cycle through code families (Surface → Hypergraph → Quantum Tanner)")
    print("• Switch between threshold and scaling analysis modes")
    print("• Adjust cavity cooperativity for gate fidelity effects")
    print("• Auto-rotation with adjustable speed")
    
    # Create model and start visualization
    threshold_model = QuantumLDPCThresholdModel()
    visualizer = ThresholdLandscape3D(threshold_model)
    visualizer.run()
    
    print("--- 3D Visualization window closed ---")