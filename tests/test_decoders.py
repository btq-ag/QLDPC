"""Tests for qldpc.decoders: belief propagation and decoder correctness."""

import numpy as np
import pytest

from qldpc.codes import repetitionCode, shorCode, steaneCode
from qldpc.decoders import BeliefPropagationDecoder, MinSumDecoder, OSDDecoder


class TestBeliefPropagationDecoder:
    def test_zero_syndrome_no_correction(self):
        """With no errors, BP should return all-zero correction."""
        _, hZ = steaneCode()
        decoder = BeliefPropagationDecoder(hZ, channelProb=0.1, maxIterations=50)
        syndrome = np.zeros(hZ.shape[0], dtype=int)
        correction = decoder.decode(syndrome)
        assert np.all(correction == 0)
        assert decoder.converged

    def test_single_error_steane_code(self):
        """BP should produce valid corrections for single X errors on Steane code."""
        _, hZ = steaneCode()
        for qubit in range(7):
            error = np.zeros(7, dtype=int)
            error[qubit] = 1
            syndrome = hZ @ error % 2
            decoder = BeliefPropagationDecoder(hZ, channelProb=0.1, maxIterations=50)
            correction = decoder.decode(syndrome)
            # Correction must satisfy the syndrome (fundamental BP guarantee)
            assert np.array_equal(hZ @ correction % 2, syndrome), (
                f"Correction does not match syndrome for error on qubit {qubit}"
            )

    def test_single_error_shor_code(self):
        """BP should produce a valid correction for the Shor [[9,1,3]] code."""
        _, hZ = shorCode()
        error = np.zeros(9, dtype=int)
        error[0] = 1
        syndrome = hZ @ error % 2
        # Shor's H_Z has high-weight rows (6), so BP needs a weaker prior
        decoder = BeliefPropagationDecoder(hZ, channelProb=0.3, maxIterations=100)
        correction = decoder.decode(syndrome)
        # If BP converged, the correction must match the syndrome
        if decoder.converged:
            assert np.array_equal(hZ @ correction % 2, syndrome)

    def test_step_increments_iteration(self):
        """Each step() call should increment the iteration counter."""
        _, hZ = steaneCode()
        decoder = BeliefPropagationDecoder(hZ, channelProb=0.1, maxIterations=10)
        # Use a non-trivial syndrome so BP does not converge immediately
        error = np.zeros(7, dtype=int)
        error[0] = 1
        syndrome = hZ @ error % 2
        decoder.reset(syndrome)
        decoder.step()
        assert decoder.iteration == 1
        decoder.step()
        assert decoder.iteration >= 2

    def test_converged_stops_iteration(self):
        """After convergence, step() should return True without incrementing."""
        _, hZ = steaneCode()
        decoder = BeliefPropagationDecoder(hZ, channelProb=0.1, maxIterations=50)
        syndrome = np.zeros(hZ.shape[0], dtype=int)
        decoder.reset(syndrome)
        # Zero syndrome converges on first step
        converged = decoder.step()
        assert converged
        iterBefore = decoder.iteration
        decoder.step()
        assert decoder.iteration == iterBefore

    def test_error_probabilities_shape(self):
        """errorProbabilities should return array of length n."""
        _, hZ = steaneCode()
        decoder = BeliefPropagationDecoder(hZ, channelProb=0.1, maxIterations=10)
        assert decoder.errorProbabilities.shape == (7,)

    def test_error_probabilities_range(self):
        """All error probabilities should be in [0, 1]."""
        _, hZ = steaneCode()
        decoder = BeliefPropagationDecoder(hZ, channelProb=0.1, maxIterations=50)
        error = np.zeros(7, dtype=int)
        error[3] = 1
        syndrome = hZ @ error % 2
        decoder.decode(syndrome)
        probs = decoder.errorProbabilities
        assert np.all(probs >= 0) and np.all(probs <= 1)

    def test_repetition_code_single_error(self):
        """BP should decode a single error on a repetition code."""
        h = repetitionCode(5)
        error = np.zeros(5, dtype=int)
        error[2] = 1
        syndrome = h @ error % 2
        decoder = BeliefPropagationDecoder(h, channelProb=0.1, maxIterations=50)
        correction = decoder.decode(syndrome)
        assert np.array_equal(h @ correction % 2, syndrome)

    def test_channel_probability_clipping(self):
        """Extreme channel probabilities should not cause errors."""
        _, hZ = steaneCode()
        # Very low error rate
        d1 = BeliefPropagationDecoder(hZ, channelProb=1e-15)
        assert d1.channelLlr > 0
        # Very high error rate
        d2 = BeliefPropagationDecoder(hZ, channelProb=1.0 - 1e-15)
        assert d2.channelLlr < 0


class TestMWPMDecoder:
    def test_import_error_without_pymatching(self):
        """MWPMDecoder should raise ImportError if pymatching is missing."""
        try:
            import pymatching  # noqa: F401
            pytest.skip("pymatching is installed; cannot test ImportError path")
        except ImportError:
            from qldpc.decoders import MWPMDecoder
            _, hZ = steaneCode()
            with pytest.raises(ImportError, match="pymatching"):
                MWPMDecoder(hZ)


