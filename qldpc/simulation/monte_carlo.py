"""Monte Carlo threshold estimation for quantum LDPC codes.

Provides shot-based simulation: sample errors, compute syndromes, decode
with BP, and measure logical/block error rates across a sweep of physical
error rates.
"""

from typing import Optional

import numpy as np

from ..decoders import BeliefPropagationDecoder
from ..noise import bitflipChannel


def estimateErrorRate(
    parityMatrix: np.ndarray,
    physicalErrorRate: float,
    nShots: int = 10000,
    maxBpIterations: int = 50,
    seed: Optional[int] = None,
) -> dict[str, float]:
    """Estimate decoder performance via Monte Carlo simulation.

    Samples random bit-flip errors at the given physical error rate,
    computes syndromes, decodes with BP, and counts failures.

    Returns a dictionary with:
      physicalErrorRate: the input error rate
      blockErrorRate: fraction of shots with nonzero residual error
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

    for _ in range(nShots):
        error = bitflipChannel(nQubits, physicalErrorRate, rng)
        syndrome = parityMatrix @ error % 2
        correction = decoder.decode(syndrome)

        if not decoder.converged:
            bpFailures += 1

        residual = (error + correction) % 2
        if np.any(residual != 0):
            blockErrors += 1

    return {
        "physicalErrorRate": physicalErrorRate,
        "blockErrorRate": blockErrors / nShots,
        "bpFailureRate": bpFailures / nShots,
        "nShots": nShots,
    }


def thresholdSweep(
    parityMatrix: np.ndarray,
    errorRates: np.ndarray,
    nShots: int = 10000,
    maxBpIterations: int = 50,
    seed: Optional[int] = None,
) -> list[dict[str, float]]:
    """Sweep physical error rates and estimate decoder performance for each.

    Returns a list of result dictionaries (one per error rate), each
    containing physicalErrorRate, blockErrorRate, bpFailureRate, and nShots.
    """
    results: list[dict[str, float]] = []
    for p in errorRates:
        result = estimateErrorRate(
            parityMatrix, float(p), nShots, maxBpIterations, seed
        )
        results.append(result)
    return results
