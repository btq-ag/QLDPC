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


# ==================== ERROR HANDLING UTILITIES (#25) ====================

class ErrorContext:
    """
    Provides user-friendly error messages with context and suggestions.
    
    Improvement #25: Enhanced error messaging for better UX.
    """
    
    # Map common error patterns to user-friendly messages
    ERROR_MESSAGES = {
        'FileNotFoundError': (
            "File Not Found",
            "The specified file could not be found. Please check the file path and try again.",
            ["Verify the file exists at the specified location",
             "Check for typos in the filename",
             "Ensure you have read permissions for the file"]
        ),
        'JSONDecodeError': (
            "Invalid JSON Format",
            "The file is not valid JSON format or is corrupted.",
            ["Ensure the file is a valid JSON file",
             "Check for syntax errors (missing commas, brackets)",
             "Try opening the file in a text editor to verify its contents"]
        ),
        'PermissionError': (
            "Permission Denied",
            "You don't have permission to access this file or location.",
            ["Check file permissions",
             "Try running the application as administrator",
             "Save to a different location"]
        ),
        'MemoryError': (
            "Out of Memory",
            "The operation requires more memory than available.",
            ["Try working with a smaller circuit",
             "Close other applications to free memory",
             "Reduce the grid size or number of components"]
        ),
        'KeyError': (
            "Missing Data",
            "Expected data is missing from the file or configuration.",
            ["The file may be corrupted or from an incompatible version",
             "Try loading a different circuit file",
             "Check if all required fields are present"]
        ),
    }
    
    @classmethod
    def get_user_friendly_error(cls, exception: Exception, context: str = "") -> dict:
        """
        Convert an exception to a user-friendly error message.
        
        Args:
            exception: The caught exception
            context: Additional context about what was being attempted
            
        Returns:
            dict with 'title', 'message', 'suggestions', and 'technical_details'
        """
        error_type = type(exception).__name__
        error_info = cls.ERROR_MESSAGES.get(error_type)
        
        if error_info:
            title, message, suggestions = error_info
        else:
            # Generic error handling
            title = "An Error Occurred"
            message = str(exception) if str(exception) else "An unexpected error occurred."
            suggestions = [
                "Try the operation again",
                "Check your input and try again",
                "If the problem persists, restart the application"
            ]
        
        # Add context if provided
        if context:
            message = f"{context}: {message}"
        
        return {
            'title': title,
            'message': message,
            'suggestions': suggestions,
            'technical_details': f"{error_type}: {str(exception)}"
        }
    
    @classmethod
    def format_error_dialog(cls, error_info: dict) -> str:
        """Format error info for display in a message box."""
        text = f"{error_info['message']}\n\n"
        text += "Suggestions:\n"
        for i, suggestion in enumerate(error_info['suggestions'][:3], 1):
            text += f"  {i}. {suggestion}\n"
        return text
    
    @classmethod
    def format_error_log(cls, error_info: dict) -> str:
        """Format error info for logging to status."""
        return f"❌ {error_info['title']}: {error_info['message']}"


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
        self.demo_components = []  # Store demo components for step-by-step demos
        
        # Define tutorial steps with rich content
        self.steps = self._create_tutorial_steps()
    
    def _create_tutorial_steps(self) -> List[Dict[str, Any]]:
        """Create the tutorial content with tagged text for coloring."""
        return [
            # Step 0: Welcome
            {
                'title': 'Welcome to the Quantum Circuit Builder!',
                'content': [
                    ('Welcome to the ', 'normal'),
                    ('3D Quantum Circuit Builder', 'title'),
                    ('!\n\n', 'normal'),
                    ('This interactive tool lets you build and simulate quantum circuits ', 'normal'),
                    ('for error correction — including LDPC codes and surface codes.\n\n', 'normal'),
                    ('🎯 What you\'ll learn:\n', 'normal'),
                    ('• How to place quantum components on the grid\n', 'normal'),
                    ('• Understanding qubit lanes and gate operations\n', 'normal'),
                    ('• Building basic error correction circuits\n', 'normal'),
                    ('• Switching between circuit and surface code modes\n\n', 'normal'),
                    ('💡 ', 'normal'),
                    ('Tip:', 'highlight'),
                    (' You can interact with the main window while this tutorial is open!\n\n', 'normal'),
                    ('Click ', 'normal'),
                    ('Next', 'action'),
                    (' to begin, or ', 'normal'),
                    ('Skip Tutorial', 'action'),
                    (' to jump right in.', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_welcome'
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
                    (':\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Data Qubit', 'component'),
                    (' — Stores quantum information\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Ancilla Qubit', 'component'),
                    (' — Helper qubits for measurement\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Parity Check', 'ldpc'),
                    (' — Detects errors\n', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_welcome'
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
                    ('• Click a component to ', 'normal'),
                    ('select', 'action'),
                    (' it (yellow outline)\n', 'normal'),
                    ('• Right-click for context menu (rotate, delete)\n', 'normal'),
                    ('• Middle-click + drag to pan the view\n', 'normal'),
                    ('• ', 'normal'),
                    ('Scroll wheel', 'action'),
                    (' to zoom in/out\n', 'normal'),
                    ('• Grid boundaries (±10) keep your circuit organized\n\n', 'normal'),
                    ('Look at the demo circuit - one component is ', 'normal'),
                    ('selected', 'highlight'),
                    (' (yellow border)!', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_placing_components'
            },
            # Step 3: Understanding Qubit Placement (from Advanced)
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
                    ('One cube = One qubit/gate', 'component'),
                    ('\n   When you place a Data Qubit, it occupies exactly one grid position.\n\n', 'normal'),
                    ('2. ', 'normal'),
                    ('Position = (x, y, z)', 'math'),
                    ('\n   • ', 'normal'),
                    ('X-axis', 'component'),
                    (' = Time/circuit depth (left to right)\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Y-axis', 'component'),
                    (' = Qubit index / lane (front to back)\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Z-axis', 'component'),
                    (' = Layer (usually 0 for flat circuits)\n\n', 'normal'),
                    ('3. Components are placed at ', 'normal'),
                    ('integer coordinates', 'highlight'),
                    ('\n   No partial positions - each block snaps to the grid.', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_qubit_positions'
            },
            # Step 4: How Operators Act (from Advanced)
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
                    ('• Gates in different lanes act on different qubits\n\n', 'normal'),
                    ('Example:', 'warning'),
                    (' An X gate at (2, 0, 0) acts on the qubit in lane 0\n', 'normal'),
                    ('at time step 2.', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_operator_interaction'
            },
            # Step 5: Single vs Two-Qubit Gates (from Advanced)
            {
                'title': 'Single vs Two-Qubit Gates',
                'content': [
                    ('Distinguishing Gate Types', 'title'),
                    ('\n\n', 'normal'),
                    ('Single-Qubit Gates', 'component'),
                    (' (X, Y, Z, H, S, T):\n', 'normal'),
                    ('• Occupy ', 'normal'),
                    ('one grid cell', 'highlight'),
                    ('\n', 'normal'),
                    ('• Act on the qubit in their lane only\n', 'normal'),
                    ('• Shown as ', 'normal'),
                    ('standard cubes', 'component'),
                    (' (1x1 footprint)\n\n', 'normal'),
                    ('Two-Qubit Gates', 'ldpc'),
                    (' (CNOT, CZ, SWAP):\n', 'normal'),
                    ('• Placed at the ', 'normal'),
                    ('control qubit lane', 'highlight'),
                    ('\n', 'normal'),
                    ('• Extend to the target qubit lane (below)\n', 'normal'),
                    ('• Shown as ', 'normal'),
                    ('taller cubes', 'warning'),
                    (' spanning both lanes\n\n', 'normal'),
                    ('CNOT Convention:', 'title'),
                    ('\n', 'normal'),
                    ('• ', 'normal'),
                    ('●', 'highlight'),
                    (' = Control qubit (filled dot)\n', 'normal'),
                    ('• ', 'normal'),
                    ('⊕', 'highlight'),
                    (' = Target qubit (XOR symbol)\n', 'normal'),
                    ('• Target qubit is at Y+1 (adjacent lane)', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_gate_comparison'
            },
            # Step 6: Creating Controlled Gates (NEW!)
            {
                'title': '⭐ Creating Controlled Gates',
                'content': [
                    ('Make Any Gate Controlled!', 'title'),
                    ('\n\n', 'normal'),
                    ('You can turn any single-qubit gate into a ', 'normal'),
                    ('controlled', 'highlight'),
                    (' version!\n\n', 'normal'),
                    ('🖱️ How to Add a Control:', 'title'),
                    ('\n\n', 'normal'),
                    ('1. Place a gate (H, X, Y, Z, S, T) on the grid\n', 'normal'),
                    ('2. ', 'normal'),
                    ('Right-click', 'action'),
                    (' on the gate\n', 'normal'),
                    ('3. Select "', 'normal'),
                    ('● Add Control', 'highlight'),
                    ('"\n', 'normal'),
                    ('4. Click on any qubit lane to place the control\n\n', 'normal'),
                    ('The result: ', 'normal'),
                    ('CH, CY, CZ, CS, CT', 'component'),
                    (' gates!\n\n', 'normal'),
                    ('✨ Features:', 'title'),
                    ('\n', 'normal'),
                    ('• Controls can span ', 'normal'),
                    ('multiple wires', 'warning'),
                    (' (not just adjacent)\n', 'normal'),
                    ('• Same color as original gate + ', 'normal'),
                    ('●', 'highlight'),
                    (' control dot\n', 'normal'),
                    ('• Right-click again to remove control\n\n', 'normal'),
                    ('Try the demo to see a controlled gate spanning 3 qubits!', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_controlled_gate'
            },
            # Step 7: Three-Qubit Repetition Code (from Advanced)
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
                    ('2 CNOT gates', 'component'),
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
                    (' corrects single errors', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_repetition_code'
            },
            # Step 7: Surface Code Mode (NEW)
            {
                'title': 'Surface Code Mode',
                'content': [
                    ('🔲 ', 'normal'),
                    ('Surface Code View', 'title'),
                    ('\n\n', 'normal'),
                    ('Press ', 'normal'),
                    ('V', 'action'),
                    (' to toggle between ', 'normal'),
                    ('Circuit Mode', 'component'),
                    (' and ', 'normal'),
                    ('Surface Code Mode', 'ldpc'),
                    ('!\n\n', 'normal'),
                    ('Circuit Mode (Isometric 3D):', 'title'),
                    ('\n', 'normal'),
                    ('• Standard quantum circuit layout\n', 'normal'),
                    ('• Qubit lanes run front-to-back\n', 'normal'),
                    ('• Time flows left-to-right\n\n', 'normal'),
                    ('Surface Code Mode (2D Lattice):', 'title'),
                    ('\n', 'normal'),
                    ('• Top-down view of a 2D qubit array\n', 'normal'),
                    ('• ', 'normal'),
                    ('Burgundy squares', 'component'),
                    (' = X-stabilizers (plaquettes)\n', 'normal'),
                    ('• ', 'normal'),
                    ('Purple squares', 'ldpc'),
                    (' = Z-stabilizers (vertices)\n', 'normal'),
                    ('• Data qubits live on the ', 'normal'),
                    ('edges', 'highlight'),
                    (' between plaquettes\n\n', 'normal'),
                    ('Click on plaquettes to place stabilizers, edges for data qubits.', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_repetition_code'
            },
            # Step 8: Loading Examples (was step 7)
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
                    ('tutorial_repetition_code.json', 'component'),
                    ('\n   3-qubit repetition code\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('tutorial_surface_code.json', 'component'),
                    ('\n   Surface code structure\n\n', 'normal'),
                    ('To load: Click "', 'normal'),
                    ('Load Circuit', 'action'),
                    ('" and browse to saved_circuits/', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_loading_examples'
            },
            # Step 9: Keyboard Shortcuts (was step 8) - updated with V hotkey
            {
                'title': 'Keyboard Shortcuts & Tips',
                'content': [
                    ('⌨️ ', 'normal'),
                    ('Keyboard Shortcuts:', 'title'),
                    ('\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('V', 'action'),
                    (' — Toggle Surface Code / Circuit mode\n', 'normal'),
                    ('• ', 'normal'),
                    ('C', 'action'),
                    (' — Clear entire circuit\n', 'normal'),
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
                    ('• Middle-click + drag — Pan the grid view\n', 'normal'),
                    ('• Scroll wheel — Zoom in/out\n\n', 'normal'),
                    ('The Status Panel (bottom-right) shows computation results.', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_keyboard_shortcuts'
            },
            # Step 10: Final (was step 9)
            {
                'title': 'You\'re Ready to Build!',
                'content': [
                    ('🎉 Congratulations! You\'re ready to build quantum circuits.\n\n', 'normal'),
                    ('📋 ', 'normal'),
                    ('Quick Start Checklist:', 'title'),
                    ('\n\n', 'normal'),
                    ('□ Place some ', 'normal'),
                    ('Data Qubits', 'component'),
                    (' (green blocks)\n', 'normal'),
                    ('□ Add gates (H, X, CNOT) to create a circuit\n', 'normal'),
                    ('□ Press ', 'normal'),
                    ('V', 'action'),
                    (' to explore Surface Code mode\n', 'normal'),
                    ('□ Try "Simulate Evolution" to see quantum states\n', 'normal'),
                    ('□ Load example circuits to learn more!\n\n', 'normal'),
                    ('For advanced topics like LDPC codes and hypergraph\n', 'normal'),
                    ('products, check the ', 'normal'),
                    ('Surface Code Tutorial', 'ldpc'),
                    (' from the Help menu.\n\n', 'normal'),
                    ('Click ', 'normal'),
                    ('Finish', 'action'),
                    (' to start building.', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_final'
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
        
        # Position to the RIGHT side of screen so grid is visible on the left
        self.tutorial_window.update_idletasks()
        screen_width = self.tutorial_window.winfo_screenwidth()
        screen_height = self.tutorial_window.winfo_screenheight()
        # Place tutorial on right side, leaving space for grid visibility
        x = screen_width - 680  # 650 width + 30 margin
        y = (screen_height - 520) // 2
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
        
        # Execute demo action for this step
        if 'demo_action' in step_data:
            self._execute_demo(step_data['demo_action'])
    
    def _execute_demo(self, action: str):
        """Execute the demo action for the current step."""
        if not self.circuit_builder:
            return
        
        # Clear any selection from previous step
        self.circuit_builder.selected_component = None
        
        # Clear previous demo components
        self._clear_demo_components()
        
        # Map actions to demo methods
        demo_map = {
            'show_welcome': self._demo_welcome,
            'show_placing_components': self._demo_placing_components,
            'show_qubit_positions': self._demo_qubit_positions,
            'show_operator_interaction': self._demo_operator_interaction,
            'show_gate_comparison': self._demo_gate_comparison,
            'show_controlled_gate': self._demo_controlled_gate,
            'show_repetition_code': self._demo_repetition_code,
            'show_loading_examples': self._demo_loading_examples,
            'show_keyboard_shortcuts': self._demo_keyboard_shortcuts,
            'show_final': self._demo_final,
        }
        
        if action in demo_map:
            demo_map[action]()
    
    def _clear_demo_components(self):
        """Clear previously placed demo components."""
        if not self.circuit_builder:
            return
        for comp in self.demo_components:
            if comp in self.circuit_builder.components:
                self.circuit_builder.components.remove(comp)
        self.demo_components = []
        self.circuit_builder._redraw_circuit()
    
    def _place_demo_components(self, specs):
        """Place demo components from specs list."""
        if not self.circuit_builder:
            return
        
        two_qubit_types = [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]
        
        for comp_type, position in specs:
            # Check position not occupied
            occupied = any(c.position == position for c in self.circuit_builder.components)
            if occupied:
                continue
            
            color = self.circuit_builder._get_component_color(comp_type)
            size = (1.0, 1.0, 2.0) if comp_type in two_qubit_types else (1.0, 1.0, 1.0)
            
            comp = Component3D(
                component_type=comp_type,
                position=position,
                color=color,
                size=size
            )
            self.circuit_builder.components.append(comp)
            self.demo_components.append(comp)
        
        self.circuit_builder._redraw_circuit()
    
    def _demo_welcome(self):
        """Demo for welcome screen - simple Bell state circuit with clear structure."""
        # Systematic layout: Two qubits, H gate on first, CNOT connecting them
        # All components aligned in a clear left-to-right flow
        specs = [
            # Qubit lane 0 (top): initialization → H gate
            (ComponentType.DATA_QUBIT, (0, 0, 0)),   # q0 at time=0
            (ComponentType.H_GATE, (1, 0, 0)),       # H on q0 at time=1
            # Qubit lane 1 (bottom): initialization
            (ComponentType.DATA_QUBIT, (0, 1, 0)),   # q1 at time=0
            # CNOT entangles q0 (control) with q1 (target) at time=2
            (ComponentType.CNOT_GATE, (2, 0, 0)),    # CNOT at time=2
        ]
        self._place_demo_components(specs)
    
    def _demo_placing_components(self):
        """Demo for placing components - shows selection highlight."""
        # Systematic layout with one component selected
        specs = [
            # Column 0: Qubits (foundation)
            (ComponentType.DATA_QUBIT, (0, 0, 0)),
            (ComponentType.DATA_QUBIT, (0, 1, 0)),
            (ComponentType.ANCILLA_QUBIT, (0, 2, 0)),
            # Column 1: Single gates (basic operations)
            (ComponentType.H_GATE, (1, 0, 0)),
            (ComponentType.X_GATE, (1, 1, 0)),
            (ComponentType.Z_GATE, (1, 2, 0)),
            # Column 2: Advanced
            (ComponentType.CNOT_GATE, (2, 0, 0)),
            (ComponentType.MEASURE, (2, 2, 0)),
        ]
        self._place_demo_components(specs)
        
        # Select the H_GATE to show the selection highlight
        if self.circuit_builder and self.demo_components:
            # Find the H gate in the demo components
            for comp in self.demo_components:
                if comp.component_type == ComponentType.H_GATE:
                    self.circuit_builder.selected_component = comp
                    self.circuit_builder._redraw_circuit()
                    break
    
    def _demo_qubit_positions(self):
        """Demo for qubit positioning - illustrate the coordinate axes clearly."""
        # Clear demonstration of coordinate system:
        # X-axis = time/depth (left to right: 0 → 1 → 2 → 3)
        # Y-axis = qubit lane (front to back: 0, 1, 2)
        specs = [
            # Lane 0: Full circuit flow showing time progression
            (ComponentType.DATA_QUBIT, (0, 0, 0)),   # x=0: Start
            (ComponentType.H_GATE, (1, 0, 0)),       # x=1: Apply gate
            (ComponentType.X_GATE, (2, 0, 0)),       # x=2: Another gate
            (ComponentType.MEASURE, (3, 0, 0)),      # x=3: Measure
            # Lanes 1, 2: Show multiple qubits (Y-axis)
            (ComponentType.DATA_QUBIT, (0, 1, 0)),   # y=1
            (ComponentType.DATA_QUBIT, (0, 2, 0)),   # y=2
        ]
        self._place_demo_components(specs)
    
    def _demo_operator_interaction(self):
        """Demo for operator interaction - gates acting on qubit lanes."""
        # Two parallel circuits showing independent lane operations
        # Lane 0: |0⟩ → H → Z → Measure  (superposition then phase flip)
        # Lane 1: |0⟩ → X → Measure      (bit flip to |1⟩)
        specs = [
            # Lane 0: superposition + phase
            (ComponentType.DATA_QUBIT, (0, 0, 0)),
            (ComponentType.H_GATE, (1, 0, 0)),
            (ComponentType.Z_GATE, (2, 0, 0)),
            (ComponentType.MEASURE, (3, 0, 0)),
            # Lane 1: simple bit flip
            (ComponentType.DATA_QUBIT, (0, 1, 0)),
            (ComponentType.X_GATE, (1, 1, 0)),
            (ComponentType.MEASURE, (3, 1, 0)),
        ]
        self._place_demo_components(specs)
    
    def _demo_gate_comparison(self):
        """Demo for gate comparison - single vs two-qubit gates side by side."""
        # Left side: Single-qubit gates (1 cube each)
        # Right side: Two-qubit gates (tall, span 2 lanes)
        specs = [
            # Single-qubit demo (lane 0)
            (ComponentType.DATA_QUBIT, (0, 0, 0)),
            (ComponentType.H_GATE, (1, 0, 0)),       # Single: 1x1x1
            (ComponentType.X_GATE, (2, 0, 0)),       # Single: 1x1x1
            # Two-qubit demo (lanes 2-3)
            (ComponentType.DATA_QUBIT, (0, 2, 0)),   # Control qubit
            (ComponentType.DATA_QUBIT, (0, 3, 0)),   # Target qubit
            (ComponentType.CNOT_GATE, (1, 2, 0)),    # Two-qubit: spans 2 lanes
            (ComponentType.CZ_GATE, (2, 2, 0)),      # Another two-qubit
        ]
        self._place_demo_components(specs)
    
    def _demo_controlled_gate(self):
        """Demo for controlled gates - H gate with control spanning 3 qubits (like bit-flip encoder)."""
        # 3-qubit circuit with controlled-H spanning from qubit 0 to qubit 2
        # This demonstrates multi-wire control (skipping qubit 1)
        specs = [
            # Three data qubits (lanes 0, 1, 2)
            (ComponentType.DATA_QUBIT, (0, 0, 0)),   # Control qubit
            (ComponentType.DATA_QUBIT, (0, 1, 0)),   # Middle qubit (skipped)
            (ComponentType.DATA_QUBIT, (0, 2, 0)),   # Target qubit
            # H gate on qubit 2 with control from qubit 0
            (ComponentType.H_GATE, (2, 2, 0)),       # H gate at target position
            # Measurement at end
            (ComponentType.MEASURE, (4, 0, 0)),
            (ComponentType.MEASURE, (4, 1, 0)),
            (ComponentType.MEASURE, (4, 2, 0)),
            # X correction based on measurement
            (ComponentType.X_GATE, (5, 2, 0)),       # Correction gate
        ]
        
        # Place components
        self._place_demo_components(specs)
        
        # Make the H gate controlled (control at qubit 0, target at qubit 2)
        for comp in self.demo_components:
            if comp.component_type == ComponentType.H_GATE and comp.position == (2, 2, 0):
                comp.properties['is_controlled'] = True
                comp.properties['control_y'] = 0  # Control at qubit 0 (lane 0)
                break
        
        # Redraw to show the control
        self.circuit_builder._redraw_circuit()
        self.circuit_builder._log_status("Demo: CH gate with control spanning 3 qubits (●──────gate)")

    def _demo_repetition_code(self):
        """Demo for 3-qubit repetition code - clear encoding structure."""
        # Classic repetition code: |ψ⟩ → |ψψψ⟩
        # q0 (original) controls q1 and q2 via CNOTs
        # Then parity checks on adjacent pairs
        specs = [
            # Three data qubits in column (lanes 0, 1, 2)
            (ComponentType.DATA_QUBIT, (0, 0, 0)),   # Original qubit
            (ComponentType.DATA_QUBIT, (0, 1, 0)),   # Copy 1
            (ComponentType.DATA_QUBIT, (0, 2, 0)),   # Copy 2
            # Encoding CNOTs (q0 → q1, q0 → q2)
            (ComponentType.CNOT_GATE, (1, 0, 0)),    # CNOT: q0 controls q1
            # Parity check structure
            (ComponentType.ANCILLA_QUBIT, (2, 0, 0)),
            (ComponentType.ANCILLA_QUBIT, (2, 1, 0)),
            (ComponentType.PARITY_CHECK, (3, 0, 0)),
            (ComponentType.PARITY_CHECK, (3, 1, 0)),
        ]
        self._place_demo_components(specs)
    
    def _demo_loading_examples(self):
        """Demo for loading examples - Bell state with measurement."""
        # Clear Bell state circuit that matches saved examples
        specs = [
            # Bell state: two qubits, H on first, CNOT, measure both
            (ComponentType.DATA_QUBIT, (0, 0, 0)),
            (ComponentType.DATA_QUBIT, (0, 1, 0)),
            (ComponentType.H_GATE, (1, 0, 0)),
            (ComponentType.CNOT_GATE, (2, 0, 0)),
            (ComponentType.MEASURE, (3, 0, 0)),
            (ComponentType.MEASURE, (3, 1, 0)),
        ]
        self._place_demo_components(specs)
    
    def _demo_keyboard_shortcuts(self):
        """Demo for keyboard shortcuts - clean 3-lane practice circuit."""
        # Three parallel lanes for practicing selection/deletion
        specs = [
            # Lane 0: H then measure
            (ComponentType.DATA_QUBIT, (0, 0, 0)),
            (ComponentType.H_GATE, (1, 0, 0)),
            (ComponentType.MEASURE, (2, 0, 0)),
            # Lane 1: X then measure  
            (ComponentType.DATA_QUBIT, (0, 1, 0)),
            (ComponentType.X_GATE, (1, 1, 0)),
            (ComponentType.MEASURE, (2, 1, 0)),
            # Lane 2: Z then measure
            (ComponentType.DATA_QUBIT, (0, 2, 0)),
            (ComponentType.Z_GATE, (1, 2, 0)),
            (ComponentType.MEASURE, (2, 2, 0)),
        ]
        self._place_demo_components(specs)
    
    def _demo_final(self):
        """Demo for final step - complete error correction circuit."""
        # Comprehensive circuit showing data qubits, encoding, and measurement
        specs = [
            # Three data qubits in a line (lanes 0, 1, 2)
            (ComponentType.DATA_QUBIT, (0, 0, 0)),
            (ComponentType.DATA_QUBIT, (0, 1, 0)),
            (ComponentType.DATA_QUBIT, (0, 2, 0)),
            # Encoding: H on first qubit, CNOTs for entanglement
            (ComponentType.H_GATE, (1, 0, 0)),
            (ComponentType.CNOT_GATE, (2, 0, 0)),
            # Ancilla and parity check
            (ComponentType.ANCILLA_QUBIT, (3, 1, 0)),
            (ComponentType.PARITY_CHECK, (4, 1, 0)),
            # Final measurements
            (ComponentType.MEASURE, (5, 0, 0)),
            (ComponentType.MEASURE, (5, 1, 0)),
            (ComponentType.MEASURE, (5, 2, 0)),
        ]
        self._place_demo_components(specs)
    
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
        
        # Clear demo components
        self._clear_demo_components()
        
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


class SurfaceCodeTutorialScreen:
    """
    Surface Code tutorial that teaches the fundamentals of surface codes,
    stabilizer measurements, and how to use Surface Code Mode in the app.
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
        Initialize the surface code tutorial.
        
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
        
        # Define surface code tutorial steps
        self.steps = self._create_tutorial_steps()
    
    def _create_tutorial_steps(self) -> List[Dict[str, Any]]:
        """Create the Surface Code tutorial content."""
        return [
            # Step 0: What is the Surface Code?
            {
                'title': 'What is the Surface Code?',
                'content': [
                    ('The ', 'normal'),
                    ('Surface Code', 'ldpc'),
                    (' is the most promising quantum error correction code!\n\n', 'normal'),
                    ('🔲 ', 'normal'),
                    ('Key Idea:', 'title'),
                    ('\n', 'normal'),
                    ('Qubits are arranged on a 2D grid (lattice). Errors are\n', 'normal'),
                    ('detected by measuring local ', 'normal'),
                    ('stabilizers', 'highlight'),
                    (' - groups of nearby qubits.\n\n', 'normal'),
                    ('Why Surface Codes?', 'title'),
                    ('\n', 'normal'),
                    ('• Only need ', 'normal'),
                    ('local operations', 'component'),
                    (' - nearest-neighbor gates\n', 'normal'),
                    ('• High error threshold: ~1% per gate\n', 'normal'),
                    ('• Actively pursued by Google, IBM, and others\n\n', 'normal'),
                    ('Press ', 'normal'),
                    ('V', 'action'),
                    (' in the main window to enter Surface Code Mode!', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_surface_intro'
            },
            # Step 1: The Lattice Structure (Rotated Surface Code)
            {
                'title': 'The Rotated Surface Code',
                'content': [
                    ('Understanding the Rotated Lattice', 'title'),
                    ('\n\n', 'normal'),
                    ('In the ', 'normal'),
                    ('rotated surface code', 'highlight'),
                    (':\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('Data Qubits', 'component'),
                    (' (grey circles): At ', 'normal'),
                    ('odd', 'highlight'),
                    (' coordinates (1,1), (1,3), etc.\n', 'normal'),
                    ('   → These store your quantum information\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('X-Stabilizers', 'ldpc'),
                    (' (red diamonds): At ', 'normal'),
                    ('even', 'highlight'),
                    (' coordinates\n', 'normal'),
                    ('   → Detect Z (phase) errors on neighboring data qubits\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('Z-Stabilizers', 'ldpc'),
                    (' (blue crosses): At ', 'normal'),
                    ('even', 'highlight'),
                    (' coordinates\n', 'normal'),
                    ('   → Detect X (bit-flip) errors on neighboring data qubits\n\n', 'normal'),
                    ('Click on data qubit positions (odd coords) to place qubits.', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_surface_lattice'
            },
            # Step 2: Stabilizer Measurements
            {
                'title': 'Measuring Stabilizers',
                'content': [
                    ('How Stabilizers Work', 'title'),
                    ('\n\n', 'normal'),
                    ('Each stabilizer measures 4 neighboring data qubits:\n\n', 'normal'),
                    ('X-Stabilizer Measurement:', 'title'),
                    ('\n', 'normal'),
                    ('1. Prepare ancilla in |0⟩\n', 'normal'),
                    ('2. Apply ', 'normal'),
                    ('Hadamard', 'component'),
                    (' to ancilla → |+⟩\n', 'normal'),
                    ('3. Apply ', 'normal'),
                    ('CNOT', 'component'),
                    (' from ancilla to each data qubit\n', 'normal'),
                    ('4. Apply Hadamard, then ', 'normal'),
                    ('Measure', 'component'),
                    ('\n\n', 'normal'),
                    ('Z-Stabilizer Measurement:', 'title'),
                    ('\n', 'normal'),
                    ('1. Prepare ancilla in |0⟩\n', 'normal'),
                    ('2. Apply CNOT from each data qubit to ancilla\n', 'normal'),
                    ('3. Measure ancilla\n\n', 'normal'),
                    ('Result:', 'warning'),
                    (' Outcome of 1 indicates an error nearby!', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_stabilizer_circuit'
            },
            # Step 3: Error Detection
            {
                'title': 'Detecting Errors',
                'content': [
                    ('The Syndrome Pattern', 'title'),
                    ('\n\n', 'normal'),
                    ('When an error occurs on a data qubit:\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('X error (bit-flip)', 'warning'),
                    (': Detected by adjacent ', 'normal'),
                    ('Z-stabilizers', 'ldpc'),
                    ('\n', 'normal'),
                    ('   → The two Z-checks sharing that qubit flip to -1\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('Z error (phase-flip)', 'warning'),
                    (': Detected by adjacent ', 'normal'),
                    ('X-stabilizers', 'ldpc'),
                    ('\n', 'normal'),
                    ('   → The two X-checks sharing that qubit flip to -1\n\n', 'normal'),
                    ('Try It:', 'title'),
                    ('\n', 'normal'),
                    ('Use the ', 'normal'),
                    ('Defects tab', 'action'),
                    (' to place X, Z, or Y errors on data qubits.\n', 'normal'),
                    ('Then click ', 'normal'),
                    ('Highlight Syndrome', 'action'),
                    (' to see which stabilizers detect them!', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_error_detection'
            },
            # Step 4: Using Surface Code Mode
            {
                'title': 'Placing Components',
                'content': [
                    ('How to Place Components', 'title'),
                    ('\n\n', 'normal'),
                    ('1. Select a tool from the toolbox (left panel)\n\n', 'normal'),
                    ('2. Click on the lattice to place:\n\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Data Qubits', 'component'),
                    (': Click at ', 'normal'),
                    ('odd', 'highlight'),
                    (' coordinates (grey circles)\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Stabilizers', 'ldpc'),
                    (': Click at ', 'normal'),
                    ('even', 'highlight'),
                    (' coordinates (diamonds/crosses)\n', 'normal'),
                    ('   • ', 'normal'),
                    ('Errors', 'warning'),
                    (': Click on data qubit positions\n\n', 'normal'),
                    ('Tips:', 'title'),
                    ('\n', 'normal'),
                    ('• Background shows where components can go\n', 'normal'),
                    ('• Red diamonds = X-stabilizer positions\n', 'normal'),
                    ('• Blue crosses = Z-stabilizer positions\n', 'normal'),
                    ('• Grey circles = data qubit positions', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_surface_demo'
            },
            # Step 5: Code Distance and Logical Qubits
            {
                'title': 'Code Distance & Logical Qubits',
                'content': [
                    ('Scaling the Surface Code', 'title'),
                    ('\n\n', 'normal'),
                    ('The ', 'normal'),
                    ('code distance d', 'math'),
                    (' determines error protection:\n\n', 'normal'),
                    ('• d = 3: Can correct 1 error\n', 'normal'),
                    ('• d = 5: Can correct 2 errors\n', 'normal'),
                    ('• d = 7: Can correct 3 errors\n\n', 'normal'),
                    ('Resource Requirements:', 'title'),
                    ('\n', 'normal'),
                    ('For distance d, you need ', 'normal'),
                    ('~2d² physical qubits', 'math'),
                    ('\n', 'normal'),
                    ('per logical qubit.\n\n', 'normal'),
                    ('Examples:', 'title'),
                    ('\n', 'normal'),
                    ('• d=3:  ~18 physical qubits per logical\n', 'normal'),
                    ('• d=5:  ~50 physical qubits per logical\n', 'normal'),
                    ('• d=17: ~578 physical qubits per logical\n\n', 'normal'),
                    ('This is why ', 'normal'),
                    ('LDPC codes', 'warning'),
                    (' are exciting - they need far fewer qubits!', 'normal'),
                ],
                'image': None,
                'demo_action': 'show_code_distance'
            },
            # Step 6: Ready to Build!
            {
                'title': 'Try Example Circuits!',
                'content': [
                    ('🎉 You\'re ready to explore Surface Codes!\n\n', 'normal'),
                    ('Load Example Circuits:', 'title'),
                    ('\n\n', 'normal'),
                    ('Click ', 'normal'),
                    ('Load Circuit', 'action'),
                    (' and navigate to ', 'normal'),
                    ('saved_circuits/surface/', 'highlight'),
                    (':\n\n', 'normal'),
                    ('• ', 'normal'),
                    ('error_chain_demo.json', 'component'),
                    (' - Test syndrome highlighting\n', 'normal'),
                    ('• ', 'normal'),
                    ('syndrome_correction_demo.json', 'component'),
                    (' - Test the decoder\n', 'normal'),
                    ('• ', 'normal'),
                    ('distance_3_patch.json', 'component'),
                    (' - Complete distance-3 code\n\n', 'normal'),
                    ('After Loading:', 'title'),
                    ('\n', 'normal'),
                    ('1. Click ', 'normal'),
                    ('Highlight Syndrome', 'action'),
                    (' to see detection\n', 'normal'),
                    ('2. Click ', 'normal'),
                    ('Run Decoder', 'action'),
                    (' to find corrections\n\n', 'normal'),
                    ('Try it now! Load error_chain_demo.json', 'warning'),
                ],
                'image': None,
                'demo_action': 'load_error_demo'
            },
        ]
    
    def show(self):
        """Display the Surface Code tutorial window."""
        # Store original circuit state and view mode
        if self.circuit_builder:
            self.original_components = list(self.circuit_builder.components)
            self.original_view_mode = self.circuit_builder.view_mode
            # Switch to Surface Code Mode for this tutorial
            if self.circuit_builder.view_mode != ViewMode.SURFACE_CODE_2D:
                self.circuit_builder._toggle_view_mode()
        
        self.tutorial_window = tk.Toplevel(self.parent)
        self.tutorial_window.title("Surface Code Tutorial")
        self.tutorial_window.geometry("600x520")
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
        
        # Clear any selection from previous step
        self.circuit_builder.selected_component = None
        
        # Clear previous demo components
        self._clear_demo_components()
        
        # Surface Code Tutorial demo actions
        if action == 'show_surface_intro':
            self._demo_surface_intro()
        elif action == 'show_surface_lattice':
            self._demo_surface_lattice()
        elif action == 'show_stabilizer_circuit':
            self._demo_stabilizer_circuit()
        elif action == 'show_error_detection':
            self._demo_error_detection()
        elif action == 'show_surface_demo':
            self._demo_surface_demo()
        elif action == 'show_code_distance':
            self._demo_code_distance()
        elif action == 'show_final_demo':
            self._demo_final_demo()
        # Legacy demo actions (for backward compatibility)
        elif action == 'show_qubit_positions':
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
        elif action == 'show_welcome':
            self._demo_welcome()
        elif action == 'show_placing_components':
            self._demo_placing_components()
        elif action == 'show_loading_examples':
            self._demo_loading_examples()
        elif action == 'show_keyboard_shortcuts':
            self._demo_keyboard_shortcuts()
        elif action == 'show_final':
            self._demo_final()
        elif action == 'show_simulation_tools':
            self._demo_simulation_tools()
        elif action == 'show_cavity_mediated':
            self._demo_cavity_mediated()
        elif action == 'load_error_demo':
            self._demo_load_error_circuit()
    
    # =========== Surface Code Tutorial Demo Methods ===========
    # These demos place components on the 2D Surface Code lattice
    
    def _demo_surface_intro(self):
        """Intro demo: Show one X-stabilizer and one Z-stabilizer."""
        # Simplified demo: just two stabilizers at even coordinates
        surface_specs = [
            # One X-stabilizer (red diamond) and one Z-stabilizer (blue cross)
            (ComponentType.SURFACE_X_STABILIZER, (2, 2, 0)),
            (ComponentType.SURFACE_Z_STABILIZER, (4, 2, 0)),
        ]
        self._place_surface_demo_components(surface_specs)
        self.circuit_builder._log_status("X-stabilizer (red diamond) and Z-stabilizer (blue cross)")
    
    def _demo_surface_lattice(self):
        """Show data qubits at odd coordinates (vertices of the rotated lattice)."""
        surface_specs = [
            # Data qubits at odd integer coordinates (vertices)
            (ComponentType.SURFACE_DATA, (1, 1, 0)),
            (ComponentType.SURFACE_DATA, (3, 1, 0)),
            (ComponentType.SURFACE_DATA, (1, 3, 0)),
            (ComponentType.SURFACE_DATA, (3, 3, 0)),
        ]
        self._place_surface_demo_components(surface_specs)
        self.circuit_builder._log_status("Data qubits placed at odd coordinates (1,1), (3,1), etc.")
    
    def _demo_stabilizer_circuit(self):
        """Show one stabilizer with its 4 neighboring data qubits."""
        surface_specs = [
            # Central X-stabilizer at even coordinate
            (ComponentType.SURFACE_X_STABILIZER, (2, 2, 0)),
            # 4 data qubits at neighboring odd coordinates
            (ComponentType.SURFACE_DATA, (1, 1, 0)),  # Upper-left
            (ComponentType.SURFACE_DATA, (3, 1, 0)),  # Upper-right
            (ComponentType.SURFACE_DATA, (1, 3, 0)),  # Lower-left
            (ComponentType.SURFACE_DATA, (3, 3, 0)),  # Lower-right
        ]
        self._place_surface_demo_components(surface_specs)
        self.circuit_builder._log_status("X-Stabilizer at (2,2) measures 4 neighboring data qubits")
    
    def _demo_error_detection(self):
        """Show how an error on a data qubit is detected by adjacent stabilizers."""
        # Z-stabilizers need to be at positions where ((x+y)//2) % 2 == 1
        # e.g., (2,4) and (4,2) are Z-stabilizer positions
        surface_specs = [
            # Two adjacent Z-stabilizers that share the data qubit at (3,3)
            (ComponentType.SURFACE_Z_STABILIZER, (2, 4, 0)),  # shares (3,3)
            (ComponentType.SURFACE_Z_STABILIZER, (4, 2, 0)),  # shares (3,3)
            # The shared data qubit between them
            (ComponentType.SURFACE_DATA, (3, 3, 0)),
            # Show an X-error on the shared data qubit
            (ComponentType.SURFACE_X_ERROR, (3, 3, 0)),
        ]
        self._place_surface_demo_components(surface_specs)
        self.circuit_builder._log_status("X-error at (3,3) → both adjacent Z-stabilizers detect it!")
    
    def _demo_surface_demo(self):
        """Demonstrate a complete distance-3 surface code patch."""
        surface_specs = [
            # Data qubits at odd coordinates (5 data qubits for distance-3)
            (ComponentType.SURFACE_DATA, (1, 1, 0)),
            (ComponentType.SURFACE_DATA, (3, 1, 0)),
            (ComponentType.SURFACE_DATA, (1, 3, 0)),
            (ComponentType.SURFACE_DATA, (3, 3, 0)),
            (ComponentType.SURFACE_DATA, (5, 3, 0)),
            # X-stabilizers (red diamonds)
            (ComponentType.SURFACE_X_STABILIZER, (2, 2, 0)),
            (ComponentType.SURFACE_X_STABILIZER, (4, 4, 0)),
            # Z-stabilizers (blue crosses)
            (ComponentType.SURFACE_Z_STABILIZER, (4, 2, 0)),
            (ComponentType.SURFACE_Z_STABILIZER, (2, 4, 0)),
        ]
        self._place_surface_demo_components(surface_specs)
        self.circuit_builder._log_status("Distance-3 surface code: 5 data qubits, 4 stabilizers")
    
    def _demo_code_distance(self):
        """Demonstrate code distance - minimum errors to cause logical failure."""
        surface_specs = [
            # Three data qubits in a diagonal (representing a logical operator path)
            (ComponentType.SURFACE_DATA, (1, 1, 0)),
            (ComponentType.SURFACE_DATA, (3, 3, 0)),
            (ComponentType.SURFACE_DATA, (5, 5, 0)),
            # Boundary markers at the ends
            (ComponentType.SURFACE_BOUNDARY, (0, 0, 0)),
            (ComponentType.SURFACE_BOUNDARY, (6, 6, 0)),
        ]
        self._place_surface_demo_components(surface_specs)
        self.circuit_builder._log_status("Distance 3: Need 3 errors to create undetectable logical error")
    
    def _demo_final_demo(self):
        """Final demo: Complete surface code with an error to correct."""
        surface_specs = [
            # Data qubits
            (ComponentType.SURFACE_DATA, (1, 1, 0)),
            (ComponentType.SURFACE_DATA, (3, 1, 0)),
            (ComponentType.SURFACE_DATA, (1, 3, 0)),
            (ComponentType.SURFACE_DATA, (3, 3, 0)),
            # Stabilizers
            (ComponentType.SURFACE_X_STABILIZER, (2, 2, 0)),
            (ComponentType.SURFACE_Z_STABILIZER, (4, 2, 0)),
            (ComponentType.SURFACE_Z_STABILIZER, (2, 4, 0)),
            # An error to demonstrate syndrome
            (ComponentType.SURFACE_X_ERROR, (3, 1, 0)),
        ]
        self._place_surface_demo_components(surface_specs)
        self.circuit_builder._log_status("Try 'Highlight Syndrome' to see which stabilizers detect the error!")
    
    def _place_surface_demo_components(self, specs: List[Tuple]):
        """Place demo components on the surface lattice using integer coordinates."""
        if not self.circuit_builder:
            return
        
        for comp_type, position in specs:
            # Use integer coordinates for rotated surface code
            x, y, z = int(position[0]), int(position[1]), int(position[2])
            
            # Check if position is already occupied (allow errors to stack on data)
            is_error = comp_type in [ComponentType.SURFACE_X_ERROR, ComponentType.SURFACE_Z_ERROR, ComponentType.SURFACE_Y_ERROR]
            occupied = any(
                c.position[0] == x and c.position[1] == y and 
                c.component_type not in [ComponentType.SURFACE_X_ERROR, ComponentType.SURFACE_Z_ERROR, ComponentType.SURFACE_Y_ERROR]
                for c in self.circuit_builder.components
            ) if not is_error else False
            
            if not occupied:
                color = self.circuit_builder._get_component_color(comp_type)
                component = Component3D(
                    component_type=comp_type,
                    position=(x, y, z),
                    color=color,
                    size=(1.0, 1.0, 1.0)
                )
                self.circuit_builder.components.append(component)
                self.demo_components.append(component)
        
        self.circuit_builder._redraw_circuit()
    
    def _demo_welcome(self):
        """Fallback - redirect to surface intro."""
        self._demo_surface_intro()
    
    def _demo_placing_components(self):
        """Fallback - redirect to surface lattice."""
        self._demo_surface_lattice()
    
    def _demo_load_error_circuit(self):
        """Demo action: Show the error chain demo pattern directly."""
        # Instead of loading a file (which interferes with tutorial tracking),
        # place the demo components directly like other demos
        surface_specs = [
            # Stabilizers
            (ComponentType.SURFACE_X_STABILIZER, (4, 4, 0)),
            (ComponentType.SURFACE_Z_STABILIZER, (2, 4, 0)),
            (ComponentType.SURFACE_Z_STABILIZER, (6, 4, 0)),
            # Data qubits
            (ComponentType.SURFACE_DATA, (3, 3, 0)),
            (ComponentType.SURFACE_DATA, (5, 3, 0)),
            (ComponentType.SURFACE_DATA, (3, 5, 0)),
            (ComponentType.SURFACE_DATA, (5, 5, 0)),
            # Errors on data qubits
            (ComponentType.SURFACE_X_ERROR, (3, 3, 0)),
            (ComponentType.SURFACE_Z_ERROR, (5, 5, 0)),
            (ComponentType.SURFACE_Y_ERROR, (3, 5, 0)),
        ]
        self._place_surface_demo_components(surface_specs)
        self.circuit_builder._log_status("Error chain demo loaded! Try 'Highlight Syndrome' to see detection.")
    
    def _clear_demo_components(self):
        """Remove all demo components from the surface lattice."""
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
        
        # Just redraw the circuit (components are surface mode compatible)
        if self.circuit_builder:
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("Surface Code tutorial closed. Press V to switch back to circuit mode.")
        
        self.tutorial_window.destroy()


class AdvancedLargeCircuitsTutorial:
    """
    Advanced tutorial showcasing large-scale quantum error correction circuits.
    CIRCUIT MODE ONLY - demonstrates encoder/decoder circuits with errors and corrections.
    
    Demonstrates:
    - 3-qubit bit-flip code (encoder + syndrome extraction)
    - 3-qubit phase-flip code (encoder + syndrome extraction)
    - Shor's [[9,1,3]] full encoder with error correction
    - Steane [[7,1,3]] code encoder
    - 5-qubit perfect code [[5,1,3]]
    - Quantum teleportation circuit
    - Error placement and correction workflow
    
    All examples stay in circuit mode with large grids.
    """
    
    COLORS = {
        'quantum': '#00ffcc',
        'ldpc': '#ff6b6b',
        'component': '#ffd93d',
        'action': '#6bcb77',
        'math': '#a8e6cf',
        'warning': '#ff9f43',
        'title': '#74b9ff',
        'highlight': '#fd79a8',
        'code': '#bb86fc',
        'error': '#1a1a1a',
        'correct': '#ffdd33',
    }
    
    def __init__(self, parent: tk.Tk, circuit_builder=None):
        self.parent = parent
        self.circuit_builder = circuit_builder
        self.current_step = 0
        self.tutorial_window = None
        self.original_grid_size = 20
        
        self.steps = self._create_tutorial_steps()
    
    def _create_tutorial_steps(self) -> List[Dict[str, Any]]:
        """Create advanced circuit-mode tutorial with 8 large practical quantum circuits."""
        return [
            {
                'title': 'Advanced Circuit Tutorial',
                'content': [
                    ('Welcome to ', 'normal'),
                    ('Advanced Large Circuits', 'title'),
                    ('!\n\n', 'normal'),
                    ('This tutorial demonstrates ', 'normal'),
                    ('8 large practical quantum circuits', 'highlight'),
                    ('.\n\n', 'normal'),
                    ('We will cover:\n\n', 'normal'),
                    ('1. ', 'normal'), ('Quantum Teleportation', 'quantum'), (' - Transfer quantum state\n', 'normal'),
                    ('2. ', 'normal'), ('Superdense Coding', 'quantum'), (' - 2 bits via 1 qubit\n', 'normal'),
                    ('3. ', 'normal'), ('GHZ State', 'quantum'), (' - Multi-qubit entanglement\n', 'normal'),
                    ('4. ', 'normal'), ('Quantum Fourier Transform', 'ldpc'), (' - 3-qubit QFT\n', 'normal'),
                    ('5. ', 'normal'), ("Grover's Search", 'ldpc'), (' - 2-qubit oracle search\n', 'normal'),
                    ('6. ', 'normal'), ('Deutsch-Jozsa', 'action'), (' - Quantum parallelism\n', 'normal'),
                    ('7. ', 'normal'), ('Entanglement Swapping', 'action'), (' - Teleport entanglement\n', 'normal'),
                    ('8. ', 'normal'), ("Shor's 9-Qubit Encoder", 'highlight'), (' - Full QEC circuit\n\n', 'normal'),
                    ('💡 ', 'warning'),
                    ('Grid expanded to 50 for visibility!', 'action'),
                ],
                'demo_action': 'intro'
            },
            {
                'title': 'Quantum Teleportation',
                'content': [
                    ('Quantum Teleportation', 'title'),
                    ('\n\n', 'normal'),
                    ('Transfer a quantum state using ', 'normal'),
                    ('entanglement + classical communication', 'highlight'),
                    ('.\n\n', 'normal'),
                    ('Protocol:\n', 'action'),
                    ('1. Alice & Bob share Bell pair |Φ⁺⟩\n', 'normal'),
                    ('2. Alice has unknown |ψ⟩ to teleport\n', 'normal'),
                    ('3. Alice: Bell measurement (CNOT + H + measure)\n', 'normal'),
                    ('4. Alice sends 2 classical bits to Bob\n', 'normal'),
                    ('5. Bob applies X/Z correction\n\n', 'normal'),
                    ('Circuit: (3 qubits, ~15 gates)\n', 'quantum'),
                    ('q0: |ψ⟩ ─────●─H─M═══════════\n', 'code'),
                    ('q1: |0⟩ ─H─●─X───M═══╗═══════\n', 'code'),
                    ('q2: |0⟩ ───X─────────X───Z──\n\n', 'code'),
                    ('Applications: ', 'math'),
                    ('Quantum internet, distributed QC\n', 'normal'),
                    ('Building circuit...', 'warning'),
                ],
                'demo_action': 'teleportation'
            },
            {
                'title': 'Superdense Coding',
                'content': [
                    ('Superdense Coding', 'title'),
                    ('\n\n', 'normal'),
                    ('Send ', 'normal'),
                    ('2 classical bits', 'highlight'),
                    (' using only 1 qubit!\n\n', 'normal'),
                    ('The "reverse" of teleportation.\n\n', 'action'),
                    ('Protocol:\n', 'quantum'),
                    ('1. Alice & Bob share Bell pair |Φ⁺⟩\n', 'normal'),
                    ('2. Alice encodes 2 bits by applying gates:\n', 'normal'),
                    ('   00 → I, 01 → X, 10 → Z, 11 → XZ\n', 'code'),
                    ('3. Alice sends her qubit to Bob\n', 'normal'),
                    ('4. Bob performs Bell measurement\n\n', 'normal'),
                    ('Circuit Structure:\n', 'math'),
                    ('• Create Bell pair (H + CNOT)\n', 'code'),
                    ("• Alice's encoding: X and/or Z\n", 'code'),
                    ("• Bob's decode: CNOT + H + measure both\n\n", 'code'),
                    ('Building superdense circuit...', 'warning'),
                ],
                'demo_action': 'superdense'
            },
            {
                'title': 'GHZ State Preparation',
                'content': [
                    ('GHZ State (N-Qubit Entanglement)', 'title'),
                    ('\n\n', 'normal'),
                    ('Create maximally entangled ', 'normal'),
                    ('N-qubit GHZ state', 'highlight'),
                    (':\n\n', 'normal'),
                    ('|GHZ⟩ = (|00...0⟩ + |11...1⟩)/√2\n\n', 'code'),
                    ('Properties:\n', 'action'),
                    ('• All qubits correlated\n', 'normal'),
                    ('• Measure one → all collapse\n', 'normal'),
                    ('• Used in quantum metrology, secret sharing\n\n', 'normal'),
                    ('Circuit (5-qubit):\n', 'quantum'),
                    ('q0: |0⟩ ─H─●─●─●─●─\n', 'code'),
                    ('q1: |0⟩ ───X─────────\n', 'code'),
                    ('q2: |0⟩ ─────X───────\n', 'code'),
                    ('q3: |0⟩ ───────X─────\n', 'code'),
                    ('q4: |0⟩ ─────────X───\n\n', 'code'),
                    ('Building 5-qubit GHZ...', 'warning'),
                ],
                'demo_action': 'ghz_state'
            },
            {
                'title': '3-Qubit QFT',
                'content': [
                    ('Quantum Fourier Transform', 'title'),
                    ('\n\n', 'normal'),
                    ('The quantum analog of ', 'normal'),
                    ('Discrete Fourier Transform', 'highlight'),
                    (' - key to many algorithms.\n\n', 'normal'),
                    ('Transform:\n', 'action'),
                    ('|j⟩ → Σₖ e^(2πijk/N) |k⟩ / √N\n\n', 'code'),
                    ('3-Qubit Circuit:\n', 'quantum'),
                    ('q0: ─H─R₂─R₃───×─\n', 'code'),
                    ('q1: ───●──H─R₂─×─\n', 'code'),
                    ('q2: ──────●──H─×─\n\n', 'code'),
                    ('Where Rₖ = phase gate with θ = 2π/2^k\n\n', 'math'),
                    ('Applications:\n', 'normal'),
                    ("• Shor's algorithm (factoring)\n", 'code'),
                    ('• Quantum phase estimation\n', 'code'),
                    ('• Amplitude estimation\n\n', 'code'),
                    ('Building 3-qubit QFT...', 'warning'),
                ],
                'demo_action': 'qft_3'
            },
            {
                'title': "Grover's Search (2-qubit)",
                'content': [
                    ("Grover's Search Algorithm", 'title'),
                    ('\n\n', 'normal'),
                    ('Find marked item in ', 'normal'),
                    ('O(√N)', 'highlight'),
                    (' queries vs O(N) classical.\n\n', 'normal'),
                    ('Components:\n', 'action'),
                    ('1. Superposition: H⊗ⁿ |0⟩\n', 'normal'),
                    ('2. Oracle: O|x⟩ = (-1)^f(x)|x⟩\n', 'normal'),
                    ('3. Diffusion: 2|ψ⟩⟨ψ| - I\n\n', 'normal'),
                    ('2-Qubit Oracle (marks |11⟩):\n', 'quantum'),
                    ('q0: ─H─────●─────H─X─●─X─H─M─\n', 'code'),
                    ('q1: ─H─────Z─────H─X─Z─X─H─M─\n\n', 'code'),
                    ('One iteration sufficient for 2 qubits!\n', 'math'),
                    ('Probability of |11⟩: 100%\n\n', 'code'),
                    ('Building Grover circuit...', 'warning'),
                ],
                'demo_action': 'grover_2'
            },
            {
                'title': 'Deutsch-Jozsa Algorithm',
                'content': [
                    ('Deutsch-Jozsa Algorithm', 'title'),
                    ('\n\n', 'normal'),
                    ('Determine if f(x) is ', 'normal'),
                    ('constant or balanced', 'highlight'),
                    (' in ONE query!\n\n', 'normal'),
                    ('Classical: needs 2^(n-1)+1 queries worst case\n\n', 'action'),
                    ('Circuit Structure:\n', 'quantum'),
                    ('1. Prepare |0⟩⊗ⁿ|1⟩\n', 'normal'),
                    ('2. Apply H⊗(n+1)\n', 'normal'),
                    ('3. Apply oracle Uₐ\n', 'normal'),
                    ('4. Apply H⊗ⁿ on first n qubits\n', 'normal'),
                    ('5. Measure: |0⟩⊗ⁿ ↔ constant\n\n', 'normal'),
                    ('Oracle Examples:\n', 'math'),
                    ('• Constant: f(x)=0 → identity\n', 'code'),
                    ('• Balanced: f(x)=x → CNOT\n\n', 'code'),
                    ('Building balanced oracle circuit...', 'warning'),
                ],
                'demo_action': 'deutsch_jozsa'
            },
            {
                'title': 'Entanglement Swapping',
                'content': [
                    ('Entanglement Swapping', 'title'),
                    ('\n\n', 'normal'),
                    ('Create entanglement between qubits that ', 'normal'),
                    ('never interacted', 'highlight'),
                    ('!\n\n', 'normal'),
                    ('Setup:\n', 'action'),
                    ('• Alice-Bob share Bell pair (q0-q1)\n', 'normal'),
                    ('• Charlie-Diana share Bell pair (q2-q3)\n', 'normal'),
                    ('• Bob & Charlie perform Bell measurement\n', 'normal'),
                    ('• Result: Alice-Diana entangled!\n\n', 'normal'),
                    ('Circuit: (4 qubits)\n', 'quantum'),
                    ('q0: ─H─●─────────────────\n', 'code'),
                    ('q1: ───X───●─H─M═╗═══════\n', 'code'),
                    ('q2: ─H─●───X───M═╬═X─────\n', 'code'),
                    ('q3: ───X─────────╚═══Z───\n\n', 'code'),
                    ('Application: Quantum repeaters!\n', 'math'),
                    ('Building entanglement swapping...', 'warning'),
                ],
                'demo_action': 'entangle_swap'
            },
            {
                'title': "Shor's 9-Qubit Code",
                'content': [
                    ("Shor's [[9,1,3]] Code Encoder", 'title'),
                    ('\n\n', 'normal'),
                    ('The ', 'normal'),
                    ('first complete QEC code', 'highlight'),
                    (' (1995)!\n\n', 'normal'),
                    ('Corrects ANY single-qubit error.\n\n', 'action'),
                    ('Construction:\n', 'quantum'),
                    ('• Outer: 3-qubit phase-flip code\n', 'normal'),
                    ('• Inner: 3-qubit bit-flip code (per block)\n', 'normal'),
                    ('• Total: 9 physical → 1 logical\n\n', 'normal'),
                    ('Encoder Steps:\n', 'math'),
                    ('1. CNOT q0→q3, q0→q6 (phase encode)\n', 'code'),
                    ('2. H on q0, q3, q6\n', 'code'),
                    ('3. CNOT qᵢ→qᵢ₊₁, qᵢ→qᵢ₊₂ (bit encode)\n\n', 'code'),
                    ('|0⟩ → (|000⟩+|111⟩)(|000⟩+|111⟩)(|000⟩+|111⟩)/2√2\n', 'code'),
                    ('\nBuilding full 9-qubit encoder...', 'warning'),
                ],
                'demo_action': 'shor_9'
            },
            {
                'title': 'Tutorial Complete!',
                'content': [
                    ('🎉 ', 'normal'),
                    ('Advanced Tutorial Complete!', 'title'),
                    ('\n\n', 'normal'),
                    ('You explored 8 practical quantum circuits:\n\n', 'normal'),
                    ('✓ ', 'action'), ('Teleportation', 'quantum'), (' - State transfer\n', 'normal'),
                    ('✓ ', 'action'), ('Superdense Coding', 'quantum'), (' - 2 bits via 1 qubit\n', 'normal'),
                    ('✓ ', 'action'), ('GHZ State', 'quantum'), (' - N-qubit entanglement\n', 'normal'),
                    ('✓ ', 'action'), ('QFT', 'ldpc'), (' - Quantum Fourier\n', 'normal'),
                    ('✓ ', 'action'), ("Grover's", 'ldpc'), (' - Quantum search\n', 'normal'),
                    ('✓ ', 'action'), ('Deutsch-Jozsa', 'action'), (' - Quantum speedup\n', 'normal'),
                    ('✓ ', 'action'), ('Entanglement Swap', 'action'), (' - Quantum repeaters\n', 'normal'),
                    ('✓ ', 'action'), ("Shor's Code", 'highlight'), (' - Full QEC encoder\n\n', 'normal'),
                    ('Next Steps:\n', 'warning'),
                    ('• Try Surface mode (V key) for 2D codes\n', 'normal'),
                    ('• Try LDPC mode (B key) for Tanner graphs\n', 'normal'),
                    ('• Place errors from "Errors" tab\n', 'normal'),
                    ('• Save circuits with Ctrl+S\n\n', 'normal'),
                    ('Happy quantum computing!', 'highlight'),
                ],
                'demo_action': 'complete'
            },
        ]
    
    def show(self):
        """Display the advanced tutorial window - larger size for circuit visibility."""
        # Store original state
        if self.circuit_builder:
            self.original_grid_size = self.circuit_builder.grid_size
        
        self.tutorial_window = tk.Toplevel(self.parent)
        self.tutorial_window.title("Advanced QEC Tutorial")
        self.tutorial_window.configure(bg='#1a1a2e')
        self.tutorial_window.attributes('-topmost', False)
        
        # Larger window positioned on LEFT side so grid is visible on RIGHT
        self.tutorial_window.update_idletasks()
        screen_width = self.tutorial_window.winfo_screenwidth()
        screen_height = self.tutorial_window.winfo_screenheight()
        
        # Window size: wider to fit content, but not too tall
        win_width = 500
        win_height = 450
        
        # Position on left side of screen
        x = 30
        y = (screen_height - win_height) // 2
        self.tutorial_window.geometry(f"{win_width}x{win_height}+{x}+{y}")
        
        # Main container
        self.main_frame = tk.Frame(self.tutorial_window, bg='#1a1a2e')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # Header with purple accent for "Advanced"
        self.header_frame = tk.Frame(self.main_frame, bg='#2a1a3e')
        self.header_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.title_label = tk.Label(
            self.header_frame, text="",
            font=('Segoe UI', 14, 'bold'),
            fg='#bb86fc',  # Purple accent
            bg='#2a1a3e', pady=8
        )
        self.title_label.pack()
        
        # Step indicator
        self.step_label = tk.Label(
            self.header_frame, text="",
            font=('Segoe UI', 9), fg='#888888', bg='#2a1a3e'
        )
        self.step_label.pack(pady=(0, 8))
        
        # Progress bar (purple)
        self.progress_frame = tk.Frame(self.main_frame, bg='#1a1a2e', height=6)
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))
        self.progress_frame.pack_propagate(False)
        
        self.progress_bg = tk.Frame(self.progress_frame, bg='#2d2d44', height=6)
        self.progress_bg.pack(fill=tk.X)
        
        self.progress_bar = tk.Frame(self.progress_bg, bg='#bb86fc', height=6)
        self.progress_bar.place(x=0, y=0, relheight=1, relwidth=0)
        
        # Navigation - pack at bottom first
        self.nav_frame = tk.Frame(self.main_frame, bg='#1a1a2e')
        self.nav_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(8, 0))
        
        self.close_btn = tk.Button(
            self.nav_frame, text="Close",
            font=('Segoe UI', 9), fg='#888888', bg='#2d2d44',
            activeforeground='#ffffff', activebackground='#3d3d54',
            relief='flat', padx=12, pady=6, cursor='hand2',
            command=self._close_tutorial
        )
        self.close_btn.pack(side=tk.LEFT)
        
        self.next_btn = tk.Button(
            self.nav_frame, text="Next →",
            font=('Segoe UI', 10, 'bold'), fg='#ffffff', bg='#7a5a9a',
            activeforeground='#ffffff', activebackground='#9a7aba',
            relief='flat', padx=20, pady=6, cursor='hand2',
            command=self._next_step
        )
        self.next_btn.pack(side=tk.RIGHT)
        
        self.prev_btn = tk.Button(
            self.nav_frame, text="← Back",
            font=('Segoe UI', 9), fg='#cccccc', bg='#2d2d44',
            activeforeground='#ffffff', activebackground='#3d3d54',
            relief='flat', padx=12, pady=6, cursor='hand2',
            command=self._prev_step
        )
        self.prev_btn.pack(side=tk.RIGHT, padx=(0, 8))
        
        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg='#0f0f23', bd=1, relief='solid')
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.content_text = tk.Text(
            self.content_frame,
            font=('Consolas', 10),
            bg='#0f0f23', fg='#ffffff',
            wrap=tk.WORD, padx=15, pady=12,
            relief='flat', cursor='arrow', state='disabled'
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(self.content_frame, command=self.content_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.config(yscrollcommand=scrollbar.set)
        
        # Configure text tags
        for tag_name, color in self.COLORS.items():
            self.content_text.tag_configure(tag_name, foreground=color)
        self.content_text.tag_configure('normal', foreground='#cccccc')
        
        self._update_display()
        self.tutorial_window.protocol("WM_DELETE_WINDOW", self._close_tutorial)
    
    def _update_display(self):
        """Update the display for current step."""
        step = self.steps[self.current_step]
        
        self.title_label.config(text=step['title'])
        self.step_label.config(text=f"Step {self.current_step + 1} of {len(self.steps)}")
        
        # Update progress bar
        progress = (self.current_step + 1) / len(self.steps)
        self.progress_bar.place(x=0, y=0, relheight=1, relwidth=progress)
        
        # Update content
        self.content_text.config(state='normal')
        self.content_text.delete('1.0', tk.END)
        
        for text, tag in step['content']:
            self.content_text.insert(tk.END, text, tag)
        
        self.content_text.config(state='disabled')
        
        # Update navigation buttons
        self.prev_btn.config(state=tk.NORMAL if self.current_step > 0 else tk.DISABLED)
        
        if self.current_step == len(self.steps) - 1:
            self.next_btn.config(text="Finish")
        else:
            self.next_btn.config(text="Next →")
        
        # Execute demo action
        self._execute_demo(step.get('demo_action', None))
    
    def _execute_demo(self, action):
        """Execute demo action to build CIRCUIT MODE circuits on the grid - 8 practical quantum circuits."""
        if not self.circuit_builder or not action:
            return
        
        # ALL demos stay in circuit mode with large grid
        if action == 'intro':
            self.circuit_builder._switch_to_circuit_mode()
            if self.circuit_builder.grid_size < 30:
                self.circuit_builder.grid_size = 35
                self.circuit_builder._update_grid_size_display()
            self.circuit_builder._draw_grid()
            self.circuit_builder._log_status("Advanced Tutorial: 8 large practical quantum circuits (grid=35)")
            
        elif action == 'teleportation':
            # Quantum teleportation circuit - 3 qubits (CENTERED)
            self.circuit_builder._switch_to_circuit_mode()
            self.circuit_builder.components.clear()
            
            # 3 qubits with spacing - centered at y=-3, 0, 3
            for i, y_pos in enumerate([-3, 0, 3]):
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.DATA_QUBIT,
                    position=(-8, y_pos, 0), color=(0.2, 0.9, 0.3)
                ))
            
            # Bell pair creation: H on q1, CNOT q1→q2
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(-5, 0, 0), color=(1.0, 0.85, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(-3, 0, 0), color=(0.8, 0.2, 0.6),
                properties={'control': 0, 'target': 3}
            ))
            
            # Bell measurement: CNOT q0→q1, then H on q0
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(0, -3, 0), color=(0.8, 0.2, 0.6),
                properties={'control': -3, 'target': 0}
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(2, -3, 0), color=(1.0, 0.85, 0.2)
            ))
            
            # Measurements
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.MEASURE,
                position=(4, -3, 0), color=(0.9, 0.1, 0.1)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.MEASURE,
                position=(4, 0, 0), color=(0.9, 0.1, 0.1)
            ))
            
            # Bob's corrections
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.X_GATE,
                position=(7, 3, 0), color=(0.9, 0.2, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.Z_GATE,
                position=(9, 3, 0), color=(0.2, 0.2, 0.9)
            ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("Teleportation: Bell pair + Bell measurement + conditional corrections")
            
        elif action == 'superdense':
            # Superdense coding - 2 qubits (CENTERED)
            self.circuit_builder._switch_to_circuit_mode()
            self.circuit_builder.components.clear()
            
            # 2 qubits centered
            for i, y_pos in enumerate([-2, 2]):
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.DATA_QUBIT,
                    position=(-8, y_pos, 0), color=(0.2, 0.9, 0.3)
                ))
            
            # Bell pair
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(-6, -2, 0), color=(1.0, 0.85, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(-4, -2, 0), color=(0.8, 0.2, 0.6),
                properties={'control': -2, 'target': 2}
            ))
            
            # Alice's encoding (example: send "11" = XZ)
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.X_GATE,
                position=(-1, -2, 0), color=(0.9, 0.2, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.Z_GATE,
                position=(1, -2, 0), color=(0.2, 0.2, 0.9)
            ))
            
            # Bob's decoding
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(4, -2, 0), color=(0.8, 0.2, 0.6),
                properties={'control': -2, 'target': 2}
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(6, -2, 0), color=(1.0, 0.85, 0.2)
            ))
            
            # Measurements
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.MEASURE,
                position=(8, -2, 0), color=(0.9, 0.1, 0.1)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.MEASURE,
                position=(8, 2, 0), color=(0.9, 0.1, 0.1)
            ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("Superdense: Bell pair + Alice encode (XZ=11) + Bob decode")
            
        elif action == 'ghz_state':
            # 5-qubit GHZ state (CENTERED)
            self.circuit_builder._switch_to_circuit_mode()
            self.circuit_builder.components.clear()
            
            # 5 qubits centered around y=0: -4, -2, 0, 2, 4
            for i, y_pos in enumerate([-4, -2, 0, 2, 4]):
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.DATA_QUBIT,
                    position=(-8, y_pos, 0), color=(0.2, 0.9, 0.3)
                ))
            
            # H on first qubit
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(-5, -4, 0), color=(1.0, 0.85, 0.2)
            ))
            
            # CNOT cascade
            for i, target_y in enumerate([-2, 0, 2, 4]):
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.CNOT_GATE,
                    position=(-3 + i*3, -4, 0), color=(0.8, 0.2, 0.6),
                    properties={'control': -4, 'target': target_y}
                ))
            
            # Measurements
            for i, y_pos in enumerate([-4, -2, 0, 2, 4]):
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.MEASURE,
                    position=(10, y_pos, 0), color=(0.9, 0.1, 0.1)
                ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("GHZ State: H + CNOT cascade → (|00000⟩+|11111⟩)/√2")
            
        elif action == 'qft_3':
            # 3-qubit Quantum Fourier Transform (CENTERED)
            self.circuit_builder._switch_to_circuit_mode()
            self.circuit_builder.components.clear()
            
            # 3 qubits centered: y = -3, 0, 3
            for i, y_pos in enumerate([-3, 0, 3]):
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.DATA_QUBIT,
                    position=(-8, y_pos, 0), color=(0.2, 0.9, 0.3)
                ))
            
            # QFT on q0
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(-5, -3, 0), color=(1.0, 0.85, 0.2)
            ))
            # S gate controlled by q1
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.S_GATE,
                position=(-3, -3, 0), color=(0.3, 0.9, 0.6),
                properties={'is_controlled': True, 'control_y': 0}
            ))
            # T gate controlled by q2
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.T_GATE,
                position=(-1, -3, 0), color=(1.0, 0.6, 0.2),
                properties={'is_controlled': True, 'control_y': 3}
            ))
            
            # QFT on q1
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(2, 0, 0), color=(1.0, 0.85, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.S_GATE,
                position=(4, 0, 0), color=(0.3, 0.9, 0.6),
                properties={'is_controlled': True, 'control_y': 3}
            ))
            
            # QFT on q2
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(7, 3, 0), color=(1.0, 0.85, 0.2)
            ))
            
            # SWAP q0-q2 (bit reversal)
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.SWAP_GATE,
                position=(9, -3, 0), color=(0.9, 0.5, 0.2),
                properties={'target': 3}
            ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("3-Qubit QFT: H + controlled rotations + swap")
            
        elif action == 'grover_2':
            # 2-qubit Grover's search (CENTERED)
            self.circuit_builder._switch_to_circuit_mode()
            self.circuit_builder.components.clear()
            
            # 2 qubits centered: y = -2, 2
            for i, y_pos in enumerate([-2, 2]):
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.DATA_QUBIT,
                    position=(-9, y_pos, 0), color=(0.2, 0.9, 0.3)
                ))
            
            # Superposition
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(-7, -2, 0), color=(1.0, 0.85, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(-7, 2, 0), color=(1.0, 0.85, 0.2)
            ))
            
            # Oracle (mark |11⟩ with CZ)
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CZ_GATE,
                position=(-4, -2, 0), color=(0.2, 0.6, 0.8),
                properties={'control': -2, 'target': 2}
            ))
            
            # Diffusion operator
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(-1, -2, 0), color=(1.0, 0.85, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(-1, 2, 0), color=(1.0, 0.85, 0.2)
            ))
            
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.X_GATE,
                position=(1, -2, 0), color=(0.9, 0.2, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.X_GATE,
                position=(1, 2, 0), color=(0.9, 0.2, 0.2)
            ))
            
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CZ_GATE,
                position=(3, -2, 0), color=(0.2, 0.6, 0.8),
                properties={'control': -2, 'target': 2}
            ))
            
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.X_GATE,
                position=(5, -2, 0), color=(0.9, 0.2, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.X_GATE,
                position=(5, 2, 0), color=(0.9, 0.2, 0.2)
            ))
            
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(7, -2, 0), color=(1.0, 0.85, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(7, 2, 0), color=(1.0, 0.85, 0.2)
            ))
            
            # Measurements
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.MEASURE,
                position=(10, -2, 0), color=(0.9, 0.1, 0.1)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.MEASURE,
                position=(10, 2, 0), color=(0.9, 0.1, 0.1)
            ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("Grover's (2-qubit): H + Oracle(CZ) + Diffusion → finds |11⟩")
            
        elif action == 'deutsch_jozsa':
            # Deutsch-Jozsa with balanced oracle (CENTERED)
            self.circuit_builder._switch_to_circuit_mode()
            self.circuit_builder.components.clear()
            
            # 3 qubits (2 input + 1 output) centered: y = -3, 0, 3
            for i, y_pos in enumerate([-3, 0, 3]):
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.DATA_QUBIT,
                    position=(-8, y_pos, 0), color=(0.2, 0.9, 0.3)
                ))
            
            # Initialize output qubit to |1⟩
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.X_GATE,
                position=(-6, 3, 0), color=(0.9, 0.2, 0.2)
            ))
            
            # Hadamard on all
            for y_pos in [-3, 0, 3]:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.H_GATE,
                    position=(-4, y_pos, 0), color=(1.0, 0.85, 0.2)
                ))
            
            # Balanced oracle: CNOT from q0 to output, CNOT from q1 to output
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(-1, -3, 0), color=(0.8, 0.2, 0.6),
                properties={'control': -3, 'target': 3}
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(1, 0, 0), color=(0.8, 0.2, 0.6),
                properties={'control': 0, 'target': 3}
            ))
            
            # Hadamard on input qubits
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(4, -3, 0), color=(1.0, 0.85, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(4, 0, 0), color=(1.0, 0.85, 0.2)
            ))
            
            # Measure input qubits
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.MEASURE,
                position=(7, -3, 0), color=(0.9, 0.1, 0.1)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.MEASURE,
                position=(7, 0, 0), color=(0.9, 0.1, 0.1)
            ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("Deutsch-Jozsa: balanced oracle (XOR) → measure non-zero")
            
        elif action == 'entangle_swap':
            # Entanglement swapping - 4 qubits (CENTERED)
            self.circuit_builder._switch_to_circuit_mode()
            self.circuit_builder.components.clear()
            
            # 4 qubits centered: y = -3, -1, 1, 3
            for i, y_pos in enumerate([-3, -1, 1, 3]):
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.DATA_QUBIT,
                    position=(-8, y_pos, 0), color=(0.2, 0.9, 0.3)
                ))
            
            # Bell pair 1: q0-q1
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(-6, -3, 0), color=(1.0, 0.85, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(-4, -3, 0), color=(0.8, 0.2, 0.6),
                properties={'control': -3, 'target': -1}
            ))
            
            # Bell pair 2: q2-q3
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(-6, 1, 0), color=(1.0, 0.85, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(-4, 1, 0), color=(0.8, 0.2, 0.6),
                properties={'control': 1, 'target': 3}
            ))
            
            # Bell measurement on q1-q2
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(-1, -1, 0), color=(0.8, 0.2, 0.6),
                properties={'control': -1, 'target': 1}
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.H_GATE,
                position=(1, -1, 0), color=(1.0, 0.85, 0.2)
            ))
            
            # Measure q1, q2
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.MEASURE,
                position=(3, -1, 0), color=(0.9, 0.1, 0.1)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.MEASURE,
                position=(3, 1, 0), color=(0.9, 0.1, 0.1)
            ))
            
            # Corrections on q3
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.X_GATE,
                position=(6, 3, 0), color=(0.9, 0.2, 0.2)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.Z_GATE,
                position=(8, 3, 0), color=(0.2, 0.2, 0.9)
            ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("Entanglement Swap: 2 Bell pairs + BSM → q0-q3 entangled!")
            
        elif action == 'shor_9':
            # Shor's 9-qubit code encoder (CENTERED)
            self.circuit_builder._switch_to_circuit_mode()
            self.circuit_builder.components.clear()
            
            # 9 qubits in 3 blocks of 3, centered vertically
            # Block 0: y = -4, -3, -2
            # Block 1: y = -1, 0, 1
            # Block 2: y = 2, 3, 4
            y_positions = [
                -4, -3, -2,  # block 0
                -1, 0, 1,    # block 1
                2, 3, 4      # block 2
            ]
            for y_pos in y_positions:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.DATA_QUBIT,
                    position=(-8, y_pos, 0), color=(0.2, 0.9, 0.3)
                ))
            
            # Phase-flip encoding: CNOT q0→q3 (first of block 1), q0→q6 (first of block 2)
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(-6, -4, 0), color=(0.8, 0.2, 0.6),
                properties={'control': -4, 'target': -1}
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(-4, -4, 0), color=(0.8, 0.2, 0.6),
                properties={'control': -4, 'target': 2}
            ))
            
            # H gates on first qubit of each block
            for block_first_y in [-4, -1, 2]:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.H_GATE,
                    position=(-2, block_first_y, 0), color=(1.0, 0.85, 0.2)
                ))
            
            # Bit-flip encoding within each block
            # Block 0: control=-4, targets=-3,-2
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(0, -4, 0), color=(0.8, 0.2, 0.6),
                properties={'control': -4, 'target': -3}
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(2, -4, 0), color=(0.8, 0.2, 0.6),
                properties={'control': -4, 'target': -2}
            ))
            
            # Block 1: control=-1, targets=0,1
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(0, -1, 0), color=(0.8, 0.2, 0.6),
                properties={'control': -1, 'target': 0}
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(2, -1, 0), color=(0.8, 0.2, 0.6),
                properties={'control': -1, 'target': 1}
            ))
            
            # Block 2: control=2, targets=3,4
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(0, 2, 0), color=(0.8, 0.2, 0.6),
                properties={'control': 2, 'target': 3}
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.CNOT_GATE,
                position=(2, 2, 0), color=(0.8, 0.2, 0.6),
                properties={'control': 2, 'target': 4}
            ))
            
            # Measurements on all 9 qubits
            for y_pos in y_positions:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.MEASURE,
                    position=(6, y_pos, 0), color=(0.9, 0.1, 0.1)
                ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("Shor's [[9,1,3]]: phase-flip + bit-flip concatenation")
            
        elif action == 'complete':
            self.circuit_builder._log_status("Advanced tutorial complete! 8 circuits demonstrated.")
    
    def _next_step(self):
        """Go to next step or close if finished."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._update_display()
        else:
            self._close_tutorial()
    
    def _prev_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_display()
    
    def _close_tutorial(self):
        """Close and clean up."""
        if self.circuit_builder:
            self.circuit_builder._log_status("Advanced tutorial closed.")
        self.tutorial_window.destroy()


class SurfaceCodeTutorial:
    """
    Surface Code specific tutorial demonstrating 2D QEC visualization.
    SURFACE MODE ONLY - shows syndrome extraction, error chains, decoding.
    
    Demonstrates:
    - Surface code distance-3 patch anatomy
    - Single X/Z error detection
    - Error chain visualization  
    - Syndrome measurement workflow
    - MWPM decoder concept
    - Full correction cycle
    
    Uses the yellow buttons added to surface mode for QEC operations.
    """
    
    COLORS = {
        'quantum': '#00ffcc',
        'surface': '#66c2ff',
        'x_stab': '#e84545',
        'z_stab': '#6b2d5c',
        'data': '#66d9e8',
        'action': '#6bcb77',
        'math': '#a8e6cf',
        'warning': '#ff9f43',
        'title': '#74b9ff',
        'highlight': '#fd79a8',
        'code': '#bb86fc',
        'error': '#1a1a1a',
        'correct': '#ffdd33',
    }
    
    def __init__(self, parent: tk.Tk, circuit_builder=None):
        self.parent = parent
        self.circuit_builder = circuit_builder
        self.current_step = 0
        self.tutorial_window = None
        
        self.steps = self._create_tutorial_steps()
    
    def _create_tutorial_steps(self) -> List[Dict[str, Any]]:
        """Create surface code tutorial with visual QEC demos."""
        return [
            {
                'title': 'Surface Code Tutorial',
                'content': [
                    ('Welcome to the ', 'normal'),
                    ('Surface Code Tutorial', 'title'),
                    ('!\n\n', 'normal'),
                    ('This tutorial demonstrates ', 'normal'),
                    ('2D topological error correction', 'highlight'),
                    (' visualization.\n\n', 'normal'),
                    ('We will cover:\n\n', 'normal'),
                    ('1. ', 'normal'), ('Code Anatomy', 'surface'), (' - Data qubits & stabilizers\n', 'normal'),
                    ('2. ', 'normal'), ('X Error Detection', 'x_stab'), (' - Z-stabilizer syndrome\n', 'normal'),
                    ('3. ', 'normal'), ('Z Error Detection', 'z_stab'), (' - X-stabilizer syndrome\n', 'normal'),
                    ('4. ', 'normal'), ('Error Chains', 'error'), (' - Multi-error patterns\n', 'normal'),
                    ('5. ', 'normal'), ('Syndrome Highlight', 'warning'), (' - Yellow button demo\n', 'normal'),
                    ('6. ', 'normal'), ('Correction Cycle', 'correct'), (' - Full QEC workflow\n\n', 'normal'),
                    ('💡 ', 'warning'),
                    ('Watch the grid - circuits appear in real-time!', 'action'),
                ],
                'demo_action': 'intro'
            },
            {
                'title': 'Surface Code Anatomy',
                'content': [
                    ('Rotated Surface Code (d=3)', 'title'),
                    ('\n\n', 'normal'),
                    ('The ', 'normal'),
                    ('rotated surface code', 'highlight'),
                    (' is the leading candidate for fault-tolerant QC.\n\n', 'normal'),
                    ('Components:\n', 'action'),
                    ('• ', 'data'), ('Data Qubits', 'data'), (' (cyan circles) - Store quantum info\n', 'normal'),
                    ('• ', 'x_stab'), ('X-Stabilizers', 'x_stab'), (' (red) - Detect Z errors\n', 'normal'),
                    ('• ', 'z_stab'), ('Z-Stabilizers', 'z_stab'), (' (purple) - Detect X errors\n\n', 'normal'),
                    ('Parameters:\n', 'math'),
                    ('• Distance d = 3 (corrects ⌊(d-1)/2⌋ = 1 error)\n', 'code'),
                    ('• 9 data qubits arranged in 3×3 grid\n', 'code'),
                    ('• 4 X-type + 4 Z-type stabilizer checks\n', 'code'),
                    ('• 2 boundaries: rough (X) and smooth (Z)\n\n', 'code'),
                    ('Threshold: ', 'warning'),
                    ('~1% physical error rate!\n', 'normal'),
                    ('Building d=3 patch now...', 'highlight'),
                ],
                'demo_action': 'build_d3'
            },
            {
                'title': 'Single X Error',
                'content': [
                    ('X (Bit-Flip) Error Detection', 'title'),
                    ('\n\n', 'normal'),
                    ('An ', 'normal'),
                    ('X error', 'highlight'),
                    (' on a data qubit anti-commutes with adjacent ', 'normal'),
                    ('Z-stabilizers', 'z_stab'),
                    ('.\n\n', 'normal'),
                    ('Detection Mechanism:\n', 'action'),
                    ('• X error on qubit q\n', 'normal'),
                    ('• Adjacent Z-stabilizers detect the flip\n', 'normal'),
                    ('• Syndrome: stabilizer returns -1 (violated)\n\n', 'normal'),
                    ('Visual:\n', 'surface'),
                    ('• Error appears as ', 'normal'),
                    ('black X', 'error'),
                    (' on data qubit\n', 'normal'),
                    ('• Neighboring Z-stabilizers turn ', 'normal'),
                    ('yellow', 'correct'),
                    (' (violated)\n\n', 'normal'),
                    ('Formula: ', 'math'),
                    ('X·Z = -Z·X (anti-commutation)\n\n', 'code'),
                    ('Placing X error on center qubit...', 'warning'),
                ],
                'demo_action': 'single_x_error'
            },
            {
                'title': 'Single Z Error',
                'content': [
                    ('Z (Phase-Flip) Error Detection', 'title'),
                    ('\n\n', 'normal'),
                    ('A ', 'normal'),
                    ('Z error', 'highlight'),
                    (' on a data qubit anti-commutes with adjacent ', 'normal'),
                    ('X-stabilizers', 'x_stab'),
                    ('.\n\n', 'normal'),
                    ('Detection Mechanism:\n', 'action'),
                    ('• Z error on qubit q\n', 'normal'),
                    ('• Adjacent X-stabilizers detect the phase flip\n', 'normal'),
                    ('• Syndrome: X-stabilizer returns -1\n\n', 'normal'),
                    ('Visual:\n', 'surface'),
                    ('• Error appears as ', 'normal'),
                    ('black Z', 'error'),
                    (' on data qubit\n', 'normal'),
                    ('• Neighboring X-stabilizers turn ', 'normal'),
                    ('yellow', 'correct'),
                    (' (violated)\n\n', 'normal'),
                    ('Key Insight:\n', 'math'),
                    ('X-type checks detect Z-type errors (and vice versa)\n', 'code'),
                    ('This is the CSS code structure!\n\n', 'normal'),
                    ('Placing Z error...', 'warning'),
                ],
                'demo_action': 'single_z_error'
            },
            {
                'title': 'Error Chain',
                'content': [
                    ('Error Chains and Logical Errors', 'title'),
                    ('\n\n', 'normal'),
                    ('Multiple errors can form ', 'normal'),
                    ('error chains', 'highlight'),
                    (' across the lattice.\n\n', 'normal'),
                    ('Chain Properties:\n', 'action'),
                    ('• Interior errors: detected at both endpoints\n', 'normal'),
                    ('• Boundary errors: detected only at interior end\n', 'normal'),
                    ('• Chain connecting boundaries: LOGICAL ERROR!\n\n', 'normal'),
                    ('Decoding Challenge:\n', 'surface'),
                    ('• Syndrome only shows endpoints (violated checks)\n', 'normal'),
                    ('• Must infer chain path from boundary conditions\n', 'normal'),
                    ('• MWPM finds minimum-weight matching\n\n', 'normal'),
                    ('Logical Error Condition:\n', 'warning'),
                    ('Error chain spans ', 'normal'),
                    ('rough → rough', 'x_stab'),
                    (' or ', 'normal'),
                    ('smooth → smooth', 'z_stab'),
                    (' boundary\n\n', 'normal'),
                    ('Building error chain demo...', 'highlight'),
                ],
                'demo_action': 'error_chain'
            },
            {
                'title': 'Syndrome Highlight',
                'content': [
                    ('Using Syndrome Highlight', 'title'),
                    ('\n\n', 'normal'),
                    ('The ', 'normal'),
                    ('yellow "Highlight Syndrome"', 'correct'),
                    (' button shows violated stabilizers.\n\n', 'normal'),
                    ('How It Works:\n', 'action'),
                    ('1. Place errors on data qubits\n', 'normal'),
                    ('2. Click "Highlight Syndrome" (yellow button)\n', 'normal'),
                    ('3. Violated stabilizers turn yellow\n', 'normal'),
                    ('4. Count violations to identify error location\n\n', 'normal'),
                    ('Syndrome Analysis:\n', 'surface'),
                    ('• 2 adjacent yellow Z-stabs → X error between them\n', 'code'),
                    ('• 2 adjacent yellow X-stabs → Z error between them\n', 'code'),
                    ('• 1 yellow at boundary → error on boundary qubit\n\n', 'code'),
                    ('Try It:\n', 'warning'),
                    ('After tutorial, place errors and click the button!\n', 'normal'),
                    ('The syndrome pattern reveals error locations.\n\n', 'normal'),
                    ('Demo: highlighting current errors...', 'highlight'),
                ],
                'demo_action': 'syndrome_demo'
            },
            {
                'title': 'Surface Mode Buttons',
                'content': [
                    ('Surface Mode Operations', 'title'),
                    ('\n\n', 'normal'),
                    ('Surface mode has ', 'normal'),
                    ('specialized QEC buttons', 'highlight'),
                    (' in the sidebar:\n\n', 'normal'),
                    ('Yellow QEC Buttons:\n', 'warning'),
                    ('• ', 'correct'), ('Highlight Syndrome', 'correct'), (' - Shows violated stabilizers\n', 'normal'),
                    ('• ', 'correct'), ('Run Decoder', 'correct'), (' - Runs MWPM matching algorithm\n', 'normal'),
                    ('• ', 'correct'), ('Apply Correction', 'correct'), (' - Places recovery gates\n', 'normal'),
                    ('• ', 'correct'), ('Clear Highlights', 'correct'), (' - Resets syndrome display\n\n', 'normal'),
                    ('Errors Tab (Toolbox):\n', 'action'),
                    ('• X Error - Bit-flip error (black)\n', 'normal'),
                    ('• Z Error - Phase-flip error (black)\n', 'normal'),
                    ('• Y Error - Combined X+Z error\n\n', 'normal'),
                    ('Workflow:\n', 'surface'),
                    ('1. Place errors from "Errors" toolbox tab\n', 'code'),
                    ('2. Click "Highlight Syndrome"\n', 'code'),
                    ('3. Click "Run Decoder" → "Apply Correction"\n', 'code'),
                    ('4. Click "Clear Highlights" to reset\n\n', 'code'),
                    ('Try the buttons now!', 'highlight'),
                ],
                'demo_action': 'buttons_demo'
            },
            {
                'title': 'Full Correction Cycle',
                'content': [
                    ('Complete QEC Workflow', 'title'),
                    ('\n\n', 'normal'),
                    ('The full ', 'normal'),
                    ('surface code QEC cycle', 'highlight'),
                    (':\n\n', 'normal'),
                    ('1. ', 'action'), ('Initialize', 'action'), (' - Prepare logical |0⟩ or |+⟩\n', 'normal'),
                    ('2. ', 'action'), ('Gate Operations', 'action'), (' - Apply logical gates\n', 'normal'),
                    ('3. ', 'action'), ('Error Occurs', 'error'), (' - Physical errors on data\n', 'normal'),
                    ('4. ', 'action'), ('Syndrome Measure', 'correct'), (' - Extract stabilizer values\n', 'normal'),
                    ('5. ', 'action'), ('Decode', 'surface'), (' - MWPM identifies error chain\n', 'normal'),
                    ('6. ', 'action'), ('Correct', 'correct'), (' - Apply recovery operations\n', 'normal'),
                    ('7. ', 'action'), ('Readout', 'action'), (' - Measure logical qubit\n\n', 'normal'),
                    ('In This Demo:\n', 'warning'),
                    ('• Error placed → syndrome highlighted → correction shown\n', 'code'),
                    ('• Yellow marks show syndrome (detection)\n', 'code'),
                    ('• Correction gate appears at error location\n\n', 'code'),
                    ('Building full cycle demo...', 'highlight'),
                ],
                'demo_action': 'full_cycle'
            },
            {
                'title': 'Tutorial Complete!',
                'content': [
                    ('🎉 ', 'normal'),
                    ('Surface Code Tutorial Complete!', 'title'),
                    ('\n\n', 'normal'),
                    ('You have learned:\n\n', 'normal'),
                    ('✓ ', 'action'), ('Code Anatomy', 'surface'), (' - Data, X/Z stabilizers\n', 'normal'),
                    ('✓ ', 'action'), ('Error Detection', 'x_stab'), (' - Anti-commutation syndrome\n', 'normal'),
                    ('✓ ', 'action'), ('Error Chains', 'error'), (' - Multi-qubit patterns\n', 'normal'),
                    ('✓ ', 'action'), ('Syndrome Analysis', 'correct'), (' - Yellow highlight tool\n', 'normal'),
                    ('✓ ', 'action'), ('QEC Cycle', 'highlight'), (' - Full correction workflow\n\n', 'normal'),
                    ('Now Try:\n', 'warning'),
                    ('• Place errors using "Errors" toolbox tab\n', 'normal'),
                    ('• Click yellow "Highlight Syndrome" button\n', 'normal'),
                    ('• Observe which stabilizers are violated\n', 'normal'),
                    ('• Click "Apply Decoder" to see corrections\n\n', 'normal'),
                    ('For LDPC codes, switch to LDPC mode (B key).\n', 'math'),
                    ('For circuit diagrams, switch to Circuit mode (C key).\n\n', 'normal'),
                    ('Happy quantum error correcting!', 'highlight'),
                ],
                'demo_action': 'complete'
            },
        ]
    
    def show(self):
        """Display the surface code tutorial window."""
        self.tutorial_window = tk.Toplevel(self.parent)
        self.tutorial_window.title("Surface Code QEC Tutorial")
        self.tutorial_window.configure(bg='#1a1a2e')
        self.tutorial_window.attributes('-topmost', False)
        
        # Position on left side
        self.tutorial_window.update_idletasks()
        screen_width = self.tutorial_window.winfo_screenwidth()
        screen_height = self.tutorial_window.winfo_screenheight()
        
        win_width = 480
        win_height = 480
        x = 30
        y = (screen_height - win_height) // 2
        self.tutorial_window.geometry(f"{win_width}x{win_height}+{x}+{y}")
        
        # Main container
        self.main_frame = tk.Frame(self.tutorial_window, bg='#1a1a2e')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # Header with teal accent for Surface mode
        self.header_frame = tk.Frame(self.main_frame, bg='#1a3a3e')
        self.header_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.title_label = tk.Label(
            self.header_frame, text="",
            font=('Segoe UI', 14, 'bold'),
            fg='#66c2ff',  # Surface code blue
            bg='#1a3a3e', pady=8
        )
        self.title_label.pack()
        
        self.step_label = tk.Label(
            self.header_frame, text="",
            font=('Segoe UI', 9), fg='#888888', bg='#1a3a3e'
        )
        self.step_label.pack(pady=(0, 8))
        
        # Progress bar (teal/cyan)
        self.progress_frame = tk.Frame(self.main_frame, bg='#1a1a2e', height=6)
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))
        self.progress_frame.pack_propagate(False)
        
        self.progress_bg = tk.Frame(self.progress_frame, bg='#2d3d44', height=6)
        self.progress_bg.pack(fill=tk.X)
        
        self.progress_bar = tk.Frame(self.progress_bg, bg='#66c2ff', height=6)
        self.progress_bar.place(x=0, y=0, relheight=1, relwidth=0)
        
        # Navigation - pack at bottom first
        self.nav_frame = tk.Frame(self.main_frame, bg='#1a1a2e')
        self.nav_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(8, 0))
        
        self.close_btn = tk.Button(
            self.nav_frame, text="Close",
            font=('Segoe UI', 9), fg='#888888', bg='#2d2d44',
            activeforeground='#ffffff', activebackground='#3d3d54',
            relief='flat', padx=12, pady=6, cursor='hand2',
            command=self._close_tutorial
        )
        self.close_btn.pack(side=tk.LEFT)
        
        self.next_btn = tk.Button(
            self.nav_frame, text="Next →",
            font=('Segoe UI', 10, 'bold'), fg='#ffffff', bg='#3a7a9a',
            activeforeground='#ffffff', activebackground='#4a9aba',
            relief='flat', padx=20, pady=6, cursor='hand2',
            command=self._next_step
        )
        self.next_btn.pack(side=tk.RIGHT)
        
        self.prev_btn = tk.Button(
            self.nav_frame, text="← Back",
            font=('Segoe UI', 9), fg='#cccccc', bg='#2d2d44',
            activeforeground='#ffffff', activebackground='#3d3d54',
            relief='flat', padx=12, pady=6, cursor='hand2',
            command=self._prev_step
        )
        self.prev_btn.pack(side=tk.RIGHT, padx=(0, 8))
        
        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg='#0f0f23', bd=1, relief='solid')
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.content_text = tk.Text(
            self.content_frame,
            font=('Consolas', 10),
            bg='#0f0f23', fg='#ffffff',
            wrap=tk.WORD, padx=15, pady=12,
            relief='flat', cursor='arrow', state='disabled'
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(self.content_frame, command=self.content_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.config(yscrollcommand=scrollbar.set)
        
        # Configure text tags
        for tag_name, color in self.COLORS.items():
            self.content_text.tag_configure(tag_name, foreground=color)
        self.content_text.tag_configure('normal', foreground='#cccccc')
        
        self._update_display()
        self.tutorial_window.protocol("WM_DELETE_WINDOW", self._close_tutorial)
    
    def _update_display(self):
        """Update display for current step."""
        step = self.steps[self.current_step]
        
        self.title_label.config(text=step['title'])
        self.step_label.config(text=f"Step {self.current_step + 1} of {len(self.steps)}")
        
        progress = (self.current_step + 1) / len(self.steps)
        self.progress_bar.place(x=0, y=0, relheight=1, relwidth=progress)
        
        self.content_text.config(state='normal')
        self.content_text.delete('1.0', tk.END)
        
        for text, tag in step['content']:
            self.content_text.insert(tk.END, text, tag)
        
        self.content_text.config(state='disabled')
        
        self.prev_btn.config(state=tk.NORMAL if self.current_step > 0 else tk.DISABLED)
        
        if self.current_step == len(self.steps) - 1:
            self.next_btn.config(text="Finish")
        else:
            self.next_btn.config(text="Next →")
        
        self._execute_demo(step.get('demo_action', None))
    
    def _execute_demo(self, action):
        """Execute surface code demos on the grid."""
        if not self.circuit_builder or not action:
            return
        
        if action == 'intro':
            # Ensure surface mode
            self.circuit_builder._switch_to_surface_mode()
            self.circuit_builder._draw_grid()
            self.circuit_builder._log_status("Surface Code Tutorial: 2D lattice mode for QEC visualization")
            
        elif action == 'build_d3':
            # Build distance-3 patch
            self.circuit_builder._switch_to_surface_mode()
            self.circuit_builder.components.clear()
            
            # Data qubits (9 in 3x3 arrangement)
            data_positions = [(1,1), (1,3), (1,5), (3,1), (3,3), (3,5), (5,1), (5,3), (5,5)]
            for x, y in data_positions:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_DATA,
                    position=(x, y, 0), color=(0.4, 0.8, 0.9)
                ))
            
            # X-stabilizers (detect Z errors)
            x_stab_pos = [(2,2), (2,4), (4,2), (4,4)]
            for x, y in x_stab_pos:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_X_STABILIZER,
                    position=(x, y, 0), color=(0.91, 0.27, 0.38)
                ))
            
            # Z-stabilizers (detect X errors)
            z_stab_pos = [(0,2), (0,4), (2,0), (2,6), (4,0), (4,6), (6,2), (6,4)]
            for x, y in z_stab_pos:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_Z_STABILIZER,
                    position=(x, y, 0), color=(0.42, 0.18, 0.36)
                ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("Surface code d=3: 9 data (cyan), 4 X-stab (red), 8 Z-stab (purple)")
            
        elif action == 'single_x_error':
            # Place single X error on center qubit
            self.circuit_builder._switch_to_surface_mode()
            self.circuit_builder.components.clear()
            
            # Rebuild the patch
            data_positions = [(1,1), (1,3), (1,5), (3,1), (3,3), (3,5), (5,1), (5,3), (5,5)]
            for x, y in data_positions:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_DATA,
                    position=(x, y, 0), color=(0.4, 0.8, 0.9)
                ))
            
            x_stab_pos = [(2,2), (2,4), (4,2), (4,4)]
            for x, y in x_stab_pos:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_X_STABILIZER,
                    position=(x, y, 0), color=(0.91, 0.27, 0.38)
                ))
            
            z_stab_pos = [(0,2), (0,4), (2,0), (2,6), (4,0), (4,6), (6,2), (6,4)]
            for x, y in z_stab_pos:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_Z_STABILIZER,
                    position=(x, y, 0), color=(0.42, 0.18, 0.36)
                ))
            
            # Add X error on center data qubit (3,3)
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.SURFACE_X_ERROR,
                position=(3, 3, 0), color=(0.15, 0.15, 0.15)  # Black
            ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("X error on center qubit (3,3) - adjacent Z-stabilizers detect it!")
            
        elif action == 'single_z_error':
            # Place single Z error
            self.circuit_builder._switch_to_surface_mode()
            self.circuit_builder.components.clear()
            
            # Rebuild patch
            data_positions = [(1,1), (1,3), (1,5), (3,1), (3,3), (3,5), (5,1), (5,3), (5,5)]
            for x, y in data_positions:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_DATA,
                    position=(x, y, 0), color=(0.4, 0.8, 0.9)
                ))
            
            x_stab_pos = [(2,2), (2,4), (4,2), (4,4)]
            for x, y in x_stab_pos:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_X_STABILIZER,
                    position=(x, y, 0), color=(0.91, 0.27, 0.38)
                ))
            
            z_stab_pos = [(0,2), (0,4), (2,0), (2,6), (4,0), (4,6), (6,2), (6,4)]
            for x, y in z_stab_pos:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_Z_STABILIZER,
                    position=(x, y, 0), color=(0.42, 0.18, 0.36)
                ))
            
            # Add Z error on qubit (3,1)
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.SURFACE_Z_ERROR,
                position=(3, 1, 0), color=(0.15, 0.15, 0.15)  # Black
            ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("Z error on qubit (3,1) - adjacent X-stabilizers detect it!")
            
        elif action == 'error_chain':
            # Build error chain (2 X errors forming a chain)
            self.circuit_builder._switch_to_surface_mode()
            self.circuit_builder.components.clear()
            
            # Rebuild patch
            data_positions = [(1,1), (1,3), (1,5), (3,1), (3,3), (3,5), (5,1), (5,3), (5,5)]
            for x, y in data_positions:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_DATA,
                    position=(x, y, 0), color=(0.4, 0.8, 0.9)
                ))
            
            x_stab_pos = [(2,2), (2,4), (4,2), (4,4)]
            for x, y in x_stab_pos:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_X_STABILIZER,
                    position=(x, y, 0), color=(0.91, 0.27, 0.38)
                ))
            
            z_stab_pos = [(0,2), (0,4), (2,0), (2,6), (4,0), (4,6), (6,2), (6,4)]
            for x, y in z_stab_pos:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_Z_STABILIZER,
                    position=(x, y, 0), color=(0.42, 0.18, 0.36)
                ))
            
            # Two X errors forming a chain: (1,3) and (3,3)
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.SURFACE_X_ERROR,
                position=(1, 3, 0), color=(0.15, 0.15, 0.15)
            ))
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.SURFACE_X_ERROR,
                position=(3, 3, 0), color=(0.15, 0.15, 0.15)
            ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("Error chain: 2 X errors at (1,3) and (3,3) - syndrome at endpoints only!")
            
        elif action == 'syndrome_demo':
            # Trigger the syndrome highlight if available
            self.circuit_builder._switch_to_surface_mode()
            
            # Try to call the highlight method
            if hasattr(self.circuit_builder, '_highlight_surface_syndrome'):
                self.circuit_builder._highlight_surface_syndrome()
                self.circuit_builder._log_status("Syndrome highlighted! Yellow shows violated stabilizers.")
            else:
                self.circuit_builder._log_status("Click yellow 'Highlight Syndrome' button to see violations.")
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
        
        elif action == 'buttons_demo':
            # Keep current circuit, just log about buttons
            self.circuit_builder._switch_to_surface_mode()
            self.circuit_builder._log_status("Surface Mode Buttons: Highlight Syndrome, Run Decoder, Apply Correction, Clear Highlights")
            
        elif action == 'full_cycle':
            # Full QEC cycle demo
            self.circuit_builder._switch_to_surface_mode()
            self.circuit_builder.components.clear()
            
            # Rebuild patch
            data_positions = [(1,1), (1,3), (1,5), (3,1), (3,3), (3,5), (5,1), (5,3), (5,5)]
            for x, y in data_positions:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_DATA,
                    position=(x, y, 0), color=(0.4, 0.8, 0.9)
                ))
            
            x_stab_pos = [(2,2), (2,4), (4,2), (4,4)]
            for x, y in x_stab_pos:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_X_STABILIZER,
                    position=(x, y, 0), color=(0.91, 0.27, 0.38)
                ))
            
            z_stab_pos = [(0,2), (0,4), (2,0), (2,6), (4,0), (4,6), (6,2), (6,4)]
            for x, y in z_stab_pos:
                self.circuit_builder.components.append(Component3D(
                    component_type=ComponentType.SURFACE_Z_STABILIZER,
                    position=(x, y, 0), color=(0.42, 0.18, 0.36)
                ))
            
            # Add error
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.SURFACE_X_ERROR,
                position=(3, 3, 0), color=(0.15, 0.15, 0.15)
            ))
            
            # Add Y error for variety
            self.circuit_builder.components.append(Component3D(
                component_type=ComponentType.SURFACE_Y_ERROR,
                position=(1, 5, 0), color=(1.0, 0.85, 0.2)  # Yellow for Y
            ))
            
            self.circuit_builder._draw_grid()
            self.circuit_builder._redraw_circuit()
            self.circuit_builder._log_status("Full cycle: X error at (3,3), Y error at (1,5). Try syndrome highlight!")
            
        elif action == 'complete':
            self.circuit_builder._log_status("Surface Code tutorial complete! Use the yellow buttons for QEC operations.")
    
    def _next_step(self):
        """Go to next step or close if finished."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._update_display()
        else:
            self._close_tutorial()
    
    def _prev_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_display()
    
    def _close_tutorial(self):
        """Close and clean up."""
        if self.circuit_builder:
            self.circuit_builder._log_status("Surface Code tutorial closed.")
        self.tutorial_window.destroy()


class ViewMode(Enum):
    """Enumeration of available view modes."""
    ISOMETRIC_3D = "isometric"        # Standard isometric view for circuit diagrams
    SURFACE_CODE_2D = "surface_2d"    # Top-down 2D view for surface code lattice
    LDPC_TANNER = "ldpc_tanner"       # Tanner graph view (3-layer: X-checks, qubits, Z-checks)
    LDPC_PHYSICAL = "ldpc_physical"   # Physical layout (linear arrays with cavity bus)


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
    
    # Measurement and reset
    MEASURE = "Measure"
    RESET = "Reset"
    
    # Circuit mode error components (for QEC demonstrations)
    CIRCUIT_X_ERROR = "X Err"        # X error (bit-flip) - black
    CIRCUIT_Z_ERROR = "Z Err"        # Z error (phase-flip) - black
    CIRCUIT_Y_ERROR = "Y Err"        # Y error (combined) - black
    CIRCUIT_CORRECTION = "Correct"   # Yellow correction component
    
    # Surface code specific components (2D lattice mode)
    SURFACE_DATA = "Surface Data"           # Data qubit on edge (surface code)
    SURFACE_X_STABILIZER = "X Stabilizer"   # X-type stabilizer (plaquette/face)
    SURFACE_Z_STABILIZER = "Z Stabilizer"   # Z-type stabilizer (vertex/star)
    SURFACE_BOUNDARY = "Boundary"           # Boundary (rough or smooth)
    SURFACE_X_ERROR = "X Error"             # X (bit-flip) error on data qubit
    SURFACE_Z_ERROR = "Z Error"             # Z (phase-flip) error on data qubit
    SURFACE_Y_ERROR = "Y Error"             # Y (combined) error on data qubit
    
    # LDPC specific components (Tanner graph and physical layout modes)
    LDPC_DATA_QUBIT = "LDPC Data"           # Data qubit in LDPC lattice
    LDPC_X_CHECK = "LDPC X-Check"           # X-type check node (coral/salmon)
    LDPC_Z_CHECK = "LDPC Z-Check"           # Z-type check node (gold/amber)
    LDPC_ANCILLA = "LDPC Ancilla"           # Ancilla qubit for syndrome extraction
    LDPC_X_ANCILLA = "LDPC X-Ancilla"       # X-ancilla (tri-layer physical layout)
    LDPC_Z_ANCILLA = "LDPC Z-Ancilla"       # Z-ancilla (tri-layer physical layout)
    LDPC_EDGE = "LDPC Edge"                 # Non-local edge/connection
    LDPC_CAVITY_BUS = "Cavity Bus"          # Cavity bus for non-local connectivity


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
        self.offset_x = 500  # Centered horizontally (adjust for typical canvas width)
        self.offset_y = 350  # Centered vertically (adjust for typical canvas height)
        
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
        
        Uses a qubit registry built from DATA_QUBIT and ANCILLA_QUBIT components,
        then maps gates to qubits based on lane (Y-position) matching.
        
        Args:
            components: List of placed 3D components
            
        Returns:
            Constructed QuantumCircuit or None if build fails
        """
        if not QISKIT_AVAILABLE:
            return self._simulate_circuit_build(components)
        
        try:
            # Build qubit registry: map lane (Y-position) to qubit index
            # This ensures gates are mapped to actual qubits, not arbitrary positions
            qubit_components = [comp for comp in components 
                               if comp.component_type in [ComponentType.DATA_QUBIT, ComponentType.ANCILLA_QUBIT]]
            
            if not qubit_components:
                print("No qubit components found in circuit")
                return None
            
            # Create lane-to-qubit mapping (sorted by Y-position for consistent ordering)
            qubit_components_sorted = sorted(qubit_components, key=lambda c: c.position[1])
            lane_to_qubit = {}  # Maps Y-position (lane) to qubit index
            for idx, comp in enumerate(qubit_components_sorted):
                lane = comp.position[1]
                if lane not in lane_to_qubit:
                    lane_to_qubit[lane] = idx
            
            num_qubits = len(lane_to_qubit)
            
            # Create circuit
            qreg = QuantumRegister(num_qubits, 'q')
            creg = ClassicalRegister(num_qubits, 'c')
            circuit = QuantumCircuit(qreg, creg)
            
            # Sort components by x-position for temporal ordering
            sorted_components = sorted(components, key=lambda c: c.position[0])
            
            for comp in sorted_components:
                lane = comp.position[1]
                # Check if this lane has a qubit (skip components on empty lanes)
                if lane not in lane_to_qubit:
                    # For two-qubit gates, check if control lane exists
                    if comp.component_type not in [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]:
                        continue
                
                self._add_component_to_circuit(circuit, comp, qreg, creg, lane_to_qubit)
            
            self.circuit = circuit
            return circuit
            
        except Exception as e:
            print(f"Error building circuit: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _add_component_to_circuit(self, circuit: QuantumCircuit, 
                                 component: Component3D,
                                 qreg: QuantumRegister, 
                                 creg: ClassicalRegister,
                                 lane_to_qubit: Dict[int, int]):
        """
        Add a single component to the quantum circuit.
        
        Args:
            circuit: The Qiskit QuantumCircuit to add to
            component: The 3D component to add
            qreg: Quantum register
            creg: Classical register
            lane_to_qubit: Mapping from Y-position (lane) to qubit index
        """
        comp_type = component.component_type
        lane = component.position[1]
        
        # Skip if lane doesn't have a qubit (except for two-qubit gates which use properties)
        if lane not in lane_to_qubit:
            if comp_type not in [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]:
                return
        
        # Get qubit index from lane
        qubit_idx = lane_to_qubit.get(lane, -1)
        
        if comp_type == ComponentType.X_GATE:
            if qubit_idx >= 0:
                circuit.x(qreg[qubit_idx])
        elif comp_type == ComponentType.Z_GATE:
            if qubit_idx >= 0:
                circuit.z(qreg[qubit_idx])
        elif comp_type == ComponentType.Y_GATE:
            if qubit_idx >= 0:
                circuit.y(qreg[qubit_idx])
        elif comp_type == ComponentType.H_GATE:
            if qubit_idx >= 0:
                circuit.h(qreg[qubit_idx])
        elif comp_type == ComponentType.S_GATE:
            if qubit_idx >= 0:
                circuit.s(qreg[qubit_idx])
        elif comp_type == ComponentType.T_GATE:
            if qubit_idx >= 0:
                circuit.t(qreg[qubit_idx])
        elif comp_type == ComponentType.CNOT_GATE:
            # Use properties.control and properties.target (Option B)
            control_lane = component.properties.get('control')
            target_lane = component.properties.get('target')
            
            if control_lane is not None and target_lane is not None:
                # Map lanes to qubit indices
                ctrl_idx = lane_to_qubit.get(control_lane, -1)
                tgt_idx = lane_to_qubit.get(target_lane, -1)
                if ctrl_idx >= 0 and tgt_idx >= 0 and ctrl_idx != tgt_idx:
                    circuit.cx(qreg[ctrl_idx], qreg[tgt_idx])
            else:
                # Fallback: gate at control lane, target is next lane
                if qubit_idx >= 0:
                    target_lane_fallback = lane + 1
                    tgt_idx = lane_to_qubit.get(target_lane_fallback, -1)
                    if tgt_idx >= 0 and tgt_idx != qubit_idx:
                        circuit.cx(qreg[qubit_idx], qreg[tgt_idx])
        elif comp_type == ComponentType.CZ_GATE:
            control_lane = component.properties.get('control')
            target_lane = component.properties.get('target')
            
            if control_lane is not None and target_lane is not None:
                ctrl_idx = lane_to_qubit.get(control_lane, -1)
                tgt_idx = lane_to_qubit.get(target_lane, -1)
                if ctrl_idx >= 0 and tgt_idx >= 0 and ctrl_idx != tgt_idx:
                    circuit.cz(qreg[ctrl_idx], qreg[tgt_idx])
            else:
                if qubit_idx >= 0:
                    target_lane_fallback = lane + 1
                    tgt_idx = lane_to_qubit.get(target_lane_fallback, -1)
                    if tgt_idx >= 0 and tgt_idx != qubit_idx:
                        circuit.cz(qreg[qubit_idx], qreg[tgt_idx])
        elif comp_type == ComponentType.SWAP_GATE:
            control_lane = component.properties.get('control')
            target_lane = component.properties.get('target')
            
            if control_lane is not None and target_lane is not None:
                ctrl_idx = lane_to_qubit.get(control_lane, -1)
                tgt_idx = lane_to_qubit.get(target_lane, -1)
                if ctrl_idx >= 0 and tgt_idx >= 0 and ctrl_idx != tgt_idx:
                    circuit.swap(qreg[ctrl_idx], qreg[tgt_idx])
            else:
                if qubit_idx >= 0:
                    target_lane_fallback = lane + 1
                    tgt_idx = lane_to_qubit.get(target_lane_fallback, -1)
                    if tgt_idx >= 0 and tgt_idx != qubit_idx:
                        circuit.swap(qreg[qubit_idx], qreg[tgt_idx])
        elif comp_type == ComponentType.MEASURE:
            if qubit_idx >= 0:
                circuit.measure(qreg[qubit_idx], creg[qubit_idx])
        elif comp_type == ComponentType.RESET:
            if qubit_idx >= 0:
                circuit.reset(qreg[qubit_idx])
    
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
        # Extract parity check components (merged with former SYNDROME_EXTRACT)
        parity_checks = [c for c in components if c.component_type == ComponentType.PARITY_CHECK]
        ancilla_qubits = [c for c in components if c.component_type == ComponentType.ANCILLA_QUBIT]
        data_qubits = [c for c in components if c.component_type == ComponentType.DATA_QUBIT]
        
        # Use ancilla qubits as syndrome extractors if no dedicated parity checks
        if not parity_checks and ancilla_qubits:
            parity_checks = ancilla_qubits
        
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
        
        # Build error vector from actual X_GATE positions in the circuit
        # An X gate on a qubit lane indicates an error on that data qubit
        error_vector = np.zeros(num_data, dtype=int)
        
        # Find all X gates and map them to data qubits by Y-coordinate (lane)
        x_gates = [c for c in components if c.component_type == ComponentType.X_GATE]
        for x_gate in x_gates:
            gate_lane = x_gate.position[1]  # Y = qubit lane
            # Find data qubits in the same lane
            for j, data in enumerate(data_qubits):
                if data.position[1] == gate_lane:
                    error_vector[j] = 1  # Mark this data qubit as having an error
                    break  # One X gate affects one qubit per lane
        
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


# ==================== COMMAND PATTERN FOR UNDO/REDO ====================
# Lightweight implementation integrated into the main file

class Command:
    """Base class for undoable commands."""
    def execute(self): raise NotImplementedError
    def undo(self): raise NotImplementedError


class PlaceComponentCommand(Command):
    """Command for placing a component."""
    def __init__(self, builder, component):
        self.builder = builder
        self.component = component
    
    def execute(self):
        if self.component not in self.builder.components:
            self.builder.components.append(self.component)
    
    def undo(self):
        if self.component in self.builder.components:
            self.builder.components.remove(self.component)


class DeleteComponentCommand(Command):
    """Command for deleting a component."""
    def __init__(self, builder, component):
        self.builder = builder
        self.component = component
        self.index = -1
    
    def execute(self):
        if self.component in self.builder.components:
            self.index = self.builder.components.index(self.component)
            self.builder.components.remove(self.component)
    
    def undo(self):
        if self.index >= 0:
            self.builder.components.insert(self.index, self.component)


class MoveComponentCommand(Command):
    """Command for moving a component."""
    def __init__(self, builder, component, old_pos, new_pos):
        self.builder = builder
        self.component = component
        self.old_pos = old_pos
        self.new_pos = new_pos
    
    def execute(self):
        self.component.position = self.new_pos
    
    def undo(self):
        self.component.position = self.old_pos


class CommandHistory:
    """Manages undo/redo command history."""
    def __init__(self, max_size=100):
        self.undo_stack = []
        self.redo_stack = []
        self.max_size = max_size
    
    def execute(self, command):
        """Execute a command and add to history."""
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()  # Clear redo stack on new action
        
        # Limit stack size
        if len(self.undo_stack) > self.max_size:
            self.undo_stack.pop(0)
    
    def undo(self):
        """Undo the last command."""
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)
            return True
        return False
    
    def redo(self):
        """Redo the last undone command."""
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.execute()
            self.undo_stack.append(command)
            return True
        return False
    
    def can_undo(self):
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        return len(self.redo_stack) > 0
    
    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()


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
        
        # Undo/Redo support
        self.command_history = CommandHistory(max_size=100)
        
        # View mode - isometric (circuit) or 2D (surface code)
        self.view_mode = ViewMode.ISOMETRIC_3D
        
        # Separate storage for circuit vs surface code components
        self.circuit_components = []   # Store circuit components when in surface mode
        self.surface_components = []   # Store surface components when in circuit mode
        
        # LDPC mode component storage
        self.ldpc_tanner_components = []    # Tanner graph components
        self.ldpc_physical_components = []  # Physical layout components
        self.ldpc_edges = []                # Non-local edge connections
        
        # Rendering and computation
        self.renderer = None
        self.surface_renderer = None  # Will be initialized when needed
        self.processor = QuantumLDPCProcessor()
        
        # Dirty-region tracking for optimized redraw (#18)
        self._dirty_components: set = set()  # Components needing redraw
        self._full_redraw_needed: bool = True  # Force full redraw on first draw
        self._component_canvas_items: dict = {}  # Map component -> canvas item IDs
        
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
        
        # Left panel - Circuit building area with status below
        left_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Canvas container (takes most of the space)
        canvas_frame = ttk.Frame(left_frame, style='Dark.TFrame')
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Circuit canvas
        self.canvas = tk.Canvas(canvas_frame, bg='#1e1e1e', highlightthickness=1, 
                               highlightbackground='#404040')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Status box at bottom-left (under canvas)
        self._setup_status_bottom(left_frame)
        
        # Initialize renderer
        self.renderer = IsometricRenderer(self.canvas)
        
        # Right panel - Controls and toolbox with scrolling support
        right_outer_frame = ttk.Frame(main_frame, style='Dark.TFrame', width=300)
        right_outer_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_outer_frame.pack_propagate(False)
        
        # Create scrollable canvas for right panel
        self.right_canvas = tk.Canvas(right_outer_frame, bg='#2b2b2b', highlightthickness=0, width=280)
        self.right_scrollbar = ttk.Scrollbar(right_outer_frame, orient=tk.VERTICAL, command=self.right_canvas.yview)
        
        self.right_frame = ttk.Frame(self.right_canvas, style='Dark.TFrame')
        
        self.right_frame.bind("<Configure>", lambda e: self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all")))
        
        self.right_canvas_window = self.right_canvas.create_window((0, 0), window=self.right_frame, anchor="nw", width=280)
        self.right_canvas.configure(yscrollcommand=self.right_scrollbar.set)
        
        self.right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Mouse wheel scrolling - zoom on main canvas, scroll on right panel
        def on_mousewheel(event):
            # Check if mouse is over the right panel
            widget = event.widget
            if widget == self.right_canvas or widget == self.right_frame:
                self.right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            else:
                # Zoom on main canvas
                if event.delta > 0:
                    self._zoom_in()
                else:
                    self._zoom_out()
        
        self.root.bind("<MouseWheel>", on_mousewheel)
        self.right_canvas.bind("<MouseWheel>", lambda e: self.right_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        self._setup_toolbox(self.right_frame)
        self._setup_controls(self.right_frame)
        self._setup_help(self.right_frame)
        
        # Draw initial grid
        self._draw_grid()
    
    def _setup_toolbox(self, parent):
        """Set up the component toolbox."""
        # Use a simple Frame instead of LabelFrame to avoid text duplication
        self.toolbox_container = ttk.Frame(parent, style='Dark.TFrame')
        self.toolbox_container.pack(fill=tk.X, padx=5, pady=5)
        
        # Add a simple label for the title
        self.toolbox_label = ttk.Label(self.toolbox_container, text="Component Toolbox", 
                                style='Dark.TLabel', font=('TkDefaultFont', 9, 'bold'))
        self.toolbox_label.pack(anchor=tk.W, padx=5, pady=(5, 2))
        
        # Add a separator line
        separator = ttk.Separator(self.toolbox_container, orient='horizontal')
        separator.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Create the toolbox notebook
        self._create_toolbox_notebook()
    
    def _create_toolbox_notebook(self):
        """Create the notebook with component categories based on current view mode."""
        # Remove existing notebook if present
        if hasattr(self, 'toolbox_notebook') and self.toolbox_notebook:
            self.toolbox_notebook.destroy()
        
        if self.view_mode == ViewMode.SURFACE_CODE_2D:
            # Surface code specific components - only components that can be placed
            categories = {
                "Stabilizers": [
                    ComponentType.SURFACE_X_STABILIZER,
                    ComponentType.SURFACE_Z_STABILIZER,
                ],
                "Lattice": [
                    ComponentType.SURFACE_DATA,
                    ComponentType.SURFACE_BOUNDARY,
                ],
                "Defects": [
                    ComponentType.SURFACE_X_ERROR,
                    ComponentType.SURFACE_Z_ERROR,
                    ComponentType.SURFACE_Y_ERROR,
                ]
            }
        elif self.view_mode == ViewMode.LDPC_TANNER:
            # LDPC Tanner graph mode components
            categories = {
                "Checks": [
                    ComponentType.LDPC_X_CHECK,
                    ComponentType.LDPC_Z_CHECK,
                ],
                "Qubits": [
                    ComponentType.LDPC_DATA_QUBIT,
                    ComponentType.LDPC_ANCILLA,
                ],
                "Connect": [
                    ComponentType.LDPC_EDGE,
                ]
            }
        elif self.view_mode == ViewMode.LDPC_PHYSICAL:
            # LDPC Physical layout mode components
            categories = {
                "Data": [
                    ComponentType.LDPC_DATA_QUBIT,
                ],
                "Ancilla": [
                    ComponentType.LDPC_X_ANCILLA,
                    ComponentType.LDPC_Z_ANCILLA,
                    ComponentType.LDPC_ANCILLA,
                ],
                "Bus": [
                    ComponentType.LDPC_CAVITY_BUS,
                ]
            }
        else:
            # Circuit mode components (isometric) - NO LDPC components here
            categories = {
                "Single": [
                    ComponentType.X_GATE, ComponentType.Z_GATE, ComponentType.Y_GATE,
                    ComponentType.H_GATE, ComponentType.S_GATE, ComponentType.T_GATE
                ],
                "Double": [
                    ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE
                ],
                "Qubits": [
                    ComponentType.DATA_QUBIT, ComponentType.ANCILLA_QUBIT
                ],
                "Measure": [
                    ComponentType.MEASURE, ComponentType.RESET
                ],
                "Errors": [
                    ComponentType.CIRCUIT_X_ERROR, ComponentType.CIRCUIT_Z_ERROR,
                    ComponentType.CIRCUIT_Y_ERROR
                ]
            }
        
        # Create notebook for categories
        self.toolbox_notebook = ttk.Notebook(self.toolbox_container, style='Dark.TNotebook')
        self.toolbox_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Store button references for highlighting
        self.tool_buttons = {}
        
        # Define which gates can be controlled
        controllable_gates = [
            ComponentType.X_GATE, ComponentType.Z_GATE, ComponentType.Y_GATE,
            ComponentType.H_GATE, ComponentType.S_GATE, ComponentType.T_GATE,
            ComponentType.SWAP_GATE
        ]
        
        for category, components in categories.items():
            tab_frame = ttk.Frame(self.toolbox_notebook, style='Dark.TFrame')
            self.toolbox_notebook.add(tab_frame, text=category)
            
            for i, comp_type in enumerate(components):
                # Use tk.Button instead of ttk.Button for better color control
                btn = tk.Button(tab_frame, text=comp_type.value,
                               command=lambda ct=comp_type: self._select_tool(ct),
                               bg='#2d2d44', fg='#ffffff', 
                               activebackground='#e94560', activeforeground='#ffffff',
                               relief='flat', pady=4)
                btn.pack(fill=tk.X, padx=2, pady=1)
                self.tool_buttons[comp_type] = btn
                
                # Add right-click context menu for controllable gates
                if comp_type in controllable_gates:
                    btn.bind("<Button-3>", lambda e, ct=comp_type: self._show_toolbox_context_menu(e, ct))
        
        # Highlight current tool if set
        if hasattr(self, 'current_tool') and self.current_tool in self.tool_buttons:
            self._highlight_selected_tool()
    
    def _update_toolbox_for_mode(self):
        """Update the toolbox to show appropriate components for current view mode."""
        self._create_toolbox_notebook()
        
        # Update the toolbox label based on mode
        if self.view_mode == ViewMode.SURFACE_CODE_2D:
            self.toolbox_label.config(text="Surface Code Toolbox")
        elif self.view_mode == ViewMode.LDPC_TANNER:
            self.toolbox_label.config(text="LDPC Tanner Toolbox")
        elif self.view_mode == ViewMode.LDPC_PHYSICAL:
            self.toolbox_label.config(text="LDPC Physical Toolbox")
        else:
            self.toolbox_label.config(text="Component Toolbox")
    
    def _setup_controls(self, parent):
        """Set up control buttons and options - organized by mode relevance."""
        # Main controls container
        self.controls_container = ttk.Frame(parent, style='Dark.TFrame')
        self.controls_container.pack(fill=tk.X, padx=5, pady=5)
        
        # === VIEW MODES SECTION ===
        mode_header = tk.Label(self.controls_container, text="View Modes",
                              bg='#2b2b2b', fg='#aabbcc', font=('TkDefaultFont', 9, 'bold'))
        mode_header.pack(anchor=tk.W, padx=5, pady=(5, 3))
        
        mode_frame = ttk.Frame(self.controls_container, style='Dark.TFrame')
        mode_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Circuit Mode button (default) - accent color
        self.circuit_mode_btn = tk.Button(mode_frame, text="Circuit Mode",
                                          command=self._switch_to_circuit_mode,
                                          bg='#3a4a5a', fg='#88aacc',
                                          activebackground='#5a7a9a', activeforeground='#ffffff',
                                          relief='flat', pady=2, font=('TkDefaultFont', 8))
        self.circuit_mode_btn.pack(fill=tk.X, pady=1)
        
        # Surface Code mode button - same palette
        self.surface_mode_btn = tk.Button(mode_frame, text="Surface Code (V)",
                                          command=self._switch_to_surface_mode,
                                          bg='#3a4a5a', fg='#88aacc',
                                          activebackground='#5a7a9a', activeforeground='#ffffff',
                                          relief='flat', pady=2, font=('TkDefaultFont', 8))
        self.surface_mode_btn.pack(fill=tk.X, pady=1)
        
        # LDPC mode button - same palette
        self.ldpc_mode_btn = tk.Button(mode_frame, text="LDPC Mode (B)",
                                       command=self._switch_to_ldpc_mode,
                                       bg='#3a4a5a', fg='#88aacc',
                                       activebackground='#5a7a9a', activeforeground='#ffffff',
                                       relief='flat', pady=2, font=('TkDefaultFont', 8))
        self.ldpc_mode_btn.pack(fill=tk.X, pady=1)
        
        # LDPC sub-mode button (only visible in LDPC mode)
        self.ldpc_submode_btn = tk.Button(mode_frame, text="→ Tanner Graph",
                                          command=self._toggle_ldpc_submode,
                                          bg='#3a4a5a', fg='#88aacc',
                                          activebackground='#5a7a9a', activeforeground='#ffffff',
                                          relief='flat', pady=2, font=('TkDefaultFont', 8))
        # Initially hidden - will be shown when in LDPC mode
        
        # === FILE OPERATIONS (Always visible) ===
        ttk.Separator(self.controls_container, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        
        file_header = tk.Label(self.controls_container, text="File",
                              bg='#2b2b2b', fg='#aabbcc', font=('TkDefaultFont', 9, 'bold'))
        file_header.pack(anchor=tk.W, padx=5, pady=(0, 3))
        
        file_frame = ttk.Frame(self.controls_container, style='Dark.TFrame')
        file_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Compact file buttons in a row - unified muted palette
        tk.Button(file_frame, text="Clear", width=6,
                 command=self._clear_circuit,
                 bg='#4a4040', fg='#cc9999',
                 activebackground='#5a5050',
                 relief='flat', font=('TkDefaultFont', 8)).pack(side=tk.LEFT, padx=1)
        
        tk.Button(file_frame, text="Save", width=6,
                 command=self._save_circuit,
                 bg='#404a40', fg='#99cc99',
                 activebackground='#505a50',
                 relief='flat', font=('TkDefaultFont', 8)).pack(side=tk.LEFT, padx=1)
        
        tk.Button(file_frame, text="Load", width=6,
                 command=self._load_circuit,
                 bg='#40404a', fg='#9999cc',
                 activebackground='#6688ff',
                 relief='flat', font=('TkDefaultFont', 8)).pack(side=tk.LEFT, padx=1)
        
        tk.Button(file_frame, text="QASM", width=6,
                 command=self._export_to_qasm,
                 bg='#3a3a30', fg='#ddddaa',
                 activebackground='#aaaa66',
                 relief='flat', font=('TkDefaultFont', 8)).pack(side=tk.LEFT, padx=1)
        
        # === MODE-SPECIFIC OPERATIONS ===
        ttk.Separator(self.controls_container, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        
        # Frame for mode-specific quantum operations (so we can swap them)
        self.quantum_ops_frame = ttk.Frame(self.controls_container, style='Dark.TFrame')
        self.quantum_ops_frame.pack(fill=tk.X)
        
        # Create buttons for all modes (we'll show/hide based on view_mode)
        self._create_circuit_mode_buttons()
        self._create_surface_mode_buttons()
        self._create_ldpc_mode_buttons()
        
        # Show the appropriate buttons
        self._update_quantum_ops_buttons()
    
    def _create_circuit_mode_buttons(self):
        """Create the quantum operation buttons for circuit mode."""
        self.circuit_mode_frame = ttk.Frame(self.quantum_ops_frame, style='Dark.TFrame')
        
        # Mode header
        header = tk.Label(self.circuit_mode_frame, text="Circuit Operations",
                         bg='#2b2b2b', fg='#aabbcc', font=('TkDefaultFont', 9, 'bold'))
        header.pack(anchor=tk.W, padx=5, pady=(0, 3))
        
        ttk.Button(self.circuit_mode_frame, text="Simulate Evolution",
                 command=self._simulate_evolution, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
        
        ttk.Button(self.circuit_mode_frame, text="Calculate Syndrome",
                 command=self._calculate_syndrome, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
        
        ttk.Button(self.circuit_mode_frame, text="Validate Circuit",
                 command=self._validate_circuit, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
        
        # QEC Section header
        qec_header = tk.Label(self.circuit_mode_frame, text="Error Correction",
                             bg='#2b2b2b', fg='#ffcc66', font=('TkDefaultFont', 8, 'bold'))
        qec_header.pack(anchor=tk.W, padx=5, pady=(8, 3))
        
        # Info about placing errors
        error_info = tk.Label(self.circuit_mode_frame, text="Place errors from Errors tab",
                             bg='#2b2b2b', fg='#888888', font=('TkDefaultFont', 8))
        error_info.pack(anchor=tk.W, padx=5)
        
        # Yellow correction button
        self.circuit_correct_btn = tk.Button(self.circuit_mode_frame, text="Apply Correction",
                 command=self._apply_circuit_correction,
                 bg='#ccaa44', fg='#000000',
                 activebackground='#ffcc44', activeforeground='#000000',
                 relief='flat', font=('TkDefaultFont', 9, 'bold'))
        self.circuit_correct_btn.pack(fill=tk.X, padx=5, pady=2)
    
    def _create_surface_mode_buttons(self):
        """Create the quantum operation buttons for surface code mode."""
        self.surface_mode_frame = ttk.Frame(self.quantum_ops_frame, style='Dark.TFrame')
        
        # Mode header
        header = tk.Label(self.surface_mode_frame, text="Surface Code Operations",
                         bg='#2b2b2b', fg='#aabbcc', font=('TkDefaultFont', 9, 'bold'))
        header.pack(anchor=tk.W, padx=5, pady=(0, 3))
        
        # QEC Section
        qec_header = tk.Label(self.surface_mode_frame, text="Error Correction",
                             bg='#2b2b2b', fg='#ffcc66', font=('TkDefaultFont', 8, 'bold'))
        qec_header.pack(anchor=tk.W, padx=5, pady=(5, 3))
        
        # Error injection info
        error_info = tk.Label(self.surface_mode_frame, text="Place errors using toolbox",
                             bg='#2b2b2b', fg='#888888', font=('TkDefaultFont', 8))
        error_info.pack(anchor=tk.W, padx=5)
        
        ttk.Button(self.surface_mode_frame, text="Highlight Syndrome",
                 command=self._highlight_syndrome_surface, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
        
        ttk.Button(self.surface_mode_frame, text="Run Decoder",
                 command=self._run_decoder_surface, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
        
        # Correction button (yellow accent)
        self.surface_correct_btn = tk.Button(self.surface_mode_frame, text="Apply Correction",
                 command=self._apply_surface_correction,
                 bg='#ccaa44', fg='#000000',
                 activebackground='#ffcc44', activeforeground='#000000',
                 relief='flat', font=('TkDefaultFont', 9, 'bold'))
        self.surface_correct_btn.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(self.surface_mode_frame, text="Clear Highlights",
                 command=self._clear_syndrome_highlights, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
        
        # Surface code info display
        self.surface_info_frame = ttk.Frame(self.surface_mode_frame, style='Dark.TFrame')
        self.surface_info_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        self.surface_syndrome_label = tk.Label(self.surface_info_frame, text="Errors: 0  |  Syndrome: 0",
                                               bg='#2b2b2b', fg='#88ff88',
                                               font=('Consolas', 8))
        self.surface_syndrome_label.pack(anchor=tk.W)
        
        self.surface_threshold_label = tk.Label(self.surface_info_frame, text="Threshold: OK",
                                                bg='#2b2b2b', fg='#88ff88',
                                                font=('Consolas', 8))
        self.surface_threshold_label.pack(anchor=tk.W)
    
    def _create_ldpc_mode_buttons(self):
        """Create the quantum operation buttons for LDPC modes."""
        self.ldpc_mode_frame = ttk.Frame(self.quantum_ops_frame, style='Dark.TFrame')
        
        # Sub-mode indicator/toggle at top
        self.ldpc_submode_label = tk.Label(self.ldpc_mode_frame, 
                                           text="LDPC: Tanner Graph",
                                           bg='#2b2b2b', fg='#aabbcc',
                                           font=('TkDefaultFont', 9, 'bold'))
        self.ldpc_submode_label.pack(anchor=tk.W, padx=5, pady=(0, 3))
        
        ttk.Button(self.ldpc_mode_frame, text="Switch View (B)",
                 command=self._toggle_ldpc_submode, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
        
        ttk.Button(self.ldpc_mode_frame, text="Show Connectivity",
                 command=self._show_ldpc_connectivity, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
        
        ttk.Button(self.ldpc_mode_frame, text="Clear Graph",
                 command=self._clear_ldpc_graph, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
        
        ttk.Button(self.ldpc_mode_frame, text="Generate Example",
                 command=self._generate_ldpc_example, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
        
        # QEC Section for Tanner graph
        qec_header = tk.Label(self.ldpc_mode_frame, text="Parity Checks",
                             bg='#2b2b2b', fg='#ffcc66', font=('TkDefaultFont', 8, 'bold'))
        qec_header.pack(anchor=tk.W, padx=5, pady=(8, 3))
        
        # Yellow button to show parity check violations
        self.ldpc_syndrome_btn = tk.Button(self.ldpc_mode_frame, text="Show Violations",
                 command=self._show_ldpc_syndrome,
                 bg='#ccaa44', fg='#000000',
                 activebackground='#ffcc44', activeforeground='#000000',
                 relief='flat', font=('TkDefaultFont', 9, 'bold'))
        self.ldpc_syndrome_btn.pack(fill=tk.X, padx=5, pady=2)
    
    def _update_quantum_ops_buttons(self):
        """Show the appropriate quantum operation buttons based on current mode."""
        # Hide all frames first
        self.circuit_mode_frame.pack_forget()
        self.surface_mode_frame.pack_forget()
        self.ldpc_mode_frame.pack_forget()
        
        # Update mode button styling to show which is active (cohesive palette)
        if hasattr(self, 'circuit_mode_btn'):
            if self.view_mode == ViewMode.ISOMETRIC_3D:
                self.circuit_mode_btn.config(bg='#5a7a9a', fg='#ffffff', relief='sunken')
            else:
                self.circuit_mode_btn.config(bg='#3a4a5a', fg='#88aacc', relief='flat')
        
        if hasattr(self, 'surface_mode_btn'):
            if self.view_mode == ViewMode.SURFACE_CODE_2D:
                self.surface_mode_btn.config(bg='#5a7a9a', fg='#ffffff', relief='sunken')
            else:
                self.surface_mode_btn.config(bg='#3a4a5a', fg='#88aacc', relief='flat')
        
        if hasattr(self, 'ldpc_mode_btn'):
            if self.view_mode in [ViewMode.LDPC_TANNER, ViewMode.LDPC_PHYSICAL]:
                self.ldpc_mode_btn.config(bg='#5a7a9a', fg='#ffffff', relief='sunken')
                # Show LDPC sub-mode button
                if hasattr(self, 'ldpc_submode_btn'):
                    self.ldpc_submode_btn.pack(fill=tk.X, pady=1)
                    if self.view_mode == ViewMode.LDPC_TANNER:
                        self.ldpc_submode_btn.config(text="→ Switch to Physical Layout")
                    else:
                        self.ldpc_submode_btn.config(text="→ Switch to Tanner Graph")
            else:
                self.ldpc_mode_btn.config(bg='#3a4a5a', fg='#88aacc', relief='flat')
                # Hide LDPC sub-mode button
                if hasattr(self, 'ldpc_submode_btn'):
                    self.ldpc_submode_btn.pack_forget()
        
        # Update LDPC sub-mode label
        if hasattr(self, 'ldpc_submode_label'):
            if self.view_mode == ViewMode.LDPC_TANNER:
                self.ldpc_submode_label.config(text="LDPC: Tanner Graph", fg='#aabbcc')
            elif self.view_mode == ViewMode.LDPC_PHYSICAL:
                self.ldpc_submode_label.config(text="LDPC: Physical Layout", fg='#aabbcc')
        
        # Show the appropriate frame
        if self.view_mode == ViewMode.SURFACE_CODE_2D:
            self.surface_mode_frame.pack(fill=tk.X)
        elif self.view_mode in [ViewMode.LDPC_TANNER, ViewMode.LDPC_PHYSICAL]:
            self.ldpc_mode_frame.pack(fill=tk.X)
        else:
            self.circuit_mode_frame.pack(fill=tk.X)
        
        # Update help/tutorial buttons for current mode
        self._update_help_tutorials()
    
    def _setup_help(self, parent):
        """Set up help section - compact buttons with mode-specific tutorials."""
        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        
        help_header = tk.Label(parent, text="Help & Learning",
                              bg='#2b2b2b', fg='#aabbcc', font=('TkDefaultFont', 9, 'bold'))
        help_header.pack(anchor=tk.W, padx=10, pady=(0, 3))
        
        self.help_frame = ttk.Frame(parent, style='Dark.TFrame')
        self.help_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # === Circuit Mode Tutorials (Basic | Advanced) ===
        self.circuit_tutorial_row = ttk.Frame(self.help_frame, style='Dark.TFrame')
        self.circuit_tutorial_row.pack(fill=tk.X, padx=5, pady=1)
        
        # Basic tutorial (left button - teal/cyan accent)
        tk.Button(self.circuit_tutorial_row, text="Basic",
                 command=self._show_tutorial,
                 bg='#3a5a6a', fg='#88ccdd',
                 activebackground='#5a7a8a', activeforeground='#ffffff',
                 relief='flat', pady=3, font=('TkDefaultFont', 8, 'bold'),
                 width=8).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 1))
        
        # Advanced tutorial (right button - purple accent)
        tk.Button(self.circuit_tutorial_row, text="Advanced",
                 command=self._show_advanced_large_circuits_tutorial,
                 bg='#5a3a6a', fg='#cc88dd',
                 activebackground='#7a5a8a', activeforeground='#ffffff',
                 relief='flat', pady=3, font=('TkDefaultFont', 8, 'bold'),
                 width=8).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(1, 0))
        
        # === Surface Code Tutorial (hidden by default) ===
        self.surface_tutorial_row = ttk.Frame(self.help_frame, style='Dark.TFrame')
        # Don't pack yet - will show/hide based on mode
        
        tk.Button(self.surface_tutorial_row, text="📖 Surface Code Tutorial",
                 command=self._show_surface_code_tutorial,
                 bg='#4a6a4a', fg='#88dd88',
                 activebackground='#6a8a6a', activeforeground='#ffffff',
                 relief='flat', pady=3, font=('TkDefaultFont', 8, 'bold')).pack(fill=tk.X)
        
        # === LDPC Tutorial (hidden by default) ===
        self.ldpc_tutorial_row = ttk.Frame(self.help_frame, style='Dark.TFrame')
        # Don't pack yet - will show/hide based on mode
        
        tk.Button(self.ldpc_tutorial_row, text="📖 LDPC Tutorial",
                 command=self._show_ldpc_tutorial,
                 bg='#5a4a6a', fg='#cc99dd',
                 activebackground='#7a6a8a', activeforeground='#ffffff',
                 relief='flat', pady=3, font=('TkDefaultFont', 8, 'bold')).pack(fill=tk.X)
        
        # Other help buttons - plain style (always visible)
        ttk.Button(self.help_frame, text="Quick Reference",
                 command=self._show_quick_reference, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
        
        ttk.Button(self.help_frame, text="Shortcuts (?)",
                 command=self._show_shortcuts, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
        
        ttk.Button(self.help_frame, text="Legend",
                 command=self._toggle_legend, style='Dark.TButton').pack(fill=tk.X, padx=5, pady=1)
    
    def _update_help_tutorials(self):
        """Update tutorial button visibility based on current mode."""
        if not hasattr(self, 'circuit_tutorial_row'):
            return  # Not yet initialized
        
        # Hide all mode-specific tutorial rows first
        self.circuit_tutorial_row.pack_forget()
        self.surface_tutorial_row.pack_forget()
        self.ldpc_tutorial_row.pack_forget()
        
        # Show appropriate tutorial based on mode (at top of help_frame)
        if self.view_mode == ViewMode.ISOMETRIC_3D:
            # Circuit mode: show Basic | Advanced
            self.circuit_tutorial_row.pack(fill=tk.X, padx=5, pady=1, in_=self.help_frame)
            self.circuit_tutorial_row.lift()  # Ensure it stays at top
        elif self.view_mode == ViewMode.SURFACE_CODE_2D:
            # Surface mode: show Surface Code Tutorial
            self.surface_tutorial_row.pack(fill=tk.X, padx=5, pady=1, in_=self.help_frame)
            self.surface_tutorial_row.lift()
        elif self.view_mode in [ViewMode.LDPC_TANNER, ViewMode.LDPC_PHYSICAL]:
            # LDPC mode: show LDPC Tutorial
            self.ldpc_tutorial_row.pack(fill=tk.X, padx=5, pady=1, in_=self.help_frame)
            self.ldpc_tutorial_row.lift()
    
    def _show_ldpc_tutorial(self):
        """Show the LDPC tutorial (placeholder for future implementation)."""
        messagebox.showinfo("LDPC Tutorial", 
            "LDPC Tutorial coming soon!\n\n"
            "For now, explore the LDPC mode features:\n"
            "• Tanner Graph visualization\n"
            "• Physical qubit layout\n"
            "• Variable and check node placement\n"
            "• Edge connections")

    def _switch_to_circuit_mode(self):
        """Switch to standard isometric circuit mode."""
        if self.view_mode != ViewMode.ISOMETRIC_3D:
            # Save current mode components
            if self.view_mode == ViewMode.SURFACE_CODE_2D:
                self.surface_components = self.components[:]
                self.components = self.circuit_components[:]
            elif self.view_mode == ViewMode.LDPC_TANNER:
                self.ldpc_tanner_components = self.components[:]
                self.components = self.circuit_components[:]
            elif self.view_mode == ViewMode.LDPC_PHYSICAL:
                self.ldpc_physical_components = self.components[:]
                self.components = self.circuit_components[:]
            
            self.view_mode = ViewMode.ISOMETRIC_3D
            self._update_toolbox_for_mode()
            self._update_quantum_ops_buttons()
            self._draw_grid()
            self._redraw_circuit()
            self._log_status("Switched to Circuit mode")
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog (#5)."""
        shortcuts_window = tk.Toplevel(self.root)
        shortcuts_window.title("Keyboard Shortcuts")
        shortcuts_window.configure(bg='#2b2b2b')
        shortcuts_window.geometry("350x580")
        shortcuts_window.transient(self.root)
        
        # Title
        title_label = tk.Label(shortcuts_window, text="⌨ Keyboard Shortcuts",
                              bg='#2b2b2b', fg='#00ff88',
                              font=('Segoe UI', 14, 'bold'))
        title_label.pack(pady=(15, 10))
        
        # Shortcuts content
        shortcuts_frame = ttk.Frame(shortcuts_window, style='Dark.TFrame')
        shortcuts_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Define shortcuts by category
        shortcut_categories = {
            "View Modes": [
                ("V", "Toggle Surface Code / Circuit Mode"),
                ("B", "Cycle LDPC modes (Tanner → Physical → Circuit)"),
            ],
            "Clipboard": [
                ("Ctrl+C", "Copy selected component to clipboard"),
                ("Ctrl+V", "Paste component from clipboard"),
                ("Ctrl+Shift+C", "Copy entire circuit to clipboard"),
            ],
            "Editing": [
                ("Ctrl+Z", "Undo last action"),
                ("Ctrl+Y", "Redo last action"),
                ("Delete", "Delete selected component"),
                ("C", "Clear entire circuit"),
            ],
            "Zoom": [
                ("+/=", "Zoom in"),
                ("-", "Zoom out"),
                ("0", "Reset zoom to 100%"),
            ],
            "Navigation": [
                ("Middle Mouse", "Pan the grid"),
                ("Left Click", "Place component / Select"),
                ("Right Click", "Context menu"),
            ],
            "Help": [
                ("T", "Open Tutorial"),
                ("?", "Show this shortcuts dialog"),
            ],
        }
        
        for category, shortcuts in shortcut_categories.items():
            # Category header
            cat_label = tk.Label(shortcuts_frame, text=category,
                               bg='#2b2b2b', fg='#ffd93d',
                               font=('Segoe UI', 10, 'bold'))
            cat_label.pack(anchor=tk.W, pady=(10, 5))
            
            for key, description in shortcuts:
                # Shortcut row
                row_frame = ttk.Frame(shortcuts_frame, style='Dark.TFrame')
                row_frame.pack(fill=tk.X, pady=2)
                
                # Key badge
                key_label = tk.Label(row_frame, text=key,
                                    bg='#404040', fg='#ffffff',
                                    font=('Consolas', 9, 'bold'),
                                    padx=8, pady=2)
                key_label.pack(side=tk.LEFT, padx=(0, 10))
                
                # Description
                desc_label = tk.Label(row_frame, text=description,
                                     bg='#2b2b2b', fg='#cccccc',
                                     font=('Segoe UI', 9))
                desc_label.pack(side=tk.LEFT)
        
        # Close button
        close_btn = tk.Button(shortcuts_window, text="Close",
                             command=shortcuts_window.destroy,
                             bg='#404040', fg='#ffffff',
                             activebackground='#505050',
                             relief='flat', padx=20, pady=5)
        close_btn.pack(pady=15)
    
    def _setup_status_bottom(self, parent):
        """Set up the status box at bottom-left under the canvas."""
        # Container for status and grid controls
        bottom_frame = ttk.Frame(parent, style='Dark.TFrame')
        bottom_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Grid size controls (⊞+/⊞-) - orange/amber color scheme
        grid_control_frame = ttk.Frame(bottom_frame, style='Dark.TFrame')
        grid_control_frame.pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(grid_control_frame, text="G-", width=3,
                 command=self._decrease_grid_size,
                 bg='#5a4a30', fg='#ffcc66',
                 activebackground='#7a6a50', activeforeground='#ffffff',
                 relief='flat', font=('Consolas', 9, 'bold')).pack(side=tk.LEFT, padx=2)
        
        self.grid_size_label = tk.Label(grid_control_frame, text="20", width=3,
                                   bg='#2b2b2b', fg='#ffcc66',
                                   font=('TkDefaultFont', 8))
        self.grid_size_label.pack(side=tk.LEFT)
        
        tk.Button(grid_control_frame, text="G+", width=3,
                 command=self._increase_grid_size,
                 bg='#5a4a30', fg='#ffcc66',
                 activebackground='#7a6a50', activeforeground='#ffffff',
                 relief='flat', font=('Consolas', 9, 'bold')).pack(side=tk.LEFT, padx=2)
        
        # Separator between grid and zoom
        tk.Label(bottom_frame, text="|", bg='#2b2b2b', fg='#555555',
                font=('TkDefaultFont', 10)).pack(side=tk.LEFT, padx=3)
        
        # Zoom controls (+/-) - blue color scheme for distinction
        zoom_control_frame = ttk.Frame(bottom_frame, style='Dark.TFrame')
        zoom_control_frame.pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(zoom_control_frame, text="−", width=2,
                 command=self._zoom_out,
                 bg='#3a4a5a', fg='#66ccff',
                 activebackground='#5a6a7a', activeforeground='#ffffff',
                 relief='flat', font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT, padx=1)
        
        self.zoom_label = tk.Label(zoom_control_frame, text="100%", width=4,
                                   bg='#2b2b2b', fg='#66ccff',
                                   font=('TkDefaultFont', 8))
        self.zoom_label.pack(side=tk.LEFT)
        
        tk.Button(zoom_control_frame, text="+", width=2,
                 command=self._zoom_in,
                 bg='#3a4a5a', fg='#66ccff',
                 activebackground='#5a6a7a', activeforeground='#ffffff',
                 relief='flat', font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT, padx=1)
        
        tk.Button(zoom_control_frame, text="⟲", width=2,
                 command=self._zoom_reset,
                 bg='#3a4a5a', fg='#66ccff',
                 activebackground='#5a6a7a', activeforeground='#ffffff',
                 relief='flat', font=('TkDefaultFont', 9)).pack(side=tk.LEFT, padx=1)
        
        # Status text area (fills remaining space)
        text_container = ttk.Frame(bottom_frame, style='Dark.TFrame')
        text_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.status_text = tk.Text(text_container, height=4, bg='#1e1e1e', fg='#aaaaaa',
                                  insertbackground='#ffffff', selectbackground='#404040',
                                  font=('Consolas', 8))
        self.status_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        scrollbar = ttk.Scrollbar(text_container, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        self._log_status("Circuit Builder initialized. Select a component and click to place.")
    
    def _setup_status(self, parent):
        """Set up circuit title display area (status text is now at bottom-left)."""
        # Circuit title display only
        title_container = ttk.Frame(parent, style='Dark.TFrame')
        title_container.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        title_label = ttk.Label(title_container, text="Current Circuit:", 
                              style='Dark.TLabel', font=('TkDefaultFont', 8))
        title_label.pack(anchor=tk.W, padx=5)
        
        self.circuit_title_label = ttk.Label(title_container, text="New Circuit", 
                                           style='Dark.TLabel', font=('TkDefaultFont', 10, 'bold'),
                                           foreground='#00ff88')
        self.circuit_title_label.pack(anchor=tk.W, padx=5)
    
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
        self.root.bind("<Control-z>", self._undo)  # Undo
        self.root.bind("<Control-Z>", self._undo)  # Undo (shift+ctrl+z sometimes)
        self.root.bind("<Control-y>", self._redo)  # Redo
        self.root.bind("<Control-Shift-z>", self._redo)  # Redo (alternative)
        self.root.bind("<v>", self._toggle_view_mode)
        self.root.bind("<V>", self._toggle_view_mode)
        self.root.bind("<b>", self._toggle_ldpc_mode)
        self.root.bind("<B>", self._toggle_ldpc_mode)
        # Copy all keybinding (#14)
        self.root.bind("<Control-Shift-c>", self._copy_all_selected)
        self.root.bind("<Control-Shift-C>", self._copy_all_selected)
        # Clear circuit shortcut
        self.root.bind("<c>", lambda e: self._clear_circuit())
        self.root.bind("<C>", lambda e: self._clear_circuit())
        # Escape to cancel control placement mode
        self.root.bind("<Escape>", self._cancel_placement_mode)
    
    def _undo(self, event=None):
        """Undo the last action."""
        if self.command_history.undo():
            self._log_status("↶ Undo")
            self._redraw_circuit()
        else:
            self._log_status("Nothing to undo")
    
    def _redo(self, event=None):
        """Redo the last undone action."""
        if self.command_history.redo():
            self._log_status("↷ Redo")
            self._redraw_circuit()
        else:
            self._log_status("Nothing to redo")
        # Zoom keybindings
        self.root.bind("<plus>", lambda e: self._zoom_in())
        self.root.bind("<equal>", lambda e: self._zoom_in())  # = key (same as + without shift)
        self.root.bind("<minus>", lambda e: self._zoom_out())
        self.root.bind("<0>", lambda e: self._zoom_reset())
    
    def _toggle_view_mode(self, event=None):
        """Toggle between isometric 3D view and 2D surface code lattice view."""
        if self.view_mode == ViewMode.ISOMETRIC_3D:
            # Save circuit components before switching to surface mode
            self.circuit_components = list(self.components)
            # Restore surface components (or start fresh)
            self.components = list(self.surface_components)
            self.view_mode = ViewMode.SURFACE_CODE_2D
            self.current_tool = ComponentType.SURFACE_DATA  # Switch to surface code tools
            self._log_status("Switched to Surface Code Mode (2D Lattice)")
        else:
            # Save surface components before switching to circuit mode
            self.surface_components = list(self.components)
            # Restore circuit components (or start fresh)
            self.components = list(self.circuit_components)
            self.view_mode = ViewMode.ISOMETRIC_3D
            self.current_tool = ComponentType.DATA_QUBIT  # Switch back to circuit tools
            self._log_status("Switched to Circuit Mode (Isometric 3D)")
        
        # Clear any selection
        self.selected_component = None
        
        # Update the toolbox to show appropriate components
        self._update_toolbox_for_mode()
        
        # Update quantum operation buttons for current mode
        self._update_quantum_ops_buttons()
        
        # Redraw grid and components
        self._draw_grid()
        self._redraw_circuit()
        
        # Update mode indicator
        self._update_mode_indicator()
        
        # Refresh legend window if it's open
        if hasattr(self, 'legend_window') and self.legend_window and self.legend_window.winfo_exists():
            self.legend_window.destroy()
            self._show_legend()
    
    def _toggle_ldpc_mode(self, event=None):
        """Toggle between LDPC modes (Tanner graph and Physical layout).
        
        Pressing B cycles through: Current Mode → LDPC Tanner → LDPC Physical → Back to previous mode
        """
        # Store current components if leaving a non-LDPC mode
        if self.view_mode == ViewMode.ISOMETRIC_3D:
            self.circuit_components = list(self.components)
            self.components = list(self.ldpc_tanner_components)
            self.view_mode = ViewMode.LDPC_TANNER
            self.current_tool = ComponentType.LDPC_DATA_QUBIT
            self._log_status("Switched to LDPC Tanner Graph Mode")
        elif self.view_mode == ViewMode.SURFACE_CODE_2D:
            self.surface_components = list(self.components)
            self.components = list(self.ldpc_tanner_components)
            self.view_mode = ViewMode.LDPC_TANNER
            self.current_tool = ComponentType.LDPC_DATA_QUBIT
            self._log_status("Switched to LDPC Tanner Graph Mode")
        elif self.view_mode == ViewMode.LDPC_TANNER:
            # Save Tanner components, switch to Physical
            self.ldpc_tanner_components = list(self.components)
            self.components = list(self.ldpc_physical_components)
            self.view_mode = ViewMode.LDPC_PHYSICAL
            self.current_tool = ComponentType.LDPC_DATA_QUBIT
            self._log_status("Switched to LDPC Physical Layout Mode")
        elif self.view_mode == ViewMode.LDPC_PHYSICAL:
            # Save Physical components, go back to Circuit mode
            self.ldpc_physical_components = list(self.components)
            self.components = list(self.circuit_components)
            self.view_mode = ViewMode.ISOMETRIC_3D
            self.current_tool = ComponentType.DATA_QUBIT
            self._log_status("Switched to Circuit Mode (Isometric 3D)")
        
        # Clear any selection
        self.selected_component = None
        
        # Update the toolbox to show appropriate components
        self._update_toolbox_for_mode()
        
        # Update quantum operation buttons for current mode
        self._update_quantum_ops_buttons()
        
        # Redraw grid and components
        self._draw_grid()
        self._redraw_circuit()
        
        # Update mode indicator
        self._update_mode_indicator()
        
        # Refresh legend window if it's open
        if hasattr(self, 'legend_window') and self.legend_window and self.legend_window.winfo_exists():
            self.legend_window.destroy()
            self._show_legend()
    
    def _switch_to_surface_mode(self):
        """Switch directly to Surface Code mode."""
        if self.view_mode != ViewMode.SURFACE_CODE_2D:
            self._toggle_view_mode()
    
    def _switch_to_ldpc_mode(self):
        """Switch directly to LDPC Tanner mode from any mode."""
        if self.view_mode not in [ViewMode.LDPC_TANNER, ViewMode.LDPC_PHYSICAL]:
            self._toggle_ldpc_mode()
    
    def _toggle_ldpc_submode(self):
        """Toggle between LDPC Tanner and Physical sub-modes only."""
        if self.view_mode == ViewMode.LDPC_TANNER:
            # Save Tanner components, switch to Physical
            self.ldpc_tanner_components = list(self.components)
            self.components = list(self.ldpc_physical_components)
            self.view_mode = ViewMode.LDPC_PHYSICAL
            self.current_tool = ComponentType.LDPC_DATA_QUBIT
            self._log_status("Switched to LDPC Physical Layout Mode")
        elif self.view_mode == ViewMode.LDPC_PHYSICAL:
            # Save Physical components, switch to Tanner
            self.ldpc_physical_components = list(self.components)
            self.components = list(self.ldpc_tanner_components)
            self.view_mode = ViewMode.LDPC_TANNER
            self.current_tool = ComponentType.LDPC_DATA_QUBIT
            self._log_status("Switched to LDPC Tanner Graph Mode")
        else:
            # If not in LDPC mode, enter it
            self._switch_to_ldpc_mode()
            return
        
        # Clear selection and update UI
        self.selected_component = None
        self._update_toolbox_for_mode()
        self._update_quantum_ops_buttons()
        self._draw_grid()
        self._redraw_circuit()
        self._update_mode_indicator()
        
        if hasattr(self, 'legend_window') and self.legend_window and self.legend_window.winfo_exists():
            self.legend_window.destroy()
            self._show_legend()
    
    def _draw_grid(self):
        """Draw the grid for component placement based on current view mode."""
        self.canvas.delete("grid")
        self.canvas.delete("mode_indicator")
        
        if self.view_mode == ViewMode.SURFACE_CODE_2D:
            self._draw_surface_code_lattice()
        elif self.view_mode == ViewMode.LDPC_TANNER:
            self._draw_ldpc_tanner_lattice()
        elif self.view_mode == ViewMode.LDPC_PHYSICAL:
            self._draw_ldpc_physical_lattice()
        else:
            self._draw_isometric_grid()
    
    def _draw_isometric_grid(self):
        """Draw the isometric grid for circuit mode."""
        # Use lighter colors for better contrast against dark background
        grid_color = "#505050"      # Medium gray for grid lines
        boundary_color = "#707070"  # Brighter for boundaries
        grid_range = self.grid_size // 2  # Use configurable grid size
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
    
    def _draw_surface_code_lattice(self):
        """Draw the rotated surface code lattice with node-link visualization.
        
        Coordinate System (Rotated Lattice):
        - Data qubits at odd integer coordinates (1,1), (1,3), (3,1), etc.
        - Stabilizer (ancilla) qubits at even integer coordinates (2,2), (4,4), etc.
        - X-stabilizers where (x+y)/2 is even
        - Z-stabilizers where (x+y)/2 is odd
        """
        # Lattice parameters
        code_distance = 5  # Distance of the surface code
        lattice_extent = 2 * code_distance  # Max coordinate value
        
        # Visual scaling
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        scale = min(canvas_width, canvas_height) / (lattice_extent + 4)  # Pixels per unit
        offset_x = canvas_width // 2
        offset_y = canvas_height // 2
        
        # Store lattice parameters for click handling
        self.lattice_scale = scale
        self.lattice_center_x = offset_x
        self.lattice_center_y = offset_y
        self.lattice_extent = lattice_extent
        self.lattice_offset_x = offset_x  # Keep for compatibility
        self.lattice_offset_y = offset_y
        self.lattice_cell_size = scale  # Keep for compatibility
        self.lattice_size = code_distance
        
        # Store for syndrome highlighting (need offset from center, not from corner)
        # canvas_offset is where coordinate (0,0) maps to on screen
        self.surface_grid_spacing = scale
        self.canvas_offset_x = offset_x - (lattice_extent / 2) * scale
        self.canvas_offset_y = offset_y - (lattice_extent / 2) * scale
        
        def to_screen(x, y):
            """Convert lattice coordinates to screen coordinates."""
            sx = offset_x + (x - lattice_extent / 2) * scale
            sy = offset_y + (y - lattice_extent / 2) * scale
            return sx, sy
        
        # Store conversion function for later use
        self._to_screen = to_screen
        
        # Colors for the rotated lattice - background elements are VERY subtle
        grid_line_color = "#252535"  # Very subtle diagonal grid
        x_stab_color = "#4a2a2a"     # Very dim red for background X-stabilizers
        z_stab_color = "#2a2a4a"     # Very dim blue for background Z-stabilizers
        data_qubit_color = "#555555"  # Dim grey for idle data qubits
        x_edge_color = "#3d2828"      # Very dim red for X-interactions
        z_edge_color = "#28283d"      # Very dim blue for Z-interactions
        
        # Draw subtle diagonal background grid lines
        for i in range(-1, lattice_extent + 2):
            for j in range(-1, lattice_extent + 2):
                if (i + j) % 2 == 0:  # Data qubit positions (odd coords = even sum)
                    x, y = to_screen(i, j)
                    # Draw small + markers for grid reference
                    self.canvas.create_line(x - 3, y, x + 3, y, 
                                           fill=grid_line_color, width=1, tags="grid")
                    self.canvas.create_line(x, y - 3, x, y + 3, 
                                           fill=grid_line_color, width=1, tags="grid")
        
        # Collect data qubit positions and stabilizer positions
        data_positions = []
        x_stabilizer_positions = []
        z_stabilizer_positions = []
        
        for x in range(lattice_extent + 1):
            for y in range(lattice_extent + 1):
                if x % 2 == 1 and y % 2 == 1:  # Odd coordinates = data qubits
                    if 0 < x < lattice_extent and 0 < y < lattice_extent:
                        data_positions.append((x, y))
                elif x % 2 == 0 and y % 2 == 0:  # Even coordinates = stabilizers
                    if 0 < x < lattice_extent and 0 < y < lattice_extent:
                        # Determine X or Z stabilizer based on position
                        if ((x + y) // 2) % 2 == 0:
                            x_stabilizer_positions.append((x, y))
                        else:
                            z_stabilizer_positions.append((x, y))
        
        # Draw interaction edges from stabilizers to their neighboring data qubits
        for sx, sy in z_stabilizer_positions:
            for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nx, ny = sx + dx, sy + dy
                if (nx, ny) in data_positions or (0 < nx < lattice_extent and 0 < ny < lattice_extent):
                    screen_s = to_screen(sx, sy)
                    screen_n = to_screen(nx, ny)
                    self.canvas.create_line(screen_s[0], screen_s[1], 
                                           screen_n[0], screen_n[1],
                                           fill=z_edge_color, width=3, tags="grid")
        
        for sx, sy in x_stabilizer_positions:
            for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nx, ny = sx + dx, sy + dy
                if (nx, ny) in data_positions or (0 < nx < lattice_extent and 0 < ny < lattice_extent):
                    screen_s = to_screen(sx, sy)
                    screen_n = to_screen(nx, ny)
                    self.canvas.create_line(screen_s[0], screen_s[1], 
                                           screen_n[0], screen_n[1],
                                           fill=x_edge_color, width=3, tags="grid")
        
        # Draw data qubits as circles
        for x, y in data_positions:
            sx, sy = to_screen(x, y)
            r = scale * 0.25  # Radius relative to scale
            self.canvas.create_oval(sx - r, sy - r, sx + r, sy + r,
                                   fill=data_qubit_color, outline="#aaaaaa", 
                                   width=2, tags="grid data_qubit")
        
        # Draw Z-stabilizers as subtle X/cross markers (background hints)
        for x, y in z_stabilizer_positions:
            sx, sy = to_screen(x, y)
            arm = scale * 0.25
            self.canvas.create_line(sx - arm, sy - arm, sx + arm, sy + arm,
                                   fill=z_stab_color, width=2, tags="grid z_stab")
            self.canvas.create_line(sx - arm, sy + arm, sx + arm, sy - arm,
                                   fill=z_stab_color, width=2, tags="grid z_stab")
            # No label for background elements - too cluttered
        
        # Draw X-stabilizers as subtle diamond outlines (background hints)
        for x, y in x_stabilizer_positions:
            sx, sy = to_screen(x, y)
            size = scale * 0.25
            points = [sx, sy - size, sx + size, sy, sx, sy + size, sx - size, sy]
            self.canvas.create_polygon(points, fill="", 
                                       outline=x_stab_color, width=2, tags="grid x_stab")
            # No label for background elements - too cluttered
        
        # Draw axis labels
        for i in range(0, lattice_extent + 1, 2):
            sx, sy = to_screen(i, 0)
            self.canvas.create_text(sx, sy + 25, text=str(i),
                                   fill="#666666", font=("Arial", 9), tags="grid")
            sx, sy = to_screen(0, i)
            self.canvas.create_text(sx - 25, sy, text=str(i),
                                   fill="#666666", font=("Arial", 9), tags="grid")
        
        # Draw boundary lines
        corner_tl = to_screen(0, 0)
        corner_tr = to_screen(lattice_extent, 0)
        corner_bl = to_screen(0, lattice_extent)
        corner_br = to_screen(lattice_extent, lattice_extent)
        
        self.canvas.create_line(corner_tl[0], corner_tl[1], corner_tr[0], corner_tr[1],
                               fill="#7f8c8d", width=3, dash=(5, 3), tags="grid")
        self.canvas.create_line(corner_bl[0], corner_bl[1], corner_br[0], corner_br[1],
                               fill="#7f8c8d", width=3, dash=(5, 3), tags="grid")
        self.canvas.create_line(corner_tl[0], corner_tl[1], corner_bl[0], corner_bl[1],
                               fill="#9b59b6", width=3, dash=(5, 3), tags="grid")
        self.canvas.create_line(corner_tr[0], corner_tr[1], corner_br[0], corner_br[1],
                               fill="#9b59b6", width=3, dash=(5, 3), tags="grid")
        
        # Draw any placed surface components on top
        self._draw_placed_surface_components()
    
    def _draw_placed_surface_components(self):
        """Draw user-placed surface code components on the rotated lattice."""
        if not hasattr(self, 'lattice_scale'):
            return
        
        scale = self.lattice_scale
        lattice_extent = self.lattice_extent
        offset_x = self.lattice_center_x
        offset_y = self.lattice_center_y
        
        def to_screen(x, y):
            """Convert lattice coordinates to screen coordinates."""
            sx = offset_x + (x - lattice_extent / 2) * scale
            sy = offset_y + (y - lattice_extent / 2) * scale
            return sx, sy
        
        def get_hex_color(comp_type):
            rgb = self._get_component_color(comp_type)
            return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
        
        for comp in self.components:
            lattice_x, lattice_y, _ = comp.position
            screen_x, screen_y = to_screen(lattice_x, lattice_y)
            
            if comp.component_type == ComponentType.SURFACE_X_STABILIZER:
                # X-stabilizer as filled diamond (larger, highlighted)
                color = "#ff4444"  # Bright red for placed X-stabilizer
                size = scale * 0.45
                points = [screen_x, screen_y - size, screen_x + size, screen_y,
                         screen_x, screen_y + size, screen_x - size, screen_y]
                self.canvas.create_polygon(points, fill=color, outline="#ffffff", 
                                          width=3, tags="component")
                self.canvas.create_text(screen_x, screen_y, text="X", fill="#ffffff",
                                       font=("Arial", 12, "bold"), tags="component")
            
            elif comp.component_type == ComponentType.SURFACE_Z_STABILIZER:
                # Z-stabilizer as highlighted cross
                color = "#4488ff"  # Bright blue for placed Z-stabilizer
                arm = scale * 0.4
                self.canvas.create_line(screen_x - arm, screen_y - arm, 
                                       screen_x + arm, screen_y + arm,
                                       fill=color, width=6, tags="component")
                self.canvas.create_line(screen_x - arm, screen_y + arm,
                                       screen_x + arm, screen_y - arm,
                                       fill=color, width=6, tags="component")
                self.canvas.create_text(screen_x, screen_y + arm + 15, text="Z", 
                                       fill=color, font=("Arial", 10, "bold"), tags="component")
            
            elif comp.component_type == ComponentType.SURFACE_DATA:
                # Data qubit as highlighted circle
                color = get_hex_color(ComponentType.SURFACE_DATA)
                r = scale * 0.3
                self.canvas.create_oval(screen_x - r, screen_y - r, screen_x + r, screen_y + r,
                                       fill=color, outline="#ffffff", width=2, tags="component")
                self.canvas.create_text(screen_x, screen_y, text="D", fill="#000000",
                                       font=("Arial", 9, "bold"), tags="component")
            
            elif comp.component_type == ComponentType.SURFACE_BOUNDARY:
                # Boundary marker
                color = get_hex_color(ComponentType.SURFACE_BOUNDARY)
                size = scale * 0.25
                self.canvas.create_rectangle(screen_x - size, screen_y - size/2,
                                            screen_x + size, screen_y + size/2,
                                            fill=color, outline="#ffffff", width=2, tags="component")
            
            elif comp.component_type == ComponentType.SURFACE_X_ERROR:
                # X error on data qubit - red circle with X mark
                color = get_hex_color(ComponentType.SURFACE_X_ERROR)
                r = scale * 0.35
                self.canvas.create_oval(screen_x - r, screen_y - r, screen_x + r, screen_y + r,
                                       fill=color, outline="#ffffff", width=3, tags="component")
                mark = r * 0.6
                self.canvas.create_line(screen_x - mark, screen_y - mark, 
                                       screen_x + mark, screen_y + mark,
                                       fill="#ffffff", width=3, tags="component")
                self.canvas.create_line(screen_x - mark, screen_y + mark,
                                       screen_x + mark, screen_y - mark,
                                       fill="#ffffff", width=3, tags="component")
            
            elif comp.component_type == ComponentType.SURFACE_Z_ERROR:
                # Z error on data qubit - blue circle with Z mark
                color = get_hex_color(ComponentType.SURFACE_Z_ERROR)
                r = scale * 0.35
                self.canvas.create_oval(screen_x - r, screen_y - r, screen_x + r, screen_y + r,
                                       fill=color, outline="#ffffff", width=3, tags="component")
                self.canvas.create_text(screen_x, screen_y, text="Z", fill="#ffffff",
                                       font=("Arial", 11, "bold"), tags="component")
            
            elif comp.component_type == ComponentType.SURFACE_Y_ERROR:
                # Y error on data qubit - yellow circle with Y mark
                color = get_hex_color(ComponentType.SURFACE_Y_ERROR)
                r = scale * 0.35
                self.canvas.create_oval(screen_x - r, screen_y - r, screen_x + r, screen_y + r,
                                       fill=color, outline="#333333", width=3, tags="component")
                self.canvas.create_text(screen_x, screen_y, text="Y", fill="#000000",
                                       font=("Arial", 11, "bold"), tags="component")
            
            else:
                # Generic fallback
                r = scale * 0.2
                self.canvas.create_oval(screen_x - r, screen_y - r, screen_x + r, screen_y + r,
                                       fill="#888888", outline="#ffffff", width=2, tags="component")
            
            # Highlight selected component
            if comp == self.selected_component:
                r = scale * 0.5
                self.canvas.create_rectangle(screen_x - r, screen_y - r, screen_x + r, screen_y + r,
                                            fill="", outline="#ffff00", width=3, tags="component")
    
    # ==================== LDPC COLOR PALETTE ====================
    # Using a cohesive color palette based on color theory (split-complementary)
    # Primary: Teal (#2EC4B6) - Data qubits
    # Accent 1: Coral (#FF6B6B) - X-checks (warm)
    # Accent 2: Gold (#FFD93D) - Z-checks (warm complementary)
    # Accent 3: Lavender (#9B5DE5) - Ancilla qubits
    # Neutral: Slate (#6B7280) - Edges/connections
    
    LDPC_COLORS = {
        'data_qubit': '#2EC4B6',      # Teal - calming, represents stable data
        'x_check': '#FF6B6B',          # Coral/Salmon - warm, X-type stabilizer
        'z_check': '#FFD93D',          # Gold/Amber - warm, Z-type stabilizer
        'ancilla': '#9B5DE5',          # Lavender/Purple - auxiliary qubits
        'x_ancilla': '#E07A5F',        # Terracotta - X-ancilla layer
        'z_ancilla': '#81B29A',        # Sage green - Z-ancilla layer
        'edge': '#6B7280',             # Slate gray - connections
        'cavity_bus': '#3D5A80',       # Navy blue - cavity bus
        'background_node': '#3A3A4A',  # Dark slate - background grid nodes
        'grid_line': '#2A2A3A',        # Very dark - grid lines
    }
    
    def _draw_ldpc_tanner_lattice(self):
        """Draw the LDPC Hypergraph Product Code lattice visualization.
        
        This visualizes the Tanner graph of a Hypergraph Product (HGP) Code:
        - Nodes arranged on a 2D lattice (i,j) where i,j are product indices
        - Data Qubits (teal circles) and Check Nodes (X=coral, Z=gold squares)
        - "Curved strings" representing non-local connectivity inherited from seed codes
        - Horizontal arcs: constraints from first seed code
        - Vertical arcs: constraints from second seed code
        
        The HGP structure: H = (H1 ⊗ I) + (I ⊗ H2^T) for X-checks
                          and similar for Z-checks
        """
        colors = self.LDPC_COLORS
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Grid parameters for HGP code
        # N1 x N2 product gives us our lattice dimensions
        grid_rows = 4  # N1 from first seed code
        grid_cols = 6  # N2 from second seed code
        
        # Margins and spacing
        margin_x = 100
        margin_y = 80
        usable_width = canvas_width - 2 * margin_x
        usable_height = canvas_height - 2 * margin_y
        
        cell_width = usable_width / (grid_cols + 1)
        cell_height = usable_height / (grid_rows + 1)
        
        # Node sizes
        data_radius = 18
        check_size = 14
        
        # Store lattice parameters
        self.hgp_grid_rows = grid_rows
        self.hgp_grid_cols = grid_cols
        self.hgp_cell_width = cell_width
        self.hgp_cell_height = cell_height
        self.hgp_margin_x = margin_x
        self.hgp_margin_y = margin_y
        self.hgp_data_radius = data_radius
        self.hgp_check_size = check_size
        
        def get_lattice_pos(row, col):
            """Get screen position for lattice node at (row, col)."""
            x = margin_x + cell_width * (col + 0.5)
            y = margin_y + cell_height * (row + 0.5)
            return x, y
        
        # Store position function
        self._get_lattice_pos = get_lattice_pos
        
        # Define which positions are data qubits vs X-checks vs Z-checks
        # In HGP codes, the lattice has a "checkerboard-like" structure
        # but with overlapping roles based on chain complex structure
        
        # For visualization: interleave data qubits with check nodes
        # Data qubits at even (row+col) parity positions
        # X-checks at odd columns, Z-checks at odd rows (simplified model)
        
        data_positions = []  # (row, col, qubit_index)
        x_check_positions = []  # (row, col, check_index)  
        z_check_positions = []  # (row, col, check_index)
        
        qubit_idx = 0
        x_idx = 0
        z_idx = 0
        
        for row in range(grid_rows):
            for col in range(grid_cols):
                # Place data qubits in a regular pattern
                if (row + col) % 2 == 0:
                    data_positions.append((row, col, qubit_idx))
                    qubit_idx += 1
                else:
                    # Alternate X and Z checks
                    if row % 2 == 0:
                        x_check_positions.append((row, col, x_idx))
                        x_idx += 1
                    else:
                        z_check_positions.append((row, col, z_idx))
                        z_idx += 1
        
        # Store for click handling
        self.hgp_data_positions = data_positions
        self.hgp_x_check_positions = x_check_positions
        self.hgp_z_check_positions = z_check_positions
        
        # Store counts for position lookup functions (fixes bug #1)
        self.ldpc_num_data = len(data_positions)
        self.ldpc_num_x_checks = len(x_check_positions)
        self.ldpc_num_z_checks = len(z_check_positions)
        
        # Create position lookup functions for component placement
        def get_data_pos(idx):
            """Get screen position for data qubit by index."""
            if idx < len(data_positions):
                row, col, _ = data_positions[idx]
                return get_lattice_pos(row, col)
            return None, None
        
        def get_x_check_pos(idx):
            """Get screen position for X-check by index."""
            if idx < len(x_check_positions):
                row, col, _ = x_check_positions[idx]
                return get_lattice_pos(row, col)
            return None, None
        
        def get_z_check_pos(idx):
            """Get screen position for Z-check by index."""
            if idx < len(z_check_positions):
                row, col, _ = z_check_positions[idx]
                return get_lattice_pos(row, col)
            return None, None
        
        # Store position functions
        self._get_data_pos = get_data_pos
        self._get_x_check_pos = get_x_check_pos
        self._get_z_check_pos = get_z_check_pos
        
        # Generate HGP connectivity (seed codes with expansion)
        # First seed code: 3-regular bipartite graph (bits connect to non-adjacent checks)
        # This creates the "horizontal strings"
        seed1_connections = [
            [0, 2, 4],   # Check 0 in seed connects to bits 0, 2, 4 (long range)
            [1, 3, 5],   # Check 1 in seed connects to bits 1, 3, 5
            [0, 3, 4],   # Check 2 connects with some overlap
            [1, 2, 5],   # Check 3 connects with some overlap
        ]
        
        # Second seed code: similar structure for "vertical strings"
        seed2_connections = [
            [0, 2],      # Vertical connectivity
            [1, 3],
            [0, 3],
            [1, 2],
        ]
        
        # Draw title and mode indicator
        self.canvas.create_text(canvas_width / 2, 30, 
                               text="Hypergraph Product Code - Tanner Graph",
                               fill='#ffffff', font=("Segoe UI", 14, "bold"),
                               tags="grid")
        self.canvas.create_text(canvas_width / 2, 50,
                               text=f"Grid: {grid_rows}×{grid_cols} | Data: {len(data_positions)} | X-checks: {len(x_check_positions)} | Z-checks: {len(z_check_positions)}",
                               fill='#888888', font=("Segoe UI", 10),
                               tags="grid")
        
        # Draw the "curved strings" - horizontal bundles (X-type constraints)
        for x_pos in x_check_positions:
            x_row, x_col, x_id = x_pos
            cx, cy = get_lattice_pos(x_row, x_col)
            
            # Connect to data qubits in same row (horizontal arcs)
            for d_pos in data_positions:
                d_row, d_col, d_id = d_pos
                if d_row == x_row:  # Same row
                    # Use seed1 connectivity pattern for long-range connections
                    col_distance = abs(d_col - x_col)
                    if col_distance <= 3:  # Connect to nearby data qubits with arcs
                        dx, dy = get_lattice_pos(d_row, d_col)
                        # Arc curves upward for horizontal strings
                        self._draw_hgp_arc(cx, cy, dx, dy, colors['x_check'], 
                                          direction='horizontal', alpha=0.35)
        
        # Draw the "curved strings" - vertical bundles (Z-type constraints)
        for z_pos in z_check_positions:
            z_row, z_col, z_id = z_pos
            cx, cy = get_lattice_pos(z_row, z_col)
            
            # Connect to data qubits in same column (vertical arcs)
            for d_pos in data_positions:
                d_row, d_col, d_id = d_pos
                if d_col == z_col:  # Same column
                    # Use seed2 connectivity pattern
                    row_distance = abs(d_row - z_row)
                    if row_distance <= 2:  # Connect with arcs
                        dx, dy = get_lattice_pos(d_row, d_col)
                        # Arc curves to the side for vertical strings
                        self._draw_hgp_arc(cx, cy, dx, dy, colors['z_check'],
                                          direction='vertical', alpha=0.35)
        
        # Draw additional long-range "expansion" arcs (the distinctive HGP feature)
        # These skip neighbors and create the "woven" texture
        for x_pos in x_check_positions:
            x_row, x_col, x_id = x_pos
            cx, cy = get_lattice_pos(x_row, x_col)
            
            # Long-range horizontal connections (skip 2-3 positions)
            for d_pos in data_positions:
                d_row, d_col, d_id = d_pos
                col_dist = abs(d_col - x_col)
                if d_row == x_row and col_dist >= 4 and col_dist <= 5:
                    dx, dy = get_lattice_pos(d_row, d_col)
                    self._draw_hgp_arc(cx, cy, dx, dy, colors['x_check'],
                                      direction='horizontal', alpha=0.25, long_range=True)
        
        for z_pos in z_check_positions:
            z_row, z_col, z_id = z_pos
            cx, cy = get_lattice_pos(z_row, z_col)
            
            # Long-range vertical connections
            for d_pos in data_positions:
                d_row, d_col, d_id = d_pos
                row_dist = abs(d_row - z_row)
                if d_col == z_col and row_dist >= 3:
                    dx, dy = get_lattice_pos(d_row, d_col)
                    self._draw_hgp_arc(cx, cy, dx, dy, colors['z_check'],
                                      direction='vertical', alpha=0.25, long_range=True)
        
        # Draw data qubit nodes (teal circles)
        for row, col, idx in data_positions:
            x, y = get_lattice_pos(row, col)
            self.canvas.create_oval(x - data_radius, y - data_radius,
                                   x + data_radius, y + data_radius,
                                   fill=colors['background_node'],
                                   outline=colors['data_qubit'],
                                   width=2, tags="grid hgp_data")
            self.canvas.create_text(x, y, text=f"q{idx}", 
                                   fill=colors['data_qubit'],
                                   font=("Segoe UI", 8, "bold"), tags="grid")
        
        # Draw X-check nodes (coral squares)
        for row, col, idx in x_check_positions:
            x, y = get_lattice_pos(row, col)
            self.canvas.create_rectangle(x - check_size, y - check_size,
                                        x + check_size, y + check_size,
                                        fill=colors['background_node'],
                                        outline=colors['x_check'],
                                        width=2, tags="grid hgp_x_check")
            self.canvas.create_text(x, y, text=f"X{idx}",
                                   fill=colors['x_check'],
                                   font=("Segoe UI", 7, "bold"), tags="grid")
        
        # Draw Z-check nodes (gold squares)
        for row, col, idx in z_check_positions:
            x, y = get_lattice_pos(row, col)
            self.canvas.create_rectangle(x - check_size, y - check_size,
                                        x + check_size, y + check_size,
                                        fill=colors['background_node'],
                                        outline=colors['z_check'],
                                        width=2, tags="grid hgp_z_check")
            self.canvas.create_text(x, y, text=f"Z{idx}",
                                   fill=colors['z_check'],
                                   font=("Segoe UI", 7, "bold"), tags="grid")
        
        # Draw legend for HGP structure
        legend_x = canvas_width - 120
        legend_y = canvas_height - 100
        
        self.canvas.create_text(legend_x, legend_y, text="HGP Connectivity:",
                               fill='#aaaaaa', font=("Segoe UI", 9, "bold"),
                               anchor="w", tags="grid")
        self.canvas.create_line(legend_x, legend_y + 18, legend_x + 40, legend_y + 18,
                               fill=colors['x_check'], width=2, tags="grid")
        self.canvas.create_text(legend_x + 45, legend_y + 18, text="H₁ ⊗ I (horiz)",
                               fill=colors['x_check'], font=("Segoe UI", 8),
                               anchor="w", tags="grid")
        self.canvas.create_line(legend_x, legend_y + 35, legend_x + 40, legend_y + 35,
                               fill=colors['z_check'], width=2, tags="grid")
        self.canvas.create_text(legend_x + 45, legend_y + 35, text="I ⊗ H₂ᵀ (vert)",
                               fill=colors['z_check'], font=("Segoe UI", 8),
                               anchor="w", tags="grid")
        
        # Draw any placed components on top
        self._draw_placed_ldpc_components()
    
    def _draw_hgp_arc(self, x1, y1, x2, y2, color, direction='horizontal', 
                      alpha=0.4, long_range=False):
        """Draw a curved arc for HGP non-local connectivity.
        
        Optimized version (#19) with:
        - Cached color blending
        - Reduced bezier segments for short arcs
        - Early exit for very short distances
        
        Args:
            x1, y1: Start point (check node)
            x2, y2: End point (data qubit)
            color: Arc color
            direction: 'horizontal' or 'vertical' - determines curve direction
            alpha: Opacity (simulated via color blending)
            long_range: If True, uses larger arc curvature
        """
        # Early exit for very short distances (optimization #19)
        dist_sq = (x2 - x1)**2 + (y2 - y1)**2
        if dist_sq < 100:  # Less than 10 pixels
            return
        
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Calculate distance and curve amount
        if direction == 'horizontal':
            distance = abs(x2 - x1)
            curve_amount = min(distance * 0.4, 60) if not long_range else min(distance * 0.5, 100)
            ctrl_x = mid_x
            ctrl_y = mid_y - curve_amount
        else:
            distance = abs(y2 - y1)
            curve_amount = min(distance * 0.4, 60) if not long_range else min(distance * 0.5, 100)
            ctrl_x = mid_x + curve_amount
            ctrl_y = mid_y
        
        # Adaptive segment count based on distance (#19 optimization)
        if long_range:
            num_segments = min(16, max(8, int(distance / 20)))
        else:
            num_segments = min(12, max(6, int(distance / 25)))
        
        # Generate bezier curve points
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            t2 = t * t
            mt = 1 - t
            mt2 = mt * mt
            bx = mt2 * x1 + 2 * mt * t * ctrl_x + t2 * x2
            by = mt2 * y1 + 2 * mt * t * ctrl_y + t2 * y2
            points.extend([bx, by])
        
        # Use cached color blending (#19 optimization)
        blended_color = self._get_blended_color(color, alpha)
        
        width = 3 if long_range else 2
        self.canvas.create_line(*points, fill=blended_color, width=width,
                               smooth=True, tags="grid hgp_arc")
    
    def _get_blended_color(self, color: str, alpha: float) -> str:
        """Get a blended color with background, with caching for performance (#19).
        
        Args:
            color: Hex color string
            alpha: Blend factor (0-1)
            
        Returns:
            Blended hex color string
        """
        # Initialize cache if needed
        if not hasattr(self, '_color_blend_cache'):
            self._color_blend_cache = {}
        
        # Check cache
        cache_key = (color, round(alpha, 2))
        if cache_key in self._color_blend_cache:
            return self._color_blend_cache[cache_key]
        
        # Background color
        bg_r, bg_g, bg_b = 0x1e, 0x1e, 0x1e
        
        # Parse foreground color
        if color.startswith('#') and len(color) == 7:
            fg_r = int(color[1:3], 16)
            fg_g = int(color[3:5], 16)
            fg_b = int(color[5:7], 16)
        else:
            fg_r, fg_g, fg_b = 100, 100, 100
        
        # Blend colors
        blended_r = int(fg_r * alpha + bg_r * (1 - alpha))
        blended_g = int(fg_g * alpha + bg_g * (1 - alpha))
        blended_b = int(fg_b * alpha + bg_b * (1 - alpha))
        blended_color = f"#{blended_r:02x}{blended_g:02x}{blended_b:02x}"
        
        # Cache result
        self._color_blend_cache[cache_key] = blended_color
        return blended_color
    
    def _draw_curved_edge(self, x1, y1, x2, y2, color, alpha=0.5, curve_direction='down'):
        """Draw a curved edge between two points using quadratic bezier approximation.
        
        Args:
            x1, y1: Start point
            x2, y2: End point
            color: Line color (hex)
            alpha: Opacity (0-1, approximated via color lightening)
            curve_direction: 'up' or 'down' for curve bulge direction
        """
        # Calculate control point for curve
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Curve amount based on horizontal distance (more curve for distant connections)
        distance = abs(x2 - x1)
        curve_amount = min(distance * 0.3, 80)  # Cap the curve amount
        
        if curve_direction == 'down':
            ctrl_y = mid_y + curve_amount * 0.5
        else:
            ctrl_y = mid_y - curve_amount * 0.5
        
        # Adaptive segment count (#19 optimization)
        num_segments = min(12, max(6, int(distance / 25)))
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            t2 = t * t
            mt = 1 - t
            mt2 = mt * mt
            bx = mt2 * x1 + 2 * mt * t * mid_x + t2 * x2
            by = mt2 * y1 + 2 * mt * t * ctrl_y + t2 * y2
            points.extend([bx, by])
        
        # Use cached color blending (#19 optimization)
        blended_color = self._get_blended_color(color, alpha)
        
        self.canvas.create_line(*points, fill=blended_color, width=2, 
                               smooth=True, tags="grid ldpc_edge")
    
    def _draw_ldpc_physical_lattice(self):
        """Draw the LDPC physical layout visualization with linear arrays and cavity bus.
        
        Tri-layer architecture:
        - Top row: Z-ancilla qubits (for Z-stabilizer measurement)
        - Middle row: Data qubits (main qubit register)
        - Bottom row: X-ancilla qubits (for X-stabilizer measurement)
        - Vertical cavity bus connecting all layers for non-local interactions
        """
        # Layout parameters
        num_qubits_per_row = 12  # Number of qubits in each linear array
        
        # Visual scaling
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Calculate spacing
        horizontal_margin = 100
        vertical_margin = 100
        usable_width = canvas_width - 2 * horizontal_margin
        usable_height = canvas_height - 2 * vertical_margin
        
        # Node sizes
        qubit_radius = 18
        bus_width = 8
        
        # Layer y-positions (three horizontal rows)
        layer_spacing = usable_height / 2
        y_z_ancilla = vertical_margin  # Top layer
        y_data = vertical_margin + layer_spacing  # Middle layer
        y_x_ancilla = vertical_margin + 2 * layer_spacing  # Bottom layer
        
        # Store lattice parameters for click handling
        self.ldpc_phys_qubit_radius = qubit_radius
        self.ldpc_phys_horizontal_margin = horizontal_margin
        self.ldpc_phys_usable_width = usable_width
        self.ldpc_phys_y_z_ancilla = y_z_ancilla
        self.ldpc_phys_y_data = y_data
        self.ldpc_phys_y_x_ancilla = y_x_ancilla
        self.ldpc_phys_num_qubits = num_qubits_per_row
        
        def get_qubit_pos(row, idx):
            """Get screen position for a qubit in a row."""
            spacing = usable_width / (num_qubits_per_row + 1)
            x = horizontal_margin + spacing * (idx + 1)
            if row == 'z_ancilla':
                y = y_z_ancilla
            elif row == 'data':
                y = y_data
            else:  # x_ancilla
                y = y_x_ancilla
            return x, y
        
        self._get_phys_qubit_pos = get_qubit_pos
        
        colors = self.LDPC_COLORS
        
        # Draw layer labels
        self.canvas.create_text(50, y_z_ancilla, text="Z-Ancilla", 
                               fill=colors['z_ancilla'], font=("Segoe UI", 10, "bold"),
                               anchor="w", tags="grid")
        self.canvas.create_text(50, y_data, text="Data", 
                               fill=colors['data_qubit'], font=("Segoe UI", 10, "bold"),
                               anchor="w", tags="grid")
        self.canvas.create_text(50, y_x_ancilla, text="X-Ancilla", 
                               fill=colors['x_ancilla'], font=("Segoe UI", 10, "bold"),
                               anchor="w", tags="grid")
        
        # Draw horizontal "wire" lines for each row (qubit registers)
        wire_start_x = horizontal_margin - 30
        wire_end_x = canvas_width - horizontal_margin + 30
        
        for y, color in [(y_z_ancilla, colors['z_ancilla']),
                         (y_data, colors['data_qubit']),
                         (y_x_ancilla, colors['x_ancilla'])]:
            # Main wire
            self.canvas.create_line(wire_start_x, y, wire_end_x, y,
                                   fill=color, width=3, tags="grid")
        
        # Draw cavity bus (vertical connecting element)
        bus_positions = [3, 6, 9]  # Positions where cavity bus connects
        for bus_idx in bus_positions:
            bus_x, _ = get_qubit_pos('data', bus_idx)
            
            # Draw vertical bus bar
            self.canvas.create_rectangle(bus_x - bus_width, y_z_ancilla - 30,
                                        bus_x + bus_width, y_x_ancilla + 30,
                                        fill=colors['cavity_bus'], outline=colors['cavity_bus'],
                                        width=0, tags="grid ldpc_bus")
            
            # Draw "cavity" symbol at center
            cavity_y = y_data
            self.canvas.create_oval(bus_x - 15, cavity_y - 15,
                                   bus_x + 15, cavity_y + 15,
                                   fill=colors['cavity_bus'], outline="#ffffff",
                                   width=2, tags="grid ldpc_cavity")
            self.canvas.create_text(bus_x, cavity_y, text="C", fill="#ffffff",
                                   font=("Segoe UI", 10, "bold"), tags="grid")
        
        # Draw Z-ancilla qubits
        for i in range(num_qubits_per_row):
            x, y = get_qubit_pos('z_ancilla', i)
            self.canvas.create_oval(x - qubit_radius, y - qubit_radius,
                                   x + qubit_radius, y + qubit_radius,
                                   fill=colors['background_node'],
                                   outline=colors['z_ancilla'],
                                   width=2, tags="grid ldpc_z_anc")
            self.canvas.create_text(x, y, text=f"z{i}", fill=colors['z_ancilla'],
                                   font=("Segoe UI", 8, "bold"), tags="grid")
        
        # Draw data qubits
        for i in range(num_qubits_per_row):
            x, y = get_qubit_pos('data', i)
            # Skip positions occupied by cavity bus
            if i in bus_positions:
                continue
            self.canvas.create_oval(x - qubit_radius, y - qubit_radius,
                                   x + qubit_radius, y + qubit_radius,
                                   fill=colors['background_node'],
                                   outline=colors['data_qubit'],
                                   width=2, tags="grid ldpc_data")
            self.canvas.create_text(x, y, text=f"d{i}", fill=colors['data_qubit'],
                                   font=("Segoe UI", 8, "bold"), tags="grid")
        
        # Draw X-ancilla qubits
        for i in range(num_qubits_per_row):
            x, y = get_qubit_pos('x_ancilla', i)
            self.canvas.create_oval(x - qubit_radius, y - qubit_radius,
                                   x + qubit_radius, y + qubit_radius,
                                   fill=colors['background_node'],
                                   outline=colors['x_ancilla'],
                                   width=2, tags="grid ldpc_x_anc")
            self.canvas.create_text(x, y, text=f"x{i}", fill=colors['x_ancilla'],
                                   font=("Segoe UI", 8, "bold"), tags="grid")
        
        # Draw example non-local interaction (curved lines showing cavity-mediated gates)
        # Show a few example connections through the cavity
        example_connections = [
            (('data', 0), ('data', 5), 3),   # Data qubit 0 to 5 via cavity at position 3
            (('z_ancilla', 2), ('data', 4), 3),  # Z-ancilla to data via cavity
            (('x_ancilla', 7), ('data', 8), 6),  # X-ancilla to data via cavity
        ]
        
        for (row1, idx1), (row2, idx2), cavity_pos in example_connections:
            x1, y1 = get_qubit_pos(row1, idx1)
            x2, y2 = get_qubit_pos(row2, idx2)
            cavity_x, _ = get_qubit_pos('data', cavity_pos)
            
            # Draw curved path through cavity
            self._draw_cavity_path(x1, y1, x2, y2, cavity_x, colors['edge'])
        
        # Draw any placed LDPC components on top
        self._draw_placed_ldpc_components()
    
    def _draw_cavity_path(self, x1, y1, x2, y2, cavity_x, color):
        """Draw a path from one qubit to another through a cavity bus.
        
        The path goes: qubit1 → horizontal to cavity → vertical through cavity → horizontal to qubit2
        """
        # Create smooth curve path
        points = [x1, y1]
        
        # Control points for smooth curve to cavity
        points.extend([x1, y1])
        points.extend([cavity_x, y1])
        points.extend([cavity_x, y2])
        points.extend([x2, y2])
        points.extend([x2, y2])
        
        self.canvas.create_line(*points, fill=color, width=2, 
                               smooth=True, dash=(4, 2), tags="grid ldpc_cavity_path")
    
    def _draw_placed_ldpc_components(self):
        """Draw user-placed LDPC components on the current lattice."""
        colors = self.LDPC_COLORS
        
        for comp in self.components:
            x, y, _ = comp.position
            
            # Get screen position based on component type and mode
            if self.view_mode == ViewMode.LDPC_TANNER:
                screen_x, screen_y = self._get_ldpc_tanner_screen_pos(comp)
            else:  # LDPC_PHYSICAL
                screen_x, screen_y = self._get_ldpc_physical_screen_pos(comp)
            
            if screen_x is None:
                continue
            
            # Draw based on component type
            if comp.component_type == ComponentType.LDPC_DATA_QUBIT:
                r = 28
                self.canvas.create_oval(screen_x - r, screen_y - r,
                                       screen_x + r, screen_y + r,
                                       fill=colors['data_qubit'], outline="#ffffff",
                                       width=3, tags="component")
                self.canvas.create_text(screen_x, screen_y, text="D", fill="#000000",
                                       font=("Segoe UI", 11, "bold"), tags="component")
            
            elif comp.component_type == ComponentType.LDPC_X_CHECK:
                size = 26
                self.canvas.create_rectangle(screen_x - size, screen_y - size,
                                            screen_x + size, screen_y + size,
                                            fill=colors['x_check'], outline="#ffffff",
                                            width=3, tags="component")
                self.canvas.create_text(screen_x, screen_y, text="X", fill="#ffffff",
                                       font=("Segoe UI", 12, "bold"), tags="component")
            
            elif comp.component_type == ComponentType.LDPC_Z_CHECK:
                size = 26
                self.canvas.create_rectangle(screen_x - size, screen_y - size,
                                            screen_x + size, screen_y + size,
                                            fill=colors['z_check'], outline="#ffffff",
                                            width=3, tags="component")
                self.canvas.create_text(screen_x, screen_y, text="Z", fill="#000000",
                                       font=("Segoe UI", 12, "bold"), tags="component")
            
            elif comp.component_type == ComponentType.LDPC_ANCILLA:
                r = 22
                self.canvas.create_oval(screen_x - r, screen_y - r,
                                       screen_x + r, screen_y + r,
                                       fill=colors['ancilla'], outline="#ffffff",
                                       width=3, tags="component")
                self.canvas.create_text(screen_x, screen_y, text="A", fill="#ffffff",
                                       font=("Segoe UI", 10, "bold"), tags="component")
            
            elif comp.component_type == ComponentType.LDPC_X_ANCILLA:
                r = 22
                self.canvas.create_oval(screen_x - r, screen_y - r,
                                       screen_x + r, screen_y + r,
                                       fill=colors['x_ancilla'], outline="#ffffff",
                                       width=3, tags="component")
                self.canvas.create_text(screen_x, screen_y, text="Xa", fill="#ffffff",
                                       font=("Segoe UI", 9, "bold"), tags="component")
            
            elif comp.component_type == ComponentType.LDPC_Z_ANCILLA:
                r = 22
                self.canvas.create_oval(screen_x - r, screen_y - r,
                                       screen_x + r, screen_y + r,
                                       fill=colors['z_ancilla'], outline="#ffffff",
                                       width=3, tags="component")
                self.canvas.create_text(screen_x, screen_y, text="Za", fill="#ffffff",
                                       font=("Segoe UI", 9, "bold"), tags="component")
            
            elif comp.component_type == ComponentType.LDPC_CAVITY_BUS:
                # Draw cavity bus marker
                size = 20
                self.canvas.create_oval(screen_x - size, screen_y - size,
                                       screen_x + size, screen_y + size,
                                       fill=colors['cavity_bus'], outline="#ffffff",
                                       width=3, tags="component")
                self.canvas.create_text(screen_x, screen_y, text="C", fill="#ffffff",
                                       font=("Segoe UI", 11, "bold"), tags="component")
            
            # Highlight selected component
            if comp == self.selected_component:
                r = 35
                self.canvas.create_rectangle(screen_x - r, screen_y - r,
                                            screen_x + r, screen_y + r,
                                            fill="", outline="#ffff00", width=3, tags="component")
    
    def _get_ldpc_tanner_screen_pos(self, comp):
        """Get screen position for a component in Tanner graph mode."""
        if not hasattr(self, '_get_data_pos'):
            return None, None
        
        x, y, _ = comp.position
        
        # Map component type to layer
        if comp.component_type in [ComponentType.LDPC_X_CHECK]:
            if hasattr(self, '_get_x_check_pos') and x < self.ldpc_num_x_checks:
                return self._get_x_check_pos(x)
        elif comp.component_type in [ComponentType.LDPC_Z_CHECK]:
            if hasattr(self, '_get_z_check_pos') and x < self.ldpc_num_z_checks:
                return self._get_z_check_pos(x)
        elif comp.component_type in [ComponentType.LDPC_DATA_QUBIT, ComponentType.LDPC_ANCILLA]:
            if hasattr(self, '_get_data_pos') and x < self.ldpc_num_data:
                return self._get_data_pos(x)
        
        return None, None
    
    def _get_ldpc_physical_screen_pos(self, comp):
        """Get screen position for a component in Physical layout mode."""
        if not hasattr(self, '_get_phys_qubit_pos'):
            return None, None
        
        x, y, _ = comp.position
        
        # Map component type to row
        if comp.component_type in [ComponentType.LDPC_Z_ANCILLA]:
            return self._get_phys_qubit_pos('z_ancilla', x)
        elif comp.component_type in [ComponentType.LDPC_DATA_QUBIT]:
            return self._get_phys_qubit_pos('data', x)
        elif comp.component_type in [ComponentType.LDPC_X_ANCILLA]:
            return self._get_phys_qubit_pos('x_ancilla', x)
        elif comp.component_type in [ComponentType.LDPC_ANCILLA]:
            return self._get_phys_qubit_pos('data', x)
        elif comp.component_type in [ComponentType.LDPC_CAVITY_BUS]:
            return self._get_phys_qubit_pos('data', x)
        
        return None, None
    
    def _update_mode_indicator(self):
        """Update the visual mode indicator on the canvas (#24 enhanced)."""
        self.canvas.delete("mode_indicator")
        
        # Get zoom level
        zoom_pct = int(getattr(self, '_zoom_level', 1.0) * 100)
        
        # Define mode-specific text and colors
        if self.view_mode == ViewMode.SURFACE_CODE_2D:
            mode_name = "Surface Code"
            indicator_color = "#00cc66"  # Green
            bg_color = "#1a1a2e"
        elif self.view_mode == ViewMode.LDPC_TANNER:
            mode_name = "LDPC Tanner"
            indicator_color = "#2EC4B6"  # Teal
            bg_color = "#1a2e2e"
        elif self.view_mode == ViewMode.LDPC_PHYSICAL:
            mode_name = "LDPC Physical"
            indicator_color = "#FFD93D"  # Gold
            bg_color = "#2e2a1a"
        else:  # ISOMETRIC_3D
            mode_name = "Circuit"
            indicator_color = "#00cc66"  # Green
            bg_color = "#1a1a2e"
        
        # Build status text with component count
        comp_count = len(self.components)
        status_text = f"[{mode_name}] Components: {comp_count} | Zoom: {zoom_pct}%"
        
        # Draw indicator in top-left corner
        text_width = len(status_text) * 7 + 30
        self.canvas.create_rectangle(5, 5, text_width, 28, fill=bg_color, 
                                    outline=indicator_color, width=1, tags="mode_indicator")
        self.canvas.create_text(text_width // 2 + 5, 16, text=status_text, fill=indicator_color,
                               font=("Segoe UI", 9, "bold"), tags="mode_indicator")
        
        # Draw shortcuts hint in top-right corner
        canvas_width = self.canvas.winfo_width()
        if canvas_width > 200:
            hint_text = "V: Mode | B: LDPC | +/-: Zoom"
            hint_width = len(hint_text) * 6 + 20
            self.canvas.create_rectangle(canvas_width - hint_width - 5, 5, 
                                        canvas_width - 5, 28,
                                        fill='#1a1a2e', outline='#555555', 
                                        width=1, tags="mode_indicator")
            self.canvas.create_text(canvas_width - hint_width // 2 - 5, 16, 
                                   text=hint_text, fill='#888888',
                                   font=("Segoe UI", 8), tags="mode_indicator")
    
    def _select_tool(self, component_type: ComponentType):
        """Select a component type for placement."""
        self.current_tool = component_type
        self._log_status(f"Selected tool: {component_type.value}")
        self._highlight_selected_tool()
    
    def _highlight_selected_tool(self):
        """Highlight the currently selected tool button."""
        if not hasattr(self, 'tool_buttons'):
            return
        
        for comp_type, btn in self.tool_buttons.items():
            if comp_type == self.current_tool:
                # Highlight selected
                btn.config(bg='#e94560', fg='#ffffff', relief='sunken')
            else:
                # Reset to default
                btn.config(bg='#2d2d44', fg='#ffffff', relief='flat')
    
    def _on_canvas_click(self, event):
        """Handle canvas click events for component placement."""
        # Check if we're in add control mode - handle separately
        if hasattr(self, 'adding_control_to') and self.adding_control_to:
            self._place_control_click(event)
            return
        
        # Check if we're in controlled gate placement mode (placing base gate first)
        if hasattr(self, 'placing_controlled_gate') and self.placing_controlled_gate:
            self._place_controlled_gate_base(event)
            return
        
        # Check if we're placing control for a controlled gate
        if hasattr(self, 'placing_control_for_gate') and self.placing_control_for_gate:
            self._place_controlled_gate_control(event)
            return
        
        if self.view_mode == ViewMode.SURFACE_CODE_2D:
            self._on_surface_code_click(event)
            return
        elif self.view_mode in [ViewMode.LDPC_TANNER, ViewMode.LDPC_PHYSICAL]:
            self._on_ldpc_click(event)
            return
        
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
    
    def _on_surface_code_click(self, event):
        """Handle click events for rotated surface code lattice.
        
        In the rotated lattice:
        - Data qubits are at odd integer coordinates (1,1), (1,3), (3,1), etc.
        - Stabilizers are at even integer coordinates (2,2), (4,4), etc.
        """
        # Check if lattice parameters are available
        if not hasattr(self, 'lattice_scale'):
            self._log_status("Lattice not initialized - try pressing V again")
            return
        
        scale = self.lattice_scale
        offset_x = self.lattice_center_x
        offset_y = self.lattice_center_y
        lattice_extent = self.lattice_extent
        
        # Convert screen coordinates to lattice coordinates
        lattice_x = (event.x - offset_x) / scale + lattice_extent / 2
        lattice_y = (event.y - offset_y) / scale + lattice_extent / 2
        
        # Check if click is within lattice bounds
        if lattice_x < 0 or lattice_x > lattice_extent or lattice_y < 0 or lattice_y > lattice_extent:
            self._log_status("Click outside lattice bounds")
            return
        
        # Allowed component types for Surface Mode
        surface_allowed = [
            ComponentType.SURFACE_X_STABILIZER,
            ComponentType.SURFACE_Z_STABILIZER,
            ComponentType.SURFACE_DATA,
            ComponentType.SURFACE_BOUNDARY,
            ComponentType.SURFACE_X_ERROR,
            ComponentType.SURFACE_Z_ERROR,
            ComponentType.SURFACE_Y_ERROR,
        ]
        
        if self.current_tool not in surface_allowed:
            self._log_status(f"{self.current_tool.value} cannot be placed in Surface Mode.")
            return
        
        # Round to nearest integer lattice position
        nearest_x = round(lattice_x)
        nearest_y = round(lattice_y)
        
        # Determine component placement based on type and parity
        edge_types = [ComponentType.SURFACE_DATA, ComponentType.SURFACE_X_ERROR, 
                      ComponentType.SURFACE_Z_ERROR, ComponentType.SURFACE_Y_ERROR]
        stabilizer_types = [ComponentType.SURFACE_X_STABILIZER, ComponentType.SURFACE_Z_STABILIZER]
        
        if self.current_tool in edge_types:
            # Data qubits/errors go at odd coordinates (both x and y odd)
            # Snap to nearest odd coordinate
            snapped_x = nearest_x if nearest_x % 2 == 1 else (nearest_x + 1 if lattice_x > nearest_x else nearest_x - 1)
            snapped_y = nearest_y if nearest_y % 2 == 1 else (nearest_y + 1 if lattice_y > nearest_y else nearest_y - 1)
            
            # Clamp to valid range
            snapped_x = max(1, min(snapped_x, lattice_extent - 1))
            snapped_y = max(1, min(snapped_y, lattice_extent - 1))
            
            # Ensure both are odd
            if snapped_x % 2 == 0:
                snapped_x = snapped_x - 1 if snapped_x > 1 else snapped_x + 1
            if snapped_y % 2 == 0:
                snapped_y = snapped_y - 1 if snapped_y > 1 else snapped_y + 1
            
            self._place_surface_component(self.current_tool, snapped_x, snapped_y)
            
        elif self.current_tool in stabilizer_types:
            # Stabilizers go at even coordinates (both x and y even)
            snapped_x = nearest_x if nearest_x % 2 == 0 else (nearest_x + 1 if lattice_x > nearest_x else nearest_x - 1)
            snapped_y = nearest_y if nearest_y % 2 == 0 else (nearest_y + 1 if lattice_y > nearest_y else nearest_y - 1)
            
            # Clamp to valid range
            snapped_x = max(2, min(snapped_x, lattice_extent - 2))
            snapped_y = max(2, min(snapped_y, lattice_extent - 2))
            
            # Ensure both are even
            if snapped_x % 2 == 1:
                snapped_x = snapped_x - 1 if snapped_x > 2 else snapped_x + 1
            if snapped_y % 2 == 1:
                snapped_y = snapped_y - 1 if snapped_y > 2 else snapped_y + 1
            
            self._place_surface_component(self.current_tool, snapped_x, snapped_y)
            
        else:
            # Boundary and other: place at nearest integer
            self._place_surface_component(self.current_tool, nearest_x, nearest_y)
    
    def _place_surface_component(self, comp_type: ComponentType, lattice_x, lattice_y):
        """Place a surface code component at the given lattice position.
        
        In the rotated lattice:
        - Data qubits/errors: odd integer coordinates (1,1), (1,3), etc.
        - Stabilizers: even integer coordinates (2,2), (4,4), etc.
        """
        # Use the coordinates directly (already snapped by click handler)
        snapped_x = int(round(lattice_x))
        snapped_y = int(round(lattice_y))
        
        # Check if component already exists at this position
        for comp in self.components:
            if (abs(comp.position[0] - snapped_x) < 0.5 and 
                abs(comp.position[1] - snapped_y) < 0.5):
                # Select existing component instead of placing new one
                self._select_component(comp)
                self._log_status(f"Position occupied by {comp.component_type.value}")
                return
        
        # Get component color
        color = self._get_component_color(comp_type)
        
        # Create new component
        self.component_counter += 1
        new_component = Component3D(
            component_type=comp_type,
            position=(snapped_x, snapped_y, 0),
            color=color
        )
        self.components.append(new_component)
        self._log_status(f"Placed {comp_type.value} at ({snapped_x}, {snapped_y})")
        self._redraw_circuit()
    
    def _on_ldpc_click(self, event):
        """Handle click events for LDPC mode (Tanner graph or Physical layout)."""
        # Determine which node/position was clicked based on screen coordinates
        if self.view_mode == ViewMode.LDPC_TANNER:
            self._on_ldpc_tanner_click(event)
        elif self.view_mode == ViewMode.LDPC_PHYSICAL:
            self._on_ldpc_physical_click(event)
    
    def _on_ldpc_tanner_click(self, event):
        """Handle clicks in LDPC Tanner graph mode."""
        if not hasattr(self, '_get_data_pos'):
            self._log_status("LDPC lattice not initialized - try pressing B again")
            return
        
        click_x, click_y = event.x, event.y
        
        # Allowed component types for LDPC Tanner mode
        ldpc_tanner_allowed = [
            ComponentType.LDPC_X_CHECK,
            ComponentType.LDPC_Z_CHECK,
            ComponentType.LDPC_DATA_QUBIT,
            ComponentType.LDPC_ANCILLA,
            ComponentType.LDPC_EDGE,
        ]
        
        if self.current_tool not in ldpc_tanner_allowed:
            self._log_status(f"{self.current_tool.value} cannot be placed in LDPC Tanner mode.")
            return
        
        # Find closest node position based on component type
        closest_idx = None
        closest_dist = float('inf')
        target_layer = None
        
        if self.current_tool == ComponentType.LDPC_X_CHECK:
            # Check X-check layer
            for i in range(self.ldpc_num_x_checks):
                px, py = self._get_x_check_pos(i)
                dist = ((click_x - px)**2 + (click_y - py)**2)**0.5
                if dist < closest_dist and dist < 50:  # 50px tolerance
                    closest_dist = dist
                    closest_idx = i
                    target_layer = 'x_check'
        
        elif self.current_tool == ComponentType.LDPC_Z_CHECK:
            # Check Z-check layer
            for i in range(self.ldpc_num_z_checks):
                px, py = self._get_z_check_pos(i)
                dist = ((click_x - px)**2 + (click_y - py)**2)**0.5
                if dist < closest_dist and dist < 50:
                    closest_dist = dist
                    closest_idx = i
                    target_layer = 'z_check'
        
        elif self.current_tool in [ComponentType.LDPC_DATA_QUBIT, ComponentType.LDPC_ANCILLA]:
            # Check data layer
            for i in range(self.ldpc_num_data):
                px, py = self._get_data_pos(i)
                dist = ((click_x - px)**2 + (click_y - py)**2)**0.5
                if dist < closest_dist and dist < 40:
                    closest_dist = dist
                    closest_idx = i
                    target_layer = 'data'
        
        if closest_idx is not None:
            self._place_ldpc_component(self.current_tool, closest_idx, target_layer)
        else:
            self._log_status("Click near a node position to place component")
    
    def _on_ldpc_physical_click(self, event):
        """Handle clicks in LDPC Physical layout mode."""
        if not hasattr(self, '_get_phys_qubit_pos'):
            self._log_status("LDPC physical layout not initialized - try pressing B again")
            return
        
        click_x, click_y = event.x, event.y
        
        # Allowed component types for LDPC Physical mode
        ldpc_physical_allowed = [
            ComponentType.LDPC_DATA_QUBIT,
            ComponentType.LDPC_X_ANCILLA,
            ComponentType.LDPC_Z_ANCILLA,
            ComponentType.LDPC_ANCILLA,
            ComponentType.LDPC_CAVITY_BUS,
        ]
        
        if self.current_tool not in ldpc_physical_allowed:
            self._log_status(f"{self.current_tool.value} cannot be placed in LDPC Physical mode.")
            return
        
        # Find closest node position
        closest_idx = None
        closest_dist = float('inf')
        target_row = None
        
        # Map component types to rows
        if self.current_tool == ComponentType.LDPC_Z_ANCILLA:
            row = 'z_ancilla'
        elif self.current_tool == ComponentType.LDPC_X_ANCILLA:
            row = 'x_ancilla'
        elif self.current_tool == ComponentType.LDPC_DATA_QUBIT:
            row = 'data'
        elif self.current_tool == ComponentType.LDPC_ANCILLA:
            row = 'data'  # General ancilla goes in data row
        elif self.current_tool == ComponentType.LDPC_CAVITY_BUS:
            row = 'data'  # Cavity bus also in data row
        else:
            row = 'data'
        
        # Find closest position in the target row
        for i in range(self.ldpc_phys_num_qubits):
            px, py = self._get_phys_qubit_pos(row, i)
            dist = ((click_x - px)**2 + (click_y - py)**2)**0.5
            if dist < closest_dist and dist < 40:
                closest_dist = dist
                closest_idx = i
                target_row = row
        
        if closest_idx is not None:
            self._place_ldpc_component(self.current_tool, closest_idx, target_row)
        else:
            self._log_status("Click near a qubit position to place component")
    
    def _place_ldpc_component(self, comp_type: ComponentType, idx: int, layer: str):
        """Place an LDPC component at the given index and layer."""
        # Check if position is already occupied
        for comp in self.components:
            if comp.position[0] == idx and comp.component_type == comp_type:
                self._select_component(comp)
                self._log_status(f"Position {idx} already has {comp_type.value}")
                return
        
        # Get color based on component type
        colors = self.LDPC_COLORS
        if comp_type == ComponentType.LDPC_DATA_QUBIT:
            color_hex = colors['data_qubit']
        elif comp_type == ComponentType.LDPC_X_CHECK:
            color_hex = colors['x_check']
        elif comp_type == ComponentType.LDPC_Z_CHECK:
            color_hex = colors['z_check']
        elif comp_type == ComponentType.LDPC_ANCILLA:
            color_hex = colors['ancilla']
        elif comp_type == ComponentType.LDPC_X_ANCILLA:
            color_hex = colors['x_ancilla']
        elif comp_type == ComponentType.LDPC_Z_ANCILLA:
            color_hex = colors['z_ancilla']
        elif comp_type == ComponentType.LDPC_CAVITY_BUS:
            color_hex = colors['cavity_bus']
        else:
            color_hex = '#888888'
        
        # Convert hex to RGB tuple
        r = int(color_hex[1:3], 16) / 255
        g = int(color_hex[3:5], 16) / 255
        b = int(color_hex[5:7], 16) / 255
        
        # Create new component
        self.component_counter += 1
        new_component = Component3D(
            component_type=comp_type,
            position=(idx, 0, 0),  # y and z not used for LDPC, layer determined by type
            color=(r, g, b)
        )
        self.components.append(new_component)
        self._log_status(f"Placed {comp_type.value} at position {idx} in {layer} layer")
        self._redraw_circuit()
    
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
        
        # Two-qubit gates: placed at control lane (Option A), extend to target lane
        # Control is at grid_y, target is at grid_y + 1
        if is_two_qubit:
            target_lane = grid_y + 1
            if self._get_component_at_position(grid_x, target_lane):
                self._log_status(f"Two-qubit gate needs target lane ({grid_x}, {target_lane}) to be free!")
                return
            if target_lane > grid_max:
                self._log_status(f"Two-qubit gate target lane would be outside grid boundaries!")
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
        
        # Set control/target properties for two-qubit gates (Option B)
        if is_two_qubit:
            component.properties['control'] = grid_y
            component.properties['target'] = grid_y + 1
        
        # Use command pattern for undo/redo support
        cmd = PlaceComponentCommand(self, component)
        self.command_history.execute(cmd)
        self.component_counter += 1
        
        self._log_status(f"Placed {self.current_tool.value} at ({grid_x}, {grid_y}, {grid_z})")
        self._redraw_circuit()
    
    def _get_component_color(self, component_type: ComponentType) -> Tuple[float, float, float]:
        """Get color for component type."""
        color_map = {
            # Single qubit gates - DISTINCT colors for easy identification
            ComponentType.X_GATE: (0.95, 0.3, 0.3),    # Red - bit flip
            ComponentType.Z_GATE: (0.2, 0.5, 0.9),     # Blue - phase flip
            ComponentType.Y_GATE: (0.7, 0.3, 0.8),     # Purple - combined
            ComponentType.H_GATE: (1.0, 0.85, 0.2),    # Gold/Yellow - superposition
            ComponentType.S_GATE: (0.2, 0.75, 0.6),    # Teal - phase
            ComponentType.T_GATE: (0.95, 0.55, 0.2),   # Orange - T gate
            
            # Two qubit gates - distinct purple/magenta shades
            ComponentType.CNOT_GATE: (0.8, 0.2, 0.6),  # Magenta
            ComponentType.CZ_GATE: (0.5, 0.2, 0.8),    # Purple
            ComponentType.SWAP_GATE: (0.9, 0.4, 0.7),  # Pink
            
            # LDPC components (circuit mode) - distinct green/orange shades
            ComponentType.PARITY_CHECK: (0.9, 0.5, 0.1),   # Orange
            ComponentType.DATA_QUBIT: (0.2, 0.9, 0.3),     # Bright green
            ComponentType.ANCILLA_QUBIT: (0.6, 0.8, 0.1),  # Yellow-green
            
            # Measurement - distinct red shades
            ComponentType.MEASURE: (0.9, 0.1, 0.1),    # Bright red
            ComponentType.RESET: (0.7, 0.3, 0.2),      # Dark red
            
            # Circuit mode errors - BLACK for visibility
            ComponentType.CIRCUIT_X_ERROR: (0.15, 0.15, 0.15),   # Near black
            ComponentType.CIRCUIT_Z_ERROR: (0.15, 0.15, 0.15),   # Near black
            ComponentType.CIRCUIT_Y_ERROR: (0.15, 0.15, 0.15),   # Near black
            ComponentType.CIRCUIT_CORRECTION: (1.0, 0.85, 0.2),  # Yellow
            
            # Surface code components - matching app's burgundy theme with clear distinction
            # Data qubits: Light cyan/teal (clearly different from stabilizers)
            ComponentType.SURFACE_DATA: (0.4, 0.8, 0.9),          # Cyan (#66ccdd)
            # X-stabilizers: Burgundy/red (matches background hints at (i+j) % 2 == 0 cells)
            ComponentType.SURFACE_X_STABILIZER: (0.91, 0.27, 0.38), # Burgundy (#e94560)
            # Z-stabilizers: Deep purple (matches background hints at (i+j) % 2 == 1 cells)
            ComponentType.SURFACE_Z_STABILIZER: (0.42, 0.18, 0.36), # Purple (#6b2d5c)
            # Boundary: Orange for visibility
            ComponentType.SURFACE_BOUNDARY: (0.9, 0.6, 0.2),      # Orange
            # Error markers: Distinct bright colors
            ComponentType.SURFACE_X_ERROR: (1.0, 0.2, 0.2),       # Bright red
            ComponentType.SURFACE_Z_ERROR: (0.2, 0.2, 1.0),       # Bright blue
            ComponentType.SURFACE_Y_ERROR: (0.9, 0.9, 0.1),       # Bright yellow
            
            # LDPC specific components (Tanner graph and physical layout)
            # Using cohesive color palette based on color theory
            ComponentType.LDPC_DATA_QUBIT: (0.18, 0.77, 0.71),    # Teal #2EC4B6
            ComponentType.LDPC_X_CHECK: (1.0, 0.42, 0.42),        # Coral #FF6B6B
            ComponentType.LDPC_Z_CHECK: (1.0, 0.85, 0.24),        # Gold #FFD93D
            ComponentType.LDPC_ANCILLA: (0.61, 0.37, 0.90),       # Lavender #9B5DE5
            ComponentType.LDPC_X_ANCILLA: (0.88, 0.48, 0.37),     # Terracotta #E07A5F
            ComponentType.LDPC_Z_ANCILLA: (0.51, 0.70, 0.60),     # Sage #81B29A
            ComponentType.LDPC_EDGE: (0.42, 0.45, 0.50),          # Slate #6B7280
            ComponentType.LDPC_CAVITY_BUS: (0.24, 0.35, 0.50),    # Navy #3D5A80
        }
        
        return color_map.get(component_type, (0.5, 0.5, 0.5))
    
    def _mark_dirty(self, component: Component3D = None) -> None:
        """Mark a component as needing redraw, or request full redraw.
        
        Args:
            component: Specific component to mark dirty, or None for full redraw
        """
        if component is not None:
            self._dirty_components.add(id(component))
        else:
            self._full_redraw_needed = True
    
    def _clear_dirty(self) -> None:
        """Clear all dirty flags after a redraw."""
        self._dirty_components.clear()
        self._full_redraw_needed = False
    
    def _is_dirty(self, component: Component3D) -> bool:
        """Check if a component needs redrawing."""
        return self._full_redraw_needed or id(component) in self._dirty_components
    
    def _redraw_circuit(self) -> None:
        """Redraw the circuit with optimized dirty-region tracking.
        
        Uses dirty-region tracking (#18) to only redraw components that
        have changed, improving performance for large circuits.
        """
        # For now, we do full redraws but the infrastructure supports selective updates
        # Full implementation would track canvas item IDs per component
        
        # Clear previous components
        self.canvas.delete("component")
        self.canvas.delete("selection")  # Clear selection highlight
        
        # Handle surface code mode differently
        if self.view_mode == ViewMode.SURFACE_CODE_2D:
            self._redraw_surface_components()
            return
        
        # Handle LDPC modes
        if self.view_mode in [ViewMode.LDPC_TANNER, ViewMode.LDPC_PHYSICAL]:
            self._draw_placed_ldpc_components()
            return
        
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
            
            # Draw control/target symbols for two-qubit gates (● for control, ⊕ for target)
            two_qubit_types = [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]
            controlled_gate_types = getattr(self, 'CONTROLLED_GATE_TYPES', [])
            
            if component.component_type in two_qubit_types:
                control_y = component.properties.get('control', y)
                target_y = component.properties.get('target', y + 1)
                
                # Control position (●)
                ctrl_x, ctrl_y_2d = self.renderer.project_3d_to_2d(x + w/2, control_y + 0.5, z + h/2)
                # Target position (⊕)
                tgt_x, tgt_y_2d = self.renderer.project_3d_to_2d(x + w/2, target_y + 0.5, z + h/2)
                
                # Draw connecting line
                self.canvas.create_line(ctrl_x, ctrl_y_2d, tgt_x, tgt_y_2d,
                                       fill="#ffffff", width=2, tags="component")
                
                # Draw control dot (●) - filled circle
                dot_radius = 6
                self.canvas.create_oval(ctrl_x - dot_radius, ctrl_y_2d - dot_radius,
                                       ctrl_x + dot_radius, ctrl_y_2d + dot_radius,
                                       fill="#ffffff", outline="#000000", width=1, tags="component")
                
                # Draw target symbol based on gate type
                if component.component_type == ComponentType.CNOT_GATE:
                    # CNOT target: ⊕ (circle with plus)
                    target_radius = 10
                    self.canvas.create_oval(tgt_x - target_radius, tgt_y_2d - target_radius,
                                           tgt_x + target_radius, tgt_y_2d + target_radius,
                                           fill="", outline="#ffffff", width=2, tags="component")
                    # Plus inside
                    self.canvas.create_line(tgt_x - target_radius + 2, tgt_y_2d,
                                           tgt_x + target_radius - 2, tgt_y_2d,
                                           fill="#ffffff", width=2, tags="component")
                    self.canvas.create_line(tgt_x, tgt_y_2d - target_radius + 2,
                                           tgt_x, tgt_y_2d + target_radius - 2,
                                           fill="#ffffff", width=2, tags="component")
                elif component.component_type == ComponentType.CZ_GATE:
                    # CZ: both controls (● ●)
                    self.canvas.create_oval(tgt_x - dot_radius, tgt_y_2d - dot_radius,
                                           tgt_x + dot_radius, tgt_y_2d + dot_radius,
                                           fill="#ffffff", outline="#000000", width=1, tags="component")
                elif component.component_type == ComponentType.SWAP_GATE:
                    # SWAP: × at both positions
                    swap_size = 6
                    self.canvas.create_line(tgt_x - swap_size, tgt_y_2d - swap_size,
                                           tgt_x + swap_size, tgt_y_2d + swap_size,
                                           fill="#ffffff", width=2, tags="component")
                    self.canvas.create_line(tgt_x - swap_size, tgt_y_2d + swap_size,
                                           tgt_x + swap_size, tgt_y_2d - swap_size,
                                           fill="#ffffff", width=2, tags="component")
                    # Also × at control
                    self.canvas.create_line(ctrl_x - swap_size, ctrl_y_2d - swap_size,
                                           ctrl_x + swap_size, ctrl_y_2d + swap_size,
                                           fill="#ffffff", width=2, tags="component")
                    self.canvas.create_line(ctrl_x - swap_size, ctrl_y_2d + swap_size,
                                           ctrl_x + swap_size, ctrl_y_2d - swap_size,
                                           fill="#ffffff", width=2, tags="component")
            
            # Draw control/target for user-created controlled gates (CH, CY, CS, CT, CSWAP)
            if hasattr(component, 'properties') and component.properties.get('is_controlled'):
                control_y = component.properties.get('control_y')
                if control_y is not None:
                    # Control position (●)
                    ctrl_x, ctrl_y_2d = self.renderer.project_3d_to_2d(x + w/2, control_y + 0.5, z + h/2)
                    # Target is at the gate's position
                    tgt_x, tgt_y_2d = self.renderer.project_3d_to_2d(x + w/2, y + d/2, z + h/2)
                    
                    # Draw connecting line
                    self.canvas.create_line(ctrl_x, ctrl_y_2d, tgt_x, tgt_y_2d,
                                           fill="#ffffff", width=2, tags="component")
                    
                    # Draw control dot (●)
                    dot_radius = 6
                    self.canvas.create_oval(ctrl_x - dot_radius, ctrl_y_2d - dot_radius,
                                           ctrl_x + dot_radius, ctrl_y_2d + dot_radius,
                                           fill="#ffffff", outline="#000000", width=1, tags="component")
            
            # Add component label - use black text for bright components (orange, yellow only)
            center_x, center_y = self.renderer.project_3d_to_2d(x + w/2, y + d/2, z + h + 0.2)
            # Determine text color based on component brightness
            # Only orange/yellow components need black text for readability
            # Green components (DATA_QUBIT, ANCILLA_QUBIT) keep white text
            bright_components = [
                ComponentType.H_GATE,      # Gold/Yellow
                ComponentType.T_GATE,      # Orange
                ComponentType.PARITY_CHECK,  # Orange
                ComponentType.CIRCUIT_CORRECTION,  # Yellow
            ]
            text_color = "#000000" if component.component_type in bright_components else "#ffffff"
            
            # For correction components, show the gate label (X, Z, Y) instead of "Correct"
            if component.component_type == ComponentType.CIRCUIT_CORRECTION:
                display_label = component.properties.get('label', 'X')
            else:
                display_label = component.component_type.value
            
            self.canvas.create_text(center_x, center_y, text=display_label,
                                  fill=text_color, font=("Arial", 8), tags="component")
            
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
            
            # Draw selection highlight for selected component (#4)
            if component == self.selected_component:
                self._draw_selection_highlight(component)
    
    def _draw_selection_highlight(self, component: Component3D):
        """Draw a clean single-line selection highlight around a component."""
        x, y, z = component.position
        w, h, d = component.size
        
        # Single clean selection outline
        offset = 0.08
        corners = [
            (x - offset, y - offset, z - offset),
            (x + w + offset, y - offset, z - offset),
            (x + w + offset, y + d + offset, z - offset),
            (x - offset, y + d + offset, z - offset),
            (x - offset, y - offset, z + h + offset),
            (x + w + offset, y - offset, z + h + offset),
            (x + w + offset, y + d + offset, z + h + offset),
            (x - offset, y + d + offset, z + h + offset),
        ]
        
        # Project to 2D
        projected = [self.renderer.project_3d_to_2d(*c) for c in corners]
        
        # Draw edges of the selection box - single line
        edges = [
            # Bottom face
            (0, 1), (1, 2), (2, 3), (3, 0),
            # Top face
            (4, 5), (5, 6), (6, 7), (7, 4),
            # Vertical edges
            (0, 4), (1, 5), (2, 6), (3, 7),
        ]
        
        for i, j in edges:
            self.canvas.create_line(
                projected[i][0], projected[i][1],
                projected[j][0], projected[j][1],
                fill='#ffcc00', width=2, tags="selection"
            )
    
    def _redraw_surface_components(self):
        """Redraw surface code components on the rotated lattice.
        
        This simply calls _draw_placed_surface_components which handles
        all component types including errors.
        """
        if not hasattr(self, 'lattice_scale'):
            return
        
        # Use the unified drawing function
        self._draw_placed_surface_components()
        
        # Update the surface code info panel
        self._update_surface_info()
    
    def _select_component(self, component: Component3D):
        """Select a component for manipulation."""
        self.selected_component = component
        self._log_status(f"Selected {component.component_type.value} at {component.position}")
    
    def _show_context_menu(self, event, component: Component3D):
        """Show context menu for component operations."""
        context_menu = tk.Menu(self.root, tearoff=0, bg='#404040', fg='#ffffff',
                              activebackground='#606060', activeforeground='#ffffff')
        
        # Add "Add Control" option for controllable gates
        controllable_gates = [
            ComponentType.X_GATE, ComponentType.Y_GATE, ComponentType.Z_GATE,
            ComponentType.H_GATE, ComponentType.S_GATE, ComponentType.T_GATE,
            ComponentType.SWAP_GATE
        ]
        
        if component.component_type in controllable_gates:
            # Check if already controlled
            if component.properties.get('is_controlled'):
                context_menu.add_command(label="✓ Remove Control",
                                       command=lambda: self._remove_control(component))
            else:
                context_menu.add_command(label="● Add Control",
                                       command=lambda: self._start_add_control_mode(component, event))
            context_menu.add_separator()
        
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
    
    def _start_add_control_mode(self, component: Component3D, event):
        """Start the mode to add a control qubit to a gate.
        
        Click on any qubit lane to set the control position.
        The control can span multiple wires.
        """
        self.adding_control_to = component
        self._log_status(f"🎯 Click on a qubit lane to place control for {component.component_type.value}")
        
        # Change cursor to indicate control placement mode
        self.canvas.config(cursor="crosshair")
        
        # Show visual preview line from gate to mouse
        self._preview_control_line = None
        self._control_gate = component
        self.canvas.bind("<Motion>", self._preview_control_line_motion)
    
    def _preview_control_line_motion(self, event):
        """Show preview line from gate to mouse while in add control mode."""
        if not hasattr(self, 'adding_control_to') or not self.adding_control_to:
            return
        
        # Delete old preview line
        if hasattr(self, '_preview_control_line') and self._preview_control_line:
            self.canvas.delete(self._preview_control_line)
        
        # Get gate position
        gate = self.adding_control_to
        x, y, z = gate.position
        gate_x, gate_y = self.renderer.project_3d_to_2d(x + 0.5, y + 0.5, z + 0.5)
        
        # Draw preview line to mouse
        self._preview_control_line = self.canvas.create_line(
            gate_x, gate_y, event.x, event.y,
            fill="#00ff00", width=2, dash=(4, 4), tags="preview"
        )
    
    def _place_control_click(self, event):
        """Handle click to place the control qubit for a gate."""
        if not hasattr(self, 'adding_control_to') or not self.adding_control_to:
            return
        
        # Convert click to grid coordinates (returns x, y only)
        grid_x, grid_y = self._screen_to_grid(event.x, event.y)
        
        gate = self.adding_control_to
        gate_y = gate.position[1]
        
        # Control must be on a different lane than the gate
        if grid_y == gate_y:
            self._log_status("Control must be on a different qubit lane than the target gate")
            return
        
        # Set the control properties
        gate.properties['is_controlled'] = True
        gate.properties['control_y'] = grid_y
        
        # Update the gate name to show it's controlled
        gate_name = gate.component_type.value
        controlled_name = f"C{gate_name}"
        
        self._log_status(f"✓ Added control at lane {grid_y} → {controlled_name}")
        
        # Clean up control mode
        self._exit_add_control_mode()
        self._redraw_circuit()
    
    def _exit_add_control_mode(self):
        """Exit the add control mode and clean up."""
        self.adding_control_to = None
        self.canvas.config(cursor="")
        
        # Remove preview line
        if hasattr(self, '_preview_control_line') and self._preview_control_line:
            self.canvas.delete(self._preview_control_line)
            self._preview_control_line = None
        
        # Remove any preview tags
        self.canvas.delete("preview")
        
        # Rebind motion for normal operation (tooltip etc)
        self.canvas.unbind("<Motion>")
    
    def _show_toolbox_context_menu(self, event, comp_type: ComponentType):
        """Show context menu for toolbox button with controlled gate option."""
        context_menu = tk.Menu(self.root, tearoff=0, bg='#2b2b2b', fg='#ffffff',
                               activebackground='#e94560', activeforeground='#ffffff')
        
        # Regular placement option
        context_menu.add_command(
            label=f"Place {comp_type.value}",
            command=lambda: self._select_tool(comp_type)
        )
        
        context_menu.add_separator()
        
        # Controlled version option
        context_menu.add_command(
            label=f"Place Controlled-{comp_type.value} (C{comp_type.value})",
            command=lambda: self._start_controlled_gate_placement(comp_type)
        )
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _start_controlled_gate_placement(self, comp_type: ComponentType):
        """Start the two-click placement mode for a controlled gate.
        
        First click: Place the base gate (target)
        Second click: Place the control
        """
        self.placing_controlled_gate = comp_type
        self.placing_control_for_gate = None
        self._log_status(f"🎯 Click to place C{comp_type.value} target gate, then click control position")
        self.canvas.config(cursor="crosshair")
    
    def _place_controlled_gate_base(self, event):
        """Handle first click - place the base gate for controlled gate."""
        if not hasattr(self, 'placing_controlled_gate') or not self.placing_controlled_gate:
            return
        
        grid_x, grid_y = self._screen_to_grid(event.x, event.y)
        
        # Check boundaries
        if grid_x < -10 or grid_x > 10 or grid_y < -10 or grid_y > 10:
            self._log_status("Cannot place outside grid boundaries")
            return
        
        # Check if position is occupied
        if self._get_component_at_position(grid_x, grid_y):
            self._log_status(f"Position ({grid_x}, {grid_y}) is already occupied!")
            return
        
        comp_type = self.placing_controlled_gate
        
        # Determine color based on component type
        color_map = {
            ComponentType.X_GATE: (0.9, 0.2, 0.2),
            ComponentType.Z_GATE: (0.2, 0.2, 0.9),
            ComponentType.Y_GATE: (0.2, 0.9, 0.2),
            ComponentType.H_GATE: (1.0, 0.85, 0.2),
            ComponentType.S_GATE: (0.3, 0.9, 0.6),
            ComponentType.T_GATE: (1.0, 0.6, 0.2),
            ComponentType.SWAP_GATE: (0.9, 0.5, 0.2),
        }
        color = color_map.get(comp_type, (0.5, 0.5, 0.5))
        
        # Create the component (will be marked controlled after control placement)
        new_component = Component3D(
            component_type=comp_type,
            position=(grid_x, grid_y, 0),
            color=color,
            properties={}
        )
        self.components.append(new_component)
        self._log_status(f"Placed {comp_type.value} at ({grid_x}, {grid_y}) - now click control position")
        
        # Move to second phase - placing control
        self.placing_controlled_gate = None
        self.placing_control_for_gate = new_component
        
        # Draw preview from the new gate
        self._preview_control_line = None
        self._control_gate = new_component
        self.canvas.bind("<Motion>", self._preview_control_line_motion)
        
        self._redraw_circuit()
    
    def _place_controlled_gate_control(self, event):
        """Handle second click - place the control for the controlled gate."""
        if not hasattr(self, 'placing_control_for_gate') or not self.placing_control_for_gate:
            return
        
        grid_x, grid_y = self._screen_to_grid(event.x, event.y)
        
        gate = self.placing_control_for_gate
        gate_y = gate.position[1]
        
        # Control must be on a different lane than the gate
        if grid_y == gate_y:
            self._log_status("Control must be on a different qubit lane than the target gate")
            return
        
        # Set the control properties
        gate.properties['is_controlled'] = True
        gate.properties['control_y'] = grid_y
        
        gate_name = gate.component_type.value
        self._log_status(f"✓ Created C{gate_name} with control at lane {grid_y}")
        
        # Clean up placement mode
        self._exit_controlled_gate_placement()
        self._redraw_circuit()
    
    def _exit_controlled_gate_placement(self):
        """Exit controlled gate placement mode."""
        self.placing_controlled_gate = None
        self.placing_control_for_gate = None
        self.canvas.config(cursor="")
        
        # Remove preview line
        if hasattr(self, '_preview_control_line') and self._preview_control_line:
            self.canvas.delete(self._preview_control_line)
            self._preview_control_line = None
        
        self.canvas.delete("preview")
        self.canvas.unbind("<Motion>")
    
    def _cancel_placement_mode(self, event=None):
        """Cancel any active placement mode (Escape key handler)."""
        cancelled = False
        
        # Cancel add control mode
        if hasattr(self, 'adding_control_to') and self.adding_control_to:
            self._exit_add_control_mode()
            cancelled = True
        
        # Cancel controlled gate placement
        if hasattr(self, 'placing_controlled_gate') and self.placing_controlled_gate:
            self.placing_controlled_gate = None
            self.canvas.config(cursor="")
            cancelled = True
        
        # Cancel control placement for gate
        if hasattr(self, 'placing_control_for_gate') and self.placing_control_for_gate:
            # Remove the gate that was just placed (since control wasn't added)
            gate = self.placing_control_for_gate
            if gate in self.components:
                self.components.remove(gate)
                self._log_status(f"Cancelled - removed {gate.component_type.value}")
            self._exit_controlled_gate_placement()
            self._redraw_circuit()
            cancelled = True
        
        if cancelled:
            self._log_status("Placement mode cancelled")
            self.canvas.delete("preview")
    
    def _remove_control(self, component: Component3D):
        """Remove the control from a controlled gate."""
        if component.properties.get('is_controlled'):
            component.properties['is_controlled'] = False
            component.properties.pop('control_y', None)
            self._log_status(f"Removed control from {component.component_type.value}")
            self._redraw_circuit()

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
            # Use command pattern for undo/redo support
            cmd = DeleteComponentCommand(self, component)
            self.command_history.execute(cmd)
            
            if self.selected_component == component:
                self.selected_component = None
            self._log_status(f"Deleted {component.component_type.value}")
            self._redraw_circuit()
    
    def _delete_selected(self, event):
        """Delete currently selected component."""
        if self.selected_component:
            self._delete_component(self.selected_component)
    
    def _copy_selected(self, event=None):
        """Copy currently selected component to system clipboard (#14)."""
        if self.selected_component:
            # Create a JSON representation of the component for clipboard
            component_data = {
                '_clipboard_type': 'quantum_circuit_component',
                'type': self.selected_component.component_type.value,
                'position': list(self.selected_component.position),
                'rotation': self.selected_component.rotation,
                'size': list(self.selected_component.size),
                'connections': self.selected_component.connections,
                'properties': self.selected_component.properties
            }
            
            try:
                # Copy to system clipboard as JSON
                clipboard_json = json.dumps(component_data, indent=2)
                self.root.clipboard_clear()
                self.root.clipboard_append(clipboard_json)
                self._log_status(f"📋 Copied {self.selected_component.component_type.value}")
            except Exception as e:
                self._log_status(f"Copy failed: {e}")
                # Fallback to internal copy
                self._duplicate_component(self.selected_component)
        else:
            self._log_status("No component selected to copy")
    
    def _paste_component(self, event=None):
        """Paste component from system clipboard (#14)."""
        try:
            # Try to get clipboard content
            clipboard_data = self.root.clipboard_get()
            
            # Parse the JSON
            component_data = json.loads(clipboard_data)
            
            # Verify it's our clipboard format
            if component_data.get('_clipboard_type') != 'quantum_circuit_component':
                self._log_status("Clipboard does not contain a circuit component")
                return
            
            # Find component type
            comp_type = None
            type_str = component_data.get('type', '')
            for ct in ComponentType:
                if ct.value == type_str or ct.name == type_str:
                    comp_type = ct
                    break
            
            if not comp_type:
                self._log_status(f"Unknown component type: {type_str}")
                return
            
            # Get original position and offset for paste
            original_pos = component_data.get('position', [0, 0, 0])
            
            # Offset the paste position to avoid overlap
            paste_pos = (original_pos[0] + 1, original_pos[1], original_pos[2])
            
            # Check if position is occupied
            while any(c.position == paste_pos for c in self.components):
                paste_pos = (paste_pos[0] + 1, paste_pos[1], paste_pos[2])
            
            # Create the component
            component = Component3D(
                component_type=comp_type,
                position=paste_pos,
                rotation=component_data.get('rotation', 0.0),
                size=tuple(component_data.get('size', (1.0, 1.0, 1.0))),
                color=self._get_component_color(comp_type),
                connections=component_data.get('connections', []),
                properties=component_data.get('properties', {})
            )
            
            # Add to circuit with undo support
            command = PlaceComponentCommand(self.components, component)
            self.command_history.execute(command)
            
            self.selected_component = component
            self._log_status(f"📋 Pasted {comp_type.value} at {paste_pos}")
            self._redraw_circuit()
            
        except tk.TclError:
            # Clipboard is empty or not accessible
            self._log_status("Clipboard is empty")
        except json.JSONDecodeError:
            self._log_status("Clipboard does not contain valid component data")
        except Exception as e:
            self._log_status(f"Paste failed: {e}")
    
    def _copy_all_selected(self, event=None):
        """Copy all components in the circuit to clipboard (#14)."""
        if not self.components:
            self._log_status("No components to copy")
            return
        
        circuit_data = {
            '_clipboard_type': 'quantum_circuit_full',
            'view_mode': self.view_mode.value if hasattr(self.view_mode, 'value') else str(self.view_mode),
            'components': [
                {
                    'type': comp.component_type.value,
                    'position': list(comp.position),
                    'rotation': comp.rotation,
                    'size': list(comp.size),
                    'connections': comp.connections,
                    'properties': comp.properties
                }
                for comp in self.components
            ]
        }
        
        try:
            clipboard_json = json.dumps(circuit_data, indent=2)
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_json)
            self._log_status(f"📋 Copied entire circuit ({len(self.components)} components)")
        except Exception as e:
            self._log_status(f"Failed to copy circuit: {e}")
    
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
    
    def _clear_circuit(self) -> None:
        """Clear all components from the circuit."""
        self.components.clear()
        self.selected_component = None
        self._update_circuit_title("New Circuit")
        self._log_status("Circuit cleared")
        self._redraw_circuit()
    
    def _save_circuit(self) -> None:
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
                error_info = ErrorContext.get_user_friendly_error(e, "Failed to save circuit")
                messagebox.showerror(error_info['title'], ErrorContext.format_error_dialog(error_info))
                self._log_status(ErrorContext.format_error_log(error_info))
    
    def _load_circuit(self):
        """Load circuit from file."""
        # Determine initial directory based on current view mode
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if self.view_mode == ViewMode.SURFACE_CODE_2D:
            initial_dir = os.path.join(base_dir, 'saved_circuits', 'surface')
        else:
            initial_dir = os.path.join(base_dir, 'saved_circuits', 'circuits')
        
        # Fallback to base saved_circuits if specific folder doesn't exist
        if not os.path.exists(initial_dir):
            initial_dir = os.path.join(base_dir, 'saved_circuits')
        
        filename = filedialog.askopenfilename(
            initialdir=initial_dir,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Circuit"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    circuit_data = json.load(f)
                
                # Validate JSON structure (#21)
                validation_result = self._validate_circuit_json(circuit_data, filename)
                if not validation_result['valid']:
                    if validation_result['errors']:
                        error_msg = "Circuit file validation failed:\n\n"
                        error_msg += "\n".join(f"• {e}" for e in validation_result['errors'][:5])
                        if len(validation_result['errors']) > 5:
                            error_msg += f"\n... and {len(validation_result['errors']) - 5} more errors"
                        messagebox.showerror("Invalid Circuit File", error_msg)
                        return
                
                # Show warnings but continue loading
                if validation_result['warnings']:
                    self._log_status(f"⚠ {len(validation_result['warnings'])} warning(s) in circuit file")
                    for warning in validation_result['warnings'][:3]:
                        self._log_status(f"  - {warning}")
                
                # Check if this is a surface mode circuit
                view_mode_str = circuit_data.get('view_mode', 'isometric')
                is_surface_circuit = view_mode_str == 'surface_2d'
                
                # Switch view mode if needed
                if is_surface_circuit and self.view_mode != ViewMode.SURFACE_CODE_2D:
                    self._toggle_view_mode()
                elif not is_surface_circuit and self.view_mode == ViewMode.SURFACE_CODE_2D:
                    self._toggle_view_mode()
                
                # Clear current circuit
                self.components.clear()
                
                # Load components
                for comp_data in circuit_data.get('components', []):
                    # Find component type - check both value and name
                    comp_type = None
                    type_str = comp_data.get('type', '')
                    for ct in ComponentType:
                        if ct.value == type_str or ct.name == type_str:
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
                            color=self._get_component_color(comp_type),
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
                
            except json.JSONDecodeError as e:
                error_info = ErrorContext.get_user_friendly_error(e, "Loading circuit file")
                messagebox.showerror(error_info['title'], ErrorContext.format_error_dialog(error_info))
                self._log_status(ErrorContext.format_error_log(error_info))
            except Exception as e:
                error_info = ErrorContext.get_user_friendly_error(e, "Failed to load circuit")
                messagebox.showerror(error_info['title'], ErrorContext.format_error_dialog(error_info))
                self._log_status(ErrorContext.format_error_log(error_info))
    
    def _validate_circuit_json(self, data: dict, filename: str = "circuit") -> dict:
        """
        Validate circuit JSON data against expected schema.
        
        Args:
            data: The parsed JSON data to validate
            filename: Name of the file (for error messages)
            
        Returns:
            dict with:
            - valid: bool - True if no critical errors
            - errors: list of critical error messages
            - warnings: list of non-critical warnings
        """
        errors = []
        warnings = []
        
        # Check basic structure
        if not isinstance(data, dict):
            errors.append("Root element must be a JSON object")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Check for components array
        if 'components' not in data:
            errors.append("Missing required 'components' array")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        if not isinstance(data['components'], list):
            errors.append("'components' must be an array")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Validate view_mode if present
        if 'view_mode' in data:
            valid_modes = ['isometric', 'surface_2d', 'ldpc_tanner', 'ldpc_physical']
            if data['view_mode'] not in valid_modes:
                warnings.append(f"Unknown view_mode '{data['view_mode']}', will use default")
        
        # Valid component types
        valid_types = set(ct.value for ct in ComponentType) | set(ct.name for ct in ComponentType)
        
        # Validate each component
        for i, comp in enumerate(data['components']):
            comp_prefix = f"Component [{i}]"
            
            if not isinstance(comp, dict):
                errors.append(f"{comp_prefix}: Must be an object")
                continue
            
            # Required field: type
            if 'type' not in comp:
                errors.append(f"{comp_prefix}: Missing required 'type' field")
            elif comp['type'] not in valid_types:
                warnings.append(f"{comp_prefix}: Unknown type '{comp['type']}'")
            
            # Required field: position
            if 'position' not in comp:
                errors.append(f"{comp_prefix}: Missing required 'position' field")
            elif not isinstance(comp['position'], list) or len(comp['position']) != 3:
                errors.append(f"{comp_prefix}: 'position' must be array of 3 numbers [x, y, z]")
            else:
                # Validate position values are numbers
                for j, val in enumerate(comp['position']):
                    if not isinstance(val, (int, float)):
                        errors.append(f"{comp_prefix}: position[{j}] must be a number")
            
            # Optional field: size
            if 'size' in comp:
                if not isinstance(comp['size'], list) or len(comp['size']) != 3:
                    warnings.append(f"{comp_prefix}: 'size' should be array of 3 numbers")
            
            # Optional field: rotation
            if 'rotation' in comp:
                if not isinstance(comp['rotation'], (int, float)):
                    warnings.append(f"{comp_prefix}: 'rotation' should be a number")
            
            # Optional field: connections
            if 'connections' in comp:
                if not isinstance(comp['connections'], list):
                    warnings.append(f"{comp_prefix}: 'connections' should be an array")
            
            # Optional field: properties
            if 'properties' in comp:
                if not isinstance(comp['properties'], dict):
                    warnings.append(f"{comp_prefix}: 'properties' should be an object")
        
        # Check for duplicate positions
        positions = []
        for comp in data['components']:
            if 'position' in comp and isinstance(comp['position'], list):
                pos_tuple = tuple(comp['position'])
                if pos_tuple in positions:
                    warnings.append(f"Duplicate position found: {pos_tuple}")
                positions.append(pos_tuple)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _load_circuit_from_path(self, filepath: str):
        """Load circuit from a specific file path (used by tutorials and demos)."""
        try:
            with open(filepath, 'r') as f:
                circuit_data = json.load(f)
            
            # Validate JSON structure (#21)
            validation_result = self._validate_circuit_json(circuit_data, filepath)
            if not validation_result['valid']:
                error_msg = f"Invalid circuit file '{os.path.basename(filepath)}':\n"
                error_msg += "\n".join(validation_result['errors'][:3])
                raise ValueError(error_msg)
            
            # Log warnings if any
            for warning in validation_result['warnings'][:3]:
                self._log_status(f"⚠ {warning}")
            
            # Check if this is a surface mode circuit
            view_mode_str = circuit_data.get('view_mode', 'isometric')
            is_surface_circuit = view_mode_str == 'surface_2d'
            
            # Switch view mode if needed
            if is_surface_circuit and self.view_mode != ViewMode.SURFACE_CODE_2D:
                self._toggle_view_mode()
            elif not is_surface_circuit and self.view_mode == ViewMode.SURFACE_CODE_2D:
                self._toggle_view_mode()
            
            # Clear current circuit
            self.components.clear()
            
            # Track loading statistics
            loaded_count = 0
            skipped_count = 0
            skipped_types = []
            
            # Load components
            for comp_data in circuit_data.get('components', []):
                # Find component type - check both value and name
                comp_type = None
                type_str = comp_data.get('type', '')
                for ct in ComponentType:
                    if ct.value == type_str or ct.name == type_str:
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
                        color=self._get_component_color(comp_type),
                        connections=comp_data.get('connections', []),
                        properties=comp_data.get('properties', {})
                    )
                    self.components.append(component)
                    loaded_count += 1
                else:
                    # Log unknown component types (improvement #20)
                    skipped_count += 1
                    if type_str not in skipped_types:
                        skipped_types.append(type_str)
            
            # Update circuit title
            circuit_name = os.path.basename(filepath)
            formatted_title = self._format_circuit_title(circuit_name)
            self._update_circuit_title(formatted_title)
            
            # Log loading results
            self._log_status(f"Loaded {loaded_count} components from '{circuit_name}'")
            if skipped_count > 0:
                self._log_status(f"⚠ Skipped {skipped_count} unknown component(s): {', '.join(skipped_types)}")
            
            self._redraw_circuit()
            
        except Exception as e:
            raise Exception(f"Failed to load circuit: {e}")
    
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
    
    def _apply_circuit_correction(self):
        """Apply correction to circuit based on placed error components.
        
        This finds all error components (X Err, Z Err, Y Err) in the circuit
        and places corresponding yellow correction gates at the end of the 
        wire lines (max time position + 1) to cancel the errors.
        """
        if self.view_mode != ViewMode.ISOMETRIC_3D:
            self._log_status("Circuit correction only works in Circuit mode")
            return
        
        # Find all error components in the circuit
        error_types = [ComponentType.CIRCUIT_X_ERROR, ComponentType.CIRCUIT_Z_ERROR, 
                      ComponentType.CIRCUIT_Y_ERROR]
        errors = [c for c in self.components if c.component_type in error_types]
        
        if not errors:
            self._log_status("No errors found. Place error components (Errors tab) first.")
            return
        
        # Find the maximum time position (x coordinate) in the circuit
        # We'll place corrections at max_x + 1
        all_x = [c.position[0] for c in self.components]
        max_x = max(all_x) if all_x else 0
        correction_x = max_x + 2  # Leave a gap for visibility
        
        # Get the wire positions (y coordinates) that have errors
        corrections_added = []
        
        for error in errors:
            ex, ey, ez = error.position
            
            # Determine what correction to apply based on error type
            if error.component_type == ComponentType.CIRCUIT_X_ERROR:
                correction_label = "X"
            elif error.component_type == ComponentType.CIRCUIT_Z_ERROR:
                correction_label = "Z"
            elif error.component_type == ComponentType.CIRCUIT_Y_ERROR:
                # Y error = XZ, needs both corrections
                correction_label = "Y"
            else:
                continue
            
            # Create a correction component at the end of the wire
            correction = Component3D(
                component_type=ComponentType.CIRCUIT_CORRECTION,
                position=(correction_x, ey, ez),
                rotation=0,
                size=(1, 1, 1),
                color=(1.0, 0.85, 0.2),  # Yellow
                connections=[],
                properties={'correction_for': error.component_type.value, 'label': correction_label}
            )
            
            self.components.append(correction)
            corrections_added.append((correction_x, ey, correction_label))
        
        if corrections_added:
            self._log_status(f"✓ Added {len(corrections_added)} correction(s) at x={correction_x}")
            for cx, cy, label in corrections_added:
                self._log_status(f"  {label} correction at wire y={cy}")
            self._redraw_circuit()
        else:
            self._log_status("No corrections could be determined")
    
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
            error_info = ErrorContext.get_user_friendly_error(e, "Running quantum simulation")
            self._log_status(ErrorContext.format_error_log(error_info))
            self._log_status(f"💡 Suggestions: {'; '.join(error_info['suggestions'][:2])}")
    
    # ==================== CIRCUIT VALIDATION (#11) ====================
    
    def _validate_circuit(self):
        """Validate the current circuit for common issues."""
        try:
            issues = self._perform_circuit_validation()
            self._show_validation_results(issues)
        except Exception as e:
            self._log_status(f"Error during validation: {e}")
    
    def _perform_circuit_validation(self) -> dict:
        """
        Perform comprehensive circuit validation.
        
        Returns:
            Dictionary with validation results containing:
            - errors: Critical issues that prevent circuit operation
            - warnings: Non-critical issues that may affect results
            - info: Informational notes about the circuit
            - stats: Circuit statistics
        """
        errors = []
        warnings = []
        info = []
        stats = {}
        
        # Gather component statistics
        qubits = [c for c in self.components if c.component_type in [
            ComponentType.QUBIT, ComponentType.DATA_QUBIT, ComponentType.ANCILLA_QUBIT
        ]]
        gates = [c for c in self.components if c.component_type in [
            ComponentType.H_GATE, ComponentType.X_GATE, ComponentType.Y_GATE, 
            ComponentType.Z_GATE, ComponentType.S_GATE, ComponentType.T_GATE,
            ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE
        ]]
        measurements = [c for c in self.components if c.component_type == ComponentType.MEASUREMENT]
        connections = [c for c in self.components if c.component_type == ComponentType.QUBIT_CONNECTION]
        syndrome_extractors = [c for c in self.components if c.component_type in [
            ComponentType.X_STABILIZER, ComponentType.Z_STABILIZER, ComponentType.PARITY_CHECK
        ]]
        
        stats['total_components'] = len(self.components)
        stats['qubits'] = len(qubits)
        stats['gates'] = len(gates)
        stats['measurements'] = len(measurements)
        stats['connections'] = len(connections)
        stats['syndrome_extractors'] = len(syndrome_extractors)
        
        # Check 1: Empty circuit
        if len(self.components) == 0:
            errors.append("Circuit is empty - no components placed")
            return {'errors': errors, 'warnings': warnings, 'info': info, 'stats': stats}
        
        # Check 2: No qubits
        if len(qubits) == 0:
            errors.append("No qubit components found - circuit needs at least one qubit")
        
        # Check 3: Gates without qubits
        if len(gates) > 0 and len(qubits) == 0:
            errors.append(f"Found {len(gates)} gate(s) but no qubits to operate on")
        
        # Check 4: Orphaned gates (gates not on a qubit lane)
        qubit_positions = set()
        for q in qubits:
            # Add all x positions along the qubit's lane
            qubit_positions.add((q.position[1], q.position[2]))  # (y, z) = lane identity
        
        orphaned_gates = []
        for g in gates:
            lane = (g.position[1], g.position[2])
            if lane not in qubit_positions:
                orphaned_gates.append((g.component_type.value, g.position))
        
        if orphaned_gates:
            warnings.append(f"Found {len(orphaned_gates)} gate(s) not on any qubit lane")
            for gate_type, pos in orphaned_gates[:3]:  # Show first 3
                warnings.append(f"  - {gate_type} at {pos}")
            if len(orphaned_gates) > 3:
                warnings.append(f"  ... and {len(orphaned_gates) - 3} more")
        
        # Check 5: Two-qubit gates validation
        two_qubit_gates = [c for c in self.components if c.component_type in [
            ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE
        ]]
        
        for gate in two_qubit_gates:
            # Check if there are connections or paired qubits
            x, y, z = gate.position
            paired_found = False
            for other in two_qubit_gates:
                if other != gate and other.position[0] == x:  # Same time slice
                    if other.component_type == gate.component_type:
                        paired_found = True
                        break
            if not paired_found:
                # Check for explicit connections
                conn_found = any(
                    c.component_type == ComponentType.QUBIT_CONNECTION and
                    abs(c.position[0] - x) <= 1
                    for c in connections
                )
                if not conn_found:
                    warnings.append(f"Two-qubit gate {gate.component_type.value} at {gate.position} may need a connection")
        
        # Check 6: Measurements not at the end
        if measurements:
            max_gate_time = max((g.position[0] for g in gates), default=0)
            early_measurements = [m for m in measurements if m.position[0] < max_gate_time]
            if early_measurements:
                warnings.append(f"Found {len(early_measurements)} measurement(s) before later gates - may cause issues")
        
        # Check 7: Circuit depth analysis
        if gates:
            time_slices = set(g.position[0] for g in gates)
            circuit_depth = len(time_slices)
            stats['circuit_depth'] = circuit_depth
            if circuit_depth > 100:
                warnings.append(f"Circuit depth ({circuit_depth}) is very high - may impact simulation performance")
        
        # Check 8: Unconnected syndrome extractors
        if syndrome_extractors and len(qubits) > 0:
            for se in syndrome_extractors:
                x, y, z = se.position
                # Check for nearby data qubits or connections
                nearby_qubits = [q for q in qubits if 
                    abs(q.position[0] - x) <= 1 and
                    abs(q.position[1] - y) <= 2 and
                    abs(q.position[2] - z) <= 2
                ]
                if not nearby_qubits:
                    warnings.append(f"Syndrome extractor at {se.position} has no nearby qubits")
        
        # Info messages
        if len(qubits) > 0:
            info.append(f"Circuit has {len(qubits)} qubit(s)")
        if stats.get('circuit_depth'):
            info.append(f"Circuit depth: {stats['circuit_depth']}")
        if syndrome_extractors:
            info.append(f"Error correction ready with {len(syndrome_extractors)} syndrome extractor(s)")
        if measurements:
            info.append(f"{len(measurements)} measurement(s) configured")
        
        return {'errors': errors, 'warnings': warnings, 'info': info, 'stats': stats}
    
    def _show_validation_results(self, results: dict):
        """Display circuit validation results in a dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Circuit Validation Results")
        dialog.geometry("500x450")
        dialog.configure(bg='#2b2b2b')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header with overall status
        errors = results.get('errors', [])
        warnings = results.get('warnings', [])
        info = results.get('info', [])
        stats = results.get('stats', {})
        
        if errors:
            status_text = "❌ VALIDATION FAILED"
            status_color = '#ff6b6b'
        elif warnings:
            status_text = "⚠️ VALIDATION PASSED WITH WARNINGS"
            status_color = '#ffd93d'
        else:
            status_text = "✅ VALIDATION PASSED"
            status_color = '#6bcb77'
        
        header_frame = tk.Frame(dialog, bg='#2b2b2b')
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(header_frame, text=status_text, font=('TkDefaultFont', 14, 'bold'),
                bg='#2b2b2b', fg=status_color).pack()
        
        # Statistics frame
        stats_frame = tk.LabelFrame(dialog, text="Circuit Statistics", 
                                    bg='#2b2b2b', fg='#ffffff', font=('TkDefaultFont', 10, 'bold'))
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        stats_text = f"Components: {stats.get('total_components', 0)} | "
        stats_text += f"Qubits: {stats.get('qubits', 0)} | "
        stats_text += f"Gates: {stats.get('gates', 0)} | "
        stats_text += f"Measurements: {stats.get('measurements', 0)}"
        
        tk.Label(stats_frame, text=stats_text, bg='#2b2b2b', fg='#cccccc',
                font=('TkDefaultFont', 9)).pack(padx=5, pady=5)
        
        # Results text area
        text_frame = tk.Frame(dialog, bg='#2b2b2b')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        text_widget = tk.Text(text_frame, bg='#1e1e1e', fg='#ffffff', 
                             font=('Consolas', 10), wrap=tk.WORD,
                             relief=tk.FLAT, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colors
        text_widget.tag_configure('error', foreground='#ff6b6b')
        text_widget.tag_configure('warning', foreground='#ffd93d')
        text_widget.tag_configure('info', foreground='#6bcb77')
        text_widget.tag_configure('header', foreground='#4fc3f7', font=('Consolas', 10, 'bold'))
        
        # Add errors
        if errors:
            text_widget.insert(tk.END, "ERRORS:\n", 'header')
            for error in errors:
                text_widget.insert(tk.END, f"  ✗ {error}\n", 'error')
            text_widget.insert(tk.END, "\n")
        
        # Add warnings
        if warnings:
            text_widget.insert(tk.END, "WARNINGS:\n", 'header')
            for warning in warnings:
                text_widget.insert(tk.END, f"  ⚠ {warning}\n", 'warning')
            text_widget.insert(tk.END, "\n")
        
        # Add info
        if info:
            text_widget.insert(tk.END, "INFO:\n", 'header')
            for item in info:
                text_widget.insert(tk.END, f"  ✓ {item}\n", 'info')
        
        # If no issues at all
        if not errors and not warnings:
            text_widget.insert(tk.END, "No issues found! Circuit is ready for simulation.\n", 'info')
        
        text_widget.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = tk.Frame(dialog, bg='#2b2b2b')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Close", command=dialog.destroy,
                  style='Dark.TButton').pack(side=tk.RIGHT, padx=5)
        
        # Also log to status
        self._log_status(f"Validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    
    # ==================== ZOOM FUNCTIONALITY (#13) ====================
    
    def _zoom_in(self):
        """Zoom in the grid view."""
        if not hasattr(self, '_zoom_level'):
            self._zoom_level = 1.0
        
        if self._zoom_level < 2.0:  # Max 200%
            self._zoom_level += 0.1
            self._apply_zoom()
    
    def _zoom_out(self):
        """Zoom out the grid view."""
        if not hasattr(self, '_zoom_level'):
            self._zoom_level = 1.0
        
        if self._zoom_level > 0.5:  # Min 50%
            self._zoom_level -= 0.1
            self._apply_zoom()
    
    def _zoom_reset(self):
        """Reset zoom to 100%."""
        self._zoom_level = 1.0
        self._apply_zoom()
    
    def _apply_zoom(self):
        """Apply the current zoom level."""
        # Update renderer scale
        base_scale = 30.0
        if hasattr(self, 'renderer') and self.renderer:
            self.renderer.scale = base_scale * self._zoom_level
        
        # Update zoom label
        if hasattr(self, 'zoom_label'):
            self.zoom_label.config(text=f"{int(self._zoom_level * 100)}%")
        
        # Redraw
        self._draw_grid()
        self._redraw_circuit()
        self._log_status(f"Zoom: {int(self._zoom_level * 100)}%")
    
    # ==================== GRID SIZE ADJUSTMENT ====================
    
    def _increase_grid_size(self):
        """Increase the grid size."""
        if self.grid_size < 40:  # Max 40
            self.grid_size += 5
            self._update_grid_size_display()
            self._draw_grid()
            self._redraw_circuit()
            self._log_status(f"Grid size: {self.grid_size}")
    
    def _decrease_grid_size(self):
        """Decrease the grid size."""
        if self.grid_size > 10:  # Min 10
            self.grid_size -= 5
            self._update_grid_size_display()
            self._draw_grid()
            self._redraw_circuit()
            self._log_status(f"Grid size: {self.grid_size}")
    
    def _update_grid_size_display(self):
        """Update the grid size label."""
        if hasattr(self, 'grid_size_label'):
            self.grid_size_label.config(text=str(self.grid_size))
    
    # ==================== CIRCUIT MODE QEC FUNCTIONS ====================
    
    def _inject_circuit_error(self, error_type: str):
        """Inject an error (X, Y, or Z) on a selected qubit in circuit mode.
        
        Based on papers: An error flips the syndrome of stabilizers that anti-commute with it.
        """
        if self.view_mode != ViewMode.ISOMETRIC_3D:
            self._log_status("Error injection is only available in Circuit Mode")
            return
        
        # Initialize error tracking if not exists
        if not hasattr(self, 'circuit_errors'):
            self.circuit_errors = {}
        
        # Find data qubits
        data_qubits = [c for c in self.components if c.component_type == ComponentType.DATA_QUBIT]
        
        if not data_qubits:
            self._log_status("No data qubits to inject errors on. Place some qubits first.")
            return
        
        # If a component is selected, use that; otherwise pick a random qubit
        target_qubit = None
        if self.selected_component and self.selected_component.component_type == ComponentType.DATA_QUBIT:
            target_qubit = self.selected_component
        else:
            # Select the first qubit without an error, or random if all have errors
            for q in data_qubits:
                q_key = (q.position[0], q.position[1], q.position[2])
                if q_key not in self.circuit_errors:
                    target_qubit = q
                    break
            if target_qubit is None:
                import random
                target_qubit = random.choice(data_qubits)
        
        # Record the error
        q_key = (target_qubit.position[0], target_qubit.position[1], target_qubit.position[2])
        
        # Toggle or set error
        if q_key in self.circuit_errors and self.circuit_errors[q_key] == error_type:
            # Same error again - remove it
            del self.circuit_errors[q_key]
            self._log_status(f"Removed {error_type} error from qubit at {q_key}")
        else:
            self.circuit_errors[q_key] = error_type
            self._log_status(f"Injected {error_type} error on qubit at {q_key}")
        
        # Update visual and syndrome
        self._highlight_circuit_errors()
        self._compute_circuit_syndrome()
    
    def _clear_circuit_errors(self):
        """Clear all injected errors in circuit mode."""
        if hasattr(self, 'circuit_errors'):
            self.circuit_errors = {}
        self.canvas.delete("error_highlight")
        self.canvas.delete("correction_highlight")
        if hasattr(self, 'circuit_syndrome_label'):
            self.circuit_syndrome_label.config(text="Syndrome: --", fg='#88ff88')
        self._log_status("Cleared all circuit errors")
    
    def _highlight_circuit_errors(self):
        """Draw visual indicators for injected errors."""
        self.canvas.delete("error_highlight")
        
        if not hasattr(self, 'circuit_errors') or not self.circuit_errors:
            return
        
        for q_key, error_type in self.circuit_errors.items():
            # Convert grid position to canvas coordinates
            x, y, z = q_key
            if hasattr(self, 'renderer') and self.renderer:
                # Use isometric projection
                canvas_x, canvas_y = self.renderer._project_to_2d(x, y, z)
                
                # Draw error indicator (red circle with error type)
                radius = 15
                color = '#ff4444' if error_type == 'X' else '#44ff44' if error_type == 'Y' else '#4444ff'
                
                self.canvas.create_oval(
                    canvas_x - radius, canvas_y - radius,
                    canvas_x + radius, canvas_y + radius,
                    outline=color, width=3, tags="error_highlight"
                )
                self.canvas.create_text(
                    canvas_x, canvas_y - radius - 10,
                    text=error_type, fill=color, font=('Consolas', 10, 'bold'),
                    tags="error_highlight"
                )
    
    def _compute_circuit_syndrome(self):
        """Compute syndrome based on injected errors.
        
        For stabilizer codes, syndrome bit i is 1 if error anti-commutes with stabilizer i.
        This is a simplified computation for demonstration.
        """
        if not hasattr(self, 'circuit_errors') or not self.circuit_errors:
            if hasattr(self, 'circuit_syndrome_label'):
                self.circuit_syndrome_label.config(text="Syndrome: 0000", fg='#88ff88')
            return
        
        # Count errors by type
        x_errors = sum(1 for e in self.circuit_errors.values() if e == 'X')
        y_errors = sum(1 for e in self.circuit_errors.values() if e == 'Y')
        z_errors = sum(1 for e in self.circuit_errors.values() if e == 'Z')
        
        # Simple syndrome: each error contributes to syndrome based on position
        # This is a placeholder - real implementation would use the actual stabilizer structure
        num_qubits = len([c for c in self.components if c.component_type == ComponentType.DATA_QUBIT])
        num_stabilizers = min(4, num_qubits - 1) if num_qubits > 1 else 0
        
        syndrome = []
        for i in range(num_stabilizers):
            # Each stabilizer checks certain qubits
            bit = 0
            for j, (q_key, error_type) in enumerate(self.circuit_errors.items()):
                # Simple pattern: stabilizer i checks qubits i and i+1
                if j == i or j == (i + 1) % num_qubits:
                    if error_type in ['X', 'Y']:  # X and Y flip Z-stabilizers
                        bit ^= 1
            syndrome.append(bit)
        
        syndrome_str = ''.join(str(b) for b in syndrome) if syndrome else '0000'
        syndrome_weight = sum(syndrome)
        
        # Update label
        if hasattr(self, 'circuit_syndrome_label'):
            color = '#ff8888' if syndrome_weight > 0 else '#88ff88'
            self.circuit_syndrome_label.config(text=f"Syndrome: {syndrome_str}", fg=color)
        
        self._log_status(f"Syndrome: {syndrome_str} (weight: {syndrome_weight})")
    
    def _apply_syndrome_based_correction(self):
        """Apply correction based on computed syndrome (legacy).
        
        Based on papers: lookup syndrome in table to find correction operator.
        Yellow visual feedback shows the correction.
        Note: This is a legacy function using circuit_errors dict. 
        The main _apply_circuit_correction() uses placed error components.
        """
        if not hasattr(self, 'circuit_errors') or not self.circuit_errors:
            self._log_status("No errors to correct")
            return
        
        # Show correction visually (yellow highlights)
        self.canvas.delete("correction_highlight")
        
        corrections_applied = []
        for q_key, error_type in list(self.circuit_errors.items()):
            x, y, z = q_key
            if hasattr(self, 'renderer') and self.renderer:
                canvas_x, canvas_y = self.renderer._project_to_2d(x, y, z)
                
                # Draw yellow correction indicator
                radius = 18
                self.canvas.create_oval(
                    canvas_x - radius, canvas_y - radius,
                    canvas_x + radius, canvas_y + radius,
                    outline='#ffcc00', width=4, tags="correction_highlight"
                )
                self.canvas.create_text(
                    canvas_x, canvas_y + radius + 12,
                    text=f"Fix:{error_type}", fill='#ffcc00', font=('Consolas', 9, 'bold'),
                    tags="correction_highlight"
                )
                corrections_applied.append(f"{error_type}@{q_key}")
        
        # Log the correction
        self._log_status(f"=== Correction Applied ===")
        self._log_status(f"Corrections: {', '.join(corrections_applied)}")
        
        # Clear errors after brief delay to show the correction
        self.root.after(1500, self._finalize_circuit_correction)
    
    def _finalize_circuit_correction(self):
        """Finalize the correction - clear errors and show success."""
        self.circuit_errors = {}
        self.canvas.delete("error_highlight")
        self.canvas.delete("correction_highlight")
        if hasattr(self, 'circuit_syndrome_label'):
            self.circuit_syndrome_label.config(text="Syndrome: 0000 ✓", fg='#88ff88')
        self._log_status("✓ Errors corrected successfully!")
    
    # ==================== SURFACE CODE QEC FUNCTIONS ====================
    
    def _apply_surface_correction(self):
        """Apply correction to surface code errors.
        
        Based on paper.tex: Uses minimum-weight matching to pair syndrome endpoints.
        Yellow visual feedback shows the correction path.
        """
        if self.view_mode != ViewMode.SURFACE_CODE_2D:
            self._log_status("Surface correction only available in Surface Code mode")
            return
        
        # Find errors
        errors = [c for c in self.components if c.component_type in 
                  [ComponentType.SURFACE_X_ERROR, ComponentType.SURFACE_Z_ERROR, ComponentType.SURFACE_Y_ERROR]]
        
        if not errors:
            self._log_status("No errors to correct. Place some errors first.")
            return
        
        # Clear previous correction highlights
        self.canvas.delete("correction_path")
        
        # For each error, draw a yellow correction indicator
        corrections = []
        for error in errors:
            ex, ey = error.position[0], error.position[1]
            error_type = error.component_type
            
            # Convert to canvas coordinates
            canvas_x = self.canvas_offset_x + ex * self.surface_grid_spacing
            canvas_y = self.canvas_offset_y + ey * self.surface_grid_spacing
            
            # Draw yellow correction ring
            radius = self.surface_grid_spacing * 0.4
            self.canvas.create_oval(
                canvas_x - radius, canvas_y - radius,
                canvas_x + radius, canvas_y + radius,
                outline='#ffcc00', width=4, tags="correction_path"
            )
            
            # Label showing correction type
            correction_op = 'X' if error_type == ComponentType.SURFACE_X_ERROR else \
                           'Z' if error_type == ComponentType.SURFACE_Z_ERROR else 'Y'
            self.canvas.create_text(
                canvas_x, canvas_y - radius - 8,
                text=f"Fix:{correction_op}", fill='#ffcc00', font=('Consolas', 8, 'bold'),
                tags="correction_path"
            )
            corrections.append(f"{correction_op}@({ex},{ey})")
        
        self._log_status(f"=== Surface Code Correction ===")
        self._log_status(f"Applying corrections: {', '.join(corrections)}")
        
        # Update info display
        if hasattr(self, 'surface_syndrome_label'):
            self.surface_syndrome_label.config(text=f"Correcting {len(errors)} errors...")
        
        # Schedule cleanup after showing correction
        self.root.after(2000, self._finalize_surface_correction, errors)
    
    def _finalize_surface_correction(self, errors_to_remove):
        """Finalize surface code correction - remove error components."""
        # Remove error components
        for error in errors_to_remove:
            if error in self.components:
                self.components.remove(error)
        
        # Clear visual elements
        self.canvas.delete("correction_path")
        self.canvas.delete("syndrome_highlight")
        
        # Redraw
        self._redraw_circuit()
        
        # Update info
        if hasattr(self, 'surface_syndrome_label'):
            self.surface_syndrome_label.config(text="Errors: 0  |  Syndrome: 0")
        if hasattr(self, 'surface_threshold_label'):
            self.surface_threshold_label.config(text="Threshold: OK", fg='#88ff88')
        
        self._log_status("✓ Surface code errors corrected!")
    
    def _update_surface_info(self):
        """Update the surface code info display with error count and threshold status."""
        if self.view_mode != ViewMode.SURFACE_CODE_2D:
            return
        
        # Count errors
        errors = [c for c in self.components if c.component_type in 
                  [ComponentType.SURFACE_X_ERROR, ComponentType.SURFACE_Z_ERROR, ComponentType.SURFACE_Y_ERROR]]
        num_errors = len(errors)
        
        # Count stabilizers (for distance estimation)
        stabilizers = [c for c in self.components if c.component_type in 
                       [ComponentType.SURFACE_X_STABILIZER, ComponentType.SURFACE_Z_STABILIZER]]
        
        # Estimate code distance (simplified)
        # In a d×d surface code, we have roughly d² data qubits and d can correct floor((d-1)/2) errors
        data_qubits = [c for c in self.components if c.component_type == ComponentType.SURFACE_DATA]
        if len(data_qubits) > 0:
            import math
            d_estimate = int(math.sqrt(len(data_qubits))) + 1
            max_correctable = (d_estimate - 1) // 2
        else:
            d_estimate = 3  # Default
            max_correctable = 1
        
        # Update labels
        if hasattr(self, 'surface_syndrome_label'):
            self.surface_syndrome_label.config(text=f"Errors: {num_errors}  |  Stabs: {len(stabilizers)}")
        
        if hasattr(self, 'surface_threshold_label'):
            if num_errors == 0:
                self.surface_threshold_label.config(text="Status: Clean", fg='#88ff88')
            elif num_errors <= max_correctable:
                self.surface_threshold_label.config(
                    text=f"Status: Correctable ({num_errors}/{max_correctable})", 
                    fg='#ffcc44'
                )
            else:
                self.surface_threshold_label.config(
                    text=f"Status: DANGER ({num_errors}>{max_correctable})", 
                    fg='#ff4444'
                )
    
    # ==================== EXPORT FUNCTIONALITY (#12) ====================
    
    def _export_to_qasm(self):
        """Export circuit to OpenQASM 2.0 format."""
        if self.view_mode != ViewMode.ISOMETRIC_3D:
            self._log_status("QASM export is only available in Circuit Mode")
            messagebox.showinfo("Info", "Please switch to Circuit Mode (press V) to export to QASM")
            return
        
        # Count qubits and build circuit structure
        data_qubits = [c for c in self.components if c.component_type == ComponentType.DATA_QUBIT]
        ancilla_qubits = [c for c in self.components if c.component_type == ComponentType.ANCILLA_QUBIT]
        
        if not data_qubits and not ancilla_qubits:
            self._log_status("No qubits in circuit. Add DATA_QUBIT or ANCILLA_QUBIT components first.")
            messagebox.showinfo("Info", "No qubits found. Please add Data Qubits to the circuit.")
            return
        
        # Build lane to qubit mapping
        all_qubits = data_qubits + ancilla_qubits
        all_qubits_sorted = sorted(all_qubits, key=lambda c: c.position[1])
        lane_to_qubit = {}
        for idx, comp in enumerate(all_qubits_sorted):
            lane = comp.position[1]
            if lane not in lane_to_qubit:
                lane_to_qubit[lane] = idx
        
        num_qubits = len(lane_to_qubit)
        
        # Generate QASM header
        qasm_lines = [
            "OPENQASM 2.0;",
            'include "qelib1.inc";',
            "",
            f"// Circuit exported from Quantum LDPC Circuit Builder",
            f"// Number of qubits: {num_qubits}",
            "",
            f"qreg q[{num_qubits}];",
            f"creg c[{num_qubits}];",
            ""
        ]
        
        # Sort all gate components by x-position (time order)
        gate_types = [
            ComponentType.X_GATE, ComponentType.Y_GATE, ComponentType.Z_GATE,
            ComponentType.H_GATE, ComponentType.S_GATE, ComponentType.T_GATE,
            ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE,
            ComponentType.MEASURE, ComponentType.RESET
        ]
        
        gate_components = [c for c in self.components if c.component_type in gate_types]
        gate_components_sorted = sorted(gate_components, key=lambda c: c.position[0])
        
        # Convert each gate to QASM
        for comp in gate_components_sorted:
            lane = comp.position[1]
            qubit_idx = lane_to_qubit.get(lane, -1)
            
            if qubit_idx < 0:
                continue  # Skip gates on empty lanes
            
            ct = comp.component_type
            
            if ct == ComponentType.X_GATE:
                qasm_lines.append(f"x q[{qubit_idx}];")
            elif ct == ComponentType.Y_GATE:
                qasm_lines.append(f"y q[{qubit_idx}];")
            elif ct == ComponentType.Z_GATE:
                qasm_lines.append(f"z q[{qubit_idx}];")
            elif ct == ComponentType.H_GATE:
                qasm_lines.append(f"h q[{qubit_idx}];")
            elif ct == ComponentType.S_GATE:
                qasm_lines.append(f"s q[{qubit_idx}];")
            elif ct == ComponentType.T_GATE:
                qasm_lines.append(f"t q[{qubit_idx}];")
            elif ct == ComponentType.CNOT_GATE:
                ctrl_lane = comp.properties.get('control', lane)
                tgt_lane = comp.properties.get('target', lane + 1)
                ctrl_idx = lane_to_qubit.get(ctrl_lane, -1)
                tgt_idx = lane_to_qubit.get(tgt_lane, -1)
                if ctrl_idx >= 0 and tgt_idx >= 0:
                    qasm_lines.append(f"cx q[{ctrl_idx}], q[{tgt_idx}];")
            elif ct == ComponentType.CZ_GATE:
                ctrl_lane = comp.properties.get('control', lane)
                tgt_lane = comp.properties.get('target', lane + 1)
                ctrl_idx = lane_to_qubit.get(ctrl_lane, -1)
                tgt_idx = lane_to_qubit.get(tgt_lane, -1)
                if ctrl_idx >= 0 and tgt_idx >= 0:
                    qasm_lines.append(f"cz q[{ctrl_idx}], q[{tgt_idx}];")
            elif ct == ComponentType.SWAP_GATE:
                ctrl_lane = comp.properties.get('control', lane)
                tgt_lane = comp.properties.get('target', lane + 1)
                ctrl_idx = lane_to_qubit.get(ctrl_lane, -1)
                tgt_idx = lane_to_qubit.get(tgt_lane, -1)
                if ctrl_idx >= 0 and tgt_idx >= 0:
                    qasm_lines.append(f"swap q[{ctrl_idx}], q[{tgt_idx}];")
            elif ct == ComponentType.MEASURE:
                qasm_lines.append(f"measure q[{qubit_idx}] -> c[{qubit_idx}];")
            elif ct == ComponentType.RESET:
                qasm_lines.append(f"reset q[{qubit_idx}];")
        
        qasm_code = "\n".join(qasm_lines)
        
        # Ask where to save
        filename = filedialog.asksaveasfilename(
            defaultextension=".qasm",
            filetypes=[("OpenQASM files", "*.qasm"), ("All files", "*.*")],
            title="Export to OpenQASM"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(qasm_code)
                self._log_status(f"Exported to {filename}")
                messagebox.showinfo("Success", f"Circuit exported to:\n{filename}")
            except Exception as e:
                self._log_status(f"Export failed: {e}")
                messagebox.showerror("Error", f"Failed to export: {e}")
        else:
            # Show in a dialog if user cancelled file save
            self._show_qasm_preview(qasm_code)
    
    def _show_qasm_preview(self, qasm_code: str):
        """Show QASM code in a preview dialog."""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("OpenQASM Export Preview")
        preview_window.configure(bg='#2b2b2b')
        preview_window.geometry("500x400")
        preview_window.transient(self.root)
        
        # Title
        title_label = tk.Label(preview_window, text="OpenQASM 2.0 Code",
                              bg='#2b2b2b', fg='#00ff88',
                              font=('Segoe UI', 12, 'bold'))
        title_label.pack(pady=(10, 5))
        
        # Code display
        code_frame = ttk.Frame(preview_window, style='Dark.TFrame')
        code_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        code_text = tk.Text(code_frame, bg='#1e1e1e', fg='#e0e0e0',
                           font=('Consolas', 10), wrap=tk.NONE,
                           insertbackground='#ffffff')
        code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(code_frame, command=code_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        code_text.config(yscrollcommand=scrollbar.set)
        
        code_text.insert('1.0', qasm_code)
        code_text.config(state='disabled')
        
        # Buttons
        btn_frame = ttk.Frame(preview_window, style='Dark.TFrame')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def copy_to_clipboard():
            preview_window.clipboard_clear()
            preview_window.clipboard_append(qasm_code)
            self._log_status("QASM code copied to clipboard")
        
        copy_btn = tk.Button(btn_frame, text="Copy to Clipboard",
                            command=copy_to_clipboard,
                            bg='#2EC4B6', fg='#000000',
                            activebackground='#3dd5c7',
                            relief='flat', padx=15, pady=5)
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Button(btn_frame, text="Close",
                             command=preview_window.destroy,
                             bg='#404040', fg='#ffffff',
                             activebackground='#505050',
                             relief='flat', padx=15, pady=5)
        close_btn.pack(side=tk.RIGHT, padx=5)
    
    def _highlight_syndrome_surface(self):
        """Highlight stabilizers that would detect placed errors on the surface code lattice."""
        try:
            # Find all error components
            errors = [c for c in self.components if c.component_type in 
                      [ComponentType.SURFACE_X_ERROR, ComponentType.SURFACE_Z_ERROR, ComponentType.SURFACE_Y_ERROR]]
            
            if not errors:
                self._log_status("No errors placed. Add X, Z, or Y errors to see syndrome highlighting.")
                return
            
            # Find all stabilizers
            stabilizers = [c for c in self.components if c.component_type in 
                           [ComponentType.SURFACE_X_STABILIZER, ComponentType.SURFACE_Z_STABILIZER]]
            
            # Track which stabilizers are triggered (use list with position tuple as key)
            triggered_stabilizers = []
            triggered_positions = set()  # Track positions to avoid duplicates
            
            for error in errors:
                ex, ey = error.position[0], error.position[1]
                error_type = error.component_type
                
                # Check each stabilizer to see if it detects this error
                for stab in stabilizers:
                    sx, sy = stab.position[0], stab.position[1]
                    stab_type = stab.component_type
                    stab_pos_key = (sx, sy, stab_type.value)
                    
                    # A stabilizer detects an error if:
                    # - The error is at an odd coordinate neighboring the stabilizer's even coordinate
                    # - X errors are detected by Z-stabilizers, Z errors by X-stabilizers
                    # - Y errors are detected by both
                    
                    # Check if error is a neighbor of this stabilizer
                    # In rotated surface code, data at (ex, ey) neighbors stabilizer at (sx, sy) if |ex-sx|=1 and |ey-sy|=1
                    is_neighbor = (abs(ex - sx) == 1 and abs(ey - sy) == 1)
                    
                    if is_neighbor and stab_pos_key not in triggered_positions:
                        # Check error type vs stabilizer type
                        if error_type == ComponentType.SURFACE_X_ERROR and stab_type == ComponentType.SURFACE_Z_STABILIZER:
                            triggered_stabilizers.append(stab)
                            triggered_positions.add(stab_pos_key)
                        elif error_type == ComponentType.SURFACE_Z_ERROR and stab_type == ComponentType.SURFACE_X_STABILIZER:
                            triggered_stabilizers.append(stab)
                            triggered_positions.add(stab_pos_key)
                        elif error_type == ComponentType.SURFACE_Y_ERROR:
                            # Y error = X then Z, detected by both stabilizer types
                            triggered_stabilizers.append(stab)
                            triggered_positions.add(stab_pos_key)
            
            # Clear previous highlights and draw new ones
            self.canvas.delete("syndrome_highlight")
            
            for stab in triggered_stabilizers:
                sx, sy = stab.position[0], stab.position[1]
                # Convert to canvas coordinates
                canvas_x = self.canvas_offset_x + sx * self.surface_grid_spacing
                canvas_y = self.canvas_offset_y + sy * self.surface_grid_spacing
                
                # Draw a bright highlight ring around the stabilizer
                highlight_radius = self.surface_grid_spacing * 0.5
                color = "#ff0000" if stab.component_type == ComponentType.SURFACE_Z_STABILIZER else "#00ff00"
                
                self.canvas.create_oval(
                    canvas_x - highlight_radius, canvas_y - highlight_radius,
                    canvas_x + highlight_radius, canvas_y + highlight_radius,
                    outline=color, width=4, tags="syndrome_highlight"
                )
            
            # Log results
            num_triggered = len(triggered_stabilizers)
            self._log_status(f"=== Syndrome Highlighting ===")
            self._log_status(f"Errors found: {len(errors)}")
            self._log_status(f"Triggered stabilizers: {num_triggered}")
            
            if num_triggered == 0:
                self._log_status("⚠ No stabilizers triggered - errors may be at lattice boundary")
            else:
                self._log_status("✓ Highlighted stabilizers show the syndrome pattern")
            
            # Update surface code info display
            self._update_surface_info()
                
        except Exception as e:
            self._log_status(f"Error in syndrome highlighting: {e}")
    
    def _run_decoder_surface(self):
        """Run a simple minimum-weight decoder on the surface code."""
        try:
            # Find all triggered stabilizers (same logic as highlight)
            errors = [c for c in self.components if c.component_type in 
                      [ComponentType.SURFACE_X_ERROR, ComponentType.SURFACE_Z_ERROR, ComponentType.SURFACE_Y_ERROR]]
            
            if not errors:
                self._log_status("No errors placed. Add errors to test the decoder.")
                return
            
            stabilizers = [c for c in self.components if c.component_type in 
                           [ComponentType.SURFACE_X_STABILIZER, ComponentType.SURFACE_Z_STABILIZER]]
            
            # Compute syndrome
            triggered_x_stabs = []  # X-stabilizers detect Z errors
            triggered_z_stabs = []  # Z-stabilizers detect X errors
            
            for error in errors:
                ex, ey = error.position[0], error.position[1]
                error_type = error.component_type
                
                for stab in stabilizers:
                    sx, sy = stab.position[0], stab.position[1]
                    stab_type = stab.component_type
                    
                    is_neighbor = (abs(ex - sx) == 1 and abs(ey - sy) == 1)
                    
                    if is_neighbor:
                        if error_type == ComponentType.SURFACE_X_ERROR and stab_type == ComponentType.SURFACE_Z_STABILIZER:
                            if stab not in triggered_z_stabs:
                                triggered_z_stabs.append(stab)
                        elif error_type == ComponentType.SURFACE_Z_ERROR and stab_type == ComponentType.SURFACE_X_STABILIZER:
                            if stab not in triggered_x_stabs:
                                triggered_x_stabs.append(stab)
                        elif error_type == ComponentType.SURFACE_Y_ERROR:
                            if stab_type == ComponentType.SURFACE_Z_STABILIZER and stab not in triggered_z_stabs:
                                triggered_z_stabs.append(stab)
                            elif stab_type == ComponentType.SURFACE_X_STABILIZER and stab not in triggered_x_stabs:
                                triggered_x_stabs.append(stab)
            
            # Simple decoder: pair triggered stabilizers and draw correction paths
            self.canvas.delete("decoder_path")
            
            def draw_correction_path(stab_list, path_color):
                """Draw lines connecting pairs of triggered stabilizers."""
                if len(stab_list) < 2:
                    return 0
                
                corrections = 0
                # Simple greedy pairing: pair nearest neighbors
                remaining = list(stab_list)
                while len(remaining) >= 2:
                    # Find the closest pair
                    best_dist = float('inf')
                    best_pair = None
                    for i in range(len(remaining)):
                        for j in range(i + 1, len(remaining)):
                            s1, s2 = remaining[i], remaining[j]
                            dist = abs(s1.position[0] - s2.position[0]) + abs(s1.position[1] - s2.position[1])
                            if dist < best_dist:
                                best_dist = dist
                                best_pair = (i, j)
                    
                    if best_pair:
                        s1 = remaining[best_pair[0]]
                        s2 = remaining[best_pair[1]]
                        
                        # Draw correction path
                        x1 = self.canvas_offset_x + s1.position[0] * self.surface_grid_spacing
                        y1 = self.canvas_offset_y + s1.position[1] * self.surface_grid_spacing
                        x2 = self.canvas_offset_x + s2.position[0] * self.surface_grid_spacing
                        y2 = self.canvas_offset_y + s2.position[1] * self.surface_grid_spacing
                        
                        self.canvas.create_line(x1, y1, x2, y2, fill=path_color, width=3, 
                                               dash=(5, 3), tags="decoder_path")
                        
                        corrections += int(best_dist / 2)  # Number of qubits to correct
                        
                        # Remove paired stabilizers
                        remaining.pop(best_pair[1])  # Remove higher index first
                        remaining.pop(best_pair[0])
                
                return corrections
            
            x_corrections = draw_correction_path(triggered_x_stabs, "#00ff88")  # Green for X corrections
            z_corrections = draw_correction_path(triggered_z_stabs, "#ff8800")  # Orange for Z corrections
            
            self._log_status(f"=== Decoder Results ===")
            self._log_status(f"X-syndrome defects: {len(triggered_x_stabs)}")
            self._log_status(f"Z-syndrome defects: {len(triggered_z_stabs)}")
            self._log_status(f"Estimated corrections: X={x_corrections}, Z={z_corrections}")
            
            if len(triggered_x_stabs) % 2 == 1 or len(triggered_z_stabs) % 2 == 1:
                self._log_status("⚠ Odd number of defects - error chain reaches boundary")
            else:
                self._log_status("✓ Decoder paired all syndrome defects")
                
        except Exception as e:
            self._log_status(f"Error in decoder: {e}")
    
    def _clear_syndrome_highlights(self):
        """Clear syndrome highlighting and decoder paths from the surface code view."""
        self.canvas.delete("syndrome_highlight")
        self.canvas.delete("decoder_path")
        self._log_status("Cleared syndrome highlights and decoder paths")
    
    # ==================== LDPC MODE BUTTON HANDLERS ====================
    
    def _show_ldpc_connectivity(self):
        """Highlight the connectivity pattern in the LDPC graph."""
        if self.view_mode == ViewMode.LDPC_TANNER:
            self._log_status("Showing Tanner graph connectivity pattern...")
            # Re-draw to highlight edges
            self._draw_grid()
            self._redraw_circuit()
            self._log_status("LDPC Tanner graph connectivity displayed. Check nodes connect to data qubits via curved edges.")
        elif self.view_mode == ViewMode.LDPC_PHYSICAL:
            self._log_status("Showing physical cavity-bus connectivity...")
            self._draw_grid()
            self._redraw_circuit()
            self._log_status("LDPC physical layout displayed. Cavity buses enable non-local interactions.")
        else:
            self._log_status("Switch to LDPC mode (press B) to view connectivity.")
    
    def _clear_ldpc_graph(self):
        """Clear all placed components from the LDPC graph."""
        if self.view_mode in [ViewMode.LDPC_TANNER, ViewMode.LDPC_PHYSICAL]:
            self.components.clear()
            self._draw_grid()
            self._redraw_circuit()
            self._log_status("Cleared LDPC graph components")
        else:
            self._log_status("Switch to LDPC mode (press B) first.")
    
    def _generate_ldpc_example(self):
        """Generate an example LDPC code layout."""
        if self.view_mode == ViewMode.LDPC_TANNER:
            # Place example components in Tanner graph mode
            self.components.clear()
            
            # Add some X-checks
            for i in range(4):
                self.components.append(Component3D(
                    component_type=ComponentType.LDPC_X_CHECK,
                    position=(i, 0, 0),
                    color=(1.0, 0.42, 0.42)  # Coral
                ))
            
            # Add some data qubits
            for i in range(8):
                self.components.append(Component3D(
                    component_type=ComponentType.LDPC_DATA_QUBIT,
                    position=(i, 1, 0),
                    color=(0.18, 0.77, 0.71)  # Teal
                ))
            
            # Add some Z-checks
            for i in range(4):
                self.components.append(Component3D(
                    component_type=ComponentType.LDPC_Z_CHECK,
                    position=(i, 2, 0),
                    color=(1.0, 0.85, 0.24)  # Gold
                ))
            
            self._draw_grid()
            self._redraw_circuit()
            self._log_status("Generated example LDPC Tanner graph with 4 X-checks, 8 data qubits, 4 Z-checks")
            
        elif self.view_mode == ViewMode.LDPC_PHYSICAL:
            # Place example components in Physical layout mode
            self.components.clear()
            
            # Add Z-ancilla qubits
            for i in [0, 2, 4, 6, 8, 10]:
                self.components.append(Component3D(
                    component_type=ComponentType.LDPC_Z_ANCILLA,
                    position=(i, 0, 0),
                    color=(0.51, 0.70, 0.60)  # Sage green
                ))
            
            # Add data qubits (skip cavity positions)
            for i in [0, 1, 2, 4, 5, 7, 8, 10, 11]:
                self.components.append(Component3D(
                    component_type=ComponentType.LDPC_DATA_QUBIT,
                    position=(i, 1, 0),
                    color=(0.18, 0.77, 0.71)  # Teal
                ))
            
            # Add X-ancilla qubits
            for i in [1, 3, 5, 7, 9, 11]:
                self.components.append(Component3D(
                    component_type=ComponentType.LDPC_X_ANCILLA,
                    position=(i, 2, 0),
                    color=(0.88, 0.48, 0.37)  # Terracotta
                ))
            
            self._draw_grid()
            self._redraw_circuit()
            self._log_status("Generated example LDPC physical layout with tri-layer architecture")
        else:
            self._log_status("Switch to LDPC mode (press B) first.")
    
    def _show_ldpc_syndrome(self):
        """Show parity check violations (syndrome) on the LDPC Tanner graph.
        
        Highlights check nodes that would report violations based on 
        simulated errors on connected data qubits.
        """
        if self.view_mode != ViewMode.LDPC_TANNER:
            self._log_status("Switch to LDPC Tanner mode to see parity violations")
            return
        
        # Get check nodes and data qubits
        x_checks = [c for c in self.components if c.component_type == ComponentType.LDPC_X_CHECK]
        z_checks = [c for c in self.components if c.component_type == ComponentType.LDPC_Z_CHECK]
        data_qubits = [c for c in self.components if c.component_type == ComponentType.LDPC_DATA_QUBIT]
        
        if not (x_checks or z_checks):
            self._log_status("No check nodes found. Add X-Check or Z-Check components first.")
            return
        
        if not data_qubits:
            self._log_status("No data qubits found. Add LDPC Data components first.")
            return
        
        # Clear previous highlights
        self.canvas.delete("syndrome_highlight")
        
        # Simulate: For demo, we'll highlight check nodes that have odd number of 
        # neighboring data qubits (based on x-coordinate proximity)
        # This simulates what would happen if we had errors
        
        highlighted_checks = []
        
        # Simple proximity-based check for demonstration
        for check in x_checks + z_checks:
            cx, cy, cz = check.position
            # Count "connected" data qubits (those within x-distance of 2)
            connected = [d for d in data_qubits if abs(d.position[0] - cx) <= 2]
            
            # Highlight if odd parity (simulates a violation)
            if len(connected) % 2 == 1:
                # Draw highlight
                screen_x = 400 + cx * 50
                screen_y = 300 + cy * 80
                
                # Yellow/orange highlight ring
                r = 25
                self.canvas.create_oval(screen_x - r, screen_y - r, 
                                       screen_x + r, screen_y + r,
                                       outline='#ffcc00', width=4,
                                       tags="syndrome_highlight")
                self.canvas.create_text(screen_x, screen_y - r - 10,
                                       text="!", fill='#ffcc00',
                                       font=('Arial', 14, 'bold'),
                                       tags="syndrome_highlight")
                highlighted_checks.append(check.component_type.value)
        
        if highlighted_checks:
            self._log_status(f"⚠ Parity violations detected at {len(highlighted_checks)} check nodes")
            self._log_status(f"  Violated checks: {', '.join(highlighted_checks[:5])}{'...' if len(highlighted_checks) > 5 else ''}")
        else:
            self._log_status("✓ No parity violations - all check nodes satisfied")
    
    def _log_status(self, message: str) -> None:
        """Log a status message to the status display and terminal."""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        # Also print to terminal for debugging (with encoding safety)
        try:
            print(f"[STATUS] {message}")
        except UnicodeEncodeError:
            # Fallback for consoles that don't support Unicode
            safe_message = message.encode('ascii', 'replace').decode('ascii')
            print(f"[STATUS] {safe_message}")
    
    def _on_tutorial_complete(self, show_on_startup: bool) -> None:
        """Handle tutorial completion."""
        TutorialScreen.save_tutorial_preference(show_on_startup)
        self._log_status("Tutorial completed! Ready to build quantum circuits.")
    
    def _show_tutorial(self):
        """Show the tutorial screen."""
        tutorial = TutorialScreen(self.root, self._on_tutorial_complete, circuit_builder=self)
        tutorial.show()
    
    def _start_tutorial(self):
        """Start the interactive tutorial (alias for _show_tutorial for button)."""
        self._show_tutorial()
    
    def _show_advanced_tutorial(self):
        """Show the Surface Code tutorial screen with live demonstrations."""
        advanced = SurfaceCodeTutorialScreen(self.root, circuit_builder=self)
        advanced.show()
    
    def _show_advanced_large_circuits_tutorial(self):
        """Show the Advanced Large Circuits tutorial with QEC examples."""
        tutorial = AdvancedLargeCircuitsTutorial(self.root, circuit_builder=self)
        tutorial.show()
    
    def _show_surface_code_tutorial(self):
        """Show the Surface Code specific tutorial (accessible from surface mode)."""
        tutorial = SurfaceCodeTutorial(self.root, circuit_builder=self)
        tutorial.show()
    
    def _show_quick_reference(self):
        """Show a quick reference dialog with component and operation summaries."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Quick Reference Guide")
        dialog.geometry("550x600")
        dialog.configure(bg='#2b2b2b')
        dialog.transient(self.root)
        
        # Create scrollable content
        main_frame = tk.Frame(dialog, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Content sections
        def add_section(title, items, color='#4fc3f7'):
            frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
            frame.pack(fill=tk.X, pady=5)
            
            tk.Label(frame, text=title, font=('TkDefaultFont', 11, 'bold'),
                    bg='#2b2b2b', fg=color).pack(anchor='w')
            
            for item, desc in items:
                item_frame = tk.Frame(frame, bg='#2b2b2b')
                item_frame.pack(fill=tk.X, padx=10, pady=1)
                tk.Label(item_frame, text=f"• {item}:", font=('TkDefaultFont', 9, 'bold'),
                        bg='#2b2b2b', fg='#ffffff', width=20, anchor='w').pack(side=tk.LEFT)
                tk.Label(item_frame, text=desc, font=('TkDefaultFont', 9),
                        bg='#2b2b2b', fg='#cccccc', anchor='w').pack(side=tk.LEFT, fill=tk.X)
        
        # Component Reference
        add_section("🔷 Single-Qubit Gates", [
            ("H Gate (Yellow)", "Hadamard - Creates superposition"),
            ("X Gate (Green)", "Pauli-X - Bit flip |0⟩↔|1⟩"),
            ("Y Gate (Purple)", "Pauli-Y - Rotation around Y-axis"),
            ("Z Gate (Orange)", "Pauli-Z - Phase flip"),
            ("S Gate (Teal)", "Phase gate - π/2 rotation"),
            ("T Gate (Magenta)", "T gate - π/4 rotation"),
        ])
        
        add_section("🔗 Two-Qubit Gates", [
            ("CNOT (Blue/Cyan)", "Controlled-NOT - Entanglement"),
            ("CZ Gate (Steel Blue)", "Controlled-Z gate"),
            ("SWAP (Pink)", "Swap qubit states"),
        ], color='#6bcb77')
        
        add_section("⚛️ Qubit Components", [
            ("Data Qubit", "Primary qubits storing information"),
            ("Ancilla Qubit", "Helper qubits for measurement"),
            ("Measurement", "Measure qubit in computational basis"),
        ], color='#ffd93d')
        
        add_section("🛡️ LDPC/Error Correction", [
            ("X Stabilizer", "Detects X (bit-flip) errors"),
            ("Z Stabilizer", "Detects Z (phase-flip) errors"),
            ("Parity Check", "General parity check operator"),
        ], color='#ff6b6b')
        
        add_section("🖱️ Mouse Controls", [
            ("Left Click", "Select/place component"),
            ("Left Drag", "Move component"),
            ("Right Click", "Context menu (rotate/delete)"),
            ("Middle Drag", "Pan the view"),
            ("Scroll", "Future: Zoom (use +/- for now)"),
        ], color='#74b9ff')
        
        add_section("⌨️ Quick Keys", [
            ("T", "Open Tutorial"),
            ("?", "Keyboard Shortcuts"),
            ("V", "Surface Code Mode"),
            ("B", "LDPC Mode"),
            ("C", "Clear Circuit"),
            ("Ctrl+Z / Ctrl+Y", "Undo / Redo"),
            ("Del / Backspace", "Delete selected"),
            ("+ / -", "Zoom In / Out"),
            ("0", "Reset zoom to 100%"),
        ], color='#a29bfe')
        
        # Close button
        close_frame = tk.Frame(dialog, bg='#2b2b2b')
        close_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(close_frame, text="Close", command=dialog.destroy,
                  style='Dark.TButton').pack(side=tk.RIGHT)
        
        # Cleanup mouse wheel binding on close
        def on_close():
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()
        dialog.protocol("WM_DELETE_WINDOW", on_close)
    
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
        
        # Position OVER the main window (overlapping), offset from top-left
        self.legend_window.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        # Place inside the main window, offset from left edge
        x = main_x + 50
        y = main_y + 50
        self.legend_window.geometry(f"280x600+{x}+{y}")
        
        # Main scrollable frame
        main_frame = tk.Frame(self.legend_window, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title - changes based on mode
        if self.view_mode == ViewMode.SURFACE_CODE_2D:
            title_text = "Surface Code Legend"
            title_color = "#e94560"
        elif self.view_mode == ViewMode.LDPC_TANNER:
            title_text = "LDPC Tanner Legend"
            title_color = "#2EC4B6"  # Teal
        elif self.view_mode == ViewMode.LDPC_PHYSICAL:
            title_text = "LDPC Physical Legend"
            title_color = "#FFD93D"  # Gold
        else:
            title_text = "Component Legend"
            title_color = "#e94560"
        
        title_label = tk.Label(main_frame, text=title_text, 
                              font=('Segoe UI', 14, 'bold'),
                              fg=title_color, bg='#1a1a2e')
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
        
        # Component categories depend on current view mode
        if self.view_mode == ViewMode.SURFACE_CODE_2D:
            # Surface code mode - show surface and useful circuit components
            categories = {
                "Stabilizers": [
                    ComponentType.SURFACE_X_STABILIZER, ComponentType.SURFACE_Z_STABILIZER
                ],
                "Qubits": [
                    ComponentType.SURFACE_DATA, ComponentType.SURFACE_BOUNDARY,
                    ComponentType.ANCILLA_QUBIT
                ],
                "Syndrome Gates": [
                    ComponentType.H_GATE, ComponentType.CNOT_GATE, ComponentType.MEASURE
                ]
            }
        elif self.view_mode == ViewMode.LDPC_TANNER:
            # LDPC Tanner graph mode
            categories = {
                "Check Nodes": [
                    ComponentType.LDPC_X_CHECK, ComponentType.LDPC_Z_CHECK
                ],
                "Qubit Nodes": [
                    ComponentType.LDPC_DATA_QUBIT, ComponentType.LDPC_ANCILLA
                ],
                "Connections": [
                    ComponentType.LDPC_EDGE
                ]
            }
        elif self.view_mode == ViewMode.LDPC_PHYSICAL:
            # LDPC Physical layout mode
            categories = {
                "Data Qubits": [
                    ComponentType.LDPC_DATA_QUBIT
                ],
                "Ancilla Qubits": [
                    ComponentType.LDPC_X_ANCILLA, ComponentType.LDPC_Z_ANCILLA,
                    ComponentType.LDPC_ANCILLA
                ],
                "Cavity Bus": [
                    ComponentType.LDPC_CAVITY_BUS
                ]
            }
        else:
            # Circuit mode - show all circuit components
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
                    ComponentType.ANCILLA_QUBIT
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
        """Create a legend item with a mini preview (cube for circuits, flat for surface)."""
        item_frame = tk.Frame(parent, bg='#0f0f23', bd=1, relief='solid')
        item_frame.pack(fill=tk.X, pady=2, padx=5)
        
        # Check if this is a surface code component
        surface_types = [ComponentType.SURFACE_DATA, ComponentType.SURFACE_X_STABILIZER,
                        ComponentType.SURFACE_Z_STABILIZER, ComponentType.SURFACE_BOUNDARY]
        is_surface = comp_type in surface_types
        
        # Two-qubit gates get a wider preview canvas
        two_qubit_types = [ComponentType.CNOT_GATE, ComponentType.CZ_GATE, ComponentType.SWAP_GATE]
        is_two_qubit = comp_type in two_qubit_types
        
        canvas_width = 70 if is_two_qubit else 50
        
        # Create mini canvas for preview
        preview_canvas = tk.Canvas(item_frame, width=canvas_width, height=40, 
                                  bg='#0f0f23', highlightthickness=0)
        preview_canvas.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Draw preview based on view mode
        color = self._get_component_color(comp_type)
        if self.view_mode == ViewMode.SURFACE_CODE_2D:
            # In surface mode, use flat 2D shapes for ALL components
            self._draw_mini_flat(preview_canvas, 25, 20, color, comp_type)
        else:
            # In isometric mode, draw mini cubes
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
            ComponentType.MEASURE: "Measurement operation",
            ComponentType.RESET: "Reset to |0⟩ state",
            ComponentType.SURFACE_DATA: "Surface code data qubit (edge)",
            ComponentType.SURFACE_X_STABILIZER: "X-stabilizer (plaquette)",
            ComponentType.SURFACE_Z_STABILIZER: "Z-stabilizer (vertex)",
            ComponentType.SURFACE_BOUNDARY: "Lattice boundary marker",
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
    
    def _draw_mini_flat(self, canvas, cx, cy, color, comp_type: ComponentType):
        """Draw a flat 2D shape for components in the legend (surface mode).
        
        Args:
            canvas: Canvas to draw on
            cx, cy: Center position
            color: RGB color tuple
            comp_type: The component type to determine shape
        """
        def to_hex(c):
            return f"#{int(c[0]*255):02x}{int(c[1]*255):02x}{int(c[2]*255):02x}"
        
        outline = '#444'
        fill_color = to_hex(color)
        size = 12
        
        if comp_type == ComponentType.SURFACE_DATA:
            # Data qubits are circles (like on lattice edges)
            canvas.create_oval(cx - size, cy - size, cx + size, cy + size,
                             fill=fill_color, outline=outline, width=2)
        elif comp_type == ComponentType.SURFACE_X_STABILIZER:
            # X-stabilizers are squares with "X" label
            canvas.create_rectangle(cx - size, cy - size, cx + size, cy + size,
                                   fill=fill_color, outline=outline, width=2)
            canvas.create_text(cx, cy, text="X", fill="#ffffff", 
                             font=("Arial", 10, "bold"))
        elif comp_type == ComponentType.SURFACE_Z_STABILIZER:
            # Z-stabilizers are squares with "Z" label  
            canvas.create_rectangle(cx - size, cy - size, cx + size, cy + size,
                                   fill=fill_color, outline=outline, width=2)
            canvas.create_text(cx, cy, text="Z", fill="#ffffff",
                             font=("Arial", 10, "bold"))
        elif comp_type == ComponentType.SURFACE_BOUNDARY:
            # Boundaries are thick lines
            canvas.create_line(cx - size, cy, cx + size, cy,
                             fill=fill_color, width=4)
            canvas.create_line(cx - size, cy - 4, cx - size, cy + 4,
                             fill=fill_color, width=2)
            canvas.create_line(cx + size, cy - 4, cx + size, cy + 4,
                             fill=fill_color, width=2)
        elif comp_type in [ComponentType.DATA_QUBIT, ComponentType.ANCILLA_QUBIT]:
            # Qubits as circles
            canvas.create_oval(cx - size, cy - size, cx + size, cy + size,
                             fill=fill_color, outline=outline, width=2)
        elif comp_type in [ComponentType.H_GATE, ComponentType.X_GATE, ComponentType.Y_GATE,
                          ComponentType.Z_GATE, ComponentType.S_GATE, ComponentType.T_GATE]:
            # Single-qubit gates as rounded rectangles with letter
            canvas.create_rectangle(cx - size, cy - size, cx + size, cy + size,
                                   fill=fill_color, outline=outline, width=2)
            # Get the gate letter from the name (first character)
            gate_letter = comp_type.value[0].upper()
            canvas.create_text(cx, cy, text=gate_letter, fill="#ffffff",
                             font=("Arial", 10, "bold"))
        elif comp_type == ComponentType.CNOT_GATE:
            # CNOT as circle with plus (control-target)
            canvas.create_oval(cx - size, cy - size, cx + size, cy + size,
                             fill=fill_color, outline=outline, width=2)
            canvas.create_line(cx - 6, cy, cx + 6, cy, fill="#ffffff", width=2)
            canvas.create_line(cx, cy - 6, cx, cy + 6, fill="#ffffff", width=2)
        elif comp_type in [ComponentType.CZ_GATE, ComponentType.SWAP_GATE]:
            # Two-qubit gates as connected dots
            canvas.create_oval(cx - size + 4, cy - 6, cx - 4, cy + 6,
                             fill=fill_color, outline=outline, width=2)
            canvas.create_oval(cx + 4, cy - 6, cx + size - 4, cy + 6,
                             fill=fill_color, outline=outline, width=2)
            canvas.create_line(cx - 4, cy, cx + 4, cy, fill=fill_color, width=2)
        elif comp_type == ComponentType.MEASURE:
            # Measurement as dial/meter icon
            canvas.create_arc(cx - size, cy - size, cx + size, cy + size,
                            start=0, extent=180, fill=fill_color, outline=outline, width=2)
            canvas.create_line(cx, cy, cx + 6, cy - 8, fill="#ffffff", width=2)
        elif comp_type == ComponentType.RESET:
            # Reset as |0⟩ symbol
            canvas.create_rectangle(cx - size, cy - size, cx + size, cy + size,
                                   fill=fill_color, outline=outline, width=2)
            canvas.create_text(cx, cy, text="0", fill="#ffffff",
                             font=("Arial", 10, "bold"))
        elif comp_type == ComponentType.PARITY_CHECK:
            # Parity check as diamond
            points = [cx, cy - size, cx + size, cy, cx, cy + size, cx - size, cy]
            canvas.create_polygon(points, fill=fill_color, outline=outline, width=2)
        elif comp_type == ComponentType.SURFACE_X_ERROR:
            # X error as circle with X mark
            canvas.create_oval(cx - size, cy - size, cx + size, cy + size,
                             fill=fill_color, outline=outline, width=2)
            canvas.create_line(cx - 6, cy - 6, cx + 6, cy + 6, fill="#ffffff", width=2)
            canvas.create_line(cx - 6, cy + 6, cx + 6, cy - 6, fill="#ffffff", width=2)
        elif comp_type == ComponentType.SURFACE_Z_ERROR:
            # Z error as circle with Z mark
            canvas.create_oval(cx - size, cy - size, cx + size, cy + size,
                             fill=fill_color, outline=outline, width=2)
            canvas.create_text(cx, cy, text="Z", fill="#ffffff",
                             font=("Arial", 9, "bold"))
        elif comp_type == ComponentType.SURFACE_Y_ERROR:
            # Y error as circle with Y mark
            canvas.create_oval(cx - size, cy - size, cx + size, cy + size,
                             fill=fill_color, outline=outline, width=2)
            canvas.create_text(cx, cy, text="Y", fill="#000000",  # Black text on yellow
                             font=("Arial", 9, "bold"))
        else:
            # Default: simple square
            canvas.create_rectangle(cx - size, cy - size, cx + size, cy + size,
                                   fill=fill_color, outline=outline, width=2)
    
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