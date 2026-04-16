"""Known quantum code constructors, CSS validation, and code analysis.

Provides constructors for standard QEC code families (Steane, Shor, HGP),
CSS commutativity validation, distance calculation, and logical operator
identification using GF(2) linear algebra.
"""

from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# GF(2) linear algebra helpers
# ---------------------------------------------------------------------------


def _gf2RowReduce(matrix: np.ndarray) -> tuple[np.ndarray, list]:
    """Row-reduce a binary matrix over GF(2).

    Returns (reduced matrix, list of pivot column indices).
    """
    m: np.ndarray = matrix.copy().astype(int) % 2
    nRows, nCols = m.shape
    pivots: list = []
    row = 0
    for col in range(nCols):
        pivotRow = None
        for r in range(row, nRows):
            if m[r, col] == 1:
                pivotRow = r
                break
        if pivotRow is None:
            continue
        m[[row, pivotRow]] = m[[pivotRow, row]]
        pivots.append(col)
        for r in range(nRows):
            if r != row and m[r, col] == 1:
                m[r] = (m[r] + m[row]) % 2
        row += 1
    return m, pivots


def _gf2NullSpace(matrix: np.ndarray) -> np.ndarray:
    """Compute the null space of a binary matrix over GF(2).

    Returns a matrix whose rows span ker(matrix) over GF(2).
    """
    if matrix.size == 0:
        n = matrix.shape[1] if len(matrix.shape) > 1 else 0
        return np.eye(n, dtype=int) if n > 0 else np.zeros((0, 0), dtype=int)

    reduced, pivots = _gf2RowReduce(matrix)
    nRows, nCols = reduced.shape
    rank = len(pivots)
    nullDim = nCols - rank

    if nullDim == 0:
        return np.zeros((0, nCols), dtype=int)

    freeCols = [c for c in range(nCols) if c not in pivots]
    nullVectors = np.zeros((nullDim, nCols), dtype=int)

    for i, fc in enumerate(freeCols):
        nullVectors[i, fc] = 1
        for j, pc in enumerate(pivots):
            if j < rank:
                nullVectors[i, pc] = reduced[j, fc]

    return nullVectors % 2


def _gf2Rank(matrix: np.ndarray) -> int:
    """Compute the rank of a binary matrix over GF(2)."""
    if matrix.size == 0:
        return 0
    _, pivots = _gf2RowReduce(matrix)
    return len(pivots)


# ---------------------------------------------------------------------------
# CSS validation
# ---------------------------------------------------------------------------


def validateCss(hX: np.ndarray, hZ: np.ndarray) -> bool:
    """Check the CSS commutativity condition: H_X @ H_Z^T = 0 (mod 2).

    Returns True if the matrices define a valid CSS code.
    """
    hX = np.asarray(hX, dtype=int)
    hZ = np.asarray(hZ, dtype=int)
    if hX.shape[1] != hZ.shape[1]:
        return False
    product = (hX @ hZ.T) % 2
    return bool(np.all(product == 0))


# ---------------------------------------------------------------------------
# Known code constructors
# ---------------------------------------------------------------------------


def hammingCode() -> np.ndarray:
    """Classical [7,4,3] Hamming code parity check matrix."""
    return np.array([
        [1, 0, 0, 1, 0, 1, 1],
        [0, 1, 0, 1, 1, 0, 1],
        [0, 0, 1, 0, 1, 1, 1],
    ], dtype=int)


def steaneCode() -> tuple[np.ndarray, np.ndarray]:
    """Steane [[7,1,3]] CSS code.

    Built from the self-orthogonal [7,4,3] Hamming code.
    Returns (hX, hZ) where both are the Hamming parity check matrix.
    """
    h = hammingCode()
    return h.copy(), h.copy()


def shorCode() -> tuple[np.ndarray, np.ndarray]:
    """Shor [[9,1,3]] CSS code.

    X stabilizers detect Z (phase) errors within each 3-qubit block.
    Z stabilizers detect X (bit-flip) errors across blocks.
    Returns (hX, hZ).
    """
    hX = np.array([
        [1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 1],
    ], dtype=int)
    hZ = np.array([
        [1, 1, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 1, 1],
    ], dtype=int)
    return hX, hZ


def repetitionCode(n: int) -> np.ndarray:
    """Classical [n, 1, n] repetition code parity check matrix.

    Returns an (n-1) x n binary matrix. For quantum use, this checks
    a single error type (X or Z) only.
    """
    h: np.ndarray = np.zeros((n - 1, n), dtype=int)
    for i in range(n - 1):
        h[i, i] = 1
        h[i, i + 1] = 1
    return h


