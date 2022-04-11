import numpy as np

from typing import Tuple, List


def serializeComplexArray(data: np.ndarray) -> Tuple[List, List]:
    return (np.real(data).tolist(), np.imag(data).tolist())
