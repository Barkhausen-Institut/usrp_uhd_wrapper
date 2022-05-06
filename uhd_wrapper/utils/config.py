from typing import List, Any
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

import numpy as np

from .serialization import (
    SerializedComplexArray,
    serializeComplexArray,
    deserializeComplexArray,
)


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

    def serialize(self) -> str:
        return self.to_json()  # type: ignore

    @staticmethod
    def deserialize(value: str) -> "RfConfig":
        return RfConfig.from_json(value)  # type: ignore


@dataclass
class RxStreamingConfig:
    receiveTimeOffset: float = 0.0
    noSamples: int = 0


@dataclass
class MimoSignal:
    signals: List[np.ndarray] = field(default_factory=list)

    def serialize(self) -> List[SerializedComplexArray]:
        return [serializeComplexArray(s) for s in self.signals]

    @staticmethod
    def deserialize(serialized: List[SerializedComplexArray]) -> "MimoSignal":
        return MimoSignal(signals=[deserializeComplexArray(s) for s in serialized])

    def __eq__(self, other: "MimoSignal") -> bool:
        return np.sum([(a == b) for a, b in zip(self.signals, other.signals)])


@dataclass
class TxStreamingConfig:
    sendTimeOffset: float = 0.0
    samples: MimoSignal = field(default_factory=list)  # type: ignore


def fillDummyRfConfig(conf: Any) -> Any:
    conf.txCarrierFrequency = [2e9]
    conf.txGain = [30]
    conf.txAnalogFilterBw = 200e6
    conf.txSamplingRate = 20e6

    conf.rxCarrierFrequency = [2.5e9]
    conf.rxGain = [40]
    conf.rxAnalogFilterBw = 100e6
    conf.rxSamplingRate = 30e6
    return conf
