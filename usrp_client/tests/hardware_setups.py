from abc import ABC, abstractmethod
from typing import Tuple
import os

import numpy as np

from uhd_wrapper.utils.config import (
    TxStreamingConfig,
    RxStreamingConfig,
    RfConfig,
    MimoSignal,
)
from usrp_client.system import System


class HardwareSetup(ABC):
    @abstractmethod
    def createSystem(self) -> None:
        pass

    @abstractmethod
    def createStreamingConfigs(self, txSignal: np.ndarray) -> None:
        pass

    @abstractmethod
    def performConfiguration(self) -> None:
        pass

    def getUsrpIps(self) -> Tuple[str, str]:
        envVariables = os.environ.keys()
        if "USRP1_IP" not in envVariables or "USRP2_IP" not in envVariables:
            raise RuntimeError(
                "Environment variables USRP1_IP/USRP2_IP must be defined."
            )
        return (os.environ["USRP1_IP"], os.environ["USRP2_IP"])


def configure(hwSetup: HardwareSetup, txSignal: np.ndarray) -> System:
    hwSetup.createSystem()
    hwSetup.createStreamingConfigs(txSignal=txSignal)
    hwSetup.performConfiguration()
    return hwSetup.system  # type: ignore


class P2pHardwareSetup(HardwareSetup):
    def createSystem(self) -> None:
        rfConfig = RfConfig()
        rfConfig.rxAnalogFilterBw = 400e6
        rfConfig.txAnalogFilterBw = 400e6
        rfConfig.rxSamplingRate = 245.76e6
        rfConfig.txSamplingRate = 245.76e6
        rfConfig.rxGain = [35]
        rfConfig.txGain = [35]
        rfConfig.rxCarrierFrequency = [2e9]
        rfConfig.txCarrierFrequency = [2e9]
        usrpIps = self.getUsrpIps()

        self.system = System()
        self.system.addUsrp(rfConfig=rfConfig, ip=usrpIps[0], usrpName="usrp1")
        self.system.addUsrp(rfConfig=rfConfig, ip=usrpIps[1], usrpName="usrp2")

    def createStreamingConfigs(self, txSignal: np.ndarray) -> None:
        self.txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0, samples=MimoSignal(signals=[txSignal])
        )
        self.rxStreamingConfig2 = RxStreamingConfig(
            receiveTimeOffset=0.0, noSamples=int(60e3)
        )

    def performConfiguration(self) -> None:
        self.system.configureTx(
            usrpName="usrp1", txStreamingConfig=self.txStreamingConfig1
        )
        self.system.configureRx(
            usrpName="usrp2", rxStreamingConfig=self.rxStreamingConfig2
        )


class LocalTransmissionHardwareSetup(HardwareSetup):
    def createSystem(self) -> None:
        rfConfig = RfConfig()
        rfConfig.rxAnalogFilterBw = 400e6
        rfConfig.txAnalogFilterBw = 400e6
        rfConfig.rxSamplingRate = 245.76e6
        rfConfig.txSamplingRate = 245.76e6
        rfConfig.rxGain = [35]
        rfConfig.txGain = [35]
        rfConfig.rxCarrierFrequency = [2e9]
        rfConfig.txCarrierFrequency = [2e9]
        usrpIps = self.getUsrpIps()

        self.system = System()
        self.system.addUsrp(rfConfig=rfConfig, ip=usrpIps[0], usrpName="usrp1")

    def createStreamingConfigs(self, txSignal: np.ndarray) -> None:
        self.txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0, samples=MimoSignal(signals=[txSignal])
        )
        self.rxStreamingConfig1 = RxStreamingConfig(
            receiveTimeOffset=0.0, noSamples=int(60e3)
        )

    def performConfiguration(self) -> None:
        self.system.configureTx(
            usrpName="usrp1", txStreamingConfig=self.txStreamingConfig1
        )
        self.system.configureRx(
            usrpName="usrp1", rxStreamingConfig=self.rxStreamingConfig1
        )


class JcasHardwareSetup(HardwareSetup):
    def createSystem(self) -> None:
        rfConfig = RfConfig()
        rfConfig.rxAnalogFilterBw = 400e6
        rfConfig.txAnalogFilterBw = 400e6
        rfConfig.rxSamplingRate = 245.76e6
        rfConfig.txSamplingRate = 245.76e6
        rfConfig.rxGain = [35]
        rfConfig.txGain = [35]
        rfConfig.rxCarrierFrequency = [2e9]
        rfConfig.txCarrierFrequency = [2e9]
        usrpIps = self.getUsrpIps()

        self.system = System()
        self.system.addUsrp(rfConfig=rfConfig, ip=usrpIps[0], usrpName="usrp1")
        self.system.addUsrp(rfConfig=rfConfig, ip=usrpIps[1], usrpName="usrp2")

    def createStreamingConfigs(self, txSignal: np.ndarray) -> None:
        self.txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.1, samples=MimoSignal(signals=[txSignal])
        )
        self.rxStreamingConfig1 = RxStreamingConfig(
            receiveTimeOffset=0.1, noSamples=int(60e3)
        )
        self.rxStreamingConfig2 = RxStreamingConfig(
            receiveTimeOffset=0.1, noSamples=int(60e3)
        )

    def performConfiguration(self) -> None:
        self.system.configureTx(
            usrpName="usrp1", txStreamingConfig=self.txStreamingConfig1
        )
        self.system.configureRx(
            usrpName="usrp1", rxStreamingConfig=self.rxStreamingConfig1
        )

        self.system.configureRx(
            usrpName="usrp2", rxStreamingConfig=self.rxStreamingConfig2
        )
