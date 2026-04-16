"""Channel noise models for quantum error correction simulation.

Provides sampling functions for standard quantum noise channels:
depolarizing, bit-flip, and phase-flip. Each function returns
error vectors compatible with syndrome-based decoding.
"""

from typing import Optional

import numpy as np


def depolarizingChannel(
    nQubits: int,
    p: float,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """Sample error labels from the depolarizing channel.

    Each qubit independently suffers X, Y, or Z error with probability p/3 each.
    Returns a length-nQubits array with values: 0 (I), 1 (X), 2 (Y), 3 (Z).
    """
    if rng is None:
        rng = np.random.default_rng()
    p = float(np.clip(p, 0.0, 1.0))
    return rng.choice(4, size=nQubits, p=[1 - p, p / 3, p / 3, p / 3])


def depolarizingErrors(
    nQubits: int,
    p: float,
    rng: Optional[np.random.Generator] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Sample X and Z error vectors from the depolarizing channel.

    Y errors contribute to both X and Z components.
    Returns (xErrors, zErrors) as binary vectors.
    """
    labels = depolarizingChannel(nQubits, p, rng)
    xErrors = ((labels == 1) | (labels == 2)).astype(int)
    zErrors = ((labels == 2) | (labels == 3)).astype(int)
    return xErrors, zErrors


def bitflipChannel(
    nQubits: int,
    p: float,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """Sample an X error vector from the bit-flip (BSC) channel.

    Each qubit independently suffers an X error with probability p.
    Returns a binary vector of length nQubits.
    """
    if rng is None:
        rng = np.random.default_rng()
    p = float(np.clip(p, 0.0, 1.0))
    return rng.binomial(1, p, size=nQubits).astype(int)


def phaseflipChannel(
    nQubits: int,
    p: float,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """Sample a Z error vector from the phase-flip channel.

    Each qubit independently suffers a Z error with probability p.
    Returns a binary vector of length nQubits.
    """
    if rng is None:
        rng = np.random.default_rng()
    p = float(np.clip(p, 0.0, 1.0))
    return rng.binomial(1, p, size=nQubits).astype(int)