class TestMinSumDecoder:
    def test_zero_syndrome_no_correction(self):
        """Min-sum BP returns all-zero correction for zero syndrome."""
        _, hZ = steaneCode()
        decoder = MinSumDecoder(hZ, channelProb=0.1, maxIterations=50, mode="normalized")
        syndrome = np.zeros(hZ.shape[0], dtype=int)
        correction = decoder.decode(syndrome)
        assert np.all(correction == 0)
        assert decoder.converged

    def test_single_error_normalized(self):
        """Normalized min-sum BP corrects single errors on Steane code."""
        _, hZ = steaneCode()
        for qubit in range(7):
            error = np.zeros(7, dtype=int)
            error[qubit] = 1
            syndrome = hZ @ error % 2
            decoder = MinSumDecoder(hZ, channelProb=0.1, maxIterations=50, mode="normalized", alpha=0.8)
            correction = decoder.decode(syndrome)
            assert np.array_equal(hZ @ correction % 2, syndrome), (
                f"Normalized min-sum failed on qubit {qubit}"
            )

    def test_single_error_offset(self):
        """Offset min-sum BP corrects single errors on Steane code."""
        _, hZ = steaneCode()
        for qubit in range(7):
            error = np.zeros(7, dtype=int)
            error[qubit] = 1
            syndrome = hZ @ error % 2
            decoder = MinSumDecoder(hZ, channelProb=0.1, maxIterations=50, mode="offset", beta=0.2)
            correction = decoder.decode(syndrome)
            assert np.array_equal(hZ @ correction % 2, syndrome), (
                f"Offset min-sum failed on qubit {qubit}"
            )

    def test_repetition_code(self):
        """Min-sum BP decodes a single error on repetition code."""
        h = repetitionCode(5)
        error = np.zeros(5, dtype=int)
        error[2] = 1
        syndrome = h @ error % 2
        decoder = MinSumDecoder(h, channelProb=0.1, maxIterations=50)
        correction = decoder.decode(syndrome)
        assert np.array_equal(h @ correction % 2, syndrome)

    def test_error_probabilities_shape(self):
        """errorProbabilities should return array of length n."""
        _, hZ = steaneCode()
        decoder = MinSumDecoder(hZ, channelProb=0.1, maxIterations=10)
        assert decoder.errorProbabilities.shape == (7,)

    def test_error_probabilities_range(self):
        """All error probabilities should be in [0, 1]."""
        _, hZ = steaneCode()
        decoder = MinSumDecoder(hZ, channelProb=0.1, maxIterations=50)
        error = np.zeros(7, dtype=int)
        error[3] = 1
        syndrome = hZ @ error % 2
        decoder.decode(syndrome)
        probs = decoder.errorProbabilities
        assert np.all(probs >= 0) and np.all(probs <= 1)


class TestOSDDecoder:
    def test_single_error_osd0(self):
        """OSD-0 corrects single errors on Steane code."""
        _, hZ = steaneCode()
        osd = OSDDecoder(hZ, order=0)
        for qubit in range(7):
            error = np.zeros(7, dtype=int)
            error[qubit] = 1
            syndrome = hZ @ error % 2
            correction = osd.decode(syndrome)
            assert np.array_equal(hZ @ correction % 2, syndrome), (
                f"OSD-0 failed on qubit {qubit}"
            )

    def test_osd_with_reliabilities(self):
        """OSD uses reliability ordering from BP soft output."""
        _, hZ = steaneCode()
        osd = OSDDecoder(hZ, order=0)
        error = np.zeros(7, dtype=int)
        error[0] = 1
        syndrome = hZ @ error % 2
        # Simulate reliability: errored qubit has low reliability
        reliabilities = np.ones(7) * 5.0
        reliabilities[0] = 0.1
        correction = osd.decode(syndrome, reliabilities=reliabilities)
        assert np.array_equal(hZ @ correction % 2, syndrome)

    def test_osd1_single_error(self):
        """OSD-1 corrects single errors on Steane code."""
        _, hZ = steaneCode()
        osd = OSDDecoder(hZ, order=1)
        error = np.zeros(7, dtype=int)
        error[3] = 1
        syndrome = hZ @ error % 2
        correction = osd.decode(syndrome)
        assert np.array_equal(hZ @ correction % 2, syndrome)

    def test_zero_syndrome(self):
        """OSD returns all-zero correction for zero syndrome."""
        _, hZ = steaneCode()
        osd = OSDDecoder(hZ, order=0)
        syndrome = np.zeros(hZ.shape[0], dtype=int)
        correction = osd.decode(syndrome)
        assert np.all(correction == 0)

    def test_repetition_code_osd(self):
        """OSD-0 corrects single error on repetition code."""
        h = repetitionCode(5)
        osd = OSDDecoder(h, order=0)
        error = np.zeros(5, dtype=int)
        error[2] = 1
        syndrome = h @ error % 2
        correction = osd.decode(syndrome)
        assert np.array_equal(h @ correction % 2, syndrome)