def hypergraphProduct(
    h1: np.ndarray, h2: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Hypergraph product CSS code from two classical parity check matrices.

    Given h1 (m1 x n1) and h2 (m2 x n2), constructs:
      H_X = [h1 (x) I_{n2} | I_{m1} (x) h2^T]
      H_Z = [I_{n1} (x) h2 | h1^T (x) I_{m2}]

    The resulting code has n = n1*n2 + m1*m2 qubits.
    CSS condition H_X @ H_Z^T = 0 (mod 2) holds automatically.
    """
    h1 = np.asarray(h1, dtype=int)
    h2 = np.asarray(h2, dtype=int)
    m1, n1 = h1.shape
    m2, n2 = h2.shape

    hX = np.hstack([
        np.kron(h1, np.eye(n2, dtype=int)),
        np.kron(np.eye(m1, dtype=int), h2.T),
    ]) % 2

    hZ = np.hstack([
        np.kron(np.eye(n1, dtype=int), h2),
        np.kron(h1.T, np.eye(m2, dtype=int)),
    ]) % 2

    return hX.astype(int), hZ.astype(int)


# ---------------------------------------------------------------------------
# Code analysis
# ---------------------------------------------------------------------------


def codeParameters(hX: np.ndarray, hZ: np.ndarray) -> tuple[int, int, int]:
    """Compute [[n, k, d]] parameters of a CSS code.

    n: number of physical qubits
    k: number of logical qubits = n - rank(H_X) - rank(H_Z)
    d: minimum distance (brute-force, feasible for small codes only)
    """
    hX = np.asarray(hX, dtype=int)
    hZ = np.asarray(hZ, dtype=int)
    n = hX.shape[1]
    k = n - _gf2Rank(hX) - _gf2Rank(hZ)
    d = codeDistance(hX, hZ)
    return n, k, d


def codeDistance(hX: np.ndarray, hZ: np.ndarray) -> int:
    """Compute the minimum distance of a CSS code by brute-force enumeration.

    d = min(d_X, d_Z) where:
      d_X = min weight of ker(H_Z) \\ rowspace(H_X)
      d_Z = min weight of ker(H_X) \\ rowspace(H_Z)

    Only feasible for small codes (n <= 30, low-dimensional quotient spaces).
    Raises ValueError for codes that are too large to enumerate.
    """
    hX = np.asarray(hX, dtype=int)
    hZ = np.asarray(hZ, dtype=int)

    dX = _minWeightInQuotient(hZ, hX)
    dZ = _minWeightInQuotient(hX, hZ)
    return min(dX, dZ)


def _minWeightInQuotient(
    hCheck: np.ndarray, hStab: np.ndarray
) -> int:
    """Find minimum weight vector in ker(hCheck) that is not in rowspace(hStab).

    Returns n+1 if the quotient space is trivial (no logical operators).
    """
    n = hCheck.shape[1]
    kernelBasis = _gf2NullSpace(hCheck)

    if kernelBasis.size == 0 or len(kernelBasis) == 0:
        return n + 1

    # Build stabilizer basis from hStab rows
    if hStab.size == 0:
        stabBasis = np.zeros((0, n), dtype=int)
    else:
        reduced, pivots = _gf2RowReduce(hStab)
        stabBasis = reduced[:len(pivots)]

    # Find quotient basis: vectors in kernel not spanned by stabilizers
    quotientBasis: list = []
    if stabBasis.size == 0 or len(stabBasis) == 0:
        augReduced = np.zeros((0, n), dtype=int)
        augPivots: list = []
    else:
        augReduced, augPivots = _gf2RowReduce(stabBasis)

    currentBasis = stabBasis.copy() if stabBasis.size > 0 else np.zeros((0, n), dtype=int)
    currentRank = len(augPivots)

    for vec in kernelBasis:
        if currentBasis.size == 0 or len(currentBasis) == 0:
            testMat = vec.reshape(1, -1)
        else:
            testMat = np.vstack([currentBasis, vec.reshape(1, -1)])
        _, testPivots = _gf2RowReduce(testMat)
        if len(testPivots) > currentRank:
            quotientBasis.append(vec)
            currentBasis = testMat
            currentRank = len(testPivots)

    if not quotientBasis:
        return n + 1

    quotientArr = np.array(quotientBasis)
    qDim = len(quotientArr)
    sDim = len(stabBasis) if stabBasis.size > 0 else 0

    # Safety check: exponential enumeration
    totalDim = qDim + sDim
    if totalDim > 25:
        raise ValueError(
            f"Code too large for brute-force distance calculation "
            f"(quotient dim {qDim}, stabilizer dim {sDim}). "
            f"Use approximate methods for codes with dim > 25."
        )

    minWeight = n + 1

    # Enumerate all non-zero quotient combinations
    for qMask in range(1, 2**qDim):
        qVec = np.zeros(n, dtype=int)
        for b in range(qDim):
            if qMask & (1 << b):
                qVec = (qVec + quotientArr[b]) % 2

        if sDim == 0:
            w = int(np.sum(qVec))
            if 0 < w < minWeight:
                minWeight = w
        else:
            for sMask in range(2**sDim):
                sVec = np.zeros(n, dtype=int)
                for b in range(sDim):
                    if sMask & (1 << b):
                        sVec = (sVec + stabBasis[b]) % 2
                total = (qVec + sVec) % 2
                w = int(np.sum(total))
                if 0 < w < minWeight:
                    minWeight = w

    return minWeight


def logicalOperators(
    hX: np.ndarray, hZ: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Find representatives of logical X and Z operators for a CSS code.

    Logical X operators: elements of ker(H_Z) not in rowspace(H_X).
    Logical Z operators: elements of ker(H_X) not in rowspace(H_Z).

    Returns (logicalX, logicalZ) as matrices whose rows are operator representatives.
    """
    hX = np.asarray(hX, dtype=int)
    hZ = np.asarray(hZ, dtype=int)
    n = hX.shape[1]

    logicalX = _quotientBasis(hZ, hX, n)
    logicalZ = _quotientBasis(hX, hZ, n)
    return logicalX, logicalZ


def _quotientBasis(
    hCheck: np.ndarray, hStab: np.ndarray, n: int
) -> np.ndarray:
    """Find basis for ker(hCheck) / rowspace(hStab) over GF(2)."""
    kernelBasis = _gf2NullSpace(hCheck)

    if kernelBasis.size == 0 or len(kernelBasis) == 0:
        return np.zeros((0, n), dtype=int)

    if hStab.size == 0:
        stabReduced: np.ndarray = np.zeros((0, n), dtype=int)
        stabRank = 0
    else:
        reduced, pivots = _gf2RowReduce(hStab)
        stabReduced = reduced[:len(pivots)]
        stabRank = len(pivots)

    result: list = []
    currentBasis = stabReduced.copy() if stabReduced.size > 0 else np.zeros((0, n), dtype=int)
    currentRank = stabRank

    for vec in kernelBasis:
        if currentBasis.size == 0 or len(currentBasis) == 0:
            testMat = vec.reshape(1, -1)
        else:
            testMat = np.vstack([currentBasis, vec.reshape(1, -1)])
        _, testPivots = _gf2RowReduce(testMat)
        if len(testPivots) > currentRank:
            result.append(vec)
            currentBasis = testMat
            currentRank = len(testPivots)

    if not result:
        return np.zeros((0, n), dtype=int)
    return np.array(result, dtype=int)


# ---------------------------------------------------------------------------
# Syndrome extraction circuit
# ---------------------------------------------------------------------------


def buildSyndromeCircuit(
    hX: np.ndarray, hZ: np.ndarray
):  # noqa: F821
    """Build a Qiskit QuantumCircuit for CSS syndrome extraction.

    X-stabilizer measurements use CNOT (ancilla as control) with H gates.
    Z-stabilizer measurements use CNOT (data as control).

    Requires Qiskit. Returns a QuantumCircuit with named registers:
    dataQubits, xAncilla, zAncilla, xSyndrome, zSyndrome.
    """
    try:
        from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
    except ImportError:
        raise ImportError(
            "Qiskit is required for circuit generation. "
            "Install with: pip install qiskit"
        )

    hX = np.asarray(hX, dtype=int)
    hZ = np.asarray(hZ, dtype=int)
    nData = hX.shape[1]
    nXChecks = hX.shape[0]
    nZChecks = hZ.shape[0]

    dataQubits = QuantumRegister(nData, "dataQubits")
    xAncilla = QuantumRegister(nXChecks, "xAncilla")
    zAncilla = QuantumRegister(nZChecks, "zAncilla")
    xSyndrome = ClassicalRegister(nXChecks, "xSyndrome")
    zSyndrome = ClassicalRegister(nZChecks, "zSyndrome")

    circuit = QuantumCircuit(
        dataQubits, xAncilla, zAncilla, xSyndrome, zSyndrome
    )

    # X-stabilizer measurements (detect Z errors)
    for i in range(nXChecks):
        circuit.h(xAncilla[i])
        for j in range(nData):
            if hX[i, j] == 1:
                circuit.cx(xAncilla[i], dataQubits[j])
        circuit.h(xAncilla[i])
        circuit.measure(xAncilla[i], xSyndrome[i])

    circuit.barrier()

    # Z-stabilizer measurements (detect X errors)
    for i in range(nZChecks):
        for j in range(nData):
            if hZ[i, j] == 1:
                circuit.cx(dataQubits[j], zAncilla[i])
        circuit.measure(zAncilla[i], zSyndrome[i])

    return circuit
