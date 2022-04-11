import numpy as np

from typing import Tuple, List


def serializeComplexArray(data: np.ndarray) -> Tuple[List, List]:
    data = np.squeeze(data)
    if (len(data.shape) == 2):
        raise ValueError("Array must be one dimensional!")
    return (np.real(data).tolist(), np.imag(data).tolist())
