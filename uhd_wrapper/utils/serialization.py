"""This module contains functions required for serialization.

Since we use zerorpc for RPC, we need to serialize non-pythonic datatypes.
"""

from typing import List, Tuple, Dict, Any, Union
import numpy as np

from uhd_wrapper.utils.config import RfConfig

SerializedComplexArray = Tuple[List, List]
"""Tuple containing real samples as `List` as first element
and complex samples as `List` as second element."""


def serializeComplexArray(data: np.ndarray) -> SerializedComplexArray:
    """Serialize a complex array.

    Args:
        data (np.ndarray): Onedimensional array of complex samples.

    Raises:
        ValueError: Array must be one dimensional.

    Returns:
        SerializedComplexArray: Serialized data.

    """
    data = np.squeeze(data)
    if len(data.shape) == 2:
        raise ValueError("Array must be one dimensional!")
    return (np.real(data).tolist(), np.imag(data).tolist())


def deserializeComplexArray(data: SerializedComplexArray) -> np.ndarray:
    """Deserialize into a complex array.

    Args:
        data (SerializedComplexArray): Samples.
    Raises:
        ValueError: Number of samples must match

    Returns:
        np.ndarray: One dimensional numpy array.
    """
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
