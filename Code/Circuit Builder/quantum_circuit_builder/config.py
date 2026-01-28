"""
Configuration constants and settings for the Quantum Circuit Builder.

This module centralizes all magic numbers, colors, and configuration values
to make the codebase more maintainable and customizable.
Author: Jeffrey Morais"""

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class GridConfig:
    """Configuration for the circuit grid."""
    min_coord: int = -10
    max_coord: int = 10
    default_scale: float = 30.0
    default_offset_x: int = 500
    default_offset_y: int = 350
    
    # Surface code lattice
    surface_code_distance: int = 5
    
    # LDPC grid
    ldpc_tanner_rows: int = 4
    ldpc_tanner_cols: int = 6
    ldpc_physical_qubits_per_row: int = 12


@dataclass
class UIConfig:
    """Configuration for UI elements."""
    # Click tolerances (in pixels)
    click_tolerance: int = 50
    ldpc_click_tolerance: int = 40
    
    # Node sizes
    data_qubit_radius: int = 18
    check_node_size: int = 14
    
    # Tutorial window
    tutorial_width: int = 650
    tutorial_height: int = 520
    
    # Legend window
    legend_width: int = 280
    legend_height: int = 600


@dataclass
class SimulationConfig:
    """Configuration for quantum simulation."""
    default_shots: int = 1024
    bp_max_iterations: int = 10
    bp_convergence_threshold: float = 1e-6
    parity_connection_distance: int = 2


# ==================== COLOR PALETTES ====================

# LDPC Color Palette (split-complementary scheme)
LDPC_COLORS: Dict[str, str] = {
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


@dataclass
class ColorPalette:
    """Color palette for the dark theme UI."""
    # Background colors
    bg_primary: str = '#2b2b2b'
    bg_secondary: str = '#1e1e1e'
    bg_tertiary: str = '#1a1a2e'
    bg_panel: str = '#16213e'
    bg_input: str = '#0f0f23'
    
    # Text colors
    text_primary: str = '#ffffff'
    text_secondary: str = '#cccccc'
    text_muted: str = '#888888'
    text_disabled: str = '#666666'
    
    # Accent colors
    accent_primary: str = '#e94560'
    accent_secondary: str = '#00cc66'
    accent_warning: str = '#ff9f43'
    accent_info: str = '#74b9ff'
    
    # Grid colors
    grid_line: str = '#505050'
    grid_boundary: str = '#707070'
    
    # Selection
    selection: str = '#ffff00'
    highlight: str = '#ff6b8a'
    
    # Surface code specific
    surface_x_stab_bg: str = '#4a2a2a'
    surface_z_stab_bg: str = '#2a2a4a'
    surface_data_bg: str = '#555555'
    
    # LDPC mode indicators
    ldpc_tanner_accent: str = '#2EC4B6'
    ldpc_physical_accent: str = '#FFD93D'


# Component color mappings (RGB tuples, 0-1 range)
COMPONENT_COLORS: Dict[str, Tuple[float, float, float]] = {
    # Single qubit gates - distinct blue shades
    'X_GATE': (0.1, 0.3, 0.9),
    'Z_GATE': (0.2, 0.5, 0.7),
    'Y_GATE': (0.4, 0.7, 1.0),
    'H_GATE': (0.0, 0.2, 0.6),
    'S_GATE': (0.3, 0.4, 0.8),
    'T_GATE': (0.5, 0.6, 0.9),
    
    # Two qubit gates - distinct purple/magenta shades
    'CNOT_GATE': (0.8, 0.2, 0.6),
    'CZ_GATE': (0.6, 0.1, 0.8),
    'SWAP_GATE': (0.9, 0.4, 0.7),
    
    # LDPC components (circuit mode) - distinct green/orange shades
    'PARITY_CHECK': (0.9, 0.5, 0.1),
    'DATA_QUBIT': (0.2, 0.9, 0.3),
    'ANCILLA_QUBIT': (0.6, 0.8, 0.1),
    
    # Measurement - distinct red shades
    'MEASURE': (0.9, 0.1, 0.1),
    'RESET': (0.7, 0.3, 0.2),
    
    # Surface code components
    'SURFACE_DATA': (0.4, 0.8, 0.9),
    'SURFACE_X_STABILIZER': (0.91, 0.27, 0.38),
    'SURFACE_Z_STABILIZER': (0.42, 0.18, 0.36),
    'SURFACE_BOUNDARY': (0.9, 0.6, 0.2),
    'SURFACE_X_ERROR': (1.0, 0.2, 0.2),
    'SURFACE_Z_ERROR': (0.2, 0.2, 1.0),
    'SURFACE_Y_ERROR': (0.9, 0.9, 0.1),
    
    # LDPC specific components
    'LDPC_DATA_QUBIT': (0.18, 0.77, 0.71),
    'LDPC_X_CHECK': (1.0, 0.42, 0.42),
    'LDPC_Z_CHECK': (1.0, 0.85, 0.24),
    'LDPC_ANCILLA': (0.61, 0.37, 0.90),
    'LDPC_X_ANCILLA': (0.88, 0.48, 0.37),
    'LDPC_Z_ANCILLA': (0.51, 0.70, 0.60),
    'LDPC_EDGE': (0.42, 0.45, 0.50),
    'LDPC_CAVITY_BUS': (0.24, 0.35, 0.50),
}


@dataclass
class Config:
    """Master configuration containing all sub-configurations."""
    grid: GridConfig = field(default_factory=GridConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    colors: ColorPalette = field(default_factory=ColorPalette)
    
    # Feature flags
    show_tutorial_on_startup: bool = True
    enable_qiskit_simulation: bool = True
    enable_ldpc_mode: bool = True
    
    # File paths
    tutorial_config_filename: str = '.tutorial_config.json'
    
    @classmethod
    def get_component_color(cls, component_name: str) -> Tuple[float, float, float]:
        """Get RGB color tuple for a component type."""
        return COMPONENT_COLORS.get(component_name, (0.5, 0.5, 0.5))


# Global default configuration instance
DEFAULT_CONFIG = Config()
