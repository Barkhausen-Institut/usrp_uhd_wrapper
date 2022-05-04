from typing import List, Union
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

import numpy as np

from uhd_wrapper.usrp_pybinding import RfConfig as RfConfigBinding


@dataclass_json
@dataclass
class RfConfig:
    txAnalogFilterBw: float = 0.0
    rxAnalogFilterBw: float = 0.0
    txSamplingRate: float = 0.0
    rxSamplingRate: float = 0.0
    txGain: List[float] = field(default_factory=list)
    rxGain: List[float] = field(default_factory=list)
    txCarrierFrequency: List[float] = field(default_factory=list)
    rxCarrierFrequency: List[float] = field(default_factory=list)


@dataclass
class TxStreamingConfig:
    sendTimeOffset: float = 0.0
    samples: List[np.ndarray] = field(default_factory=list)


@dataclass
class RxStreamingConfig:
    receiveTimeOffset: float = 0.0
    noSamples: int = 0


def fillDummyRfConfig(
    conf: Union[RfConfig, RfConfigBinding]
) -> Union[RfConfig, RfConfigBinding]:
    conf.txCarrierFrequency = [2e9]
    conf.txGain = [30]
    conf.txAnalogFilterBw = 200e6
    conf.txSamplingRate = 20e6

    conf.rxCarrierFrequency = [2.5e9]
    conf.rxGain = [40]
    conf.rxAnalogFilterBw = 100e6
    conf.rxSamplingRate = 30e6
    return conf
