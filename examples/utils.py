from typing import Tuple

import numpy as np


def createRandom(noSamples: int, zeropad: int = 0) -> np.ndarray:
    return np.hstack(
        [
            np.zeros(zeropad, dtype=complex),
            np.random.rand(noSamples) + 1j * np.random.rand(noSamples),
        ]
    )


def findFirstSampleInFrameOfSignal(
    frame: np.ndarray, txSignal: np.ndarray
) -> Tuple[int, np.ndarray]:
    correlation = np.abs(np.correlate(frame, txSignal))
    return np.argsort(correlation)[-1], correlation
