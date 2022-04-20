from typing import List

import zerorpc
import numpy as np

from utils.serialization import serializeComplexArray, deserializeComplexArray
from utils.config import RxStreamingConfig, TxStreamingConfig, RfConfig


class UsrpClient:
    def __init__(self, rpcClient: zerorpc.Client) -> None:
        self.__rpcClient = rpcClient

    def configureRx(self, rxConfig: RxStreamingConfig) -> None:
        self.__rpcClient.configureRx(rxConfig.receiveTimeOffset, rxConfig.noSamples)

    def configureTx(self, txConfig: TxStreamingConfig) -> None:
        self.__rpcClient.configureTx(
            txConfig.sendTimeOffset,
            [serializeComplexArray(antSignal) for antSignal in txConfig.samples],
        )

    def execute(self, baseTime: float) -> None:
        self.__rpcClient.execute(baseTime)

    def collect(self) -> List[np.ndarray]:
        return [deserializeComplexArray(frame) for frame in self.__rpcClient.collect()]

    def configureRfConfig(self, rfConfig: RfConfig) -> None:
        self.__rpcClient.configureRfConfig(
            rfConfig.txGain,
            rfConfig.rxGain,
            rfConfig.txCarrierFrequency,
            rfConfig.rxCarrierFrequency,
            rfConfig.txAnalogFilterBw,
            rfConfig.rxAnalogFilterBw,
            rfConfig.txSamplingRate,
            rfConfig.rxSamplingRate,
        )

    def setTimeToZeroNextPps(self) -> None:
        self.__rpcClient.setTimeToZeroNextPps()

    def getCurrentFpgaTime(self) -> int:
        return self.__rpcClient.getCurrentFpgaTime()

    def getCurrentSystemTime(self) -> int:
        return self.__rpcClient.getCurrentSystemTime()
