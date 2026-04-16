"""Decoder implementations for quantum LDPC codes.

Provides sum-product belief propagation and optional MWPM decoders
for syndrome-based decoding of binary linear codes.
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
        self._syndrome = np.asarray(syndrome, dtype=int).copy()
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
