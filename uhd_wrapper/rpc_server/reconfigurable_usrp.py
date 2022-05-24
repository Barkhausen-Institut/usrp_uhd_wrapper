from typing import List
import time
import sys

import uhd_wrapper.usrp_pybinding as pybinding
from uhd_wrapper.usrp_pybinding import RfConfig, RxStreamingConfig, TxStreamingConfig
from uhd_wrapper.utils.config import MimoSignal


class RestartingUsrp:
    RestartTrials = 3

    def __init__(self, ip: str) -> None:
        self._ip = ip

        usrpStarted = self._startUsrpMultipleTimes()
        if not usrpStarted:
            sys.exit("Could not start USRP... exiting.")

    def _startUsrpMultipleTimes(self) -> bool:
        startAttempt = 1
        usrpStarted = False
        while not usrpStarted and startAttempt <= self.RestartTrials:
            try:
                self._usrp = pybinding.createUsrp(self._ip)
                usrpStarted = True
            except RuntimeError:
                print("Creation of USRP failed... Retrying after 2 seconds.")
                time.sleep(2)
                startAttempt += 1
        return usrpStarted

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

    def collect(self) -> List[MimoSignal]:
        return [MimoSignal(signals=c) for c in self._usrp.collect()]

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
            _ = self._startUsrpMultipleTimes()
        self._usrp.setRfConfig(rfConfig)
        self._currentRfConfig = rfConfig

    def __mimoConfigChanged(self, newRfConfig: RfConfig) -> bool:
        hasChanged = False
        if self._currentRfConfig is not None:
            hasChanged = (
                self._currentRfConfig.noRxAntennas != newRfConfig.noRxAntennas
            ) or (self._currentRfConfig.noTxAntennas != newRfConfig.noTxAntennas)
        return hasChanged
