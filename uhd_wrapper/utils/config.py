from typing import List, Tuple
from dataclasses import dataclass, field

import numpy as np


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
