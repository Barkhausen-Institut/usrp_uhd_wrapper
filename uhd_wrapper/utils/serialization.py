from typing import List, Tuple, Dict, Any, Union
import numpy as np
import json

from uhd_wrapper.usrp_pybinding import Usrp
from uhd_wrapper.usrp_pybinding import RfConfig as RfConfigServer
from usrp_client.config import RfConfig as RfConfigClient
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


def serializeClientRfConfig(conf: Union[RfConfigServer, RfConfigClient]) -> Dict[str, Dict[str, Any]]:
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


def deserializeRfConfigClient(serializedConf: Dict[str, Dict[str, Any]]) -> RfConfigClient:
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


def deserializeRfConfigServer(serializedConf: Dict[str, Dict[str, Any]]) -> RfConfigServer:
    conf = RfConfigServer()
    conf.txSamplingRate = serializedConf["tx"]["samplingRate"]
    conf.txGain = serializedConf["tx"]["gain"]
    conf.txCarrierFrequency = serializedConf["tx"]["carrierFrequency"]
    conf.txAnalogFilterBw = serializedConf["tx"]["analogFilterBw"]
    conf.rxSamplingRate = serializedConf["rx"]["samplingRate"]
    conf.rxGain = serializedConf["rx"]["gain"]
    conf.rxCarrierFrequency = serializedConf["rx"]["carrierFrequency"]
    conf.rxAnalogFilterBw = serializedConf["rx"]["analogFilterBw"]
    return conf
