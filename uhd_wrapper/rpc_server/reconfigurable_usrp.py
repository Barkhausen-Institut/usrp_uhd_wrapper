from typing import List
import time
import sys

import uhd_wrapper.usrp_pybinding as pybinding
from uhd_wrapper.usrp_pybinding import RfConfig, RxStreamingConfig, TxStreamingConfig
from uhd_wrapper.utils.config import MimoSignal


class ReconfigurableUsrp:
    RestartTrials = 3

    def __init__(self, ip: str) -> None:
        startAttempt = 1
        usrpStarted = False
        while not usrpStarted and startAttempt <= self.RestartTrials:
            try:
                self.__usrp = pybinding.createUsrp(ip)
                usrpStarted = True
            except RuntimeError:
                print("Creation of USRP failed... Retrying after 2 seconds.")
                time.sleep(2)
                startAttempt += 1

        if not usrpStarted:
            sys.exit("Could not start USRP... exiting.")

    def setRfConfig(self, rfConfig: RfConfig) -> None:
        self.__usrp.setRfConfig(rfConfig)

    def setRxConfig(self, rxConfig: RxStreamingConfig) -> None:
        self.__usrp.setRxConfig(rxConfig)

    def setTxConfig(self, txConfig: TxStreamingConfig) -> None:
        self.__usrp.setTxConfig(txConfig)

    def setTimeToZeroNextPps(self) -> None:
        self.__usrp.setTimeToZeroNextPps()

    def getCurrentSystemTime(self) -> int:
        return self.__usrp.getCurrentSystemTime()

    def getCurrentFpgaTime(self) -> int:
        return self.__usrp.getCurrentFpgaTime()

    def execute(self, baseTime: float) -> None:
        self.__usrp.execute(baseTime)

    def collect(self) -> List[MimoSignal]:
        return [MimoSignal(signals=c) for c in self.__usrp.collect()]

    def resetStreamingConfigs(self) -> None:
        self.__usrp.resetStreamingConfigs()

    def getMasterClockRate(self) -> float:
        return self.__usrp.getMasterClockRate()

    def getRfConfig(self) -> RfConfig:
        return self.__usrp.getRfConfig()
