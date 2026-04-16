"""
qldpc - Interactive Python Toolkit for Quantum LDPC Error Correction

Drag-and-drop 3D circuit builder with surface code and Tanner graph modes,
real-time belief propagation simulation, cavity QED parameter exploration,
and threshold analysis.

Author: Jeffrey Morais
"""

from qldpc.codes import (
    bivariateBicycleCode,
    buildSyndromeCircuit,
    codeDistance,
    codeParameters,
    fiberBundleCode,
    hypergraphProduct,
    logicalOperators,
    repetitionCode,
    scheduledSyndromeCircuit,
    shorCode,
    steaneCode,
    validateCss,
)
from qldpc.components import Component3D, ComponentType, ViewMode
from qldpc.config import LDPC_COLORS, ColorPalette, Config, GridConfig
from qldpc.decoders import (
    BeliefPropagationDecoder,
    MinSumDecoder,
    OSDDecoder,
    SlidingWindowDecoder,
)
from qldpc.noise import (
    bitflipChannel,
    depolarizingChannel,
    depolarizingErrors,
    phaseflipChannel,
)
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
    "BeliefPropagationDecoder",
    "MinSumDecoder",
    "OSDDecoder",
    "SlidingWindowDecoder",
    "validateCss",
    "steaneCode",
    "shorCode",
    "repetitionCode",
    "hypergraphProduct",
    "bivariateBicycleCode",
    "fiberBundleCode",
    "codeParameters",
    "codeDistance",
    "logicalOperators",
    "buildSyndromeCircuit",
    "scheduledSyndromeCircuit",
    "depolarizingChannel",
    "depolarizingErrors",
    "bitflipChannel",
    "phaseflipChannel",
]
