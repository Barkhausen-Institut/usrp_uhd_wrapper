from dataclasses import fields
from typing import List

from uhd_wrapper.utils.serialization import (
    serializeComplexArray,
    deserializeComplexArray,
    SerializedComplexArray,
    serializeRfConfig,
    deserializeRfConfig,
)
from uhd_wrapper.usrp_pybinding import (
    Usrp,
    TxStreamingConfig,
    RxStreamingConfig,
)
from uhd_wrapper.usrp_pybinding import RfConfig as RfConfigBinding
from uhd_wrapper.utils.config import RfConfig


def RfConfigFromBinding(rfConfigBinding: RfConfigBinding) -> RfConfig:
    c = RfConfig()
    for field in fields(RfConfig):
        setattr(c, field.name, getattr(rfConfigBinding, field.name))
    return c


def RfConfigToBinding(rfConfig: RfConfig) -> RfConfigBinding:
    cBinding = RfConfigBinding()
    for field in fields(RfConfig):
        setattr(cBinding, field.name, getattr(rfConfig, field.name))
    return cBinding


class UsrpServer:
    def __init__(self, usrp: Usrp) -> None:
        self.__usrp = usrp

    def __del__(self) -> None:
        self.__usrp.reset()

    def configureTx(
        self, sendTimeOffset: float, samples: List[SerializedComplexArray]
    ) -> None:
        self.__usrp.setTxConfig(
            TxStreamingConfig(
                samples=[deserializeComplexArray(frame) for frame in samples],
                sendTimeOffset=sendTimeOffset,
            )
        )

    def configureRx(self, receiveTimeOffset: float, noSamples: int) -> None:
        self.__usrp.setRxConfig(
            RxStreamingConfig(noSamples=noSamples, receiveTimeOffset=receiveTimeOffset)
        )

    def configureRfConfig(self, serializedRfConfig: str) -> None:
        self.__usrp.setRfConfig(
            RfConfigToBinding(deserializeRfConfig(serializedRfConfig))
        )

    def execute(self, baseTime: float) -> None:
        self.__usrp.execute(baseTime)

    def setTimeToZeroNextPps(self) -> None:
        self.__usrp.setTimeToZeroNextPps()

    def collect(self) -> List[SerializedComplexArray]:
        samplesInFpga = self.__usrp.collect()
        return [serializeComplexArray(frame) for frame in samplesInFpga]

    def getCurrentFpgaTime(self) -> int:
        return self.__usrp.getCurrentFpgaTime()

    def getCurrentSystemTime(self) -> int:
        return self.__usrp.getCurrentSystemTime()

    def getRfConfig(self) -> str:
        return serializeRfConfig(RfConfigFromBinding(self.__usrp.getRfConfig()))

    def getMasterClockRate(self) -> float:
        return self.__usrp.getMasterClockRate()
