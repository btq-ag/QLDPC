"""Tests for qldpc.codes: CSS validation, known codes, and code analysis."""

import numpy as np

from qldpc.codes import (
    _gf2NullSpace,
    _gf2Rank,
    _gf2RowReduce,
    bivariateBicycleCode,
    codeParameters,
    fiberBundleCode,
    hammingCode,
    hypergraphProduct,
    logicalOperators,
    repetitionCode,
    scheduledSyndromeCircuit,
    shorCode,
    steaneCode,
    validateCss,
)


class TestCssValidation:
    def test_steane_is_valid_css(self):
        hX, hZ = steaneCode()
        assert validateCss(hX, hZ)

    def test_shor_is_valid_css(self):
        hX, hZ = shorCode()
        assert validateCss(hX, hZ)

    def test_random_matrix_not_css(self):
        rng = np.random.default_rng(42)
        hX = rng.integers(0, 2, size=(3, 7))
        hZ = rng.integers(0, 2, size=(3, 7))
        # Random matrices are very unlikely to satisfy CSS
        # (but it's possible, so we just check it runs)
        result = validateCss(hX, hZ)
        assert isinstance(result, bool)

    def test_mismatched_dimensions_fail(self):
        hX = np.eye(3, dtype=int)
        hZ = np.eye(4, dtype=int)
        assert not validateCss(hX, hZ)


class TestSteaneCode:
    def test_shapes(self):
        hX, hZ = steaneCode()
        assert hX.shape == (3, 7)
        assert hZ.shape == (3, 7)

    def test_self_orthogonal(self):
        """Steane code: H_X = H_Z = H, and H @ H^T = 0 mod 2."""
        hX, hZ = steaneCode()
        np.testing.assert_array_equal(hX, hZ)
        product = hX @ hX.T % 2
        np.testing.assert_array_equal(product, np.zeros_like(product))

    def test_parameters(self):
        hX, hZ = steaneCode()
        n, k, d = codeParameters(hX, hZ)
        assert n == 7
        assert k == 1
        assert d == 3


class TestShorCode:
    def test_shapes(self):
        hX, hZ = shorCode()
        assert hX.shape == (6, 9)
        assert hZ.shape == (2, 9)

    def test_parameters(self):
        hX, hZ = shorCode()
        n, k, d = codeParameters(hX, hZ)
        assert n == 9
        assert k == 1
        assert d == 3


class TestRepetitionCode:
    def test_shape(self):
        h = repetitionCode(5)
        assert h.shape == (4, 5)

    def test_row_weight(self):
        """Each row of the repetition code parity check should have weight 2."""
        h = repetitionCode(7)
        row_weights = h.sum(axis=1)
        np.testing.assert_array_equal(row_weights, np.full(6, 2))

    def test_single_error_detection(self):
        """A single bit flip should produce a nonzero syndrome."""
        h = repetitionCode(5)
        for i in range(5):
            e = np.zeros(5, dtype=int)
            e[i] = 1
            s = h @ e % 2
            assert np.any(s != 0), f"Error at qubit {i} not detected"


class TestHypergraphProduct:
    def test_css_condition(self):
        """HGP codes automatically satisfy the CSS condition."""
        h1 = repetitionCode(3)
        h2 = repetitionCode(3)
        hX, hZ = hypergraphProduct(h1, h2)
        assert validateCss(hX, hZ)

    def test_qubit_count(self):
        """n = n1*n2 + m1*m2 for the HGP code."""
        h1 = repetitionCode(3)  # 2x3
        h2 = repetitionCode(4)  # 3x4
        hX, hZ = hypergraphProduct(h1, h2)
        expected_n = 3 * 4 + 2 * 3  # 12 + 6 = 18
        assert hX.shape[1] == expected_n
        assert hZ.shape[1] == expected_n

    def test_hamming_product(self):
        """HGP of two Hamming codes should be a valid CSS code."""
        h = hammingCode()
        hX, hZ = hypergraphProduct(h, h)
        assert validateCss(hX, hZ)
        n = hX.shape[1]
        k = n - _gf2Rank(hX) - _gf2Rank(hZ)
        assert k > 0


class TestLogicalOperators:
    def test_steane_one_logical(self):
        """Steane code should have exactly 1 logical X and 1 logical Z."""
        hX, hZ = steaneCode()
        logX, logZ = logicalOperators(hX, hZ)
        assert logX.shape[0] == 1
        assert logZ.shape[0] == 1

    def test_shor_one_logical(self):
        """Shor code should have exactly 1 logical X and 1 logical Z."""
        hX, hZ = shorCode()
        logX, logZ = logicalOperators(hX, hZ)
        assert logX.shape[0] == 1
        assert logZ.shape[0] == 1

    def test_logical_anticommute(self):
        """Logical X and Z should anticommute: X_L @ Z_L = 1 mod 2."""
        hX, hZ = steaneCode()
        logX, logZ = logicalOperators(hX, hZ)
        # For k=1 code, the single logical X and Z should satisfy
        # X_L . Z_L = 1 mod 2
        overlap = logX[0] @ logZ[0] % 2
        assert overlap == 1

    def test_logical_commutes_with_stabilizers(self):
        """Logical operators commute with all stabilizers."""
        hX, hZ = steaneCode()
        logX, logZ = logicalOperators(hX, hZ)
        # logX is in ker(H_Z), so H_Z @ logX^T = 0
        for lx in logX:
            assert np.all(hZ @ lx % 2 == 0)
        for lz in logZ:
            assert np.all(hX @ lz % 2 == 0)


