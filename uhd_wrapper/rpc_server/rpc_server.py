from dataclasses import fields
from typing import List, Dict, Any

from uhd_wrapper.utils.serialization import (
    serializeComplexArray,
    deserializeComplexArray,
    SerializedComplexArray,
    serializeRfConfig,
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

    def configureRfConfig(
        self,
        txGain: List[float],
        rxGain: List[float],
        txCarrierFrequency: List[float],
        rxCarrierFrequency: List[float],
        txAnalogFilterBw: float,
        rxAnalogFilterBw: float,
        txSamplingRate: float,
        rxSamplingRate: float,
    ) -> None:
        self.__usrp.setRfConfig(
            RfConfig(
                txGain=txGain,
                rxGain=rxGain,
                txCarrierFrequency=txCarrierFrequency,
                rxCarrierFrequency=rxCarrierFrequency,
                txAnalogFilterBw=txAnalogFilterBw,
                rxAnalogFilterBw=rxAnalogFilterBw,
                txSamplingRate=txSamplingRate,
                rxSamplingRate=rxSamplingRate,
            )
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

    def getRfConfig(self) -> Dict[str, Dict[str, Any]]:
        return serializeRfConfig(self.__usrp.getRfConfig())
