from typing import Tuple, List

from uhd_wrapper.utils.serialization import (
    serializeComplexArray,
    deserializeComplexArray,
    SerializedComplexArray,)
from uhd_wrapper.usrp_pybinding import Usrp, TxStreamingConfig, RxStreamingConfig, RfConfig



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
