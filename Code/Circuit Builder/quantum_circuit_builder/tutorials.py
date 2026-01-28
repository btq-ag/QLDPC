"""
Tutorial screens for the Quantum Circuit Builder.

This module provides interactive tutorials that guide users through:
- Basic component placement and circuit building
- Surface code concepts and stabilizer measurements
- LDPC code structures and non-local connectivity
Author: Jeffrey Morais"""

import tkinter as tk
from tkinter import ttk
import json
import os
from typing import Dict, List, Any, Optional, Callable, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .main import CircuitBuilder3D


class BaseTutorialScreen(ABC):
    """
    Abstract base class for tutorial screens.
    
    Provides common functionality for multi-step tutorials with:
    - Styled text display with color-coded keywords
    - Progress tracking
    - Navigation controls
    - Demo component placement
    """
    
    # Color scheme for highlighted keywords (shared across all tutorials)
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
    
    def __init__(self, parent: tk.Tk, circuit_builder: 'CircuitBuilder3D' = None,
                 on_complete_callback: Callable[[bool], None] = None):
        """
        Initialize the tutorial screen.
        
        Args:
            parent: Parent tkinter window
            circuit_builder: Reference to the CircuitBuilder3D instance
            on_complete_callback: Function to call when tutorial is completed
        """
        self.parent = parent
        self.circuit_builder = circuit_builder
        self.on_complete = on_complete_callback
        self.current_step = 0
        self.tutorial_window: Optional[tk.Toplevel] = None
        self.demo_components: List = []
        
        # UI elements (set by subclasses)
        self.title_label: Optional[tk.Label] = None
        self.step_label: Optional[tk.Label] = None
        self.progress_bar: Optional[tk.Frame] = None
        self.content_text: Optional[tk.Text] = None
        self.prev_btn: Optional[tk.Button] = None
        self.next_btn: Optional[tk.Button] = None
        
        # Must be set by subclasses
        self.steps: List[Dict[str, Any]] = []
    
    @property
    @abstractmethod
    def window_title(self) -> str:
        """Title for the tutorial window."""
        pass
    
    @property
    @abstractmethod
    def window_geometry(self) -> str:
        """Window geometry string (e.g., '650x520')."""
        pass
    
    @property
    @abstractmethod
    def accent_color(self) -> str:
        """Primary accent color for this tutorial."""
        pass
    
    @abstractmethod
    def _create_tutorial_steps(self) -> List[Dict[str, Any]]:
        """Create and return the tutorial step definitions."""
        pass
    
    @abstractmethod
    def _execute_demo(self, action: str):
        """Execute a demo action for the current step."""
        pass
    
    def show(self):
        """Display the tutorial window."""
        self.steps = self._create_tutorial_steps()
        
        self.tutorial_window = tk.Toplevel(self.parent)
        self.tutorial_window.title(self.window_title)
        self.tutorial_window.geometry(self.window_geometry)
        self.tutorial_window.configure(bg='#1a1a2e')
        self.tutorial_window.attributes('-topmost', False)
        
        # Position to the left of screen
        self.tutorial_window.update_idletasks()
        x = 50
        y = (self.tutorial_window.winfo_screenheight() - 520) // 2
        geo = self.window_geometry.split('x')
        self.tutorial_window.geometry(f"{geo[0]}x{geo[1]}+{x}+{y}")
        
        self._setup_ui()
        self._update_display()
        
        self.tutorial_window.protocol("WM_DELETE_WINDOW", self._close_tutorial)
    
    def _setup_ui(self):
        """Set up the common UI elements."""
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
            fg=self.accent_color,
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
        
        self.progress_bar = tk.Frame(self.progress_bg, bg=self.accent_color, height=8)
        self.progress_bar.place(x=0, y=0, relheight=1, relwidth=0)
        
        # Navigation buttons - pack at bottom first
        self.nav_frame = tk.Frame(self.main_frame, bg='#1a1a2e')
        self.nav_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        self._setup_nav_buttons()
        
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
        
        # Configure text tags for colors
        for tag_name, color in self.COLORS.items():
            self.content_text.tag_configure(tag_name, foreground=color)
        self.content_text.tag_configure('normal', foreground='#cccccc')
    
    def _setup_nav_buttons(self):
        """Set up navigation buttons. Override for custom buttons."""
        # Close/Skip button
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
            bg=self.accent_color,
            activeforeground='#ffffff',
            activebackground=self._lighten_color(self.accent_color),
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
        
        # Change next button text on last step
        if self.current_step == len(self.steps) - 1:
            self.next_btn.config(text="Finish ✓", bg='#27ae60')
        else:
            self.next_btn.config(text="Next →", bg=self.accent_color)
        
        # Execute demo action
        if 'demo_action' in step_data:
            self._execute_demo(step_data['demo_action'])
    
    def _next_step(self):
        """Go to the next tutorial step or finish."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._update_display()
        else:
            self._close_tutorial()
    
    def _prev_step(self):
        """Go to the previous tutorial step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_display()
    
    def _close_tutorial(self):
        """Close the tutorial and clean up."""
        self._clear_demo_components()
        
        if self.circuit_builder:
            self.circuit_builder._redraw_circuit()
        
        if self.on_complete:
            self.on_complete(True)
        
        self.tutorial_window.destroy()
    
    def _clear_demo_components(self):
        """Remove all demo components from the circuit."""
        if not self.circuit_builder:
            return
        
        for comp in self.demo_components:
            if comp in self.circuit_builder.components:
                self.circuit_builder.components.remove(comp)
        
        self.demo_components = []
        if self.circuit_builder:
            self.circuit_builder._redraw_circuit()
    
    @staticmethod
    def _lighten_color(hex_color: str) -> str:
        """Lighten a hex color for hover effects."""
        if not hex_color.startswith('#'):
            return hex_color
        
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Lighten by 20%
        r = min(255, int(r * 1.2))
        g = min(255, int(g * 1.2))
        b = min(255, int(b * 1.2))
        
        return f"#{r:02x}{g:02x}{b:02x}"


# Tutorial preference management
TUTORIAL_CONFIG_FILENAME = '.tutorial_config.json'


def should_show_tutorial() -> bool:
    """Check if tutorial should be shown based on saved preferences."""
    config_path = os.path.join(os.path.dirname(__file__), TUTORIAL_CONFIG_FILENAME)
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('show_tutorial', True)
    except:
        pass
    return True


def save_tutorial_preference(show_on_startup: bool):
    """Save the tutorial display preference."""
    config_path = os.path.join(os.path.dirname(__file__), TUTORIAL_CONFIG_FILENAME)
    try:
        with open(config_path, 'w') as f:
            json.dump({'show_tutorial': show_on_startup}, f)
    except:
        pass