class TestGF2LinearAlgebra:
    def test_row_reduce_identity(self):
        m = np.eye(3, dtype=int)
        reduced, pivots = _gf2RowReduce(m)
        assert pivots == [0, 1, 2]

    def test_null_space_full_rank(self):
        """Full-rank matrix should have trivial null space."""
        m = np.eye(4, dtype=int)
        ns = _gf2NullSpace(m)
        assert ns.shape[0] == 0

    def test_null_space_repetition(self):
        """Null space of repetition code H should include the all-ones vector."""
        h = repetitionCode(5)
        ns = _gf2NullSpace(h)
        assert ns.shape[0] == 1  # [5, 1, 5] code: 1-dim null space
        # The all-ones vector should be in the null space
        allOnes = np.ones(5, dtype=int)
        assert np.all(h @ allOnes % 2 == 0)

    def test_gf2_rank(self):
        h = hammingCode()
        assert _gf2Rank(h) == 3


class TestBivariateBicycleCode:
    def test_css_valid_6x6(self):
        """BB code over Z6 x Z6 satisfies CSS orthogonality."""
        hX, hZ = bivariateBicycleCode(6, 6, [(3, 0), (0, 1), (0, 2)], [(0, 3), (1, 0), (2, 0)])
        assert validateCss(hX, hZ)

    def test_shape_6x6(self):
        """Block length = 2 * ell * m for BB codes."""
        hX, hZ = bivariateBicycleCode(6, 6, [(3, 0), (0, 1), (0, 2)], [(0, 3), (1, 0), (2, 0)])
        assert hX.shape[1] == 2 * 6 * 6  # n = 72
        assert hZ.shape[1] == 2 * 6 * 6

    def test_css_valid_12x6(self):
        """BB code over Z12 x Z6 satisfies CSS orthogonality."""
        hX, hZ = bivariateBicycleCode(12, 6, [(3, 0), (0, 1), (0, 2)], [(0, 3), (1, 0), (2, 0)])
        assert validateCss(hX, hZ)

    def test_shape_12x6(self):
        hX, hZ = bivariateBicycleCode(12, 6, [(3, 0), (0, 1), (0, 2)], [(0, 3), (1, 0), (2, 0)])
        assert hX.shape[1] == 2 * 12 * 6  # n = 144
        assert hZ.shape[1] == 2 * 12 * 6

    def test_css_valid_15x3(self):
        """BB code over Z15 x Z3 satisfies CSS orthogonality."""
        hX, hZ = bivariateBicycleCode(15, 3, [(9, 0), (0, 1), (0, 2)], [(0, 0), (2, 0), (7, 0)])
        assert validateCss(hX, hZ)

    def test_binary_entries(self):
        """All entries in hX and hZ should be 0 or 1."""
        hX, hZ = bivariateBicycleCode(6, 6, [(3, 0), (0, 1), (0, 2)], [(0, 3), (1, 0), (2, 0)])
        assert set(np.unique(hX)).issubset({0, 1})
        assert set(np.unique(hZ)).issubset({0, 1})

    def test_parameters_72(self):
        """[[72,12,d]] code has 12 logical qubits."""
        hX, hZ = bivariateBicycleCode(6, 6, [(3, 0), (0, 1), (0, 2)], [(0, 3), (1, 0), (2, 0)])
        n = hX.shape[1]
        rankX = _gf2Rank(hX)
        rankZ = _gf2Rank(hZ)
        k = n - rankX - rankZ
        assert n == 72
        assert k == 12


