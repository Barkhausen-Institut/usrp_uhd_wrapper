"""This module contains classes and functions for configuring the USRPs"""

from typing import List
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
    """Describes the RF configuration of the USRP. In particular, carrier
    frequency, sampling rate, TX/RX gains are contained in this structure.
    Moreover, the stream to antenna mapping is described in the elements
    `txAntennaMapping` and `rxAntennaMapping`.

    """
    txAnalogFilterBw: float = 0.0
    rxAnalogFilterBw: float = 0.0
    txSamplingRate: float = 0.0
    rxSamplingRate: float = 0.0
    txGain: float = 0.0
    rxGain: float = 0.0
    txCarrierFrequency: float = 0.0
    rxCarrierFrequency: float = 0.0
    noTxStreams: int = 1
    noRxStreams: int = 1

    txAntennaMapping: List[int] = field(default_factory=list)
    """Describes the mapping from a TX stream to an according TX antenna. If not
    empty, contains a list which describes the stream mapping. The nth element
    of the list identifies the antenna index (zero-based) where the nth stream
    is transmitted from.

    If empty, uses a default mapping (i.e. first stream is mapped to first
    antenna, second stream to second antenna and so on), i.e. `[0, 1, 2, ...,
    noTxStreams-1]`.
    """

    rxAntennaMapping: List[int] = field(default_factory=list)
    """Describes the mapping from an RX antenna to the RX streams. Consider the
    `txAntennaMapping` for a description of the format.
    """

    def serialize(self) -> str:
        return self.to_json()  # type: ignore

    @staticmethod
    def deserialize(value: str) -> "RfConfig":
        return RfConfig.from_json(value)  # type: ignore


@dataclass
class RxStreamingConfig:
    receiveTimeOffset: float = 0.0
    noSamples: int = 0
    numRepetitions: int = 1
    repetitionPeriod: int = 0
    antennaPort: str = ""


@dataclass
class MimoSignal:
    signals: List[np.ndarray] = field(default_factory=list)

    """Each List item corresponds to one antenna frame."""

    def serialize(self) -> List[SerializedComplexArray]:
        return [serializeComplexArray(s) for s in self.signals]

    @staticmethod
    def deserialize(serialized: List[SerializedComplexArray]) -> "MimoSignal":
        return MimoSignal(signals=[deserializeComplexArray(s) for s in serialized])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MimoSignal):
            return False
        else:
            return np.sum([(a == b) for a, b in zip(self.signals, other.signals)])


def rxContainsClippedValue(mimoSignal: MimoSignal) -> bool:
    """Checks if `mimoSignal` contains values above 1.0 in absolute value."""
    for s in mimoSignal.signals:
        if np.any(np.abs(np.real(s)) >= 1.0) or np.any(np.abs(np.imag(s)) >= 1.0):
            return True
    return False


def txContainsClippedValue(mimoSignal: MimoSignal) -> bool:
    for s in mimoSignal.signals:
        if np.any(np.abs(np.real(s)) > 1.0) or np.any(np.abs(np.imag(s)) > 1.0):
            return True
    return False


@dataclass
class TxStreamingConfig:
    sendTimeOffset: float = 0.0
    """
    Offset in seconds from the basetime `System.execute()`.
    """

    samples: MimoSignal = field(  # type: ignore
        default_factory=lambda: [MimoSignal(signals=[])]
    )

    repetitions: int = 1
    """
    Determines how often the signal should be repeated before exiting. If
    not equal 1, the signal length must be aligned to the word size. Otherwise
    an error is raised.
    """
