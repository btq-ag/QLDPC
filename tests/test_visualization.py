"""Smoke tests for visualization modules (H8).

Uses matplotlib Agg backend to avoid display requirements.
Verifies functions execute without errors on valid inputs.
"""


import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


class TestSyndromeVisualization:
    def test_create_syndrome_extraction_circuit(self):
        from qldpc.simulation.syndrome import create_syndrome_extraction_circuit
        create_syndrome_extraction_circuit()
        plt.close("all")

    def test_create_syndrome_error_analysis(self):
        from qldpc.simulation.syndrome import create_syndrome_error_analysis
        create_syndrome_error_analysis()
        plt.close("all")


class TestCavityGatesVisualization:
    def test_import(self):
        from qldpc.simulation import cavity_gates
        assert cavity_gates is not None


class TestGHZVisualization:
    def test_import(self):
        from qldpc.simulation import ghz
        assert ghz is not None


class TestQuantumCircuitsVisualization:
    def test_import(self):
        from qldpc.simulation import quantum_circuits
        assert quantum_circuits is not None


class TestAnimationsVisualization:
    def test_import(self):
        from qldpc.simulation import animations
        assert animations is not None


class TestNoiseModule:
    def test_bitflip_channel(self):
        from qldpc.noise import bitflipChannel
        rng = np.random.default_rng(42)
        errors = bitflipChannel(10, 0.1, rng)
        assert errors.shape == (10,)
        assert np.all((errors == 0) | (errors == 1))

    def test_phaseflip_channel(self):
        from qldpc.noise import phaseflipChannel
        rng = np.random.default_rng(42)
        errors = phaseflipChannel(10, 0.1, rng)
        assert errors.shape == (10,)
        assert np.all((errors == 0) | (errors == 1))

    def test_depolarizing_channel(self):
        from qldpc.noise import depolarizingChannel
        rng = np.random.default_rng(42)
        errors = depolarizingChannel(10, 0.1, rng)
        assert errors.shape == (10,)
        assert np.all((errors >= 0) & (errors <= 3))

    def test_depolarizing_errors(self):
        from qldpc.noise import depolarizingErrors
        rng = np.random.default_rng(42)
        xErr, zErr = depolarizingErrors(10, 0.1, rng)
        assert xErr.shape == (10,)
        assert zErr.shape == (10,)


class TestMonteCarloModule:
    def test_estimate_error_rate(self):
        from qldpc.codes import steaneCode
        from qldpc.simulation.monte_carlo import estimateErrorRate
        _, hZ = steaneCode()
        result = estimateErrorRate(hZ, 0.01, nShots=100, seed=42)
        assert "blockErrorRate" in result
        assert "bpFailureRate" in result
        assert 0 <= result["blockErrorRate"] <= 1
        assert 0 <= result["bpFailureRate"] <= 1

    def test_threshold_sweep(self):
        from qldpc.codes import steaneCode
        from qldpc.simulation.monte_carlo import thresholdSweep
        _, hZ = steaneCode()
        rates = np.array([0.01, 0.05])
        results = thresholdSweep(hZ, rates, nShots=50, seed=42)
        assert len(results) == 2
        # Higher error rate should have higher block error rate
        assert results[1]["blockErrorRate"] >= results[0]["blockErrorRate"]
