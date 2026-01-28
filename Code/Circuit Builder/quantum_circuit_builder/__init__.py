"""
Quantum LDPC Circuit Builder - Interactive 3D Circuit Construction Platform

This package provides a comprehensive GUI application for building and simulating
quantum circuits with support for LDPC codes, surface codes, and standard quantum gates.

Modules:
    components: Component types and 3D component data structures
    config: Application configuration and constants
    processor: Quantum computation backend
    renderers: Isometric, surface code, and LDPC rendering
    tutorials: Interactive tutorial screens
    ui: User interface components
    main: Main application class
"""

from .components import ComponentType, Component3D, ViewMode
from .config import Config, GridConfig, ColorPalette, LDPC_COLORS
from .processor import QuantumLDPCProcessor
from .main import CircuitBuilder3D

__version__ = "1.0.0"
__author__ = "Jeffrey Morais"

__all__ = [
    "ComponentType",
    "Component3D", 
    "ViewMode",
    "Config",
    "GridConfig",
    "ColorPalette",
    "LDPC_COLORS",
    "QuantumLDPCProcessor",
    "CircuitBuilder3D",
]