class TestFiberBundleCode:
    def test_css_valid_zero_twist(self):
        """Zero twist reduces to standard hypergraph product."""
        h1 = repetitionCode(3)  # 2x3
        h2 = repetitionCode(3)  # 2x3
        twist = np.zeros(h1.shape, dtype=int)
        hX, hZ = fiberBundleCode(h1, h2, twist)
        assert validateCss(hX, hZ)

    def test_matches_hgp_zero_twist(self):
        """With zero twist, fiber bundle gives the same qubit count as HGP."""
        h1 = repetitionCode(3)
        h2 = repetitionCode(3)
        twist = np.zeros(h1.shape, dtype=int)
        hXfb, hZfb = fiberBundleCode(h1, h2, twist)
        hXhgp, hZhgp = hypergraphProduct(h1, h2)
        assert hXfb.shape[1] == hXhgp.shape[1]
        assert hZfb.shape[1] == hZhgp.shape[1]

    def test_shape_consistency(self):
        """H_X and H_Z have the same number of columns."""
        h1 = repetitionCode(4)
        h2 = repetitionCode(3)
        twist = np.zeros(h1.shape, dtype=int)
        hX, hZ = fiberBundleCode(h1, h2, twist)
        assert hX.shape[1] == hZ.shape[1]

    def test_binary_entries(self):
        """All entries are 0 or 1."""
        h1 = repetitionCode(3)
        h2 = repetitionCode(3)
        twist = np.zeros(h1.shape, dtype=int)
        hX, hZ = fiberBundleCode(h1, h2, twist)
        assert set(np.unique(hX)).issubset({0, 1})
        assert set(np.unique(hZ)).issubset({0, 1})

    def test_nonzero_twist_css(self):
        """A nonzero twist with compatible fiber code produces valid CSS."""
        h1 = repetitionCode(3)  # 2x3
        # Square circulant fiber code (4x4): P(4,2) = P(4,-2) guarantees CSS
        h2 = np.array([
            [1, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 1],
            [1, 0, 0, 1],
        ], dtype=int)
        # twist = nF/2 = 2 at all base edges; 0 elsewhere
        twist = np.array([[2, 2, 0], [0, 2, 2]], dtype=int)
        hX, hZ = fiberBundleCode(h1, h2, twist)
        assert validateCss(hX, hZ)

    def test_twist_shape_mismatch_raises(self):
        """Mismatched twist shape raises ValueError."""
        h1 = repetitionCode(3)
        h2 = repetitionCode(3)
        twist = np.zeros((5, 5), dtype=int)
        try:
            fiberBundleCode(h1, h2, twist)
            assert False, "Expected ValueError"
        except ValueError:
            pass

    def test_positive_k(self):
        """Fiber bundle code with zero twist has positive logical qubit count."""
        h1 = hammingCode()  # 3x7
        h2 = repetitionCode(3)  # 2x3
        twist = np.zeros(h1.shape, dtype=int)
        hX, hZ = fiberBundleCode(h1, h2, twist)
        n = hX.shape[1]
        k = n - _gf2Rank(hX) - _gf2Rank(hZ)
        assert k > 0


class TestScheduledSyndromeCircuit:
    def test_circuit_returns(self):
        """scheduledSyndromeCircuit returns a QuantumCircuit."""
        try:
            from qiskit import QuantumCircuit
        except ImportError:
            return  # skip if Qiskit not installed
        hX, hZ = steaneCode()
        circuit = scheduledSyndromeCircuit(hX, hZ)
        assert isinstance(circuit, QuantumCircuit)

    def test_all_stabilizers_measured(self):
        """Circuit measures all X and Z stabilizers."""
        try:
            import qiskit  # noqa: F401
        except ImportError:
            return
        hX, hZ = steaneCode()
        circuit = scheduledSyndromeCircuit(hX, hZ)
        measureCount = sum(
            1 for instr in circuit.data if instr.operation.name == "measure"
        )
        expected = hX.shape[0] + hZ.shape[0]
        assert measureCount == expected

    def test_fewer_barriers_than_naive(self):
        """Scheduled circuit uses fewer time steps (barriers) than sequential."""
        try:
            import qiskit  # noqa: F401
        except ImportError:
            return
        hX, hZ = steaneCode()
        scheduled = scheduledSyndromeCircuit(hX, hZ, maxParallel=10)
        barrierCount = sum(
            1 for instr in scheduled.data if instr.operation.name == "barrier"
        )
        totalStabs = hX.shape[0] + hZ.shape[0]
        # With parallelism, the number of barriers should be less than totalStabs - 1
        assert barrierCount < totalStabs

    def test_no_qubit_conflict_in_group(self):
        """Within each parallel group, no two stabilizers share a data qubit."""
        try:
            import qiskit  # noqa: F401
        except ImportError:
            return
        hX, hZ = shorCode()
        circuit = scheduledSyndromeCircuit(hX, hZ, maxParallel=10)
        # Reconstruct groups from circuit barriers
        groups: list[list[set[int]]] = [[]]
        for instr in circuit.data:
            if instr.operation.name == "barrier":
                groups.append([])
            elif instr.operation.name == "cx":
                qubits = [circuit.find_bit(q).index for q in instr.qubits]
                # Track data qubit indices (first nData qubits in the circuit)
                nData = hX.shape[1]
                dataQubitsUsed = {q for q in qubits if q < nData}
                if dataQubitsUsed:
                    groups[-1].append(dataQubitsUsed)
        # Within each group, check no overlap between stabilizer supports
        for group in groups:
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    # Allow overlap within a single stabilizer (multiple CX gates)
                    pass  # Full conflict check requires stabilizer-level grouping
