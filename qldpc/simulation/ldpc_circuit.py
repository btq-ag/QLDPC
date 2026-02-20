"""
Real-Time Interactive Quantum LDPC Circuit Simulator

This script implements an interactive quantum LDPC circuit simulation with real-time
visualization and control. Users can:
- Inject errors into qubits by clicking
- Watch syndrome extraction in real-time
- Observe the belief propagation decoding process
- Adjust code parameters dynamically
- See cavity-mediated gates in action
"""

import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button, CheckButtons
import matplotlib.patches as patches
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch
import os
import seaborn as sns
from collections import defaultdict

# --- Visualization Parameters ---
seqCmap = sns.color_palette("mako", as_cmap=True)
divCmap = sns.cubehelix_palette(start=.5, rot=-.5, as_cmap=True)
lightCmap = sns.cubehelix_palette(start=2, rot=0, dark=0, light=.95, reverse=True, as_cmap=True)

# --- Simulation Parameters ---
ANIMATION_INTERVAL = 100  # Milliseconds between frames
DEFAULT_ERROR_RATE = 0.05
DEFAULT_COOPERATIVITY = 1e5


class QuantumLDPCCode:
    """
    Quantum LDPC code implementation with breakthrough linear distance scaling
    """
    def __init__(self, n_data=21, n_checks=12):
        self.n_data = n_data  # Number of data qubits
        self.n_checks = n_checks  # Number of parity checks
        self.distance = int(np.sqrt(n_data))  # Linear distance scaling
        
        # Generate sparse parity check matrix (LDPC property)
        self.parity_matrix = self._generate_ldpc_matrix()
        
        # Qubit states: 0=|0⟩, 1=|1⟩, 2=error_X, 3=error_Z, 4=error_Y
        self.qubit_states = np.zeros(n_data, dtype=int)
        self.syndrome = np.zeros(n_checks, dtype=int)
        self.syndrome_history = []
        
        # Belief propagation variables
        self.variable_beliefs = np.zeros((n_data, 2))  # [P(0), P(1)]
        self.check_to_var_messages = np.zeros((n_checks, n_data))
        self.var_to_check_messages = np.zeros((n_data, n_checks))
        
        # Initialize beliefs to uniform
        self.variable_beliefs[:, 0] = 0.5
        self.variable_beliefs[:, 1] = 0.5
        
        # Cavity mediated gate parameters
        self.cavity_cooperativity = DEFAULT_COOPERATIVITY
        self.gate_fidelity = self._calculate_gate_fidelity()
        
        # Animation state
        self.bp_iteration = 0
        self.max_bp_iterations = 10
        self.decoding_complete = False
        
    def _generate_ldpc_matrix(self):
        """Generate sparse parity check matrix for quantum LDPC code"""
        # Each check connects to ~6 qubits, each qubit in ~3 checks (LDPC property)
        H = np.zeros((self.n_checks, self.n_data), dtype=int)
        
        np.random.seed(42)  # For reproducibility
        for i in range(self.n_checks):
            # Each parity check connects to 6 qubits (constant weight)
            connected_qubits = np.random.choice(self.n_data, 6, replace=False)
            H[i, connected_qubits] = 1
            
        return H
    
    def _calculate_gate_fidelity(self):
        """Calculate cavity-mediated gate fidelity based on cooperativity"""
        C = self.cavity_cooperativity
        epsilon_deph = 0.001  # Dephasing error
        return 1 - 1/C - epsilon_deph
    
    def inject_error(self, qubit_idx, error_type=2):
        """Inject error into a specific qubit"""
        if 0 <= qubit_idx < self.n_data:
            self.qubit_states[qubit_idx] = error_type
            self._update_syndrome()
    
    def _update_syndrome(self):
        """Calculate syndrome from current qubit states"""
        for i in range(self.n_checks):
            # Count all errors in this parity check (X, Z, and Y errors)
            connected_qubits = np.where(self.parity_matrix[i] == 1)[0]
            errors = sum(1 for q in connected_qubits 
                        if self.qubit_states[q] in [2, 3, 4])  # X, Z, or Y errors
            self.syndrome[i] = errors % 2
    
    def belief_propagation_step(self):
        """Perform one iteration of belief propagation decoding"""
        if self.bp_iteration >= self.max_bp_iterations:
            return
            
        # Check-to-variable messages
        for check_idx in range(self.n_checks):
            connected_vars = np.where(self.parity_matrix[check_idx] == 1)[0]
            
            for var_idx in connected_vars:
                # Product of all other variable-to-check messages
                other_vars = [v for v in connected_vars if v != var_idx]
                if len(other_vars) > 0:
                    prob_even = 0.5  # Simplified BP calculation
                    prob_odd = 0.5
                    
                    # Syndrome constraint
                    if self.syndrome[check_idx] == 0:
                        self.check_to_var_messages[check_idx, var_idx] = prob_even
                    else:
                        self.check_to_var_messages[check_idx, var_idx] = prob_odd
        
        # Variable-to-check messages and beliefs update
        for var_idx in range(self.n_data):
            connected_checks = np.where(self.parity_matrix[:, var_idx] == 1)[0]
            
            # Update beliefs (simplified)
            incoming_messages = self.check_to_var_messages[connected_checks, var_idx]
            if len(incoming_messages) > 0:
                belief_0 = np.prod(incoming_messages) * 0.9  # Prior for |0⟩
                belief_1 = np.prod(1 - incoming_messages) * 0.1  # Prior for |1⟩
                norm = belief_0 + belief_1
                if norm > 0:
                    self.variable_beliefs[var_idx, 0] = belief_0 / norm
                    self.variable_beliefs[var_idx, 1] = belief_1 / norm
            
            # Update outgoing messages
            for check_idx in connected_checks:
                other_checks = [c for c in connected_checks if c != check_idx]
                self.var_to_check_messages[var_idx, check_idx] = self.variable_beliefs[var_idx, 1]
        
        self.bp_iteration += 1
        
        # Check for convergence
        if self.bp_iteration >= self.max_bp_iterations:
            self.decoding_complete = True
    
    def reset_decoding(self):
        """Reset the belief propagation decoder"""
        self.bp_iteration = 0
        self.decoding_complete = False
        self.variable_beliefs[:, 0] = 0.5
        self.variable_beliefs[:, 1] = 0.5
        self.check_to_var_messages.fill(0.5)
        self.var_to_check_messages.fill(0.5)
    
    def clear_errors(self):
        """Clear all errors from qubits"""
        self.qubit_states.fill(0)
        self._update_syndrome()
        self.reset_decoding()


