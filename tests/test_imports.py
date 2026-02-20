"""
Import smoke tests for all qldpc submodules.

Verifies that the package structure is valid and all modules
can be imported without errors.
"""

import pytest


def test_import_qldpc():
    """Top-level package imports cleanly."""
    import qldpc
    assert hasattr(qldpc, "__version__")
    assert qldpc.__version__ == "1.0.0"


def test_import_components():
    """components module exports core types."""
    from qldpc.components import ComponentType, Component3D, ViewMode
    assert ComponentType.X_GATE.value == "X"
    assert ViewMode.ISOMETRIC_3D.value == "isometric"


def test_import_config():
    """config module exports configuration classes."""
    from qldpc.config import (
        Config, GridConfig, UIConfig, SimulationConfig,
        ColorPalette, LDPC_COLORS, COMPONENT_COLORS, DEFAULT_CONFIG,
    )
    assert isinstance(DEFAULT_CONFIG, Config)
    assert "data_qubit" in LDPC_COLORS


def test_import_processor():
    """processor module exports QuantumLDPCProcessor."""
    from qldpc.processor import QuantumLDPCProcessor
    proc = QuantumLDPCProcessor()
    assert proc is not None


def test_import_simulation_ldpc():
    """simulation.ldpc_circuit exports QuantumLDPCCode."""
    from qldpc.simulation.ldpc_circuit import QuantumLDPCCode
    code = QuantumLDPCCode(n_data=12, n_checks=6)
    assert code.n_data == 12


def test_import_simulation_submodules():
    """All simulation submodules import without error."""
    from qldpc.simulation import cavity_gates
    from qldpc.simulation import ghz
    from qldpc.simulation import syndrome
    from qldpc.simulation import animations
    from qldpc.simulation import quantum_circuits


def test_import_tanner_submodules():
    """Tanner submodules import without error."""
    from qldpc.tanner import graph_3d
    from qldpc.tanner import threshold_3d


def test_qiskit_optional():
    """Qiskit import failure is handled gracefully."""
    from qldpc.processor import QISKIT_AVAILABLE
    # This should be a bool regardless of whether Qiskit is installed
    assert isinstance(QISKIT_AVAILABLE, bool)
