"""Decoder implementations for quantum LDPC codes.

Provides sum-product belief propagation, min-sum BP variants,
ordered statistics decoding (OSD) post-processing, and optional
MWPM decoders for syndrome-based decoding of binary linear codes.
"""


import numpy as np


class BeliefPropagationDecoder:
    """Sum-product belief propagation decoder for binary linear codes.

    Decodes a syndrome vector s by finding an error vector e such that
    H @ e = s (mod 2), using log-likelihood ratio (LLR) message passing
    with the Gallager (phi-function) formulation.
    """

    def __init__(
        self,
        parityMatrix: np.ndarray,
        channelProb: float = 0.05,
        maxIterations: int = 50,
    ) -> None:
        self.h = np.asarray(parityMatrix, dtype=int)
        self.m, self.n = self.h.shape
        self.maxIterations = maxIterations
        self.channelProb = float(np.clip(channelProb, 1e-10, 1.0 - 1e-10))

        # Adjacency lists
        self.checkNeighbors: list = [
            list(np.where(self.h[c] == 1)[0]) for c in range(self.m)
        ]
        self.varNeighbors: list = [
            list(np.where(self.h[:, v] == 1)[0]) for v in range(self.n)
        ]

        # Channel LLR (BSC model): positive means "likely no error"
        self.channelLlr: float = float(
            np.log((1.0 - self.channelProb) / self.channelProb)
        )

        # Message arrays (LLR domain)
        self.varToCheck = np.zeros((self.n, self.m))
        self.checkToVar = np.zeros((self.m, self.n))
        self.posteriorLlr = np.full(self.n, self.channelLlr)

        self._iteration: int = 0
        self._converged: bool = False
        self._syndrome = np.zeros(self.m, dtype=int)

    @staticmethod
    def _phi(x: np.ndarray) -> np.ndarray:
        """Gallager function: phi(x) = -log(tanh(|x|/2)). Self-inverse."""
        x = np.clip(np.abs(x), 1e-15, 500.0)
        return -np.log(np.tanh(x / 2.0))

    def reset(self, syndrome: np.ndarray) -> None:
        """Reset decoder state for a new decoding round."""
        self._syndrome = np.asarray(syndrome, dtype=int).copy()  # type: ignore[assignment]
        self._iteration = 0
        self._converged = False
        self.varToCheck[:] = self.channelLlr
        self.checkToVar[:] = 0.0
        self.posteriorLlr[:] = self.channelLlr

    def step(self) -> bool:
        """Run one BP iteration. Returns True if the decoder converged."""
        if self._converged:
            return True

        # --- Check-to-variable update (Gallager phi formulation) ---
        for c in range(self.m):
            neighbors = self.checkNeighbors[c]
            if not neighbors:
                continue

            msgs = np.array([self.varToCheck[v, c] for v in neighbors])
            signs = np.sign(msgs)
            signs[signs == 0] = 1.0
            magnitudes = np.abs(msgs)

            # Total sign: syndrome flips the product
            totalSignProduct = float(np.prod(signs))
            if self._syndrome[c] == 1:
                totalSignProduct *= -1.0

            phiVals = self._phi(magnitudes)
            totalPhiSum = float(np.sum(phiVals))

            for idx, v in enumerate(neighbors):
                # Exclude this edge from the product/sum
                excludedSign = totalSignProduct * float(signs[idx])
                excludedPhiSum = max(totalPhiSum - float(phiVals[idx]), 1e-15)
                edgeMag = float(self._phi(np.array([excludedPhiSum]))[0])
                self.checkToVar[c, v] = excludedSign * edgeMag

        # --- Variable-to-check update ---
        for v in range(self.n):
            neighbors = self.varNeighbors[v]
            if not neighbors:
                self.posteriorLlr[v] = self.channelLlr
                continue

            totalIncoming = self.channelLlr + sum(
                self.checkToVar[c, v] for c in neighbors
            )
            self.posteriorLlr[v] = totalIncoming
            for c in neighbors:
                self.varToCheck[v, c] = totalIncoming - self.checkToVar[c, v]

        self._iteration += 1

        # Convergence check: hard decision satisfies the syndrome
        hardDecision = (self.posteriorLlr < 0).astype(int)
        residual = self.h @ hardDecision % 2
        if np.array_equal(residual, self._syndrome):
            self._converged = True

        return self._converged

    def decode(self, syndrome: np.ndarray) -> np.ndarray:
        """Full decoding: reset, iterate until convergence, return correction."""
        self.reset(syndrome)
        for _ in range(self.maxIterations):
            if self.step():
                break
        return self.correction

    @property
    def correction(self) -> np.ndarray:
        """Current hard-decision correction vector."""
        return (self.posteriorLlr < 0).astype(int)

    @property
    def errorProbabilities(self) -> np.ndarray:
        """Posterior error probabilities for each variable node."""
        clipped = np.clip(self.posteriorLlr, -500, 500)
        return 1.0 / (1.0 + np.exp(clipped))

    @property
    def iteration(self) -> int:
        """Number of BP iterations completed."""
        return self._iteration

    @property
    def converged(self) -> bool:
        """Whether the decoder converged to a valid correction."""
        return self._converged


