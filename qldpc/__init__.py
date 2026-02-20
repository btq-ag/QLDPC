"""
qldpc - Interactive Python Toolkit for Quantum LDPC Error Correction

Drag-and-drop 3D circuit builder with surface code and Tanner graph modes,
real-time belief propagation simulation, cavity QED parameter exploration,
and threshold analysis.

Author: Jeffrey Morais
"""

from qldpc.components import ComponentType, Component3D, ViewMode
from qldpc.config import Config, GridConfig, ColorPalette, LDPC_COLORS
from qldpc.processor import QuantumLDPCProcessor

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
]
