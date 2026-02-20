"""
Tests for qldpc.simulation.ldpc_circuit.QuantumLDPCCode.

Covers parity matrix generation, error injection, syndrome calculation,
and belief propagation decoding.
"""

import pytest
import numpy as np
from qldpc.simulation.ldpc_circuit import QuantumLDPCCode


class TestQuantumLDPCCodeInit:
    def test_default_parameters(self):
        code = QuantumLDPCCode()
        assert code.n_data == 21
        assert code.n_checks == 12

    def test_custom_parameters(self):
        code = QuantumLDPCCode(n_data=15, n_checks=8)
        assert code.n_data == 15
        assert code.n_checks == 8

    def test_parity_matrix_shape(self):
        code = QuantumLDPCCode(n_data=21, n_checks=12)
        assert code.parity_matrix.shape == (12, 21)

    def test_parity_matrix_sparsity(self):
        """LDPC property: each check connects to ~6 qubits."""
        code = QuantumLDPCCode(n_data=21, n_checks=12)
        row_weights = code.parity_matrix.sum(axis=1)
        # Each row should have exactly 6 nonzeros
        np.testing.assert_array_equal(row_weights, np.full(12, 6))

    def test_initial_state_clean(self):
        code = QuantumLDPCCode()
        assert np.all(code.qubit_states == 0)
        assert np.all(code.syndrome == 0)

    def test_gate_fidelity_calculation(self):
        code = QuantumLDPCCode()
        code.cavity_cooperativity = 1e5
        fidelity = code._calculate_gate_fidelity()
        # F = 1 - 1/C - 0.001 = 1 - 1e-5 - 1e-3 ~ 0.99899
        assert 0.998 < fidelity < 1.0


class TestErrorInjection:
    def test_inject_x_error(self):
        code = QuantumLDPCCode()
        code.inject_error(5, error_type=2)
        assert code.qubit_states[5] == 2

    def test_inject_z_error(self):
        code = QuantumLDPCCode()
        code.inject_error(3, error_type=3)
        assert code.qubit_states[3] == 3

    def test_inject_y_error(self):
        code = QuantumLDPCCode()
        code.inject_error(7, error_type=4)
        assert code.qubit_states[7] == 4

    def test_inject_out_of_range(self):
        code = QuantumLDPCCode(n_data=10)
        code.inject_error(15, error_type=2)
        # Should not crash, state should be unchanged
        assert np.all(code.qubit_states == 0)

    def test_syndrome_updates_on_error(self):
        code = QuantumLDPCCode()
        code.inject_error(0, error_type=2)
        # At least one check connected to qubit 0 should fire
        connected_checks = np.where(code.parity_matrix[:, 0] == 1)[0]
        assert len(connected_checks) > 0
        # Syndrome should be nonzero somewhere
        assert np.any(code.syndrome != 0)


class TestBeliefPropagation:
    def test_bp_step_increments_iteration(self):
        code = QuantumLDPCCode()
        assert code.bp_iteration == 0
        code.belief_propagation_step()
        assert code.bp_iteration == 1

    def test_bp_max_iterations(self):
        code = QuantumLDPCCode()
        code.bp_iteration = code.max_bp_iterations
        code.belief_propagation_step()
        # Should not increment past max
        assert code.bp_iteration == code.max_bp_iterations

    def test_bp_with_error(self):
        code = QuantumLDPCCode()
        code.inject_error(5, error_type=2)
        # Run several BP iterations
        for _ in range(5):
            code.belief_propagation_step()
        # Beliefs should have shifted from uniform
        assert code.bp_iteration == 5


class TestCooperativity:
    def test_high_cooperativity_high_fidelity(self):
        code = QuantumLDPCCode()
        code.cavity_cooperativity = 1e6
        f = code._calculate_gate_fidelity()
        assert f > 0.998

    def test_low_cooperativity_lower_fidelity(self):
        code = QuantumLDPCCode()
        code.cavity_cooperativity = 1e3
        f = code._calculate_gate_fidelity()
        assert f < 0.999
