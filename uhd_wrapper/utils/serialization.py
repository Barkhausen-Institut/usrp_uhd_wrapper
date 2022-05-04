from typing import List, Tuple
import numpy as np

from uhd_wrapper.utils.config import RfConfig

SerializedComplexArray = Tuple[List, List]


def serializeComplexArray(data: np.ndarray) -> SerializedComplexArray:
    data = np.squeeze(data)
    if len(data.shape) == 2:
        raise ValueError("Array must be one dimensional!")
    return (np.real(data).tolist(), np.imag(data).tolist())


def deserializeComplexArray(data: SerializedComplexArray) -> np.ndarray:
    if len(data[0]) != len(data[1]):
        raise ValueError(
            """Number of imaginary samples
                            mismatches number of real samples."""
        )
    arr = np.array(data[0]) + 1j * np.array(data[1])
    return arr


def serializeRfConfig(conf: RfConfig) -> str:
    return conf.to_json()  # type: ignore


def deserializeRfConfig(serializedConf: str) -> RfConfig:
    return RfConfig.from_json(serializedConf)  # type: ignore