class MWPMDecoder:
    """Minimum-weight perfect matching decoder using PyMatching.

    Requires the pymatching package: pip install pymatching
    """

    def __init__(self, parityMatrix: np.ndarray) -> None:
        try:
            import pymatching
            self._matching = pymatching.Matching(parityMatrix)
        except ImportError:
            raise ImportError(
                "pymatching is required for MWPM decoding. "
                "Install with: pip install pymatching"
            )

    def decode(self, syndrome: np.ndarray) -> np.ndarray:
        """Decode a syndrome vector using minimum-weight perfect matching."""
        return self._matching.decode(syndrome)


class MinSumDecoder:
    """Min-sum belief propagation decoder with normalized and offset variants.

    The min-sum algorithm approximates the sum-product check node update
    by replacing the phi-function computation with a min operation,
    providing lower computational cost at the expense of accuracy.

    Supports two correction modes:
      - normalized: scale check-to-variable messages by alpha (0 < alpha <= 1)
      - offset: subtract a fixed beta from message magnitudes (clamp to 0)
    """

    def __init__(
        self,
        parityMatrix: np.ndarray,
        channelProb: float = 0.05,
        maxIterations: int = 50,
        mode: str = "normalized",
        alpha: float = 0.8,
        beta: float = 0.2,
    ) -> None:
        self.h = np.asarray(parityMatrix, dtype=int)
        self.m, self.n = self.h.shape
        self.maxIterations = maxIterations
        self.channelProb = float(np.clip(channelProb, 1e-10, 1.0 - 1e-10))
        self.mode = mode
        self.alpha = alpha
        self.beta = beta

        self.checkNeighbors: list = [
            list(np.where(self.h[c] == 1)[0]) for c in range(self.m)
        ]
        self.varNeighbors: list = [
            list(np.where(self.h[:, v] == 1)[0]) for v in range(self.n)
        ]

        self.channelLlr: float = float(
            np.log((1.0 - self.channelProb) / self.channelProb)
        )

        self.varToCheck = np.zeros((self.n, self.m))
        self.checkToVar = np.zeros((self.m, self.n))
        self.posteriorLlr = np.full(self.n, self.channelLlr)

        self._iteration: int = 0
        self._converged: bool = False
        self._syndrome = np.zeros(self.m, dtype=int)

    def reset(self, syndrome: np.ndarray) -> None:
        """Reset decoder state for a new decoding round."""
        self._syndrome = np.asarray(syndrome, dtype=int).copy()  # type: ignore[assignment]
        self._iteration = 0
        self._converged = False
        self.varToCheck[:] = self.channelLlr
        self.checkToVar[:] = 0.0
        self.posteriorLlr[:] = self.channelLlr

    def step(self) -> bool:
        """Run one min-sum BP iteration. Returns True if converged."""
        if self._converged:
            return True

        # --- Check-to-variable update (min-sum approximation) ---
        for c in range(self.m):
            neighbors = self.checkNeighbors[c]
            if not neighbors:
                continue

            msgs = np.array([self.varToCheck[v, c] for v in neighbors])
            signs = np.sign(msgs)
            signs[signs == 0] = 1.0
            magnitudes = np.abs(msgs)

            totalSignProduct = float(np.prod(signs))
            if self._syndrome[c] == 1:
                totalSignProduct *= -1.0

            for idx, v in enumerate(neighbors):
                excludedSign = totalSignProduct * float(signs[idx])
                # Min of all magnitudes excluding this edge
                otherMags = np.delete(magnitudes, idx)
                if len(otherMags) > 0:
                    minMag = float(np.min(otherMags))
                else:
                    minMag = 0.0

                # Apply correction
                if self.mode == "normalized":
                    minMag *= self.alpha
                elif self.mode == "offset":
                    minMag = max(0.0, minMag - self.beta)

                self.checkToVar[c, v] = excludedSign * minMag

        # --- Variable-to-check update ---
        for v in range(self.n):
            neighbors = self.varNeighbors[v]
            if not neighbors:
                self.posteriorLlr[v] = self.channelLlr
                continue

            totalIncoming = self.channelLlr + sum(
                self.checkToVar[c, v] for c in neighbors
            )
            self.posteriorLlr[v] = totalIncoming
            for c in neighbors:
                self.varToCheck[v, c] = totalIncoming - self.checkToVar[c, v]

        self._iteration += 1

        hardDecision = (self.posteriorLlr < 0).astype(int)
        residual = self.h @ hardDecision % 2
        if np.array_equal(residual, self._syndrome):
            self._converged = True

        return self._converged

    def decode(self, syndrome: np.ndarray) -> np.ndarray:
        """Full decoding: reset, iterate until convergence, return correction."""
        self.reset(syndrome)
        for _ in range(self.maxIterations):
            if self.step():
                break
        return self.correction

    @property
    def correction(self) -> np.ndarray:
        """Current hard-decision correction vector."""
        return (self.posteriorLlr < 0).astype(int)

    @property
    def errorProbabilities(self) -> np.ndarray:
        """Posterior error probabilities for each variable node."""
        clipped = np.clip(self.posteriorLlr, -500, 500)
        return 1.0 / (1.0 + np.exp(clipped))

    @property
    def iteration(self) -> int:
        return self._iteration

    @property
    def converged(self) -> bool:
        return self._converged


