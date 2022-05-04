"""This module contains functions required for serialization.

Since we use zerorpc for RPC, we need to serialize non-pythonic datatypes.
"""

from typing import List, Tuple, Dict, Any, Union
import numpy as np

try:
    from uhd_wrapper.usrp_pybinding import RfConfig as RfConfigServer
except ImportError:
    RfConfigServer = None
from uhd_wrapper.utils.config import RfConfig as RfConfigClient

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
        ValueError: Number of samples msut match

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


def serializeRfConfig(
    conf: Union[RfConfigClient, RfConfigServer]
) -> Dict[str, Dict[str, Any]]:
    """Serializes the radio frontend configuration.

    Args:
        conf (Union[RfConfigClient, RfConfigServer]): Configuration to be serialized.

    Returns:
        Dict[str, Dict[str, Any]]: Serialized configuration.
    """
    return {
        "rx": {
            "analogFilterBw": conf.rxAnalogFilterBw,
            "carrierFrequency": conf.rxCarrierFrequency,
            "gain": conf.rxGain,
            "samplingRate": conf.rxSamplingRate,
        },
        "tx": {
            "analogFilterBw": conf.txAnalogFilterBw,
            "carrierFrequency": conf.txCarrierFrequency,
            "gain": conf.txGain,
            "samplingRate": conf.txSamplingRate,
        },
    }


def deserializeRfConfig(serializedConf: Dict[str, Dict[str, Any]]) -> RfConfigClient:
    """Deserializes dict into RfConfig.

    Args:
        serializedConf (Dict[str, Dict[str, Any]]): Dictionary containing configuration.

    Returns:
        RfConfigClient: Rf configuration.
    """
    conf = RfConfigClient()
    conf.txSamplingRate = serializedConf["tx"]["samplingRate"]
    conf.txGain = serializedConf["tx"]["gain"]
    conf.txCarrierFrequency = serializedConf["tx"]["carrierFrequency"]
    conf.txAnalogFilterBw = serializedConf["tx"]["analogFilterBw"]
    conf.rxSamplingRate = serializedConf["rx"]["samplingRate"]
    conf.rxGain = serializedConf["rx"]["gain"]
    conf.rxCarrierFrequency = serializedConf["rx"]["carrierFrequency"]
    conf.rxAnalogFilterBw = serializedConf["rx"]["analogFilterBw"]
    return conf
