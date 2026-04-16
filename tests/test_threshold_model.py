"""Tests for qldpc.tanner.threshold_3d: threshold model smoke tests (H7)."""

import matplotlib
import numpy as np

matplotlib.use("Agg")

from qldpc.tanner.threshold_3d import QuantumLDPCThresholdModel


class TestThresholdModelInit:
    def test_default_construction(self):
        model = QuantumLDPCThresholdModel()
        assert model is not None


class TestThresholdSurface:
    def test_threshold_surface_shape(self):
        model = QuantumLDPCThresholdModel()
        P, D, Z = model.calculate_threshold_surface()
        assert P.shape == D.shape == Z.shape
        assert P.ndim == 2
        assert P.shape[0] > 0 and P.shape[1] > 0

    def test_threshold_surface_values(self):
        model = QuantumLDPCThresholdModel()
        P, D, Z = model.calculate_threshold_surface()
        # Z (logical error rates) should be non-negative
        assert np.all(Z >= 0)
        # Physical error rates should be positive
        assert np.all(P >= 0)


class TestScalingSurface:
    def test_scaling_surface_shape(self):
        model = QuantumLDPCThresholdModel()
        N, R, Z = model.calculate_scaling_surface()
        assert N.shape == R.shape == Z.shape
        assert N.ndim == 2

    def test_scaling_surface_values(self):
        model = QuantumLDPCThresholdModel()
        N, R, Z = model.calculate_scaling_surface()
        assert np.all(Z >= 0)
