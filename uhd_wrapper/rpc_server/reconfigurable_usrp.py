from typing import List
import time

import numpy as np

import uhd_wrapper.usrp_pybinding as pybinding
from uhd_wrapper.usrp_pybinding import (
    RfConfig,
    RxStreamingConfig,
    TxStreamingConfig,
    Usrp,
)


class RestartingUsrp:
    RestartTrials = 3

    def __init__(self, ip: str) -> None:
        self._ip = ip

        self._usrp = self._startUsrpMultipleTimes()

    def _startUsrpMultipleTimes(self) -> Usrp:
        for _ in range(self.RestartTrials):
            try:
                return pybinding.createUsrp(self._ip)
            except RuntimeError:
                print("Creation of USRP failed... Retrying after 2 seconds.")
                time.sleep(2)
        raise RuntimeError("Could not start USRP... exiting.")

    def setRfConfig(self, rfConfig: RfConfig) -> None:
        self._usrp.setRfConfig(rfConfig)

    def setRxConfig(self, rxConfig: RxStreamingConfig) -> None:
        self._usrp.setRxConfig(rxConfig)

    def setTxConfig(self, txConfig: TxStreamingConfig) -> None:
        self._usrp.setTxConfig(txConfig)

    def setTimeToZeroNextPps(self) -> None:
        self._usrp.setTimeToZeroNextPps()

    def getCurrentSystemTime(self) -> int:
        return self._usrp.getCurrentSystemTime()

    def getCurrentFpgaTime(self) -> int:
        return self._usrp.getCurrentFpgaTime()

    def execute(self, baseTime: float) -> None:
        self._usrp.execute(baseTime)

    def collect(self) -> List[List[np.ndarray]]:
        return self._usrp.collect()

    def resetStreamingConfigs(self) -> None:
        self._usrp.resetStreamingConfigs()

    def getMasterClockRate(self) -> float:
        return self._usrp.getMasterClockRate()

    def getRfConfig(self) -> RfConfig:
        return self._usrp.getRfConfig()


class MimoReconfiguringUsrp(RestartingUsrp):
    def __init__(self, ip: str) -> None:
        super().__init__(ip)
        self._currentRfConfig: RfConfig = None

    def setRfConfig(self, rfConfig: RfConfig) -> None:
        if self.__mimoConfigChanged(rfConfig):
            del self._usrp
            self._usrp = self._startUsrpMultipleTimes()
        self._usrp.setRfConfig(rfConfig)
        self._currentRfConfig = rfConfig

    def __mimoConfigChanged(self, newRfConfig: RfConfig) -> bool:
        hasChanged = False
        if self._currentRfConfig is not None:
            hasChanged = (
                self._currentRfConfig.noRxAntennas != newRfConfig.noRxAntennas
            ) or (self._currentRfConfig.noTxAntennas != newRfConfig.noTxAntennas)
        return hasChanged
