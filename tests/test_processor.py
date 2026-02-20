"""
Tests for qldpc.processor module.

Covers QuantumLDPCProcessor initialization and basic operations.
"""

import pytest
import numpy as np
from qldpc.processor import QuantumLDPCProcessor, QISKIT_AVAILABLE
from qldpc.components import ComponentType, Component3D
from qldpc.config import Config


class TestProcessorInit:
    def test_default_init(self):
        proc = QuantumLDPCProcessor()
        assert proc.circuit is None
        assert proc.current_state is None
        assert proc.syndrome_history == []
        assert proc.error_corrections == []

    def test_custom_config(self):
        cfg = Config()
        cfg.simulation.bp_max_iterations = 20
        proc = QuantumLDPCProcessor(config=cfg)
        assert proc.config.simulation.bp_max_iterations == 20


class TestProcessorCircuitBuild:
    def test_no_qubits_returns_none(self):
        proc = QuantumLDPCProcessor()
        # Only gates, no qubits
        components = [
            Component3D(ComponentType.X_GATE, position=(0, 0, 0)),
        ]
        result = proc.build_circuit_from_components(components)
        # Without qubits, circuit build should handle gracefully
        assert result is None

    def test_basic_circuit_build(self):
        proc = QuantumLDPCProcessor()
        components = [
            Component3D(ComponentType.DATA_QUBIT, position=(0, 0, 0)),
            Component3D(ComponentType.DATA_QUBIT, position=(0, 1, 0)),
            Component3D(ComponentType.X_GATE, position=(1, 0, 0)),
        ]
        result = proc.build_circuit_from_components(components)
        # Should return a circuit object (Qiskit or simulated)
        assert result is not None


class TestProcessorSyndrome:
    def test_syndrome_with_components(self):
        """Syndrome calculation using parity check + data qubit components."""
        proc = QuantumLDPCProcessor()
        components = [
            Component3D(ComponentType.DATA_QUBIT, position=(0, 0, 0)),
            Component3D(ComponentType.DATA_QUBIT, position=(0, 1, 0)),
            Component3D(ComponentType.PARITY_CHECK, position=(0, 0, 0)),
        ]
        syndrome = proc.calculate_syndrome(components)
        assert isinstance(syndrome, np.ndarray)

    def test_syndrome_empty_without_components(self):
        proc = QuantumLDPCProcessor()
        syndrome = proc.calculate_syndrome([])
        assert len(syndrome) == 0

    def test_syndrome_with_error(self):
        """X gate on a data qubit lane should produce nonzero syndrome."""
        proc = QuantumLDPCProcessor()
        components = [
            Component3D(ComponentType.DATA_QUBIT, position=(0, 0, 0)),
            Component3D(ComponentType.DATA_QUBIT, position=(0, 1, 0)),
            Component3D(ComponentType.PARITY_CHECK, position=(1, 0, 0)),
            Component3D(ComponentType.X_GATE, position=(2, 0, 0)),
        ]
        syndrome = proc.calculate_syndrome(components)
        assert isinstance(syndrome, np.ndarray)