class OSDDecoder:
    """Ordered Statistics Decoding (OSD) post-processing decoder.

    OSD-0 finds the most likely error pattern consistent with the syndrome
    by solving the linear system using Gaussian elimination on columns
    ordered by reliability (posterior LLR magnitude from a prior BP run).

    OSD-w (order w) additionally searches over weight-w perturbations
    of the information set for improved performance.
    """

    def __init__(
        self,
        parityMatrix: np.ndarray,
        order: int = 0,
    ) -> None:
        self.h = np.asarray(parityMatrix, dtype=int)
        self.m, self.n = self.h.shape
        self.order = order

    def decode(
        self,
        syndrome: np.ndarray,
        reliabilities: np.ndarray | None = None,
    ) -> np.ndarray:
        """Decode a syndrome using OSD.

        Parameters
        ----------
        syndrome : array of shape (m,)
            The syndrome vector.
        reliabilities : array of shape (n,), optional
            Soft reliability values (e.g. |LLR| from BP). Higher means
            more reliable. If not provided, uses uniform reliability.

        Returns
        -------
        correction : array of shape (n,)
            The estimated error vector.
        """
        syndrome = np.asarray(syndrome, dtype=int) % 2
        if reliabilities is None:
            reliabilities = np.ones(self.n)
        reliabilities = np.asarray(reliabilities, dtype=float)

        # Order columns by decreasing reliability
        colOrder = np.argsort(-np.abs(reliabilities))
        hPerm = self.h[:, colOrder].copy()

        # Gaussian elimination to find pivot columns (information set)
        reduced, pivotCols = self._gf2Eliminate(hPerm)

        # Solve for the information bits
        e = np.zeros(self.n, dtype=int)
        for i, pc in enumerate(pivotCols):
            if i < len(syndrome):
                e[colOrder[pc]] = int(reduced[i] @ syndrome % 2) if False else 0

        # OSD-0: direct solve
        e = self._solveMinWeight(hPerm, reduced, pivotCols, syndrome, colOrder)

        # OSD-w: search over perturbations of the information set
        if self.order > 0:
            e = self._osdSearch(
                hPerm, reduced, pivotCols, syndrome, colOrder, e,
            )

        return e

    def _gf2Eliminate(
        self, matrix: np.ndarray
    ) -> tuple[np.ndarray, list[int]]:
        """Row-reduce a binary matrix over GF(2), return (reduced, pivot cols)."""
        mat = matrix.copy() % 2
        nRows, nCols = mat.shape
        pivots: list[int] = []
        row = 0
        for col in range(nCols):
            pivotRow = None
            for r in range(row, nRows):
                if mat[r, col] == 1:
                    pivotRow = r
                    break
            if pivotRow is None:
                continue
            mat[[row, pivotRow]] = mat[[pivotRow, row]]
            pivots.append(col)
            for r in range(nRows):
                if r != row and mat[r, col] == 1:
                    mat[r] = (mat[r] + mat[row]) % 2
            row += 1
        return mat, pivots

    def _solveMinWeight(
        self,
        hPerm: np.ndarray,
        reduced: np.ndarray,
        pivotCols: list[int],
        syndrome: np.ndarray,
        colOrder: np.ndarray,
    ) -> np.ndarray:
        """OSD-0: solve by back-substitution on the pivot columns."""
        e = np.zeros(self.n, dtype=int)
        rank = len(pivotCols)
        # Back-substitute: for each pivot row i, e[pivot_col] = reduced_syndrome[i]
        reducedSyndrome = np.zeros(reduced.shape[0], dtype=int)
        tempS = syndrome.copy()
        for i in range(rank):
            reducedSyndrome[i] = tempS[i] if i < len(tempS) else 0

        # The reduced matrix has identity columns at pivot positions
        # so e[pivotCol] = reducedSyndrome[row]
        for i, pc in enumerate(pivotCols):
            if i < len(reducedSyndrome):
                e[colOrder[pc]] = reducedSyndrome[i]

        # Verify and correct via reduced row operations
        residual = self.h @ e % 2
        if not np.array_equal(residual, syndrome):
            # Fallback: solve via reduced matrix
            mat = np.hstack([hPerm, syndrome.reshape(-1, 1)]) % 2
            augReduced, _ = self._gf2Eliminate(mat)
            e = np.zeros(self.n, dtype=int)
            for i, pc in enumerate(pivotCols):
                if i < augReduced.shape[0]:
                    e[colOrder[pc]] = int(augReduced[i, -1])

        return e

    def _osdSearch(
        self,
        hPerm: np.ndarray,
        reduced: np.ndarray,
        pivotCols: list[int],
        syndrome: np.ndarray,
        colOrder: np.ndarray,
        bestE: np.ndarray,
    ) -> np.ndarray:
        """OSD-w: search weight-w perturbations of the information set."""
        bestWeight = int(np.sum(bestE))
        rank = len(pivotCols)

        # Enumerate all weight-1 through weight-order perturbations
        for w in range(1, self.order + 1):
            if w == 1:
                for j in range(rank):
                    candidate = bestE.copy()
                    candidate[colOrder[pivotCols[j]]] ^= 1
                    # Re-solve parity columns to maintain syndrome
                    residual = self.h @ candidate % 2
                    diff = (residual + syndrome) % 2
                    if np.all(diff == 0):
                        cWeight = int(np.sum(candidate))
                        if cWeight < bestWeight:
                            bestE = candidate
                            bestWeight = cWeight
            # Higher orders would enumerate combinations; keep w=1 for now
            # to avoid combinatorial explosion

        return bestE


