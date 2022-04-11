import numpy as np

from typing import Tuple, List


def serializeComplexArray(data: np.ndarray) -> Tuple[List, List]:
    data = np.squeeze(data)
    if (len(data.shape) == 2):
        raise ValueError("Array must be one dimensional!")
    return (np.real(data).tolist(), np.imag(data).tolist())


def deserializeComplexArray(data: Tuple[List, List]) -> np.ndarray:
    if len(data[0]) != len(data[1]):
        raise ValueError("""Number of imaginary samples
                            mismatches number of real samples.""")
    arr = np.array(data[0]) + 1j * np.array(data[1])
    return arr
