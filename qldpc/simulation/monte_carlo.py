"""Monte Carlo threshold estimation for quantum LDPC codes.

Provides shot-based simulation: sample errors, compute syndromes, decode
with BP, and measure logical/block error rates across a sweep of physical
error rates.
"""


import numpy as np

from ..codes import _gf2Rank
from ..decoders import BeliefPropagationDecoder
from ..noise import bitflipChannel


def _isLogicalError(
    residual: np.ndarray, stabilizerMatrix: np.ndarray | None
) -> bool:
    """Check if a residual error is a nontrivial logical operator.

    If stabilizerMatrix is provided, the residual is a logical error only
    when it increases the rank of the stabilizer matrix (i.e. it lies
    outside the row space of the stabilizers). Otherwise, any nonzero
    residual counts as a failure.
    """
    if np.all(residual == 0):
        return False
    if stabilizerMatrix is None:
        return True
    baseRank = _gf2Rank(stabilizerMatrix)
    augmented = np.vstack([stabilizerMatrix, residual.reshape(1, -1)])
    return _gf2Rank(augmented) > baseRank


def estimateErrorRate(
    parityMatrix: np.ndarray,
    physicalErrorRate: float,
    nShots: int = 10000,
    maxBpIterations: int = 50,
    seed: int | None = None,
    stabilizerMatrix: np.ndarray | None = None,
) -> dict[str, float]:
    """Estimate decoder performance via Monte Carlo simulation.

    Samples random bit-flip errors at the given physical error rate,
    computes syndromes, decodes with BP, and counts failures.

    When stabilizerMatrix is provided, the residual is checked for
    membership in the stabilizer row space. Only residuals outside
    the stabilizer group count as logical errors. Without it, any
    nonzero residual counts as a block error (classical behavior).

    Returns a dictionary with:
      physicalErrorRate: the input error rate
      blockErrorRate: fraction of shots with nonzero residual error
      logicalErrorRate: fraction of shots with nontrivial logical error
      bpFailureRate: fraction of shots where BP did not converge
      nShots: number of shots run
    """
    rng = np.random.default_rng(seed)
    decoder = BeliefPropagationDecoder(
        parityMatrix,
        channelProb=physicalErrorRate,
        maxIterations=maxBpIterations,
    )
    nQubits = parityMatrix.shape[1]

    bpFailures = 0
    blockErrors = 0
    logicalErrors = 0

    for _ in range(nShots):
        error = bitflipChannel(nQubits, physicalErrorRate, rng)
        syndrome = parityMatrix @ error % 2
        correction = decoder.decode(syndrome)

        if not decoder.converged:
            bpFailures += 1

        residual = (error + correction) % 2
        if np.any(residual != 0):
            blockErrors += 1
        if _isLogicalError(residual, stabilizerMatrix):
            logicalErrors += 1

    return {
        "physicalErrorRate": physicalErrorRate,
        "blockErrorRate": blockErrors / nShots,
        "logicalErrorRate": logicalErrors / nShots,
        "bpFailureRate": bpFailures / nShots,
        "nShots": nShots,
    }


def thresholdSweep(
    parityMatrix: np.ndarray,
    errorRates: np.ndarray,
    nShots: int = 10000,
    maxBpIterations: int = 50,
    seed: int | None = None,
    stabilizerMatrix: np.ndarray | None = None,
) -> list[dict[str, float]]:
    """Sweep physical error rates and estimate decoder performance for each.

    Returns a list of result dictionaries (one per error rate), each
    containing physicalErrorRate, blockErrorRate, logicalErrorRate,
    bpFailureRate, and nShots.
    """
    results: list[dict[str, float]] = []
    for p in errorRates:
        result = estimateErrorRate(
            parityMatrix, float(p), nShots, maxBpIterations, seed,
            stabilizerMatrix=stabilizerMatrix,
        )
        results.append(result)
    return results
