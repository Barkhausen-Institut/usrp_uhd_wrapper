from dataclasses import fields
from typing import List

from uhd_wrapper.utils.serialization import (
    SerializedComplexArray,
)
from uhd_wrapper.usrp_pybinding import (
    Usrp,
    TxStreamingConfig,
    RxStreamingConfig,
    UsrpException,
)
from uhd_wrapper.usrp_pybinding import RfConfig as RfConfigBinding
from uhd_wrapper.utils.config import RfConfig, MimoSignal
from uhd_wrapper.utils.annotated_usrp_exception import AnnotatedUsrpException


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

    def configureTx(
        self, sendTimeOffset: float, samples: List[SerializedComplexArray]
    ) -> None:
        mimoSignal = MimoSignal.deserialize(samples)
        self.__usrp.setTxConfig(
            TxStreamingConfig(
                samples=mimoSignal.signals,
                sendTimeOffset=sendTimeOffset,
            )
        )

    def configureRx(self, receiveTimeOffset: float, noSamples: int) -> None:
        self.__usrp.setRxConfig(
            RxStreamingConfig(noSamples=noSamples, receiveTimeOffset=receiveTimeOffset)
        )

    def configureRfConfig(self, serializedRfConfig: str) -> None:
        try:
            self.__usrp.setRfConfig(
                RfConfigToBinding(RfConfig.deserialize(serializedRfConfig))
            )
        except UsrpException as e:
            raise AnnotatedUsrpException(str(e))

    def execute(self, baseTime: float) -> None:
        try:
            self.__usrp.execute(baseTime)
        except UsrpException as e:
            raise AnnotatedUsrpException(str(e))

    def setTimeToZeroNextPps(self) -> None:
        self.__usrp.setTimeToZeroNextPps()

    def collect(self) -> List[List[SerializedComplexArray]]:
        try:
            mimoSignals = [MimoSignal(signals=c) for c in self.__usrp.collect()]
        except UsrpException as e:
            raise AnnotatedUsrpException(str(e))

        return [s.serialize() for s in mimoSignals]

    def getCurrentFpgaTime(self) -> int:
        return self.__usrp.getCurrentFpgaTime()

    def getCurrentSystemTime(self) -> int:
        return self.__usrp.getCurrentSystemTime()

    def getRfConfig(self) -> str:
        return RfConfigFromBinding(self.__usrp.getRfConfig()).serialize()

    def getMasterClockRate(self) -> float:
        return self.__usrp.getMasterClockRate()

    def resetStreamingConfigs(self) -> None:
        self.__usrp.resetStreamingConfigs()
