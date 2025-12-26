"""
Interactive 3D Quantum LDPC Circuit Builder

This module implements a real-time interactive quantum circuit builder using tkinter
with a dark theme GUI framework. The application provides a 2.5D isometric perspective
where users can drag and drop 3D quantum circuit components from a toolbox onto a
grid-based building area to construct quantum LDPC circuits and perform real-time quantum computations.

GUI Framework: tkinter with tkinter.ttk for native dark theme support
Dark Theme: Custom dark color scheme with modern UI elements
Architecture: Event-driven GUI with real-time quantum computation backend

Author: Jeffrey Morais
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import os

# Quantum computing libraries
try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
    from qiskit.quantum_info import Statevector, Operator
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    QuantumCircuit = None  # Placeholder for type hints
    QuantumRegister = None
    ClassicalRegister = None
    print("Warning: Qiskit not available. Some quantum computations will be simulated.")

# Scientific computing
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import seaborn as sns

# Set up color palettes for consistency with project standards
sns.set_style("darkgrid")
seqCmap = sns.color_palette("mako", as_cmap=True)
divCmap = sns.cubehelix_palette(start=.5, rot=-.5, as_cmap=True)
lightCmap = sns.cubehelix_palette(start=2, rot=0, dark=0, light=.95, reverse=True, as_cmap=True)


class TutorialScreen:
    """
    Interactive tutorial screen that guides users through the Quantum LDPC Circuit Builder.
    
    Displays a multi-step tutorial with colored keywords explaining:
    - Basic component placement and circuit building
    - Quantum LDPC concepts (parity checks, syndrome extraction)
    - Running computations and error correction
    """
    
    # Color scheme for highlighted keywords
    COLORS = {
        'quantum': '#00ffcc',      # Cyan for quantum terms
        'ldpc': '#ff6b6b',         # Coral red for LDPC terms  
        'component': '#ffd93d',    # Yellow for component names
        'action': '#6bcb77',       # Green for user actions
        'math': '#a8e6cf',         # Light green for math/formulas
        'warning': '#ff9f43',      # Orange for important notes
        'title': '#74b9ff',        # Light blue for titles
        'highlight': '#fd79a8',    # Pink for emphasis
    }
    
    def __init__(self, parent: tk.Tk, on_complete_callback=None, circuit_builder=None):
        """
        Initialize the tutorial screen.
        
        Args:
            parent: Parent tkinter window
            on_complete_callback: Function to call when tutorial is completed/skipped
            circuit_builder: Reference to the CircuitBuilder3D instance for hint functionality
        """
        self.parent = parent
        self.on_complete = on_complete_callback
        self.circuit_builder = circuit_builder
        self.current_step = 0
        self.tutorial_window = None
        self.hint_active = False  # Track whether hint circuit is currently placed
        self.hint_components = []  # Store hint component references for removal
        
        # Define tutorial steps with rich content
        self.steps = self._create_tutorial_steps()
    
    def _create_tutorial_steps(self) -> List[Dict[str, Any]]:
        """Create the tutorial content with tagged text for coloring."""
        return [
            # Step 0: Welcome
            {
                'title': 'Welcome to the Quantum LDPC Circuit Builder!',
                'content': [
                    ('Welcome to the ', 'normal'),
                    ('3D Quantum Circuit Builder', 'title'),
                    ('!\n\n', 'normal'),
                    ('This interactive tool lets you build and simulate quantum ', 'normal'),
                    ('Low-Density Parity-Check (LDPC)', 'ldpc'),
                    (' codes — the breakthrough quantum error correction technology from 2020-2022.\n\n', 'normal'),
                    ('🎯 What you\'ll learn:\n', 'normal'),
                    ('• How to place quantum components on the isometric grid\n', 'normal'),
                    ('• Building ', 'normal'),
                    ('LDPC parity check', 'ldpc'),
                    (' structures\n', 'normal'),
                    ('• Running syndrome extraction and error correction\n\n', 'normal'),
                    ('💡 ', 'normal'),
                    ('Tip:', 'highlight'),
                    (' You can interact with the main window while this tutorial is open!\n\n', 'normal'),
                    ('Click ', 'normal'),
                    ('Next', 'action'),
                    (' to begin, or ', 'normal'),
                    ('Skip Tutorial', 'action'),
                    (' to jump right in.', 'normal'),
                ],
                'image': None
            },
            # Step 1: Basic Components
            {
                'title': 'Understanding Quantum Components',
                'content': [
                    ('The Component Toolbox (right panel) contains:\n\n', 'normal'),
                    ('📦 ', 'normal'),
                    ('Single Qubit Gates:', 'title'),
                    ('\n', 'normal'),
                    ('   • X Gate — Bit flip (Pauli-X): |0⟩ ↔ |1⟩\n', 'normal'),
                    ('   • Z Gate — Phase flip (Pauli-Z)\n', 'normal'),
                    ('   • H Gate — Hadamard, creates superposition\n\n', 'normal'),
                    ('🔗 ', 'normal'),
                    ('Two Qubit Gates:', 'title'),
                    ('\n', 'normal'),
                    ('   • CNOT — Controlled-NOT for entanglement\n', 'normal'),
                    ('   • CZ — Controlled-Z gate\n\n', 'normal'),
                    ('🛡️ ', 'normal'),
                    ('LDPC Components', 'ldpc'),
                    (' (the important ones!):\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Data Qubit', 'component'),
                    (' — Stores quantum information\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Ancilla Qubit', 'component'),
                    (' — Helper qubits for measurement\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Parity Check', 'ldpc'),
                    (' — Detects errors\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Syndrome Extract', 'ldpc'),
                    (' — Measures error syndromes\n', 'normal'),
                ],
                'image': None
            },
            # Step 2: Placing Components
            {
                'title': 'Placing Components on the Grid',
                'content': [
                    ('The isometric grid is your quantum circuit canvas!\n\n', 'normal'),
                    ('🖱️ How to place components:\n\n', 'normal'),
                    ('1. ', 'normal'),
                    ('Select', 'action'),
                    (' a component from the toolbox tabs\n', 'normal'),
                    ('2. ', 'normal'),
                    ('Click', 'action'),
                    (' anywhere on the grid to place it\n', 'normal'),
                    ('3. ', 'normal'),
                    ('Drag', 'action'),
                    (' existing components to move them\n\n', 'normal'),
                    ('⚡ Pro Tips:\n', 'normal'),
                    ('• Right-click a component to rotate, duplicate, or delete\n', 'normal'),
                    ('• Middle-click + drag to pan the grid view\n', 'normal'),
                    ('• Components auto-connect when placed nearby\n', 'normal'),
                    ('• Grid boundaries (±10) keep your circuit organized\n\n', 'normal'),
                    ('⚠️ ', 'warning'),
                    ('Note:', 'warning'),
                    (' Only one component per grid position.', 'normal'),
                ],
                'image': None
            },
            # Step 3: What is LDPC?
            {
                'title': 'What are Quantum LDPC Codes?',
                'content': [
                    ('Quantum ', 'normal'),
                    ('LDPC', 'ldpc'),
                    (' codes are error-correcting codes where:\n\n', 'normal'),
                    ('• Each stabilizer check involves only a few qubits (sparse)\n', 'normal'),
                    ('• Each qubit participates in only a few checks\n\n', 'normal'),
                    ('📊 ', 'normal'),
                    ('The 2020-2022 Breakthrough:', 'title'),
                    ('\n', 'normal'),
                    ('Panteleev-Kalachev and Leverrier-Zémor achieved:\n\n', 'normal'),
                    ('• Linear distance: ', 'normal'),
                    ('d = Θ(n)', 'math'),
                    (' — error correction scales with code size\n', 'normal'),
                    ('• Constant rate: ', 'normal'),
                    ('R = Θ(1)', 'math'),
                    (' — efficient encoding\n\n', 'normal'),
                    ('🎯 Why this matters:\n', 'normal'),
                    ('Surface codes need ~3000 qubits for tasks that LDPC codes\naccomplish with only ', 'normal'),
                    ('~300 qubits', 'highlight'),
                    ('!', 'normal'),
                ],
                'image': None
            },
            # Step 4: Building an LDPC Code
            {
                'title': 'Building Your First LDPC Code',
                'content': [
                    ('Let\'s build a simple LDPC error correction circuit!\n\n', 'normal'),
                    ('📐 ', 'normal'),
                    ('Basic Structure:', 'title'),
                    ('\n\n', 'normal'),
                    ('1. Place 3 ', 'normal'),
                    ('Data Qubits', 'component'),
                    (' in a row (they\'re green)\n', 'normal'),
                    ('   → These store your quantum information\n\n', 'normal'),
                    ('2. Place 2 ', 'normal'),
                    ('Parity Checks', 'ldpc'),
                    (' adjacent to data qubits (orange)\n', 'normal'),
                    ('   → These detect bit-flip errors\n\n', 'normal'),
                    ('3. Add an X Gate on one data qubit\n', 'normal'),
                    ('   → This simulates a ', 'normal'),
                    ('bit-flip error', 'warning'),
                    ('\n\n', 'normal'),
                    ('💡 The parity check matrix H is built from positions:\n', 'normal'),
                    ('   ', 'normal'),
                    ('H·e = s', 'math'),
                    ('  (error × check = syndrome)\n\n', 'normal'),
                    ('Try loading ', 'normal'),
                    ('error_correction_demo.json', 'action'),
                    (' to see this!', 'normal'),
                ],
                'image': None
            },
            # Step 5: Syndrome and Error Correction
            {
                'title': 'Syndrome Extraction & Error Correction',
                'content': [
                    ('Syndrome Extraction', 'title'),
                    (' is how we detect errors!\n\n', 'normal'),
                    ('The ', 'normal'),
                    ('DiVincenzo-Aliferis method', 'ldpc'),
                    (' (from Brennen et al.):\n\n', 'normal'),
                    ('1. Ancilla qubits are prepared in |+⟩ state\n', 'normal'),
                    ('2. CNOT gates couple ancillas to data qubits\n', 'normal'),
                    ('3. Measure ancillas to get the syndrome vector\n', 'normal'),
                    ('4. Syndrome reveals error locations\n\n', 'normal'),
                    ('🔧 ', 'normal'),
                    ('Using the Controls:', 'title'),
                    ('\n\n', 'normal'),
                    ('• Click "', 'normal'),
                    ('Calculate Syndrome', 'action'),
                    ('" to extract error information\n', 'normal'),
                    ('• Click "', 'normal'),
                    ('Run Error Correction', 'action'),
                    ('" to run belief propagation decoding\n', 'normal'),
                    ('• Click "', 'normal'),
                    ('Simulate Evolution', 'action'),
                    ('" to see quantum state probabilities', 'normal'),
                ],
                'image': None
            },
            # Step 6: Cavity-Mediated Gates
            {
                'title': 'Cavity-Mediated Non-Local Gates',
                'content': [
                    ('🔮 ', 'normal'),
                    ('The Secret Sauce:', 'title'),
                    (' How do LDPC codes work in hardware?\n\n', 'normal'),
                    ('LDPC codes require non-local connections — qubits far apart\n', 'normal'),
                    ('must interact. Brennen et al.\'s solution:\n\n', 'normal'),
                    ('Cavity QED', 'ldpc'),
                    (' — qubits coupled through a shared cavity mode!\n\n', 'normal'),
                    ('The key parameter is Cooperativity:\n', 'normal'),
                    ('   ', 'normal'),
                    ('C = g²/(κγ) ~ 10⁴ to 10⁶', 'math'),
                    ('\n\n', 'normal'),
                    ('Where:\n', 'normal'),
                    ('• g = atom-cavity coupling strength\n', 'normal'),
                    ('• κ = cavity decay rate\n', 'normal'),
                    ('• γ = atomic spontaneous emission\n\n', 'normal'),
                    ('Gate fidelity: ', 'normal'),
                    ('F ≈ 1 - 1/C', 'math'),
                    (' — higher C means better gates!', 'normal'),
                ],
                'image': None
            },
            # Step 7: Loading Examples
            {
                'title': 'Exploring Pre-Built Circuits',
                'content': [
                    ('The ', 'normal'),
                    ('saved_circuits/', 'action'),
                    (' folder contains example circuits:\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('error_correction_demo.json', 'component'),
                    ('\n   Basic LDPC with error injection\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('syndrome_extraction.json', 'component'),
                    ('\n   DiVincenzo-Aliferis protocol\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('hypergraph_product_ldpc.json', 'component'),
                    ('\n   Tensor product construction (√n distance)\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('quantum_tanner_linear_decoder.json', 'component'),
                    ('\n   Breakthrough linear distance code\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('surface_code_syndrome_cycle.json', 'component'),
                    ('\n   Comparison with surface codes\n\n', 'normal'),
                    ('To load: Click "', 'normal'),
                    ('Load Circuit', 'action'),
                    ('" and browse to saved_circuits/', 'normal'),
                ],
                'image': None
            },
            # Step 8: Keyboard Shortcuts
            {
                'title': 'Keyboard Shortcuts & Tips',
                'content': [
                    ('⌨️ ', 'normal'),
                    ('Keyboard Shortcuts:', 'title'),
                    ('\n\n', 'normal'),
                    ('• Delete — Remove selected component\n', 'normal'),
                    ('• Ctrl+C — Copy (duplicate adjacent)\n', 'normal'),
                    ('• Ctrl+S — Save circuit to file\n', 'normal'),
                    ('• Ctrl+O — Open/load circuit\n\n', 'normal'),
                    ('🖱️ ', 'normal'),
                    ('Mouse Actions:', 'title'),
                    ('\n\n', 'normal'),
                    ('• Left-click — Place or select component\n', 'normal'),
                    ('• Drag — Move component\n', 'normal'),
                    ('• Right-click — Context menu (rotate, delete, properties)\n', 'normal'),
                    ('• Middle-click + drag — Pan the grid view\n\n', 'normal'),
                    ('The Status Panel (bottom-right) shows computation results.', 'normal'),
                ],
                'image': None
            },
            # Step 9: Final / Let's Go!
            {
                'title': 'You\'re Ready to Build!',
                'content': [
                    ('🎉 Congratulations! You\'re ready to explore quantum LDPC codes.\n\n', 'normal'),
                    ('📋 ', 'normal'),
                    ('Quick Start Checklist:', 'title'),
                    ('\n\n', 'normal'),
                    ('□ Place some ', 'normal'),
                    ('Data Qubits', 'component'),
                    (' (green blocks)\n', 'normal'),
                    ('□ Add ', 'normal'),
                    ('Parity Checks', 'ldpc'),
                    (' nearby (orange blocks)\n', 'normal'),
                    ('□ Insert an X Gate to simulate an error\n', 'normal'),
                    ('□ Click "Calculate Syndrome" to detect errors\n', 'normal'),
                    ('□ Click "Run Error Correction" to fix them!\n\n', 'normal'),
                    ('Remember: These are the codes that will enable fault-tolerant\n', 'normal'),
                    ('quantum computing with ', 'normal'),
                    ('10x fewer qubits', 'highlight'),
                    ('!\n\n', 'normal'),
                    ('Click ', 'normal'),
                    ('Finish', 'action'),
                    (' to start building.', 'normal'),
                ],
                'image': None
            },
        ]
    
    def show(self):
        """Display the tutorial window."""
        self.tutorial_window = tk.Toplevel(self.parent)
        self.tutorial_window.title("Tutorial - Quantum LDPC Circuit Builder")
        self.tutorial_window.geometry("650x520")
        self.tutorial_window.configure(bg='#1a1a2e')
        # Don't use transient or grab_set - allows interaction with main window
        self.tutorial_window.attributes('-topmost', False)
        
        # Position to the side of main window (not centered, to allow seeing both)
        self.tutorial_window.update_idletasks()
        x = 50  # Left side of screen
        y = (self.tutorial_window.winfo_screenheight() - 520) // 2
        self.tutorial_window.geometry(f"650x520+{x}+{y}")
        
        # Main container with gradient-like header
        self.main_frame = tk.Frame(self.tutorial_window, bg='#1a1a2e')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header with step indicator
        self.header_frame = tk.Frame(self.main_frame, bg='#16213e')
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="", 
            font=('Segoe UI', 16, 'bold'),
            fg='#e94560',
            bg='#16213e',
            pady=10
        )
        self.title_label.pack()
        
        # Step indicator
        self.step_label = tk.Label(
            self.header_frame,
            text="",
            font=('Segoe UI', 10),
            fg='#888888',
            bg='#16213e'
        )
        self.step_label.pack(pady=(0, 10))
        
        # Progress bar frame
        self.progress_frame = tk.Frame(self.main_frame, bg='#1a1a2e', height=8)
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))
        self.progress_frame.pack_propagate(False)
        
        self.progress_bg = tk.Frame(self.progress_frame, bg='#2d2d44', height=8)
        self.progress_bg.pack(fill=tk.X)
        
        self.progress_bar = tk.Frame(self.progress_bg, bg='#e94560', height=8)
        self.progress_bar.place(x=0, y=0, relheight=1, relwidth=0)
        
        # === NAVIGATION BUTTONS - Pack FIRST at bottom to ensure visibility ===
        self.nav_frame = tk.Frame(self.main_frame, bg='#1a1a2e')
        self.nav_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        # Skip button (left)
        self.skip_btn = tk.Button(
            self.nav_frame,
            text="Skip Tutorial",
            font=('Segoe UI', 10),
            fg='#888888',
            bg='#2d2d44',
            activeforeground='#ffffff',
            activebackground='#3d3d54',
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2',
            command=self._skip_tutorial
        )
        self.skip_btn.pack(side=tk.LEFT)
        
        # Don't show again checkbox
        self.show_again_var = tk.BooleanVar(value=True)
        self.show_again_check = tk.Checkbutton(
            self.nav_frame,
            text="Show on startup",
            variable=self.show_again_var,
            font=('Segoe UI', 9),
            fg='#888888',
            bg='#1a1a2e',
            activeforeground='#888888',
            activebackground='#1a1a2e',
            selectcolor='#2d2d44',
            cursor='hand2'
        )
        self.show_again_check.pack(side=tk.LEFT, padx=(15, 0))
        
        # Next button (right)
        self.next_btn = tk.Button(
            self.nav_frame,
            text="Next →",
            font=('Segoe UI', 11, 'bold'),
            fg='#ffffff',
            bg='#e94560',
            activeforeground='#ffffff',
            activebackground='#ff6b8a',
            relief='flat',
            padx=25,
            pady=8,
            cursor='hand2',
            command=self._next_step
        )
        self.next_btn.pack(side=tk.RIGHT)
        
        # Previous button
        self.prev_btn = tk.Button(
            self.nav_frame,
            text="← Back",
            font=('Segoe UI', 10),
            fg='#cccccc',
            bg='#2d2d44',
            activeforeground='#ffffff',
            activebackground='#3d3d54',
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2',
            command=self._prev_step
        )
        self.prev_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Hint button (center-right, between back and next)
        self.hint_btn = tk.Button(
            self.nav_frame,
            text="💡 Show Hint",
            font=('Segoe UI', 10),
            fg='#ffd93d',
            bg='#2d2d44',
            activeforeground='#ffffff',
            activebackground='#4a4a6a',
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2',
            command=self._toggle_hint
        )
        self.hint_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # === CONTENT AREA - Pack AFTER nav so it fills remaining space ===
        self.content_frame = tk.Frame(self.main_frame, bg='#0f0f23', bd=1, relief='solid')
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        
        # Text widget for rich content
        self.content_text = tk.Text(
            self.content_frame,
            font=('Consolas', 11),
            bg='#0f0f23',
            fg='#ffffff',
            wrap=tk.WORD,
            padx=20,
            pady=15,
            relief='flat',
            cursor='arrow',
            state='disabled'
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.content_frame, command=self.content_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.config(yscrollcommand=scrollbar.set)
        
        # Configure text tags for colors
        for tag_name, color in self.COLORS.items():
            self.content_text.tag_configure(tag_name, foreground=color)
        self.content_text.tag_configure('normal', foreground='#cccccc')
        
        # Display first step
        self._update_display()
        
        # Handle window close
        self.tutorial_window.protocol("WM_DELETE_WINDOW", self._skip_tutorial)
    
    def _update_display(self):
        """Update the display for the current step."""
        step_data = self.steps[self.current_step]
        
        # Update title
        self.title_label.config(text=step_data['title'])
        
        # Update step indicator
        self.step_label.config(text=f"Step {self.current_step + 1} of {len(self.steps)}")
        
        # Update progress bar
        progress = (self.current_step + 1) / len(self.steps)
        self.progress_bar.place(x=0, y=0, relheight=1, relwidth=progress)
        
        # Update content
        self.content_text.config(state='normal')
        self.content_text.delete('1.0', tk.END)
        
        for text, tag in step_data['content']:
            self.content_text.insert(tk.END, text, tag)
        
        self.content_text.config(state='disabled')
        
        # Update button states
        self.prev_btn.config(state='normal' if self.current_step > 0 else 'disabled')
        
        # Show hint button only on step 4 (Building Your First LDPC Code)
        # and step 9 (final checklist)
        if self.current_step in [4, 9] and self.circuit_builder is not None:
            self.hint_btn.pack(side=tk.RIGHT, padx=(0, 10))
            # Update hint button text based on state
            if self.hint_active:
                self.hint_btn.config(text="↩ Remove Hint", fg='#ff6b6b')
            else:
                self.hint_btn.config(text="💡 Show Hint", fg='#ffd93d')
        else:
            self.hint_btn.pack_forget()
        
        # Change next button text on last step
        if self.current_step == len(self.steps) - 1:
            self.next_btn.config(text="Finish ✓", bg='#27ae60')
        else:
            self.next_btn.config(text="Next →", bg='#e94560')
    
    def _next_step(self):
        """Go to the next tutorial step or finish."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._update_display()
        else:
            self._finish_tutorial()
    
    def _prev_step(self):
        """Go to the previous tutorial step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_display()
    
    def _skip_tutorial(self):
        """Skip the tutorial."""
        self._finish_tutorial()
    
    def _finish_tutorial(self):
        """Close the tutorial and call the completion callback."""
        # Remove any hint components before closing
        if self.hint_active:
            self._remove_hint_components()
        
        show_on_startup = self.show_again_var.get()
        self.tutorial_window.destroy()
        
        if self.on_complete:
            self.on_complete(show_on_startup)
    
    def _toggle_hint(self):
        """Toggle the hint circuit on/off."""
        if not self.circuit_builder:
            return
        
        if self.hint_active:
            self._remove_hint_components()
        else:
            self._place_hint_components()
        
        self.hint_active = not self.hint_active
        self._update_display()  # Update button text
    
    def _place_hint_components(self):
        """Place the example LDPC circuit components for the hint."""
        if not self.circuit_builder:
            return
        
        # Define a simple LDPC demo circuit matching saved_circuits/error_correction_demo.json:
        # Layout follows quantum circuit convention:
        #   x-axis = time/operations (left to right)
        #   y-axis = qubit lanes (stacked vertically)
        #
        # Time step 0: Data qubits (column x=0)
        # Time step 1: Parity checks (column x=1) 
        # Time step 2: X gate error (column x=2)
        #
        #   y=0: [Data0] [Parity0] 
        #   y=1: [Data1] [Parity1] [X Gate]
        #   y=2: [Data2]
        
        hint_specs = [
            # Data qubits in a column (x=0, varying y)
            (ComponentType.DATA_QUBIT, (0, 0, 0)),
            (ComponentType.DATA_QUBIT, (0, 1, 0)),
            (ComponentType.DATA_QUBIT, (0, 2, 0)),
            # Parity checks adjacent (x=1)
            (ComponentType.PARITY_CHECK, (1, 0, 0)),
            (ComponentType.PARITY_CHECK, (1, 1, 0)),
            # X gate (error) on middle data qubit line (x=2, y=1)
            (ComponentType.X_GATE, (2, 1, 0)),
        ]
        
        self.hint_components = []
        
        two_qubit_types = [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]
        
        for comp_type, position in hint_specs:
            # Check if position is free
            occupied = False
            for existing in self.circuit_builder.components:
                if existing.position == position:
                    occupied = True
                    break
            
            if not occupied:
                color = self.circuit_builder._get_component_color(comp_type)
                # Two-qubit gates span 2 lanes
                if comp_type in two_qubit_types:
                    size = (1.0, 1.0, 2.0)  # (width, height, depth) - depth=2 for Y direction
                else:
                    size = (1.0, 1.0, 1.0)
                component = Component3D(
                    component_type=comp_type,
                    position=position,
                    color=color,
                    size=size
                )
                self.circuit_builder.components.append(component)
                self.hint_components.append(component)
        
        # Redraw the circuit
        self.circuit_builder._redraw_circuit()
        self.circuit_builder._log_status("Hint: Example LDPC circuit placed (3 data qubits + 2 parity checks + X gate)")
    
    def _remove_hint_components(self):
        """Remove the hint circuit components."""
        if not self.circuit_builder:
            return
        
        # Remove hint components from the circuit builder
        for hint_comp in self.hint_components:
            if hint_comp in self.circuit_builder.components:
                self.circuit_builder.components.remove(hint_comp)
        
        self.hint_components = []
        
        # Redraw the circuit
        self.circuit_builder._redraw_circuit()
        self.circuit_builder._log_status("Hint circuit removed")
    
    @staticmethod
    def should_show_tutorial() -> bool:
        """Check if tutorial should be shown based on saved preferences."""
        config_path = os.path.join(os.path.dirname(__file__), '.tutorial_config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('show_tutorial', True)
        except:
            pass
        return True
    
    @staticmethod
    def save_tutorial_preference(show_on_startup: bool):
        """Save the tutorial display preference."""
        config_path = os.path.join(os.path.dirname(__file__), '.tutorial_config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump({'show_tutorial': show_on_startup}, f)
        except:
            pass


class AdvancedTutorialScreen:
    """
    Advanced interactive tutorial that demonstrates qubit placement, operator actions,
    and gate distinctions with live visual demonstrations on the circuit grid.
    """
    
    # Color scheme for highlighted keywords
    COLORS = {
        'quantum': '#00ffcc',      # Cyan for quantum terms
        'ldpc': '#ff6b6b',         # Coral red for LDPC terms  
        'component': '#ffd93d',    # Yellow for component names
        'action': '#6bcb77',       # Green for user actions
        'math': '#a8e6cf',         # Light green for math/formulas
        'warning': '#ff9f43',      # Orange for important notes
        'title': '#74b9ff',        # Light blue for titles
        'highlight': '#fd79a8',    # Pink for emphasis
        'qubit': '#00ff88',        # Green for qubits
        'gate': '#ffaa00',         # Orange for gates
    }
    
    def __init__(self, parent: tk.Tk, circuit_builder=None):
        """
        Initialize the advanced tutorial.
        
        Args:
            parent: Parent tkinter window
            circuit_builder: Reference to the CircuitBuilder3D instance
        """
        self.parent = parent
        self.circuit_builder = circuit_builder
        self.current_step = 0
        self.tutorial_window = None
        self.demo_components = []  # Track components placed for demonstration
        self.original_components = []  # Store original circuit state
        
        # Define advanced tutorial steps
        self.steps = self._create_tutorial_steps()
    
    def _create_tutorial_steps(self) -> List[Dict[str, Any]]:
        """Create the advanced tutorial content."""
        return [
            # Step 0: Where Qubits Live
            {
                'title': 'Understanding Qubit Placement',
                'content': [
                    ('Where Do Qubits Live on the Grid?', 'title'),
                    ('\n\n', 'normal'),
                    ('In this circuit builder, each ', 'normal'),
                    ('grid cell', 'highlight'),
                    (' represents a single quantum component.\n\n', 'normal'),
                    ('Key Concepts:', 'title'),
                    ('\n\n', 'normal'),
                    ('1. ', 'normal'),
                    ('One cube = One qubit/gate', 'qubit'),
                    ('\n   When you place a Data Qubit, it occupies exactly one grid position.\n\n', 'normal'),
                    ('2. ', 'normal'),
                    ('Position = (x, y, z)', 'math'),
                    ('\n   • ', 'normal'),
                    ('X-axis', 'component'),
                    (' = Time/circuit depth (left to right)\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Y-axis', 'component'),
                    (' = Qubit index (front to back)\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Z-axis', 'component'),
                    (' = Layer (usually 0 for flat circuits)\n\n', 'normal'),
                    ('3. Components are placed at ', 'normal'),
                    ('integer coordinates', 'highlight'),
                    ('\n   No partial positions - each block snaps to the grid.\n\n', 'normal'),
                    ('Look at the grid now!', 'warning'),
                    (' Demo qubits have been placed to show positioning.', 'normal'),
                ],
                'demo_action': 'show_qubit_positions'
            },
            # Step 1: Operator Actions
            {
                'title': 'How Operators Act on Qubits',
                'content': [
                    ('Operators & Qubit Interactions', 'title'),
                    ('\n\n', 'normal'),
                    ('Gates (operators) act on qubits in the same ', 'normal'),
                    ('qubit lane', 'highlight'),
                    (' (same Y coordinate).\n\n', 'normal'),
                    ('Circuit Flow:', 'title'),
                    ('\n', 'normal'),
                    ('Time flows left → right along the X-axis.\n\n', 'normal'),
                    ('   [Qubit] → [Gate] → [Gate] → [Measure]\n', 'math'),
                    ('      x=0      x=1      x=2       x=3\n\n', 'normal'),
                    ('Visual Indication:', 'title'),
                    ('\n', 'normal'),
                    ('When a gate is in the same lane as a qubit:\n', 'normal'),
                    ('• The gate operates on that qubit at that time step\n', 'normal'),
                    ('• ', 'normal'),
                    ('Highlighted cubes', 'warning'),
                    (' show where operators meet qubits\n\n', 'normal'),
                    ('On the grid:', 'warning'),
                    (' See how the X gate (blue) follows the Data Qubit (green)\n', 'normal'),
                    ('in the same lane - this means X acts on that qubit!', 'normal'),
                ],
                'demo_action': 'show_operator_interaction'
            },
            # Step 2: Single vs Two-Qubit Gates
            {
                'title': 'Single vs Two-Qubit Gates',
                'content': [
                    ('Distinguishing Gate Types', 'title'),
                    ('\n\n', 'normal'),
                    ('Single-Qubit Gates', 'qubit'),
                    (' (X, Y, Z, H, S, T):\n', 'normal'),
                    ('• Occupy ', 'normal'),
                    ('one grid cell', 'highlight'),
                    ('\n', 'normal'),
                    ('• Act on the qubit in their lane only\n', 'normal'),
                    ('• Shown as ', 'normal'),
                    ('standard cubes', 'component'),
                    (' (1x1 footprint)\n\n', 'normal'),
                    ('Two-Qubit Gates', 'gate'),
                    (' (CNOT, CZ, SWAP):\n', 'normal'),
                    ('• Span ', 'normal'),
                    ('two adjacent lanes', 'highlight'),
                    (' (control + target)\n', 'normal'),
                    ('• Create entanglement between qubits\n', 'normal'),
                    ('• Shown as ', 'normal'),
                    ('wider cubes', 'warning'),
                    (' (1x2 footprint spanning both lanes)\n\n', 'normal'),
                    ('Visual Difference:', 'title'),
                    ('\n', 'normal'),
                    ('On the grid, notice:\n', 'normal'),
                    ('• Single gates: 1 unit wide (1 lane)\n', 'normal'),
                    ('• Two-qubit gates: ', 'normal'),
                    ('2 units deep', 'gate'),
                    (' bridging two qubit lanes\n\n', 'normal'),
                    ('The demo shows both types - compare their sizes!', 'warning'),
                ],
                'demo_action': 'show_gate_comparison'
            },
            # Step 3: Three-Qubit Repetition Code
            {
                'title': 'Three-Qubit Repetition Code',
                'content': [
                    ('Classical Error Correction: The Repetition Code', 'title'),
                    ('\n\n', 'normal'),
                    ('The simplest quantum error correction is the ', 'normal'),
                    ('3-qubit bit-flip code', 'ldpc'),
                    ('.\n\n', 'normal'),
                    ('Encoding:', 'title'),
                    ('\n', 'normal'),
                    ('   |0⟩ → |000⟩    |1⟩ → |111⟩\n', 'math'),
                    ('\nThis uses ', 'normal'),
                    ('2 CNOT gates', 'gate'),
                    (' to copy the logical state:\n\n', 'normal'),
                    ('Circuit Structure:', 'title'),
                    ('\n', 'normal'),
                    ('   q0: ─────●─────●─────\n', 'math'),
                    ('            │     │\n', 'math'),
                    ('   q1: ─────⊕─────┼─────\n', 'math'),
                    ('                  │\n', 'math'),
                    ('   q2: ───────────⊕─────\n\n', 'math'),
                    ('Error Detection:', 'title'),
                    ('\n', 'normal'),
                    ('• Parity checks compare adjacent qubits\n', 'normal'),
                    ('• Syndrome reveals which qubit flipped\n', 'normal'),
                    ('• ', 'normal'),
                    ('Majority voting', 'highlight'),
                    (' corrects single errors\n\n', 'normal'),
                    ('On the grid:', 'warning'),
                    (' See 3 data qubits with CNOT encoding!', 'normal'),
                ],
                'demo_action': 'show_repetition_code'
            },
            # Step 4: Surface Code Introduction
            {
                'title': 'The Surface Code',
                'content': [
                    ('Surface Code: The Industry Standard', 'title'),
                    ('\n\n', 'normal'),
                    ('The ', 'normal'),
                    ('surface code', 'ldpc'),
                    (' is the most studied quantum error correction code.\n\n', 'normal'),
                    ('Key Properties:', 'title'),
                    ('\n', 'normal'),
                    ('• Data qubits on ', 'normal'),
                    ('vertices', 'component'),
                    (' of a 2D lattice\n', 'normal'),
                    ('• Ancilla qubits on ', 'normal'),
                    ('faces', 'component'),
                    (' (X-type) and ', 'normal'),
                    ('edges', 'component'),
                    (' (Z-type)\n', 'normal'),
                    ('• Distance d requires ', 'normal'),
                    ('O(d²) physical qubits', 'math'),
                    ('\n\n', 'normal'),
                    ('Stabilizers:', 'title'),
                    ('\n', 'normal'),
                    ('• ', 'normal'),
                    ('X-stabilizers', 'qubit'),
                    (' (plaquettes): Detect Z errors\n', 'normal'),
                    ('• ', 'normal'),
                    ('Z-stabilizers', 'gate'),
                    (' (vertices): Detect X errors\n\n', 'normal'),
                    ('Layout Pattern:', 'title'),
                    ('\n', 'normal'),
                    ('   D─A─D\n', 'math'),
                    ('   │ │ │\n', 'math'),
                    ('   A─D─A   (D=Data, A=Ancilla)\n', 'math'),
                    ('   │ │ │\n', 'math'),
                    ('   D─A─D\n\n', 'math'),
                    ('Limitation:', 'warning'),
                    (' Surface codes need ~1000+ qubits per logical qubit!', 'normal'),
                ],
                'demo_action': 'show_surface_code'
            },
            # Step 5: Quantum LDPC Codes - Part 1
            {
                'title': 'Quantum LDPC Codes: The Breakthrough',
                'content': [
                    ('Why LDPC Codes Matter', 'title'),
                    ('\n\n', 'normal'),
                    ('Quantum ', 'normal'),
                    ('LDPC (Low-Density Parity-Check)', 'ldpc'),
                    (' codes achieve:\n\n', 'normal'),
                    ('Revolutionary Properties:', 'title'),
                    ('\n', 'normal'),
                    ('1. ', 'normal'),
                    ('Constant Rate', 'highlight'),
                    (': k/n = Θ(1)\n', 'normal'),
                    ('   → Encode many logical qubits efficiently\n\n', 'normal'),
                    ('2. ', 'normal'),
                    ('Linear Distance', 'highlight'),
                    (': d = Θ(n)\n', 'normal'),
                    ('   → Error correction improves with code size\n\n', 'normal'),
                    ('3. ', 'normal'),
                    ('Sparse Checks', 'highlight'),
                    (': Each check involves O(1) qubits\n', 'normal'),
                    ('   → Practical syndrome extraction\n\n', 'normal'),
                    ('Comparison with Surface Codes:', 'title'),
                    ('\n', 'normal'),
                    ('• Surface: n = O(d²) qubits, k = 1 logical qubit\n', 'normal'),
                    ('• LDPC: n = O(d) qubits, k = Θ(n) logical qubits\n\n', 'normal'),
                    ('Result: ', 'normal'),
                    ('10-100x fewer qubits', 'warning'),
                    (' for same protection!', 'normal'),
                ],
                'demo_action': 'show_ldpc_concept'
            },
            # Step 6: Quantum LDPC Codes - Part 2 (Hypergraph Product)
            {
                'title': 'LDPC Construction: Hypergraph Product',
                'content': [
                    ('Building LDPC Codes', 'title'),
                    ('\n\n', 'normal'),
                    ('The ', 'normal'),
                    ('hypergraph product construction', 'ldpc'),
                    (' (Tillich-Zémor 2009):\n\n', 'normal'),
                    ('Recipe:', 'title'),
                    ('\n', 'normal'),
                    ('1. Start with classical LDPC code H\n', 'normal'),
                    ('2. Compute: HGP(H) = H ⊗ Iₙ + Iₘ ⊗ Hᵀ\n', 'normal'),
                    ('3. Get quantum code with X and Z checks!\n\n', 'normal'),
                    ('Structure on Grid:', 'title'),
                    ('\n', 'normal'),
                    ('• ', 'normal'),
                    ('Data qubits', 'qubit'),
                    (' (green): Store quantum information\n', 'normal'),
                    ('• ', 'normal'),
                    ('Parity checks', 'gate'),
                    (' (orange): X-type stabilizers\n', 'normal'),
                    ('• ', 'normal'),
                    ('Syndrome extractors', 'component'),
                    (' (teal): Z-type stabilizers\n\n', 'normal'),
                    ('Code Parameters:', 'title'),
                    ('\n', 'normal'),
                    ('   [[n, k, d]] where d = Θ(√n)\n', 'math'),
                    ('\n(Panteleev-Kalachev improved this to d = Θ(n)!)\n\n', 'normal'),
                    ('On the grid:', 'warning'),
                    (' See the hypergraph product structure!', 'normal'),
                ],
                'demo_action': 'show_hypergraph_product'
            },
            # Step 7: Quantum LDPC Codes - Part 3 (Syndrome Extraction)
            {
                'title': 'LDPC Syndrome Extraction',
                'content': [
                    ('Non-Local Syndrome Measurement', 'title'),
                    ('\n\n', 'normal'),
                    ('LDPC codes have a challenge: ', 'normal'),
                    ('non-local checks', 'warning'),
                    ('!\n\n', 'normal'),
                    ('The Problem:', 'title'),
                    ('\n', 'normal'),
                    ('• Checks connect distant qubits\n', 'normal'),
                    ('• Hardware usually has only local connectivity\n', 'normal'),
                    ('• Need clever solutions!\n\n', 'normal'),
                    ('Brennen et al. Solution:', 'title'),
                    (' Cavity-Mediated Gates\n\n', 'normal'),
                    ('Method:', 'title'),
                    ('\n', 'normal'),
                    ('1. ', 'normal'),
                    ('Ancilla preparation', 'qubit'),
                    (': |+⟩ state\n', 'normal'),
                    ('2. ', 'normal'),
                    ('CNOT sequence', 'gate'),
                    (': Ancilla → Data qubits\n', 'normal'),
                    ('3. ', 'normal'),
                    ('Measurement', 'component'),
                    (': Extract syndrome bit\n\n', 'normal'),
                    ('Circuit Pattern:', 'title'),
                    ('\n', 'normal'),
                    ('   Ancilla: |+⟩──●──●──●──M\n', 'math'),
                    ('                 │  │  │\n', 'math'),
                    ('   Data 1: ──────⊕──┼──┼──\n', 'math'),
                    ('   Data 2: ─────────⊕──┼──\n', 'math'),
                    ('   Data 3: ────────────⊕──\n\n', 'math'),
                    ('On the grid:', 'warning'),
                    (' See syndrome extraction in action!', 'normal'),
                ],
                'demo_action': 'show_syndrome_extraction'
            },
        ]
    
    def show(self):
        """Display the advanced tutorial window."""
        # Store original circuit state
        if self.circuit_builder:
            self.original_components = list(self.circuit_builder.components)
        
        self.tutorial_window = tk.Toplevel(self.parent)
        self.tutorial_window.title("Advanced Tutorial - Quantum LDPC Circuit Builder")
        self.tutorial_window.geometry("600x480")
        self.tutorial_window.configure(bg='#1a1a2e')
        self.tutorial_window.attributes('-topmost', False)
        
        # Position to the left of screen
        self.tutorial_window.update_idletasks()
        x = 50
        y = (self.tutorial_window.winfo_screenheight() - 480) // 2
        self.tutorial_window.geometry(f"600x480+{x}+{y}")
        
        # Main container
        self.main_frame = tk.Frame(self.tutorial_window, bg='#1a1a2e')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        self.header_frame = tk.Frame(self.main_frame, bg='#16213e')
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="", 
            font=('Segoe UI', 14, 'bold'),
            fg='#ff9f43',  # Orange for advanced
            bg='#16213e',
            pady=10
        )
        self.title_label.pack()
        
        # Step indicator
        self.step_label = tk.Label(
            self.header_frame,
            text="",
            font=('Segoe UI', 10),
            fg='#888888',
            bg='#16213e'
        )
        self.step_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_frame = tk.Frame(self.main_frame, bg='#1a1a2e', height=8)
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))
        self.progress_frame.pack_propagate(False)
        
        self.progress_bg = tk.Frame(self.progress_frame, bg='#2d2d44', height=8)
        self.progress_bg.pack(fill=tk.X)
        
        self.progress_bar = tk.Frame(self.progress_bg, bg='#ff9f43', height=8)
        self.progress_bar.place(x=0, y=0, relheight=1, relwidth=0)
        
        # Navigation - pack at bottom first
        self.nav_frame = tk.Frame(self.main_frame, bg='#1a1a2e')
        self.nav_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        # Close button
        self.close_btn = tk.Button(
            self.nav_frame,
            text="Close",
            font=('Segoe UI', 10),
            fg='#888888',
            bg='#2d2d44',
            activeforeground='#ffffff',
            activebackground='#3d3d54',
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2',
            command=self._close_tutorial
        )
        self.close_btn.pack(side=tk.LEFT)
        
        # Next button
        self.next_btn = tk.Button(
            self.nav_frame,
            text="Next →",
            font=('Segoe UI', 11, 'bold'),
            fg='#ffffff',
            bg='#ff9f43',
            activeforeground='#ffffff',
            activebackground='#ffb366',
            relief='flat',
            padx=25,
            pady=8,
            cursor='hand2',
            command=self._next_step
        )
        self.next_btn.pack(side=tk.RIGHT)
        
        # Previous button
        self.prev_btn = tk.Button(
            self.nav_frame,
            text="← Back",
            font=('Segoe UI', 10),
            fg='#cccccc',
            bg='#2d2d44',
            activeforeground='#ffffff',
            activebackground='#3d3d54',
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2',
            command=self._prev_step
        )
        self.prev_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg='#0f0f23', bd=1, relief='solid')
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.content_text = tk.Text(
            self.content_frame,
            font=('Consolas', 11),
            bg='#0f0f23',
            fg='#ffffff',
            wrap=tk.WORD,
            padx=20,
            pady=15,
            relief='flat',
            cursor='arrow',
            state='disabled'
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(self.content_frame, command=self.content_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.config(yscrollcommand=scrollbar.set)
        
        # Configure text tags
        for tag_name, color in self.COLORS.items():
            self.content_text.tag_configure(tag_name, foreground=color)
        self.content_text.tag_configure('normal', foreground='#cccccc')
        
        # Display first step
        self._update_display()
        
        # Handle window close
        self.tutorial_window.protocol("WM_DELETE_WINDOW", self._close_tutorial)
    
    def _update_display(self):
        """Update the display for the current step."""
        step_data = self.steps[self.current_step]
        
        # Update title
        self.title_label.config(text=step_data['title'])
        
        # Update step indicator
        self.step_label.config(text=f"Step {self.current_step + 1} of {len(self.steps)}")
        
        # Update progress bar
        progress = (self.current_step + 1) / len(self.steps)
        self.progress_bar.place(x=0, y=0, relheight=1, relwidth=progress)
        
        # Update content
        self.content_text.config(state='normal')
        self.content_text.delete('1.0', tk.END)
        
        for text, tag in step_data['content']:
            self.content_text.insert(tk.END, text, tag)
        
        self.content_text.config(state='disabled')
        
        # Update button states
        self.prev_btn.config(state='normal' if self.current_step > 0 else 'disabled')
        
        if self.current_step == len(self.steps) - 1:
            self.next_btn.config(text="Finish", bg='#27ae60')
        else:
            self.next_btn.config(text="Next →", bg='#ff9f43')
        
        # Execute demo action for this step
        if 'demo_action' in step_data:
            self._execute_demo(step_data['demo_action'])
    
    def _execute_demo(self, action: str):
        """Execute the demo action for the current step."""
        if not self.circuit_builder:
            return
        
        # Clear previous demo components
        self._clear_demo_components()
        
        if action == 'show_qubit_positions':
            self._demo_qubit_positions()
        elif action == 'show_operator_interaction':
            self._demo_operator_interaction()
        elif action == 'show_gate_comparison':
            self._demo_gate_comparison()
        elif action == 'show_repetition_code':
            self._demo_repetition_code()
        elif action == 'show_surface_code':
            self._demo_surface_code()
        elif action == 'show_ldpc_concept':
            self._demo_ldpc_concept()
        elif action == 'show_hypergraph_product':
            self._demo_hypergraph_product()
        elif action == 'show_syndrome_extraction':
            self._demo_syndrome_extraction()
    
    def _demo_qubit_positions(self):
        """Demonstrate qubit positioning on the grid."""
        # Place data qubits at different positions to show grid usage
        demo_specs = [
            (ComponentType.DATA_QUBIT, (0, 0, 0)),   # Origin
            (ComponentType.DATA_QUBIT, (0, 2, 0)),   # Different Y (lane)
            (ComponentType.DATA_QUBIT, (0, 4, 0)),   # Another lane
            (ComponentType.ANCILLA_QUBIT, (2, 1, 0)), # Ancilla for contrast
        ]
        self._place_demo_components(demo_specs)
        self.circuit_builder._log_status("Demo: Qubits placed at grid positions (0,0), (0,2), (0,4), and ancilla at (2,1)")
    
    def _demo_operator_interaction(self):
        """Demonstrate how operators interact with qubits."""
        # Show a qubit followed by gates in the same lane
        demo_specs = [
            (ComponentType.DATA_QUBIT, (0, 0, 0)),   # Qubit at start
            (ComponentType.H_GATE, (1, 0, 0)),       # H gate acts on it
            (ComponentType.X_GATE, (2, 0, 0)),       # X gate next
            (ComponentType.MEASURE, (3, 0, 0)),      # Measurement
            # Second lane for comparison
            (ComponentType.DATA_QUBIT, (0, 2, 0)),   # Another qubit
            (ComponentType.Z_GATE, (1, 2, 0)),       # Z gate
        ]
        self._place_demo_components(demo_specs)
        self.circuit_builder._log_status("Demo: Gates operate on qubits in the same lane (Y coordinate)")
    
    def _demo_gate_comparison(self):
        """Demonstrate the difference between single and two-qubit gates."""
        # Place single-qubit gates and two-qubit gates for comparison
        demo_specs = [
            # Lane 0 & 1: Two-qubit gate demo
            (ComponentType.DATA_QUBIT, (0, 0, 0)),
            (ComponentType.DATA_QUBIT, (0, 1, 0)),
            (ComponentType.CNOT_GATE, (1, 0, 0)),    # CNOT spans lanes 0-1
            # Lane 3: Single-qubit gate demo
            (ComponentType.DATA_QUBIT, (0, 3, 0)),
            (ComponentType.X_GATE, (1, 3, 0)),       # Single X gate
            (ComponentType.H_GATE, (2, 3, 0)),       # Single H gate
        ]
        self._place_demo_components(demo_specs)
        
        # Mark two-qubit gates visually
        self._highlight_two_qubit_gates()
        
        self.circuit_builder._log_status("Demo: Compare CNOT (two-qubit, taller) vs X/H gates (single-qubit, standard)")
    
    def _highlight_two_qubit_gates(self):
        """Add visual distinction to two-qubit gates."""
        if not self.circuit_builder:
            return
        
        # Mark two-qubit gates with a special property for rendering
        two_qubit_types = [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]
        
        for comp in self.circuit_builder.components:
            if comp.component_type in two_qubit_types:
                # Add a glow property for visual distinction
                comp.properties['two_qubit_highlight'] = True
                # Two-qubit gates span 2 lanes (depth=2)
                comp.size = (1.0, 1.0, 2.0)
        
        self.circuit_builder._redraw_circuit()
    
    def _demo_repetition_code(self):
        """Demonstrate the 3-qubit bit-flip repetition code."""
        # 3-qubit repetition code: |ψ⟩ → |ψψψ⟩
        # q0 is the original, CNOT copies to q1 and q2
        demo_specs = [
            # Three data qubits (lanes 0, 1, 2)
            (ComponentType.DATA_QUBIT, (0, 0, 0)),   # q0 - original qubit
            (ComponentType.DATA_QUBIT, (0, 1, 0)),   # q1 - copy target
            (ComponentType.DATA_QUBIT, (0, 2, 0)),   # q2 - copy target
            # CNOT from q0 to q1 (control at y=0, spans to y=1)
            (ComponentType.CNOT_GATE, (1, 0, 0)),
            # CNOT from q0 to q2 (control at y=0, spans to y=1, but we show at y=1 to y=2)
            (ComponentType.CNOT_GATE, (2, 1, 0)),
            # Parity checks for error detection
            (ComponentType.PARITY_CHECK, (3, 0, 0)),
            (ComponentType.PARITY_CHECK, (3, 1, 0)),
        ]
        self._place_demo_components(demo_specs)
        self.circuit_builder._log_status("Demo: 3-qubit repetition code - CNOT gates copy qubit state, parity checks detect errors")
    
    def _demo_surface_code(self):
        """Demonstrate a small surface code patch."""
        # 3x3 surface code layout
        # D = Data qubit (vertices), A = Ancilla (faces for X-checks)
        # Pattern: D-A-D / A-D-A / D-A-D
        demo_specs = [
            # Row 0: D-A-D
            (ComponentType.DATA_QUBIT, (0, 0, 0)),
            (ComponentType.ANCILLA_QUBIT, (0, 1, 0)),
            (ComponentType.DATA_QUBIT, (0, 2, 0)),
            # Row 1: A-D-A
            (ComponentType.ANCILLA_QUBIT, (1, 0, 0)),
            (ComponentType.DATA_QUBIT, (1, 1, 0)),
            (ComponentType.ANCILLA_QUBIT, (1, 2, 0)),
            # Row 2: D-A-D
            (ComponentType.DATA_QUBIT, (2, 0, 0)),
            (ComponentType.ANCILLA_QUBIT, (2, 1, 0)),
            (ComponentType.DATA_QUBIT, (2, 2, 0)),
            # Add measurement at the end
            (ComponentType.MEASURE, (3, 1, 0)),
        ]
        self._place_demo_components(demo_specs)
        self.circuit_builder._log_status("Demo: 3x3 Surface code patch - Data qubits (green) on vertices, Ancillas (yellow-green) on faces")
    
    def _demo_ldpc_concept(self):
        """Demonstrate LDPC code concept with sparse connectivity."""
        # Show sparse parity check structure
        # Data qubits with few parity checks each connecting to few data qubits
        demo_specs = [
            # 4 Data qubits
            (ComponentType.DATA_QUBIT, (0, 0, 0)),
            (ComponentType.DATA_QUBIT, (0, 2, 0)),
            (ComponentType.DATA_QUBIT, (0, 4, 0)),
            (ComponentType.DATA_QUBIT, (0, 6, 0)),
            # Sparse parity checks (each touches only 2-3 data qubits)
            (ComponentType.PARITY_CHECK, (1, 1, 0)),   # Check between q0, q1
            (ComponentType.PARITY_CHECK, (1, 3, 0)),   # Check between q1, q2
            (ComponentType.PARITY_CHECK, (1, 5, 0)),   # Check between q2, q3
            # Syndrome extraction
            (ComponentType.SYNDROME_EXTRACT, (2, 1, 0)),
            (ComponentType.SYNDROME_EXTRACT, (2, 3, 0)),
            (ComponentType.SYNDROME_EXTRACT, (2, 5, 0)),
        ]
        self._place_demo_components(demo_specs)
        self.circuit_builder._log_status("Demo: LDPC structure - sparse checks (orange) connect few data qubits (green)")
    
    def _demo_hypergraph_product(self):
        """Demonstrate hypergraph product LDPC code structure."""
        # Hypergraph product creates a 2D structure from 1D classical codes
        # Show the tensor product structure
        demo_specs = [
            # Data qubits in a grid pattern (represents n = n1 × n2)
            (ComponentType.DATA_QUBIT, (0, 0, 0)),
            (ComponentType.DATA_QUBIT, (0, 2, 0)),
            (ComponentType.DATA_QUBIT, (0, 4, 0)),
            (ComponentType.DATA_QUBIT, (2, 0, 0)),
            (ComponentType.DATA_QUBIT, (2, 2, 0)),
            (ComponentType.DATA_QUBIT, (2, 4, 0)),
            # X-type checks (horizontal)
            (ComponentType.PARITY_CHECK, (1, 0, 0)),
            (ComponentType.PARITY_CHECK, (1, 2, 0)),
            (ComponentType.PARITY_CHECK, (1, 4, 0)),
            # Z-type checks (vertical) - use syndrome extract
            (ComponentType.SYNDROME_EXTRACT, (0, 1, 0)),
            (ComponentType.SYNDROME_EXTRACT, (0, 3, 0)),
            (ComponentType.SYNDROME_EXTRACT, (2, 1, 0)),
            (ComponentType.SYNDROME_EXTRACT, (2, 3, 0)),
            # Ancillas for measurement
            (ComponentType.ANCILLA_QUBIT, (3, 1, 0)),
            (ComponentType.ANCILLA_QUBIT, (3, 3, 0)),
        ]
        self._place_demo_components(demo_specs)
        self.circuit_builder._log_status("Demo: Hypergraph product - Data (green), X-checks (orange), Z-checks (teal)")
    
    def _demo_syndrome_extraction(self):
        """Demonstrate LDPC syndrome extraction circuit."""
        # DiVincenzo-Aliferis style syndrome extraction
        # Ancilla prepared in |+⟩, then CNOT to each data qubit, then measure
        demo_specs = [
            # Ancilla qubit (prepared in |+⟩)
            (ComponentType.ANCILLA_QUBIT, (0, 0, 0)),
            (ComponentType.H_GATE, (1, 0, 0)),  # H gate creates |+⟩
            # Data qubits that this check covers
            (ComponentType.DATA_QUBIT, (0, 2, 0)),
            (ComponentType.DATA_QUBIT, (0, 4, 0)),
            (ComponentType.DATA_QUBIT, (0, 6, 0)),
            # CNOT gates from ancilla to each data qubit
            # Note: In real LDPC, these would be non-local (cavity-mediated)
            (ComponentType.CNOT_GATE, (2, 0, 0)),  # Ancilla to Data1
            (ComponentType.CNOT_GATE, (3, 2, 0)),  # To Data2
            (ComponentType.CNOT_GATE, (4, 4, 0)),  # To Data3
            # Measurement of ancilla
            (ComponentType.MEASURE, (5, 0, 0)),
            # Syndrome result
            (ComponentType.SYNDROME_EXTRACT, (6, 0, 0)),
        ]
        self._place_demo_components(demo_specs)
        self.circuit_builder._log_status("Demo: Syndrome extraction - Ancilla (yellow-green) + H + CNOTs to data qubits + Measure")

    def _place_demo_components(self, specs: List[Tuple]):
        """Place demo components on the grid."""
        two_qubit_types = [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]
        
        for comp_type, position in specs:
            # Check if position is free
            occupied = any(c.position == position for c in self.circuit_builder.components)
            
            if not occupied:
                color = self.circuit_builder._get_component_color(comp_type)
                # Two-qubit gates span 2 Y positions
                if comp_type in two_qubit_types:
                    size = (1.0, 1.0, 2.0)  # (width, height, depth) - depth=2 for Y direction
                else:
                    size = (1.0, 1.0, 1.0)
                component = Component3D(
                    component_type=comp_type,
                    position=position,
                    color=color,
                    size=size
                )
                self.circuit_builder.components.append(component)
                self.demo_components.append(component)
        
        self.circuit_builder._redraw_circuit()
    
    def _clear_demo_components(self):
        """Remove all demo components."""
        if not self.circuit_builder:
            return
        
        for comp in self.demo_components:
            if comp in self.circuit_builder.components:
                self.circuit_builder.components.remove(comp)
        
        self.demo_components = []
        self.circuit_builder._redraw_circuit()
    
    def _next_step(self):
        """Go to the next step or finish."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._update_display()
        else:
            self._close_tutorial()
    
    def _prev_step(self):
        """Go to the previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_display()
    
    def _close_tutorial(self):
        """Close the tutorial and clean up."""
        # Remove demo components
        self._clear_demo_components()
        
        # Reset any modified component properties (but preserve correct sizes)
        if self.circuit_builder:
            two_qubit_types = [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]
            for comp in self.circuit_builder.components:
                # Restore correct size based on gate type
                if comp.component_type in two_qubit_types:
                    comp.size = (1.0, 1.0, 2.0)  # Two-qubit gates span 2 Y lanes
                else:
                    comp.size = (1.0, 1.0, 1.0)
                if 'two_qubit_highlight' in comp.properties:
                    del comp.properties['two_qubit_highlight']
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("Advanced tutorial closed.")
        
        self.tutorial_window.destroy()


class ComponentType(Enum):
    """Enumeration of available quantum circuit components."""
    
    # Single qubit gates
    X_GATE = "X"
    Z_GATE = "Z"
    Y_GATE = "Y"
    H_GATE = "H"
    S_GATE = "S"
    T_GATE = "T"
    
    # Two qubit gates
    CNOT_GATE = "CNOT"
    CZ_GATE = "CZ"
    SWAP_GATE = "SWAP"
    
    # LDPC specific components
    PARITY_CHECK = "Parity Check"
    DATA_QUBIT = "Data Qubit"
    ANCILLA_QUBIT = "Ancilla"
    SYNDROME_EXTRACT = "Syndrome"
    
    # Measurement and reset
    MEASURE = "Measure"
    RESET = "Reset"


@dataclass
class Component3D:
    """
    Represents a 3D quantum circuit component with position and properties.
    
    Attributes:
        component_type: Type of quantum component
        position: (x, y, z) grid coordinates
        rotation: Rotation angle in degrees
        size: (width, height, depth) in grid units
        color: RGB color tuple for rendering
        connections: List of connected component IDs
        properties: Component-specific properties dictionary
    """
    
    component_type: ComponentType
    position: Tuple[int, int, int]
    rotation: float = 0.0
    size: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    color: Tuple[float, float, float] = (0.5, 0.5, 0.8)
    connections: List[int] = None
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.connections is None:
            self.connections = []
        if self.properties is None:
            self.properties = {}


class IsometricRenderer:
    """
    Handles 2.5D isometric rendering of 3D components on a tkinter canvas.
    
    This class provides methods to convert 3D coordinates to 2D isometric
    projections and render quantum circuit components as 3D blocks.
    """
    
    def __init__(self, canvas: tk.Canvas, scale: float = 30.0):
        """
        Initialize the isometric renderer.
        
        Args:
            canvas: tkinter Canvas widget for rendering
            scale: Scaling factor for isometric projection
        """
        self.canvas = canvas
        self.scale = scale
        self.offset_x = 400  # Moved grid more to the right
        self.offset_y = 200  # Moved grid down
        
        # Isometric projection angles (30 degrees)
        self.cos_30 = math.cos(math.radians(30))
        self.sin_30 = math.sin(math.radians(30))
    
    def project_3d_to_2d(self, x: float, y: float, z: float) -> Tuple[float, float]:
        """
        Convert 3D coordinates to 2D isometric projection.
        
        Args:
            x, y, z: 3D coordinates
            
        Returns:
            Tuple of 2D screen coordinates
        """
        iso_x = (x - y) * self.cos_30 * self.scale + self.offset_x
        iso_y = (x + y) * self.sin_30 * self.scale - z * self.scale + self.offset_y
        return iso_x, iso_y
    
    def draw_cube(self, x: float, y: float, z: float, 
                  width: float, height: float, depth: float,
                  color: Tuple[float, float, float], 
                  outline: str = "#333333") -> List[int]:
        """
        Draw a 3D cube using isometric projection.
        
        In this isometric projection:
        - +x axis goes to the lower-right
        - +y axis goes to the lower-left  
        - +z axis goes straight up
        
        Args:
            x, y, z: Bottom-left-front corner position
            width, height, depth: Cube dimensions (width=x, height=z, depth=y)
            color: RGB color tuple (0-1 range)
            outline: Outline color hex string
            
        Returns:
            List of canvas item IDs for the rendered cube
        """
        # Define cube vertices
        vertices = [
            (x, y, z),                          # 0: bottom-front-left
            (x + width, y, z),                  # 1: bottom-front-right
            (x + width, y + depth, z),          # 2: bottom-back-right
            (x, y + depth, z),                  # 3: bottom-back-left
            (x, y, z + height),                 # 4: top-front-left
            (x + width, y, z + height),         # 5: top-front-right
            (x + width, y + depth, z + height), # 6: top-back-right
            (x, y + depth, z + height)          # 7: top-back-left
        ]
        
        # Project vertices to 2D
        projected = [self.project_3d_to_2d(*v) for v in vertices]
        
        items = []
        
        # Draw all 6 faces from back to front (Painter's Algorithm)
        
        # Bottom face (darkest)
        bottom_color = self._brighten_color(color, 0.5)
        bottom_hex = self._rgb_to_hex(bottom_color)
        items.append(self.canvas.create_polygon(
            projected[0][0], projected[0][1],
            projected[1][0], projected[1][1],
            projected[2][0], projected[2][1],
            projected[3][0], projected[3][1],
            fill=bottom_hex, outline=outline, width=1
        ))
        
        # Back-right face
        back_right_color = self._brighten_color(color, 0.6)
        back_right_hex = self._rgb_to_hex(back_right_color)
        items.append(self.canvas.create_polygon(
            projected[2][0], projected[2][1],
            projected[3][0], projected[3][1],
            projected[7][0], projected[7][1],
            projected[6][0], projected[6][1],
            fill=back_right_hex, outline=outline, width=1
        ))
        
        # Back-left face
        back_left_color = self._brighten_color(color, 0.55)
        back_left_hex = self._rgb_to_hex(back_left_color)
        items.append(self.canvas.create_polygon(
            projected[1][0], projected[1][1],
            projected[2][0], projected[2][1],
            projected[6][0], projected[6][1],
            projected[5][0], projected[5][1],
            fill=back_left_hex, outline=outline, width=1
        ))
        
        # Left face (front-left)
        left_color = self._brighten_color(color, 0.7)
        left_hex = self._rgb_to_hex(left_color)
        items.append(self.canvas.create_polygon(
            projected[0][0], projected[0][1],
            projected[3][0], projected[3][1],
            projected[7][0], projected[7][1],
            projected[4][0], projected[4][1],
            fill=left_hex, outline=outline, width=1
        ))
        
        # Right face (front-right)
        right_color = self._brighten_color(color, 0.85)
        right_hex = self._rgb_to_hex(right_color)
        items.append(self.canvas.create_polygon(
            projected[0][0], projected[0][1],
            projected[1][0], projected[1][1],
            projected[5][0], projected[5][1],
            projected[4][0], projected[4][1],
            fill=right_hex, outline=outline, width=1
        ))
        
        # Top face (lightest)
        top_color = self._brighten_color(color, 1.1)
        top_hex = self._rgb_to_hex(top_color)
        items.append(self.canvas.create_polygon(
            projected[4][0], projected[4][1],
            projected[5][0], projected[5][1],
            projected[6][0], projected[6][1],
            projected[7][0], projected[7][1],
            fill=top_hex, outline=outline, width=1
        ))
        
        return items
    
    def _rgb_to_hex(self, color: Tuple[float, float, float]) -> str:
        """Convert RGB tuple (0-1 range) to hex color string."""
        r, g, b = [int(c * 255) for c in color]
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _brighten_color(self, color: Tuple[float, float, float], factor: float) -> Tuple[float, float, float]:
        """Brighten or darken a color by a given factor."""
        return tuple(min(1.0, c * factor) for c in color)


class QuantumLDPCProcessor:
    """
    Handles quantum LDPC computations for real-time circuit analysis.
    
    This class processes the built quantum circuits and performs:
    - Syndrome calculation
    - Error correction decoding
    - Quantum state evolution
    """
    
    def __init__(self):
        """Initialize the quantum processor."""
        self.circuit = None
        self.current_state = None
        self.syndrome_history = []
        self.error_corrections = []
    
    def build_circuit_from_components(self, components: List[Component3D]) -> Optional[QuantumCircuit]:
        """
        Build a Qiskit quantum circuit from placed components.
        
        Args:
            components: List of placed 3D components
            
        Returns:
            Constructed QuantumCircuit or None if build fails
        """
        if not QISKIT_AVAILABLE:
            return self._simulate_circuit_build(components)
        
        try:
            # Determine circuit size from component positions
            qubit_positions = [comp.position[1] for comp in components 
                             if comp.component_type in [ComponentType.DATA_QUBIT, ComponentType.ANCILLA_QUBIT]]
            
            if not qubit_positions:
                # No qubits found, use maximum y-position from all components
                max_qubit = max([comp.position[1] for comp in components if comp.position[1] >= 0], default=0)
            else:
                max_qubit = max(qubit_positions)
            
            num_qubits = max_qubit + 1
            
            # Create circuit
            qreg = QuantumRegister(num_qubits, 'q')
            creg = ClassicalRegister(num_qubits, 'c')
            circuit = QuantumCircuit(qreg, creg)
            
            # Sort components by x-position for temporal ordering
            sorted_components = sorted(components, key=lambda c: c.position[0])
            
            for comp in sorted_components:
                qubit_idx = comp.position[1]
                if qubit_idx < 0 or qubit_idx >= num_qubits:
                    continue
                
                self._add_component_to_circuit(circuit, comp, qreg, creg)
            
            self.circuit = circuit
            return circuit
            
        except Exception as e:
            print(f"Error building circuit: {e}")
            return None
    
    def _add_component_to_circuit(self, circuit: QuantumCircuit, 
                                 component: Component3D,
                                 qreg: QuantumRegister, 
                                 creg: ClassicalRegister):
        """Add a single component to the quantum circuit."""
        comp_type = component.component_type
        qubit = component.position[1]
        
        if comp_type == ComponentType.X_GATE:
            circuit.x(qreg[qubit])
        elif comp_type == ComponentType.Z_GATE:
            circuit.z(qreg[qubit])
        elif comp_type == ComponentType.Y_GATE:
            circuit.y(qreg[qubit])
        elif comp_type == ComponentType.H_GATE:
            circuit.h(qreg[qubit])
        elif comp_type == ComponentType.S_GATE:
            circuit.s(qreg[qubit])
        elif comp_type == ComponentType.T_GATE:
            circuit.t(qreg[qubit])
        elif comp_type == ComponentType.CNOT_GATE:
            # For CNOT, use adjacent qubit as control if no specific connection
            if component.connections and len(component.connections) > 0:
                control_qubit = component.connections[0]
                if 0 <= control_qubit < len(qreg) and control_qubit != qubit:
                    circuit.cx(qreg[control_qubit], qreg[qubit])
            else:
                # Default: use qubit-1 as control if it exists and is different
                control_qubit = max(0, qubit - 1)
                if control_qubit != qubit and control_qubit < len(qreg):
                    circuit.cx(qreg[control_qubit], qreg[qubit])
        elif comp_type == ComponentType.CZ_GATE:
            # Similar logic for CZ gate
            if component.connections and len(component.connections) > 0:
                control_qubit = component.connections[0]
                if 0 <= control_qubit < len(qreg) and control_qubit != qubit:
                    circuit.cz(qreg[control_qubit], qreg[qubit])
            else:
                control_qubit = max(0, qubit - 1)
                if control_qubit != qubit and control_qubit < len(qreg):
                    circuit.cz(qreg[control_qubit], qreg[qubit])
        elif comp_type == ComponentType.MEASURE:
            circuit.measure(qreg[qubit], creg[qubit])
        elif comp_type == ComponentType.RESET:
            circuit.reset(qreg[qubit])
    
    def _simulate_circuit_build(self, components: List[Component3D]) -> Dict[str, Any]:
        """Simulate circuit building when Qiskit is not available."""
        return {
            'num_qubits': len(set(comp.position[1] for comp in components)),
            'num_gates': len(components),
            'depth': max([comp.position[0] for comp in components], default=0) + 1
        }
    
    def calculate_syndrome(self, components: List[Component3D]) -> np.ndarray:
        """
        Calculate syndrome for current circuit configuration.
        
        Args:
            components: List of placed components
            
        Returns:
            Syndrome vector as numpy array
        """
        # Extract components - use ancilla qubits as syndrome extractors if no parity checks
        parity_checks = [c for c in components if c.component_type == ComponentType.PARITY_CHECK]
        ancilla_qubits = [c for c in components if c.component_type == ComponentType.ANCILLA_QUBIT]
        syndrome_extractors = [c for c in components if c.component_type == ComponentType.SYNDROME_EXTRACT]
        data_qubits = [c for c in components if c.component_type == ComponentType.DATA_QUBIT]
        
        # Use ancilla qubits as syndrome extractors if no dedicated parity checks
        if not parity_checks and ancilla_qubits:
            parity_checks = ancilla_qubits
        elif syndrome_extractors:
            parity_checks.extend(syndrome_extractors)
        
        if not parity_checks or not data_qubits:
            return np.array([])
        
        # Build parity check matrix
        num_checks = len(parity_checks)
        num_data = len(data_qubits)
        
        parity_matrix = np.zeros((num_checks, num_data), dtype=int)
        
        # Simulate connections between parity checks and data qubits
        for i, check in enumerate(parity_checks):
            for j, data in enumerate(data_qubits):
                # Simple distance-based connection rule
                distance = abs(check.position[0] - data.position[0]) + abs(check.position[1] - data.position[1])
                if distance <= 2:  # Connect if within Manhattan distance 2
                    parity_matrix[i, j] = 1
        
        # Check if we have any connections
        if np.sum(parity_matrix) == 0:
            # If no automatic connections, create a simple pattern
            for i in range(min(num_checks, num_data)):
                parity_matrix[i, i] = 1
                if i + 1 < num_data:
                    parity_matrix[i, i + 1] = 1
        
        # Simulate error vector (random for demonstration)
        error_vector = np.random.randint(0, 2, size=num_data)
        
        # Calculate syndrome
        syndrome = np.dot(parity_matrix, error_vector) % 2
        
        self.syndrome_history.append(syndrome.copy())
        return syndrome
    
    def perform_error_correction(self, syndrome: np.ndarray, components: List[Component3D]) -> Dict[str, Any]:
        """
        Perform belief propagation decoding for error correction.
        
        Args:
            syndrome: Current syndrome vector
            components: List of circuit components
            
        Returns:
            Dictionary with correction results
        """
        if len(syndrome) == 0:
            return {'success': False, 'error': 'No syndrome available'}
        
        # Count data qubits
        data_qubits = [c for c in components if c.component_type == ComponentType.DATA_QUBIT]
        num_bits = len(data_qubits)
        
        if num_bits == 0:
            return {'success': False, 'error': 'No data qubits found'}
        
        # Simple belief propagation simulation
        max_iterations = 10
        convergence_threshold = 1e-6
        
        # Initialize belief probabilities
        beliefs = np.ones(num_bits) * 0.5  # Initial probability of error
        
        correction_history = []
        
        for iteration in range(max_iterations):
            old_beliefs = beliefs.copy()
            
            # Update beliefs based on syndrome constraints
            # (Simplified belief propagation)
            if len(syndrome) > 0:
                syndrome_weight = np.sum(syndrome) / len(syndrome)
                # Adjust beliefs based on syndrome weight
                for i in range(num_bits):
                    # Simple heuristic: if syndrome indicates errors, increase error probability
                    if syndrome_weight > 0.5:
                        beliefs[i] = min(0.9, beliefs[i] + syndrome_weight * 0.2)
                    else:
                        beliefs[i] = max(0.1, beliefs[i] - (1 - syndrome_weight) * 0.1)
            
            beliefs = np.clip(beliefs, 0.01, 0.99)
            correction_history.append(beliefs.copy())
            
            # Check convergence
            if np.linalg.norm(beliefs - old_beliefs) < convergence_threshold:
                break
        
        # Determine correction
        correction = (beliefs > 0.5).astype(int)
        
        result = {
            'success': True,
            'correction': correction,
            'beliefs': beliefs,
            'iterations': iteration + 1,
            'history': correction_history,
            'syndrome_weight': np.sum(syndrome),
            'num_data_qubits': num_bits
        }
        
        self.error_corrections.append(result)
        return result


class CircuitBuilder3D:
    """
    Main application class for the 3D Quantum LDPC Circuit Builder.
    
    This class manages the GUI, user interactions, and coordinates between
    the rendering system and quantum computation backend.
    """
    
    def __init__(self):
        """Initialize the circuit builder application."""
        self.root = self._setup_gui()
        self.components = []
        self.selected_component = None
        self.component_counter = 0
        self.grid_size = 20
        self.current_tool = ComponentType.DATA_QUBIT
        
        # Rendering and computation
        self.renderer = None
        self.processor = QuantumLDPCProcessor()
        
        # Drag and drop state
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_component = None
        
        # Grid panning state
        self.panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        self._setup_ui()
        self._bind_events()
    
    def _setup_gui(self) -> tk.Tk:
        """Set up the main GUI window with dark theme."""
        root = tk.Tk()
        root.title("Quantum LDPC Circuit Builder 3D")
        root.geometry("1400x900")
        root.configure(bg='#2b2b2b')
        
        # Configure dark theme style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Dark theme colors
        style.configure('Dark.TFrame', background='#2b2b2b')
        style.configure('Dark.TLabel', background='#2b2b2b', foreground='#ffffff')
        style.configure('Dark.TLabelframe', background='#2b2b2b', foreground='#ffffff', 
                       borderwidth=1, relief='solid')
        style.configure('Dark.TLabelframe.Label', background='#2b2b2b', foreground='#ffffff',
                       font=('TkDefaultFont', 9, 'bold'))
        style.configure('Dark.TButton', background='#404040', foreground='#ffffff')
        style.configure('Dark.TNotebook', background='#2b2b2b')
        style.configure('Dark.TNotebook.Tab', background='#404040', foreground='#ffffff')
        
        return root
    
    def _setup_ui(self):
        """Set up the user interface components."""
        # Clear any existing widgets first
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Circuit building area
        left_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Circuit canvas
        self.canvas = tk.Canvas(left_frame, bg='#1e1e1e', highlightthickness=1, 
                               highlightbackground='#404040')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initialize renderer
        self.renderer = IsometricRenderer(self.canvas)
        
        # Right panel - Controls and toolbox
        right_frame = ttk.Frame(main_frame, style='Dark.TFrame', width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)
        
        self._setup_toolbox(right_frame)
        self._setup_controls(right_frame)
        self._setup_help(right_frame)
        self._setup_status(right_frame)
        
        # Draw initial grid
        self._draw_grid()
    
    def _setup_toolbox(self, parent):
        """Set up the component toolbox."""
        # Use a simple Frame instead of LabelFrame to avoid text duplication
        toolbox_container = ttk.Frame(parent, style='Dark.TFrame')
        toolbox_container.pack(fill=tk.X, padx=5, pady=5)
        
        # Add a simple label for the title
        toolbox_label = ttk.Label(toolbox_container, text="Component Toolbox", 
                                style='Dark.TLabel', font=('TkDefaultFont', 9, 'bold'))
        toolbox_label.pack(anchor=tk.W, padx=5, pady=(5, 2))
        
        # Add a separator line
        separator = ttk.Separator(toolbox_container, orient='horizontal')
        separator.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Component categories (short tab names for better UI)
        categories = {
            "Single": [
                ComponentType.X_GATE, ComponentType.Z_GATE, ComponentType.Y_GATE,
                ComponentType.H_GATE, ComponentType.S_GATE, ComponentType.T_GATE
            ],
            "Double": [
                ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE
            ],
            "LDPC": [
                ComponentType.PARITY_CHECK, ComponentType.DATA_QUBIT, 
                ComponentType.ANCILLA_QUBIT, ComponentType.SYNDROME_EXTRACT
            ],
            "Measure": [
                ComponentType.MEASURE, ComponentType.RESET
            ]
        }
        
        # Create notebook for categories
        notebook = ttk.Notebook(toolbox_container, style='Dark.TNotebook')
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        for category, components in categories.items():
            tab_frame = ttk.Frame(notebook, style='Dark.TFrame')
            notebook.add(tab_frame, text=category)
            
            for i, comp_type in enumerate(components):
                btn = ttk.Button(tab_frame, text=comp_type.value,
                               command=lambda ct=comp_type: self._select_tool(ct),
                               style='Dark.TButton')
                btn.pack(fill=tk.X, padx=2, pady=1)
    
    def _setup_controls(self, parent):
        """Set up control buttons and options."""
        # Use a simple Frame instead of LabelFrame to avoid text duplication
        controls_container = ttk.Frame(parent, style='Dark.TFrame')
        controls_container.pack(fill=tk.X, padx=5, pady=5)
        
        # Add a simple label for the title
        controls_label = ttk.Label(controls_container, text="Controls", 
                                 style='Dark.TLabel', font=('TkDefaultFont', 9, 'bold'))
        controls_label.pack(anchor=tk.W, padx=5, pady=(5, 2))
        
        # Add a separator line
        separator = ttk.Separator(controls_container, orient='horizontal')
        separator.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Circuit operations
        ttk.Button(controls_container, text="Clear Circuit",
                  command=self._clear_circuit, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(controls_container, text="Save Circuit",
                  command=self._save_circuit, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(controls_container, text="Load Circuit",
                  command=self._load_circuit, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=2)
        
        # Separator
        ttk.Separator(controls_container, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        
        # Quantum operations
        ttk.Button(controls_container, text="Calculate Syndrome",
                  command=self._calculate_syndrome, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(controls_container, text="Run Error Correction",
                  command=self._run_error_correction, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(controls_container, text="Simulate Evolution",
                  command=self._simulate_evolution, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=2)
    
    def _setup_help(self, parent):
        """Set up help section with tutorial and legend."""
        help_container = ttk.Frame(parent, style='Dark.TFrame')
        help_container.pack(fill=tk.X, padx=5, pady=5)
        
        # Add a simple label for the title
        help_label = ttk.Label(help_container, text="Help", 
                              style='Dark.TLabel', font=('TkDefaultFont', 9, 'bold'))
        help_label.pack(anchor=tk.W, padx=5, pady=(5, 2))
        
        # Add a separator line
        separator = ttk.Separator(help_container, orient='horizontal')
        separator.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Button(help_container, text="Show Tutorial",
                  command=self._show_tutorial, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(help_container, text="Advanced Tutorial",
                  command=self._show_advanced_tutorial, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(help_container, text="Component Legend",
                  command=self._toggle_legend, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=2)
    
    def _setup_status(self, parent):
        """Set up status display area."""
        # Circuit title display
        title_container = ttk.Frame(parent, style='Dark.TFrame')
        title_container.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        title_label = ttk.Label(title_container, text="Current Circuit:", 
                              style='Dark.TLabel', font=('TkDefaultFont', 8))
        title_label.pack(anchor=tk.W, padx=5)
        
        self.circuit_title_label = ttk.Label(title_container, text="New Circuit", 
                                           style='Dark.TLabel', font=('TkDefaultFont', 10, 'bold'),
                                           foreground='#00ff88')
        self.circuit_title_label.pack(anchor=tk.W, padx=5)
        
        # Add separator
        separator = ttk.Separator(title_container, orient='horizontal')
        separator.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        # Use a simple Frame instead of LabelFrame to avoid text duplication
        status_container = ttk.Frame(parent, style='Dark.TFrame')
        status_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add a simple label for the title
        status_label = ttk.Label(status_container, text="Status", 
                               style='Dark.TLabel', font=('TkDefaultFont', 9, 'bold'))
        status_label.pack(anchor=tk.W, padx=5, pady=(5, 2))
        
        # Add a separator line
        separator = ttk.Separator(status_container, orient='horizontal')
        separator.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Status text container
        text_container = ttk.Frame(status_container, style='Dark.TFrame')
        text_container.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Status text
        self.status_text = tk.Text(text_container, height=6, bg='#1e1e1e', fg='#ffffff',
                                  insertbackground='#ffffff', selectbackground='#404040')
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(text_container, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        self._log_status("Circuit Builder initialized. Select a component and click to place.")
    
    def _format_circuit_title(self, filename):
        """Format a filename into a clean circuit title."""
        if not filename:
            return "New Circuit"
        
        # Remove file extension
        name = filename
        if name.endswith('.json'):
            name = name[:-5]
        
        # Replace underscores with spaces and capitalize words
        name = name.replace('_', ' ')
        
        # Capitalize each word
        words = name.split()
        formatted_words = []
        for word in words:
            if word:  # Skip empty strings
                formatted_words.append(word.capitalize())
        
        return ' '.join(formatted_words) if formatted_words else "New Circuit"
    
    def _update_circuit_title(self, title):
        """Update the circuit title display."""
        if hasattr(self, 'circuit_title_label'):
            self.circuit_title_label.config(text=title)
    
    def _bind_events(self):
        """Bind mouse and keyboard events."""
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Button-2>", self._on_middle_click)  # Middle mouse for panning
        self.canvas.bind("<B2-Motion>", self._on_pan_drag)
        self.canvas.bind("<ButtonRelease-2>", self._on_pan_release)
        self.root.bind("<Delete>", self._delete_selected)
        self.root.bind("<Control-c>", self._copy_selected)
        self.root.bind("<Control-v>", self._paste_component)
    
    def _draw_grid(self):
        """Draw the isometric grid for component placement."""
        self.canvas.delete("grid")
        
        # Use lighter colors for better contrast against dark background
        grid_color = "#505050"      # Medium gray for grid lines
        boundary_color = "#707070"  # Brighter for boundaries
        grid_range = 10  # Match the grid boundaries
        grid_z = -0.05  # Draw grid slightly below z=0 so cubes sit on top
        
        for i in range(-grid_range, grid_range + 1):
            for j in range(-grid_range, grid_range + 1):
                x1, y1 = self.renderer.project_3d_to_2d(i, j, grid_z)
                x2, y2 = self.renderer.project_3d_to_2d(i + 1, j, grid_z)
                x3, y3 = self.renderer.project_3d_to_2d(i, j + 1, grid_z)
                
                # Use boundary color for edge lines
                is_boundary = (i == -grid_range or i == grid_range or 
                              j == -grid_range or j == grid_range)
                color = boundary_color if is_boundary else grid_color
                
                if i < grid_range:  # Don't draw beyond the boundary
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, tags="grid")
                if j < grid_range:  # Don't draw beyond the boundary
                    self.canvas.create_line(x1, y1, x3, y3, fill=color, tags="grid")
    
    def _select_tool(self, component_type: ComponentType):
        """Select a component type for placement."""
        self.current_tool = component_type
        self._log_status(f"Selected tool: {component_type.value}")
    
    def _on_canvas_click(self, event):
        """Handle canvas click events for component placement."""
        # Convert screen coordinates to grid coordinates
        grid_x, grid_y = self._screen_to_grid(event.x, event.y)
        
        # Check if clicking on existing component
        clicked_component = self._get_component_at_position(grid_x, grid_y)
        
        if clicked_component:
            self._select_component(clicked_component)
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            self.drag_component = clicked_component
        else:
            # Place new component
            self._place_component(grid_x, grid_y, 0)
    
    def _on_canvas_drag(self, event):
        """Handle canvas drag events for component movement."""
        if self.dragging and self.drag_component:
            grid_x, grid_y = self._screen_to_grid(event.x, event.y)
            
            # Define grid boundaries
            grid_min = -10
            grid_max = 10
            
            # Check if new position is within grid boundaries
            if (grid_x < grid_min or grid_x > grid_max or 
                grid_y < grid_min or grid_y > grid_max):
                return  # Don't allow dragging outside grid
            
            # Check if new position is occupied by another component
            existing_component = self._get_component_at_position(grid_x, grid_y)
            if existing_component and existing_component != self.drag_component:
                return  # Don't allow stacking components
            
            # Update component position
            old_pos = self.drag_component.position
            self.drag_component.position = (grid_x, grid_y, old_pos[2])
            
            self._redraw_circuit()
    
    def _on_canvas_release(self, event):
        """Handle canvas button release events."""
        self.dragging = False
        self.drag_component = None
    
    def _on_right_click(self, event):
        """Handle right-click context menu."""
        grid_x, grid_y = self._screen_to_grid(event.x, event.y)
        component = self._get_component_at_position(grid_x, grid_y)
        
        if component:
            self._show_context_menu(event, component)
    
    def _on_middle_click(self, event):
        """Handle middle-click for grid panning."""
        self.panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
    
    def _on_pan_drag(self, event):
        """Handle grid panning with middle mouse drag."""
        if self.panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            
            # Update renderer offset
            self.renderer.offset_x += dx
            self.renderer.offset_y += dy
            
            # Redraw grid and components
            self._draw_grid()
            self._redraw_circuit()
            
            # Update pan start position
            self.pan_start_x = event.x
            self.pan_start_y = event.y
    
    def _on_pan_release(self, event):
        """Handle middle mouse button release."""
        self.panning = False
    
    def _screen_to_grid(self, screen_x: float, screen_y: float) -> Tuple[int, int]:
        """Convert screen coordinates to grid coordinates."""
        # Reverse isometric projection (approximate)
        relative_x = screen_x - self.renderer.offset_x
        relative_y = screen_y - self.renderer.offset_y
        
        # Simple approximation - can be improved for accuracy
        grid_x = round((relative_x / self.renderer.scale / self.renderer.cos_30 + 
                       relative_y / self.renderer.scale / self.renderer.sin_30) / 2)
        grid_y = round((relative_y / self.renderer.scale / self.renderer.sin_30 - 
                       relative_x / self.renderer.scale / self.renderer.cos_30) / 2)
        
        return grid_x, grid_y
    
    def _get_component_at_position(self, grid_x: int, grid_y: int) -> Optional[Component3D]:
        """Get component at specified grid position."""
        for component in self.components:
            comp_x, comp_y, comp_z = component.position
            if comp_x == grid_x and comp_y == grid_y:
                return component
        return None
    
    def _place_component(self, grid_x: int, grid_y: int, grid_z: int):
        """Place a new component at the specified grid position."""
        # Define grid boundaries
        grid_min = -10
        grid_max = 10
        
        # Check if position is within grid boundaries
        if (grid_x < grid_min or grid_x > grid_max or 
            grid_y < grid_min or grid_y > grid_max):
            self._log_status(f"Cannot place component outside grid boundaries ({grid_min} to {grid_max})")
            return
        
        # Check if position is occupied
        if self._get_component_at_position(grid_x, grid_y):
            self._log_status(f"Position ({grid_x}, {grid_y}) is already occupied!")
            return
        
        # Determine if this is a two-qubit gate (spans 2 lanes)
        two_qubit_types = [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]
        is_two_qubit = self.current_tool in two_qubit_types
        
        # Two-qubit gates need the adjacent lane to be free
        if is_two_qubit:
            if self._get_component_at_position(grid_x, grid_y + 1):
                self._log_status(f"Two-qubit gate needs adjacent lane ({grid_x}, {grid_y + 1}) to be free!")
                return
        
        # Get component color based on type
        color = self._get_component_color(self.current_tool)
        
        # Set size: two-qubit gates span 2 Y positions (depth=2)
        if is_two_qubit:
            size = (1.0, 1.0, 2.0)  # Two-qubit gates span 2 Y lanes (width, height, depth)
        else:
            size = (1.0, 1.0, 1.0)
        
        # Create new component
        component = Component3D(
            component_type=self.current_tool,
            position=(grid_x, grid_y, grid_z),
            color=color,
            size=size
        )
        
        self.components.append(component)
        self.component_counter += 1
        
        self._log_status(f"Placed {self.current_tool.value} at ({grid_x}, {grid_y}, {grid_z})")
        self._redraw_circuit()
    
    def _get_component_color(self, component_type: ComponentType) -> Tuple[float, float, float]:
        """Get color for component type."""
        color_map = {
            # Single qubit gates - distinct blue shades
            ComponentType.X_GATE: (0.1, 0.3, 0.9),     # Bright blue
            ComponentType.Z_GATE: (0.2, 0.5, 0.7),     # Medium blue
            ComponentType.Y_GATE: (0.4, 0.7, 1.0),     # Light blue
            ComponentType.H_GATE: (0.0, 0.2, 0.6),     # Dark blue
            ComponentType.S_GATE: (0.3, 0.4, 0.8),     # Purple-blue
            ComponentType.T_GATE: (0.5, 0.6, 0.9),     # Lavender
            
            # Two qubit gates - distinct purple/magenta shades
            ComponentType.CNOT_GATE: (0.8, 0.2, 0.6),  # Magenta
            ComponentType.CZ_GATE: (0.6, 0.1, 0.8),    # Purple
            ComponentType.SWAP_GATE: (0.9, 0.4, 0.7),  # Pink
            
            # LDPC components - distinct green/orange shades
            ComponentType.PARITY_CHECK: (0.9, 0.5, 0.1),   # Orange
            ComponentType.DATA_QUBIT: (0.2, 0.9, 0.3),     # Bright green
            ComponentType.ANCILLA_QUBIT: (0.6, 0.8, 0.1),  # Yellow-green
            ComponentType.SYNDROME_EXTRACT: (0.1, 0.7, 0.5), # Teal
            
            # Measurement - distinct red shades
            ComponentType.MEASURE: (0.9, 0.1, 0.1),    # Bright red
            ComponentType.RESET: (0.7, 0.3, 0.2),      # Dark red
        }
        
        return color_map.get(component_type, (0.5, 0.5, 0.5))
    
    def _redraw_circuit(self):
        """Redraw the entire circuit with proper depth sorting."""
        # Clear previous components
        self.canvas.delete("component")
        
        # Sort components by depth for proper rendering (Painter's Algorithm)
        sorted_components = sorted(
            self.components, 
            key=lambda c: (c.position[0] + c.position[1], c.position[2])
        )
        
        # Draw all components from back to front
        for component in sorted_components:
            x, y, z = component.position
            w, h, d = component.size
            
            # Draw the component cube
            items = self.renderer.draw_cube(x, y, z, w, h, d, component.color)
            
            # Tag items for deletion and selection
            for item in items:
                self.canvas.addtag_withtag("component", item)
            
            # Add component label
            center_x, center_y = self.renderer.project_3d_to_2d(x + w/2, y + d/2, z + h + 0.2)
            self.canvas.create_text(center_x, center_y, text=component.component_type.value,
                                  fill="#ffffff", font=("Arial", 8), tags="component")
            
            # Add rotation indicator if component is rotated
            if component.rotation != 0:
                arrow_length = 15
                angle_rad = math.radians(component.rotation)
                arrow_end_x = center_x + arrow_length * math.cos(angle_rad)
                arrow_end_y = center_y + arrow_length * math.sin(angle_rad)
                
                self.canvas.create_line(center_x, center_y, arrow_end_x, arrow_end_y,
                                      fill="#ffff00", width=2, arrow=tk.LAST, tags="component")
                self.canvas.create_text(center_x + 20, center_y - 10, text=f"{component.rotation}°",
                                      fill="#ffff00", font=("Arial", 7), tags="component")
    
    def _select_component(self, component: Component3D):
        """Select a component for manipulation."""
        self.selected_component = component
        self._log_status(f"Selected {component.component_type.value} at {component.position}")
    
    def _show_context_menu(self, event, component: Component3D):
        """Show context menu for component operations."""
        context_menu = tk.Menu(self.root, tearoff=0, bg='#404040', fg='#ffffff',
                              activebackground='#606060', activeforeground='#ffffff')
        
        context_menu.add_command(label="Rotate", 
                               command=lambda: self._rotate_component(component))
        context_menu.add_command(label="Duplicate", 
                               command=lambda: self._duplicate_component(component))
        context_menu.add_command(label="Delete", 
                               command=lambda: self._delete_component(component))
        context_menu.add_separator()
        context_menu.add_command(label="Properties", 
                               command=lambda: self._show_properties(component))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _rotate_component(self, component: Component3D):
        """Rotate a component by 90 degrees."""
        component.rotation = (component.rotation + 90) % 360
        self._log_status(f"Rotated {component.component_type.value} to {component.rotation}°")
        self._redraw_circuit()
    
    def _duplicate_component(self, component: Component3D):
        """Duplicate a component at an adjacent position."""
        x, y, z = component.position
        
        # Try to find an adjacent free position
        adjacent_positions = [(x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z)]
        
        for new_x, new_y, new_z in adjacent_positions:
            # Check grid boundaries
            if (new_x < -10 or new_x > 10 or new_y < -10 or new_y > 10):
                continue
                
            # Check if position is free
            if not self._get_component_at_position(new_x, new_y):
                new_component = Component3D(
                    component_type=component.component_type,
                    position=(new_x, new_y, new_z),
                    rotation=component.rotation,
                    size=component.size,
                    color=component.color,
                    connections=component.connections.copy(),
                    properties=component.properties.copy()
                )
                
                self.components.append(new_component)
                self._log_status(f"Duplicated {component.component_type.value} at ({new_x}, {new_y}, {new_z})")
                self._redraw_circuit()
                return
        
        # No free adjacent position found
        self._log_status("No free adjacent position available for duplication")
    
    def _delete_component(self, component: Component3D):
        """Delete a component from the circuit."""
        if component in self.components:
            self.components.remove(component)
            if self.selected_component == component:
                self.selected_component = None
            self._log_status(f"Deleted {component.component_type.value}")
            self._redraw_circuit()
    
    def _delete_selected(self, event):
        """Delete currently selected component."""
        if self.selected_component:
            self._delete_component(self.selected_component)
    
    def _copy_selected(self, event):
        """Copy currently selected component."""
        if self.selected_component:
            self._duplicate_component(self.selected_component)
    
    def _paste_component(self, event):
        """Paste component at cursor position."""
        # Implementation for paste functionality
        pass
    
    def _show_properties(self, component: Component3D):
        """Show component properties dialog."""
        props_window = tk.Toplevel(self.root)
        props_window.title(f"{component.component_type.value} Properties")
        props_window.configure(bg='#2b2b2b')
        props_window.geometry("300x400")
        
        # Properties display
        props_frame = ttk.Frame(props_window, style='Dark.TFrame')
        props_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Component info
        ttk.Label(props_frame, text=f"Type: {component.component_type.value}",
                 style='Dark.TLabel').pack(anchor=tk.W, pady=2)
        ttk.Label(props_frame, text=f"Position: {component.position}",
                 style='Dark.TLabel').pack(anchor=tk.W, pady=2)
        ttk.Label(props_frame, text=f"Rotation: {component.rotation}°",
                 style='Dark.TLabel').pack(anchor=tk.W, pady=2)
        ttk.Label(props_frame, text=f"Size: {component.size}",
                 style='Dark.TLabel').pack(anchor=tk.W, pady=2)
        
        # Additional properties
        if component.properties:
            ttk.Separator(props_frame, orient='horizontal').pack(fill=tk.X, pady=10)
            ttk.Label(props_frame, text="Custom Properties:",
                     style='Dark.TLabel').pack(anchor=tk.W, pady=2)
            
            for key, value in component.properties.items():
                ttk.Label(props_frame, text=f"{key}: {value}",
                         style='Dark.TLabel').pack(anchor=tk.W, pady=1)
    
    def _clear_circuit(self):
        """Clear all components from the circuit."""
        self.components.clear()
        self.selected_component = None
        self._update_circuit_title("New Circuit")
        self._log_status("Circuit cleared")
        self._redraw_circuit()
    
    def _save_circuit(self):
        """Save current circuit to file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Circuit"
        )
        
        if filename:
            try:
                circuit_data = {
                    'components': [
                        {
                            'type': comp.component_type.value,
                            'position': comp.position,
                            'rotation': comp.rotation,
                            'size': comp.size,
                            'color': comp.color,
                            'connections': comp.connections,
                            'properties': comp.properties
                        }
                        for comp in self.components
                    ]
                }
                
                with open(filename, 'w') as f:
                    json.dump(circuit_data, f, indent=2)
                
                # Update circuit title
                circuit_name = os.path.basename(filename)
                formatted_title = self._format_circuit_title(circuit_name)
                self._update_circuit_title(formatted_title)
                
                self._log_status(f"Circuit saved to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save circuit: {e}")
    
    def _load_circuit(self):
        """Load circuit from file."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Circuit"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    circuit_data = json.load(f)
                
                # Clear current circuit
                self.components.clear()
                
                # Load components
                for comp_data in circuit_data.get('components', []):
                    # Find component type
                    comp_type = None
                    for ct in ComponentType:
                        if ct.value == comp_data['type']:
                            comp_type = ct
                            break
                    
                    if comp_type:
                        # Determine correct size based on gate type
                        two_qubit_types = [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]
                        if comp_type in two_qubit_types:
                            size = (1.0, 1.0, 2.0)  # Two-qubit gates span 2 Y lanes
                        else:
                            size = tuple(comp_data.get('size', (1.0, 1.0, 1.0)))
                        
                        component = Component3D(
                            component_type=comp_type,
                            position=tuple(comp_data['position']),
                            rotation=comp_data.get('rotation', 0.0),
                            size=size,
                            color=tuple(comp_data.get('color', (0.5, 0.5, 0.5))),
                            connections=comp_data.get('connections', []),
                            properties=comp_data.get('properties', {})
                        )
                        self.components.append(component)
                
                # Update circuit title
                circuit_name = os.path.basename(filename)
                formatted_title = self._format_circuit_title(circuit_name)
                self._update_circuit_title(formatted_title)
                
                self._log_status(f"Circuit loaded from {filename}")
                self._redraw_circuit()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load circuit: {e}")
    
    def _calculate_syndrome(self):
        """Calculate syndrome for current circuit."""
        try:
            syndrome = self.processor.calculate_syndrome(self.components)
            
            if len(syndrome) > 0:
                # Count circuit components for context
                data_qubits = len([c for c in self.components if c.component_type == ComponentType.DATA_QUBIT])
                ancilla_qubits = len([c for c in self.components if c.component_type == ComponentType.ANCILLA_QUBIT])
                parity_checks = len([c for c in self.components if c.component_type == ComponentType.PARITY_CHECK])
                
                self._log_status(f"=== Syndrome Calculation ===")
                self._log_status(f"Data qubits: {data_qubits}, Ancilla qubits: {ancilla_qubits}, Parity checks: {parity_checks}")
                self._log_status(f"Syndrome: {syndrome}")
                self._log_status(f"Syndrome weight: {np.sum(syndrome)} / {len(syndrome)}")
                
                if np.sum(syndrome) == 0:
                    self._log_status("✓ No errors detected (all syndrome bits are 0)")
                else:
                    self._log_status(f"⚠ Errors detected (syndrome weight: {np.sum(syndrome)})")
            else:
                self._log_status("No syndrome extractors found. Need ancilla qubits or parity check components.")
                
        except Exception as e:
            self._log_status(f"Error calculating syndrome: {e}")
    
    def _run_error_correction(self):
        """Run error correction algorithm."""
        try:
            # First calculate syndrome
            syndrome = self.processor.calculate_syndrome(self.components)
            
            if len(syndrome) == 0:
                self._log_status("No syndrome available for error correction. Need ancilla qubits or parity checks.")
                return
            
            # Run error correction
            result = self.processor.perform_error_correction(syndrome, self.components)
            
            if result['success']:
                correction = result['correction']
                beliefs = result['beliefs']
                iterations = result['iterations']
                syndrome_weight = result.get('syndrome_weight', 0)
                num_data_qubits = result.get('num_data_qubits', 0)
                
                self._log_status(f"=== Error Correction Results ===")
                self._log_status(f"Converged in {iterations} iterations")
                self._log_status(f"Data qubits: {num_data_qubits}, Syndrome weight: {syndrome_weight}")
                self._log_status(f"Correction vector: {correction}")
                self._log_status(f"Error probabilities: {[f'{p:.3f}' for p in beliefs]}")
                
                # Provide interpretation
                if np.sum(correction) == 0:
                    self._log_status("✓ No corrections needed")
                else:
                    self._log_status(f"⚠ Applying {np.sum(correction)} corrections")
                    
            else:
                self._log_status(f"Error correction failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self._log_status(f"Error during error correction: {e}")
                
        except Exception as e:
            self._log_status(f"Error in correction algorithm: {e}")
    
    def _simulate_evolution(self):
        """Simulate quantum state evolution."""
        try:
            circuit = self.processor.build_circuit_from_components(self.components)
            
            if circuit is None:
                self._log_status("Failed to build quantum circuit")
                return
            
            if QISKIT_AVAILABLE and hasattr(circuit, 'num_qubits'):
                # Run actual quantum simulation
                simulator = AerSimulator()
                
                # Add measurements if not present
                if not any(instr.operation.name == 'measure' for instr in circuit.data):
                    circuit.measure_all()
                
                # Execute circuit
                transpiled = transpile(circuit, simulator)
                job = simulator.run(transpiled, shots=1024)
                result = job.result()
                counts = result.get_counts()
                
                self._log_status("Quantum state evolution completed")
                self._log_status(f"Measurement results: {counts}")
                
                # Display most frequent outcomes
                sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                for state, count in sorted_counts[:5]:
                    probability = count / 1024
                    self._log_status(f"State |{state}>: {probability:.3f}")
            
            else:
                # Fallback simulation
                self._log_status("Quantum evolution simulation (classical fallback)")
                self._log_status(f"Circuit stats: {circuit}")
                
        except Exception as e:
            self._log_status(f"Error in quantum simulation: {e}")
    
    def _log_status(self, message: str):
        """Log a status message to the status display."""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
    
    def _on_tutorial_complete(self, show_on_startup: bool):
        """Handle tutorial completion."""
        TutorialScreen.save_tutorial_preference(show_on_startup)
        self._log_status("Tutorial completed! Ready to build quantum circuits.")
    
    def _show_tutorial(self):
        """Show the tutorial screen."""
        tutorial = TutorialScreen(self.root, self._on_tutorial_complete, circuit_builder=self)
        tutorial.show()
    
    def _show_advanced_tutorial(self):
        """Show the advanced tutorial screen with live demonstrations."""
        advanced = AdvancedTutorialScreen(self.root, circuit_builder=self)
        advanced.show()
    
    def _toggle_legend(self):
        """Toggle the component legend panel."""
        if hasattr(self, 'legend_window') and self.legend_window and self.legend_window.winfo_exists():
            self.legend_window.destroy()
            self.legend_window = None
        else:
            self._show_legend()
    
    def _show_legend(self):
        """Show the component legend panel with 3D cube previews."""
        self.legend_window = tk.Toplevel(self.root)
        self.legend_window.title("Component Legend")
        self.legend_window.geometry("280x600")
        self.legend_window.configure(bg='#1a1a2e')
        self.legend_window.attributes('-topmost', False)
        
        # Position to the right of main window
        self.legend_window.update_idletasks()
        main_x = self.root.winfo_x()
        main_width = self.root.winfo_width()
        x = main_x + main_width + 10
        y = self.root.winfo_y()
        self.legend_window.geometry(f"280x600+{x}+{y}")
        
        # Main scrollable frame
        main_frame = tk.Frame(self.legend_window, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="🎨 Component Legend", 
                              font=('Segoe UI', 14, 'bold'),
                              fg='#e94560', bg='#1a1a2e')
        title_label.pack(pady=(0, 10))
        
        # Scrollable canvas for components
        canvas_frame = tk.Frame(main_frame, bg='#1a1a2e')
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        legend_canvas = tk.Canvas(canvas_frame, bg='#1a1a2e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=legend_canvas.yview)
        scrollable_frame = tk.Frame(legend_canvas, bg='#1a1a2e')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: legend_canvas.configure(scrollregion=legend_canvas.bbox("all"))
        )
        
        legend_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        legend_canvas.configure(yscrollcommand=scrollbar.set)
        
        legend_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Component categories (short names matching toolbox)
        categories = {
            "Single Qubit Gates": [
                ComponentType.X_GATE, ComponentType.Z_GATE, ComponentType.Y_GATE,
                ComponentType.H_GATE, ComponentType.S_GATE, ComponentType.T_GATE
            ],
            "Two Qubit Gates": [
                ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE
            ],
            "LDPC Components": [
                ComponentType.PARITY_CHECK, ComponentType.DATA_QUBIT, 
                ComponentType.ANCILLA_QUBIT, ComponentType.SYNDROME_EXTRACT
            ],
            "Measurement": [
                ComponentType.MEASURE, ComponentType.RESET
            ]
        }
        
        for category, components in categories.items():
            # Category header
            cat_frame = tk.Frame(scrollable_frame, bg='#16213e')
            cat_frame.pack(fill=tk.X, pady=(10, 5), padx=5)
            
            cat_label = tk.Label(cat_frame, text=category, 
                               font=('Segoe UI', 10, 'bold'),
                               fg='#74b9ff', bg='#16213e', pady=5)
            cat_label.pack(anchor=tk.W, padx=5)
            
            # Components in this category
            for comp_type in components:
                self._create_legend_item(scrollable_frame, comp_type)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            legend_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        legend_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Cleanup when window closes
        def on_close():
            legend_canvas.unbind_all("<MouseWheel>")
            self.legend_window.destroy()
            self.legend_window = None
        
        self.legend_window.protocol("WM_DELETE_WINDOW", on_close)
    
    def _create_legend_item(self, parent, comp_type: ComponentType):
        """Create a legend item with a mini 3D cube preview."""
        item_frame = tk.Frame(parent, bg='#0f0f23', bd=1, relief='solid')
        item_frame.pack(fill=tk.X, pady=2, padx=5)
        
        # Two-qubit gates get a wider preview canvas
        two_qubit_types = [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]
        is_two_qubit = comp_type in two_qubit_types
        
        canvas_width = 70 if is_two_qubit else 50
        
        # Create mini canvas for cube preview
        preview_canvas = tk.Canvas(item_frame, width=canvas_width, height=40, 
                                  bg='#0f0f23', highlightthickness=0)
        preview_canvas.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Draw mini isometric cube (two-qubit gates are wider in depth)
        color = self._get_component_color(comp_type)
        depth = 2.0 if is_two_qubit else 1.0
        self._draw_mini_cube(preview_canvas, 25, 25, color, depth=depth)
        
        # Component name and description
        text_frame = tk.Frame(item_frame, bg='#0f0f23')
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        name_label = tk.Label(text_frame, text=comp_type.value,
                            font=('Segoe UI', 9, 'bold'),
                            fg='#ffffff', bg='#0f0f23', anchor='w')
        name_label.pack(anchor=tk.W)
        
        # Add description based on component type
        descriptions = {
            ComponentType.X_GATE: "Bit-flip gate (Pauli-X)",
            ComponentType.Y_GATE: "Pauli-Y rotation",
            ComponentType.Z_GATE: "Phase-flip gate (Pauli-Z)",
            ComponentType.H_GATE: "Hadamard superposition",
            ComponentType.S_GATE: "Phase gate (√Z)",
            ComponentType.T_GATE: "π/8 gate (√S)",
            ComponentType.CNOT_GATE: "Controlled-NOT gate",
            ComponentType.CZ_GATE: "Controlled-Z gate",
            ComponentType.SWAP_GATE: "Swap two qubits",
            ComponentType.PARITY_CHECK: "LDPC parity check node",
            ComponentType.DATA_QUBIT: "Data qubit (stores info)",
            ComponentType.ANCILLA_QUBIT: "Ancilla (syndrome helper)",
            ComponentType.SYNDROME_EXTRACT: "Syndrome measurement",
            ComponentType.MEASURE: "Measurement operation",
            ComponentType.RESET: "Reset to |0⟩ state",
        }
        
        desc = descriptions.get(comp_type, "Quantum component")
        desc_label = tk.Label(text_frame, text=desc,
                            font=('Segoe UI', 7),
                            fg='#888888', bg='#0f0f23', anchor='w')
        desc_label.pack(anchor=tk.W)
    
    def _draw_mini_cube(self, canvas, cx, cy, color, depth=1.0):
        """Draw a small isometric cube on a canvas for the legend.
        
        Args:
            canvas: Canvas to draw on
            cx, cy: Center position
            color: RGB color tuple
            depth: Depth multiplier (2.0 for two-qubit gates)
        """
        # Mini isometric projection
        size = 12
        size_depth = size * depth  # Extend in Y direction for two-qubit gates
        cos30 = math.cos(math.radians(30))
        sin30 = math.sin(math.radians(30))
        
        # Calculate vertices for mini cube
        def project(x, y, z):
            iso_x = (x - y) * cos30 + cx
            iso_y = (x + y) * sin30 - z + cy
            return iso_x, iso_y
        
        # 8 vertices of the cube (depth extended for two-qubit gates)
        v = [
            project(0, 0, 0),                # 0: bottom-front-left
            project(size, 0, 0),             # 1: bottom-front-right
            project(size, size_depth, 0),    # 2: bottom-back-right
            project(0, size_depth, 0),       # 3: bottom-back-left
            project(0, 0, size),             # 4: top-front-left
            project(size, 0, size),          # 5: top-front-right
            project(size, size_depth, size), # 6: top-back-right
            project(0, size_depth, size),    # 7: top-back-left
        ]
        
        # Helper to brighten color
        def brighten(c, factor):
            return tuple(min(1.0, x * factor) for x in c)
        
        def to_hex(c):
            return f"#{int(c[0]*255):02x}{int(c[1]*255):02x}{int(c[2]*255):02x}"
        
        # Draw all 6 faces (back to front, Painter's Algorithm)
        outline = '#444'
        
        # Bottom face (darkest)
        canvas.create_polygon(v[0][0], v[0][1], v[1][0], v[1][1],
                             v[2][0], v[2][1], v[3][0], v[3][1],
                             fill=to_hex(brighten(color, 0.5)), outline=outline)
        
        # Back-right face (facing +y)
        canvas.create_polygon(v[2][0], v[2][1], v[3][0], v[3][1],
                             v[7][0], v[7][1], v[6][0], v[6][1],
                             fill=to_hex(brighten(color, 0.6)), outline=outline)
        
        # Back-left face (facing +x)
        canvas.create_polygon(v[1][0], v[1][1], v[2][0], v[2][1],
                             v[6][0], v[6][1], v[5][0], v[5][1],
                             fill=to_hex(brighten(color, 0.55)), outline=outline)
        
        # Left face (front-left)
        canvas.create_polygon(v[0][0], v[0][1], v[3][0], v[3][1], 
                             v[7][0], v[7][1], v[4][0], v[4][1],
                             fill=to_hex(brighten(color, 0.7)), outline=outline)
        
        # Right face (front-right)
        canvas.create_polygon(v[0][0], v[0][1], v[1][0], v[1][1],
                             v[5][0], v[5][1], v[4][0], v[4][1],
                             fill=to_hex(brighten(color, 0.85)), outline=outline)
        
        # Top face (lightest)
        canvas.create_polygon(v[4][0], v[4][1], v[5][0], v[5][1],
                             v[6][0], v[6][1], v[7][0], v[7][1],
                             fill=to_hex(brighten(color, 1.1)), outline=outline)
    
    def run(self):
        """Start the application main loop."""
        self._log_status("Starting Quantum LDPC Circuit Builder 3D")
        self._log_status("Ready for interactive circuit construction!")
        self._log_status("TIP: Middle-click and drag to pan the grid view")
        self._log_status("TIP: Right-click components for rotation and other options")
        self._log_status("IMPROVEMENT: Grid boundaries enforced - components cannot be placed outside grid")
        self._log_status("IMPROVEMENT: Component stacking prevented - only one component per grid position")
        
        # Show tutorial on startup if enabled
        if TutorialScreen.should_show_tutorial():
            # Schedule tutorial to show after main window is displayed
            self.root.after(100, self._show_tutorial)
        
        self.root.mainloop()


def main():
    """Main entry point for the application."""
    try:
        app = CircuitBuilder3D()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()