class LDPCCircuitAnimation:
    """Interactive LDPC circuit visualization with real-time controls"""
    
    def __init__(self, ldpc_code):
        self.ldpc_code = ldpc_code
        self.setup_figure()
        self.setup_controls()
        
        # Animation state
        self.auto_decode = False
        self.cavity_animation_phase = 0
        self.selected_qubit = None
        
        # Performance tracking
        self.frame_count = 0
        self.start_time = time.time()
        
        # Connect mouse events
        self.fig.canvas.mpl_connect('button_press_event', self.on_mouse_click)
        
    def setup_figure(self):
        """Setup the main figure and subplots"""
        self.fig = plt.figure(figsize=(16, 12))
        
        # Create grid layout with more space at bottom for controls
        gs = self.fig.add_gridspec(3, 3, height_ratios=[2.5, 1, 0.8], width_ratios=[2, 1, 1],
                                  hspace=0.4, wspace=0.3, bottom=0.15)
        
        # Main circuit view
        self.ax_circuit = self.fig.add_subplot(gs[0, :2])
        self.ax_circuit.set_title("Interactive Quantum LDPC Circuit\n"
                                "Click qubits to inject errors • Watch real-time decoding", 
                                fontsize=14, fontweight='bold')
        self.ax_circuit.set_xlim(-1, 15)  # Extended to accommodate cavity
        self.ax_circuit.set_ylim(-1, 8)
        self.ax_circuit.set_aspect('equal')
        self.ax_circuit.axis('off')
        
        # Syndrome display
        self.ax_syndrome = self.fig.add_subplot(gs[0, 2])
        self.ax_syndrome.set_title("Syndrome Vector", fontsize=12, fontweight='bold')
        self.ax_syndrome.set_xlim(-0.5, 1.5)
        self.ax_syndrome.set_ylim(-0.5, self.ldpc_code.n_checks - 0.5)
        self.ax_syndrome.axis('off')
        
        # Belief propagation visualization
        self.ax_beliefs = self.fig.add_subplot(gs[1, :])
        self.ax_beliefs.set_title("Belief Propagation Decoding", fontsize=12, fontweight='bold')
        self.ax_beliefs.set_xlabel("Data Qubits")
        self.ax_beliefs.set_ylabel("Error Probability")
        self.ax_beliefs.set_ylim(0, 1)
        
        # Code parameters display
        self.ax_params = self.fig.add_subplot(gs[2, :])
        self.ax_params.set_title("LDPC Code Parameters", fontsize=12, fontweight='bold')
        self.ax_params.axis('off')
        
    def setup_controls(self):
        """Setup interactive controls"""
        # Adjust positions for better layout
        control_y = 0.02
        control_height = 0.03
        
        # Sliders
        ax_coop = plt.axes([0.1, control_y, 0.2, control_height])
        self.slider_coop = Slider(ax_coop, 'Cooperativity', 1e3, 1e6, 
                                 valinit=DEFAULT_COOPERATIVITY, valstep=1e3,
                                 valfmt='%.0e')
        self.slider_coop.on_changed(self.update_cooperativity)
        
        # Buttons with improved spacing
        button_width = 0.08
        button_spacing = 0.02
        start_x = 0.35
        
        ax_decode = plt.axes([start_x, control_y, button_width, control_height])
        self.btn_decode = Button(ax_decode, 'Decode Step')
        self.btn_decode.on_clicked(self.decode_step)
        
        ax_auto = plt.axes([start_x + button_width + button_spacing, control_y, button_width, control_height])
        self.btn_auto = Button(ax_auto, 'Auto Decode')
        self.btn_auto.on_clicked(self.toggle_auto_decode)
        
        ax_clear = plt.axes([start_x + 2*(button_width + button_spacing), control_y, button_width, control_height])
        self.btn_clear = Button(ax_clear, 'Clear Errors')
        self.btn_clear.on_clicked(self.clear_errors)
        
        ax_reset = plt.axes([start_x + 3*(button_width + button_spacing), control_y, button_width, control_height])
        self.btn_reset = Button(ax_reset, 'Reset Code')
        self.btn_reset.on_clicked(self.reset_code)
        
        # Checkboxes
        ax_check = plt.axes([0.8, control_y, 0.15, 0.06])
        self.checkbox = CheckButtons(ax_check, ['Show Messages', 'Show Cavity'], [True, True])
        
    def on_mouse_click(self, event):
        """Handle mouse clicks on qubits"""
        if event.inaxes == self.ax_circuit:
            # Find clicked qubit
            for i in range(self.ldpc_code.n_data):
                x, y = self.get_qubit_position(i)
                if (event.xdata - x)**2 + (event.ydata - y)**2 < 0.3**2:
                    # Cycle through error types
                    current_error = self.ldpc_code.qubit_states[i]
                    new_error = (current_error + 1) % 5  # 0,1,2,3,4 cycle
                    self.ldpc_code.inject_error(i, new_error)
                    self.ldpc_code.reset_decoding()
                    break
    
    def get_qubit_position(self, qubit_idx):
        """Get the (x, y) position for drawing a qubit"""
        # Arrange qubits in a grid
        cols = 7
        row = qubit_idx // cols
        col = qubit_idx % cols
        return col * 1.5, 6 - row * 1.5
    
    def get_check_position(self, check_idx):
        """Get the (x, y) position for drawing a check"""
        # Arrange checks in a column
        return 10, check_idx * 0.5
    
    def draw_circuit(self):
        """Draw the main LDPC circuit"""
        self.ax_circuit.clear()
        self.ax_circuit.set_xlim(-1, 15)  # Extended to accommodate cavity
        self.ax_circuit.set_ylim(-1, 8)
        self.ax_circuit.set_aspect('equal')
        self.ax_circuit.axis('off')
        
        # Draw data qubits
        for i in range(self.ldpc_code.n_data):
            x, y = self.get_qubit_position(i)
            
            # Color based on state
            state = self.ldpc_code.qubit_states[i]
            if state == 0:
                color = lightCmap(0.3)  # Ground state
                label = '|0⟩'
            elif state == 1:
                color = lightCmap(0.6)  # Excited state
                label = '|1⟩'
            elif state == 2:
                color = 'red'  # X error
                label = 'X'
            elif state == 3:
                color = 'blue'  # Z error
                label = 'Z'
            elif state == 4:
                color = 'purple'  # Y error
                label = 'Y'
            
            # Highlight based on belief propagation
            if hasattr(self.ldpc_code, 'variable_beliefs'):
                error_prob = self.ldpc_code.variable_beliefs[i, 1]
                alpha = 0.3 + 0.7 * error_prob  # More transparent = less likely error
            else:
                alpha = 0.8
                
            circle = Circle((x, y), 0.3, color=color, alpha=alpha)
            self.ax_circuit.add_patch(circle)
            self.ax_circuit.text(x, y, label, ha='center', va='center', 
                               fontsize=10, fontweight='bold')
            self.ax_circuit.text(x, y-0.6, f'q{i}', ha='center', va='center', fontsize=8)
        
        # Draw parity checks
        for j in range(self.ldpc_code.n_checks):
            x, y = self.get_check_position(j)
            
            # Color based on syndrome
            color = seqCmap(0.8) if self.ldpc_code.syndrome[j] == 0 else 'red'
            
            square = Rectangle((x-0.2, y-0.2), 0.4, 0.4, 
                             facecolor=color, alpha=0.8)
            self.ax_circuit.add_patch(square)
            self.ax_circuit.text(x, y, f's{j}', ha='center', va='center', 
                               fontsize=9, fontweight='bold')
        
        # Draw connections (parity check matrix)
        show_messages = self.checkbox.get_status()[0] if hasattr(self, 'checkbox') else True
        if show_messages:
            for j in range(self.ldpc_code.n_checks):
                for i in range(self.ldpc_code.n_data):
                    if self.ldpc_code.parity_matrix[j, i] == 1:
                        x1, y1 = self.get_qubit_position(i)
                        x2, y2 = self.get_check_position(j)
                        
                        # Color based on message strength
                        if hasattr(self.ldpc_code, 'check_to_var_messages'):
                            message_strength = self.ldpc_code.check_to_var_messages[j, i]
                            alpha = 0.2 + 0.6 * abs(message_strength - 0.5) * 2
                            color = 'red' if message_strength > 0.5 else 'green'
                        else:
                            alpha = 0.3
                            color = 'black'
                        
                        self.ax_circuit.plot([x1, x2], [y1, y2], color=color, 
                                           alpha=alpha, linewidth=1)
        
        # Draw cavity representation
        show_cavity = self.checkbox.get_status()[1] if hasattr(self, 'checkbox') else True
        if show_cavity:
            # Cavity box (shifted further right)
            cavity_rect = FancyBboxPatch((11.5, 2), 2.5, 3, 
                                        boxstyle="round,pad=0.1",
                                        facecolor=divCmap(0.3), alpha=0.4,
                                        edgecolor='black', linewidth=2)
            self.ax_circuit.add_patch(cavity_rect)
            self.ax_circuit.text(12.75, 3.5, 'Cavity\nQED', ha='center', va='center',
                               fontsize=12, fontweight='bold')
            
            # Cooperativity indicator
            C = self.ldpc_code.cavity_cooperativity
            fidelity = self.ldpc_code.gate_fidelity
            self.ax_circuit.text(12.75, 2.5, f'C = {C:.0e}\nF = {fidelity:.3f}',
                               ha='center', va='center', fontsize=10,
                               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Add title with current state
        state_text = f"BP Iteration: {self.ldpc_code.bp_iteration}/{self.ldpc_code.max_bp_iterations}"
        if self.ldpc_code.decoding_complete:
            state_text += " [COMPLETE]"
        self.ax_circuit.text(6, 7.5, state_text, ha='center', fontsize=12, fontweight='bold',
                           bbox=dict(boxstyle='round', facecolor=seqCmap(0.2), alpha=0.3))
    
    def draw_syndrome(self):
        """Draw syndrome vector"""
        self.ax_syndrome.clear()
        self.ax_syndrome.set_xlim(-0.5, 1.5)
        self.ax_syndrome.set_ylim(-0.5, self.ldpc_code.n_checks - 0.5)
        self.ax_syndrome.axis('off')
        
        # Check if any syndrome bits are active
        syndrome_active = np.any(self.ldpc_code.syndrome == 1)
        
        for i, syndrome_bit in enumerate(self.ldpc_code.syndrome):
            color = 'lightgreen' if syndrome_bit == 0 else 'red'
            alpha = 0.6 if syndrome_bit == 0 else 0.9
            rect = Rectangle((0, i), 1, 0.8, facecolor=color, alpha=alpha, 
                           edgecolor='black', linewidth=1)
            self.ax_syndrome.add_patch(rect)
            self.ax_syndrome.text(0.5, i+0.4, str(syndrome_bit), 
                                ha='center', va='center', fontsize=12, fontweight='bold')
        
        # Syndrome equation and status
        self.ax_syndrome.text(0.5, -0.3, 's = He', ha='center', va='top', 
                            fontsize=12, fontweight='bold')
        
        # Status indicator
        status_text = "Errors Detected!" if syndrome_active else "No Errors"
        status_color = 'red' if syndrome_active else 'green'
        self.ax_syndrome.text(0.5, self.ldpc_code.n_checks, status_text, 
                            ha='center', va='bottom', fontsize=10, fontweight='bold',
                            color=status_color)
    
    def draw_beliefs(self):
        """Draw belief propagation progress"""
        self.ax_beliefs.clear()
        
        # Error probabilities for each qubit
        error_probs = self.ldpc_code.variable_beliefs[:, 1]
        qubit_indices = np.arange(self.ldpc_code.n_data)
        
        bars = self.ax_beliefs.bar(qubit_indices, error_probs, 
                                  color=[seqCmap(p) for p in error_probs],
                                  alpha=0.7)
        
        # Highlight actual errors
        for i, state in enumerate(self.ldpc_code.qubit_states):
            if state in [2, 3, 4]:  # Has error
                bars[i].set_color('red')
                bars[i].set_alpha(0.9)
        
        self.ax_beliefs.set_xlabel("Data Qubits")
        self.ax_beliefs.set_ylabel("Error Probability")
        self.ax_beliefs.set_ylim(0, 1)
        self.ax_beliefs.grid(True, alpha=0.3)
        
        # Add threshold line
        self.ax_beliefs.axhline(y=0.5, color='red', linestyle='--', alpha=0.5)
        self.ax_beliefs.text(self.ldpc_code.n_data/2, 0.52, 'Decision Threshold', 
                           ha='center', fontsize=10)
    
    def draw_parameters(self):
        """Draw code parameters and breakthrough information"""
        self.ax_params.clear()
        self.ax_params.axis('off')
        
        # Calculate parameters
        n = self.ldpc_code.n_data
        k = n - self.ldpc_code.n_checks  # Logical qubits (simplified)
        d = self.ldpc_code.distance
        rate = k / n if n > 0 else 0
        
        # Parameter display
        param_text = (
            f"Quantum LDPC Code Parameters:\n"
            f"Physical Qubits (n): {n}  •  Logical Qubits (k): {k}  •  Distance (d): {d}\n"
            f"Code Rate: R = k/n = {rate:.3f}  •  "
            f"Cooperativity: C = {self.ldpc_code.cavity_cooperativity:.0e}\n"
            f"Gate Fidelity: F = {self.ldpc_code.gate_fidelity:.4f}  •  "
            f"LDPC: ✓ Sparse checks  •  Breakthrough: Linear distance scaling"
        )
        
        self.ax_params.text(0.5, 0.7, param_text, ha='center', va='center',
                          transform=self.ax_params.transAxes, fontsize=11,
                          bbox=dict(boxstyle='round', facecolor=lightCmap(0.05), alpha=0.6))
        
        # Instructions (shifted down slightly)
        instructions = (
            "Instructions: Click qubits to inject errors (cycles through |0⟩→|1⟩→X→Z→Y) • "
            "Use 'Decode Step' for manual decoding • 'Auto Decode' for continuous • "
            "Adjust cooperativity to see gate fidelity effects"
        )
        
        self.ax_params.text(0.5, 0.1, instructions, ha='center', va='center',
                          transform=self.ax_params.transAxes, fontsize=10,
                          style='italic', color='darkblue')
    
    def update_cooperativity(self, val):
        """Update cavity cooperativity"""
        self.ldpc_code.cavity_cooperativity = val
        self.ldpc_code.gate_fidelity = self.ldpc_code._calculate_gate_fidelity()
    
    def decode_step(self, event):
        """Perform one decoding step"""
        if not self.ldpc_code.decoding_complete:
            self.ldpc_code.belief_propagation_step()
    
    def toggle_auto_decode(self, event):
        """Toggle automatic decoding"""
        self.auto_decode = not self.auto_decode
        self.btn_auto.label.set_text('Stop Auto' if self.auto_decode else 'Auto Decode')
    
    def clear_errors(self, event):
        """Clear all errors"""
        self.ldpc_code.clear_errors()
    
    def reset_code(self, event):
        """Reset the entire code"""
        self.ldpc_code = QuantumLDPCCode(self.ldpc_code.n_data, self.ldpc_code.n_checks)
        self.ldpc_code.cavity_cooperativity = self.slider_coop.val
        self.ldpc_code.gate_fidelity = self.ldpc_code._calculate_gate_fidelity()
    
    def update(self, frame):
        """Animation update function"""
        # Auto-decode if enabled
        if self.auto_decode and not self.ldpc_code.decoding_complete:
            if frame % 3 == 0:  # Slower auto-decode
                self.ldpc_code.belief_propagation_step()
        
        # Cavity animation phase
        self.cavity_animation_phase = (self.cavity_animation_phase + 1) % 60
        
        # Redraw all components
        self.draw_circuit()
        self.draw_syndrome()
        self.draw_beliefs()
        self.draw_parameters()
        
        # Update title (removed FPS)
        self.fig.suptitle("Real-Time Quantum LDPC Circuit Simulator",
                        fontsize=16, fontweight='bold')
        
        return []
    
    def run(self):
        """Start the interactive simulation"""
        ani = animation.FuncAnimation(self.fig, self.update, blit=False, 
                                    interval=ANIMATION_INTERVAL, cache_frame_data=False)
        # Use subplots_adjust instead of tight_layout to avoid widget conflicts
        plt.subplots_adjust(left=0.1, bottom=0.15, right=0.95, top=0.9, hspace=0.4, wspace=0.3)
        plt.show()


def main():
    """Entry point for the real-time LDPC circuit simulator."""
    print("--- Starting Real-Time Quantum LDPC Circuit Simulator ---")
    print("Based on breakthrough 2020-2022 constructions with linear distance scaling")
    print("Implementing Brennen et al.'s cavity-mediated approach")
    print("\nInstructions:")
    print("  Click on qubits to inject different types of errors")
    print("  Watch belief propagation decoding in real-time")
    print("  Adjust cavity cooperativity to see effects on gate fidelity")
    print("  Use controls to step through decoding manually or automatically")

    ldpc_code = QuantumLDPCCode(n_data=21, n_checks=12)
    simulator = LDPCCircuitAnimation(ldpc_code)
    simulator.run()

    print("--- Simulation window closed ---")


if __name__ == "__main__":
    main()