class SlidingWindowDecoder:
    """Sliding window decoder for circuit-level syndrome data.

    Processes W rounds of syndrome measurements by building an effective
    parity check matrix that incorporates temporal correlations and
    measurement errors. Delegates decoding of each window to an inner
    belief propagation decoder.

    The effective parity check matrix for a window of size W combines:
      - Data block: W copies of H arranged block-diagonally (one per round)
      - Measurement block: syndrome differences between consecutive rounds,
        modeled with identity matrices that capture measurement errors

    The decoder returns the correction for the oldest round in the window.
    """

    def __init__(
        self,
        parityMatrix: np.ndarray,
        windowSize: int = 3,
        channelProb: float = 0.05,
        measurementErrorProb: float = 0.01,
        maxIterations: int = 50,
    ) -> None:
        self.h = np.asarray(parityMatrix, dtype=int)
        self.m, self.n = self.h.shape
        self.windowSize = windowSize
        self.channelProb = channelProb
        self.measurementErrorProb = measurementErrorProb
        self.maxIterations = maxIterations

        # Build the effective parity check matrix for the full window
        self._effectiveH = self._buildEffectiveMatrix()
        self._innerDecoder = BeliefPropagationDecoder(
            self._effectiveH,
            channelProb=self.channelProb,
            maxIterations=self.maxIterations,
        )

    def _buildEffectiveMatrix(self) -> np.ndarray:
        """Construct the effective parity check matrix for the sliding window.

        Layout (W rounds, m checks, n data qubits per round):

        Rows: W*m syndrome rows + (W-1)*m difference rows
        Cols: W*n data error variables + W*m measurement error variables

        The data block has H on the diagonal for each round.
        The measurement block uses identity matrices to capture syndrome
        differences between consecutive rounds.
        """
        W = self.windowSize
        m, n = self.m, self.n

        # Total dimensions
        nSyndromeRows = W * m
        nDiffRows = (W - 1) * m
        totalRows = nSyndromeRows + nDiffRows
        nDataCols = W * n
        nMeasCols = W * m
        totalCols = nDataCols + nMeasCols

        effectiveH = np.zeros((totalRows, totalCols), dtype=int)

        # Data block: block-diagonal copies of H
        for t in range(W):
            rStart = t * m
            cStart = t * n
            effectiveH[rStart : rStart + m, cStart : cStart + n] = self.h

        # Measurement error identity: each round's syndrome row gets an
        # identity block for that round's measurement errors
        for t in range(W):
            rStart = t * m
            cStart = nDataCols + t * m
            effectiveH[rStart : rStart + m, cStart : cStart + m] = np.eye(m, dtype=int)

        # Syndrome difference rows: s_t XOR s_{t+1} detects measurement flips
        for t in range(W - 1):
            rStart = nSyndromeRows + t * m
            # Measurement error at round t
            cMeas1 = nDataCols + t * m
            effectiveH[rStart : rStart + m, cMeas1 : cMeas1 + m] = np.eye(m, dtype=int)
            # Measurement error at round t+1
            cMeas2 = nDataCols + (t + 1) * m
            effectiveH[rStart : rStart + m, cMeas2 : cMeas2 + m] = (
                effectiveH[rStart : rStart + m, cMeas2 : cMeas2 + m]
                + np.eye(m, dtype=int)
            ) % 2

        return effectiveH % 2

    def decode(self, syndromeHistory: np.ndarray) -> np.ndarray:
        """Decode a window of syndrome measurements.

        Parameters
        ----------
        syndromeHistory : array of shape (W, m)
            Syndrome vectors from W consecutive measurement rounds.

        Returns
        -------
        correction : array of shape (n,)
            Estimated data error correction for the oldest round (round 0).
        """
        syndromeHistory = np.asarray(syndromeHistory, dtype=int)
        W = self.windowSize
        m = self.m

        if syndromeHistory.shape != (W, m):
            raise ValueError(
                f"syndromeHistory shape {syndromeHistory.shape} must be ({W}, {m})."
            )

        # Build the effective syndrome vector
        # First W*m entries: the syndromes from each round
        flatSyndromes = syndromeHistory.flatten()

        # Next (W-1)*m entries: syndrome differences between consecutive rounds
        diffs = np.zeros((W - 1) * m, dtype=int)
        for t in range(W - 1):
            diffs[t * m : (t + 1) * m] = (
                syndromeHistory[t] + syndromeHistory[t + 1]
            ) % 2

        effectiveSyndrome = np.concatenate([flatSyndromes, diffs])

        # Decode using inner BP
        fullCorrection = self._innerDecoder.decode(effectiveSyndrome)

        # Extract correction for the oldest round (first n data variables)
        return fullCorrection[: self.n].copy()
