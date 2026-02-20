"""
qldpc.builder - Interactive 3D Quantum Circuit Builder

The main GUI application for building and simulating quantum circuits
with isometric 3D, surface code, and LDPC visualization modes.
"""

from qldpc.builder.app import CircuitBuilder3D, main

__all__ = ["CircuitBuilder3D", "main"]
