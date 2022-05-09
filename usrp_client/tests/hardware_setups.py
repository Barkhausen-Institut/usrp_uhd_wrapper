from abc import ABC, abstractmethod
from typing import Any, Tuple

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
    def createSystem(self) -> System:
        pass

    @abstractmethod
    def createStreamingConfigs(self, txSignal: np.ndarray) -> Any:
        pass


class P2PHardwareSetup(HardwareSetup):
    def createSystem(self) -> System:
        rfConfig = RfConfig()
        rfConfig.rxAnalogFilterBw = 400e6
        rfConfig.txAnalogFilterBw = 400e6
        rfConfig.rxSamplingRate = 245.76e6
        rfConfig.txSamplingRate = 245.76e6
        rfConfig.rxGain = [35]
        rfConfig.txGain = [35]
        rfConfig.rxCarrierFrequency = [2e9]
        rfConfig.txCarrierFrequency = [2e9]

        system = System()
        system.addUsrp(rfConfig=rfConfig, ip="192.168.189.132", usrpName="usrp1")
        system.addUsrp(rfConfig=rfConfig, ip="192.168.189.133", usrpName="usrp2")
        return system

    def createStreamingConfigs(
        self, txSignal: np.ndarray
    ) -> Tuple[TxStreamingConfig, RxStreamingConfig]:
        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0, samples=MimoSignal(signals=[txSignal])
        )
        rxStreamingConfig2 = RxStreamingConfig(
            receiveTimeOffset=0.0, noSamples=int(60e3)
        )
        return txStreamingConfig1, rxStreamingConfig2


class LocalTransmissionHWSetup(HardwareSetup):
    def createSystem(self) -> System:
        rfConfig = RfConfig()
        rfConfig.rxAnalogFilterBw = 400e6
        rfConfig.txAnalogFilterBw = 400e6
        rfConfig.rxSamplingRate = 245.76e6
        rfConfig.txSamplingRate = 245.76e6
        rfConfig.rxGain = [35]
        rfConfig.txGain = [35]
        rfConfig.rxCarrierFrequency = [2e9]
        rfConfig.txCarrierFrequency = [2e9]

        system = System()
        system.addUsrp(rfConfig=rfConfig, ip="192.168.189.132", usrpName="usrp1")
        return system

    def createStreamingConfigs(
        self, txSignal: np.ndarray
    ) -> Tuple[TxStreamingConfig, RxStreamingConfig]:
        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0, samples=MimoSignal(signals=[txSignal])
        )
        rxStreamingConfig1 = RxStreamingConfig(
            receiveTimeOffset=0.0, noSamples=int(60e3)
        )
        return txStreamingConfig1, rxStreamingConfig1


class JcasSetup(HardwareSetup):
    def createSystem(self) -> System:
        rfConfig = RfConfig()
        rfConfig.rxAnalogFilterBw = 400e6
        rfConfig.txAnalogFilterBw = 400e6
        rfConfig.rxSamplingRate = 245.76e6
        rfConfig.txSamplingRate = 245.76e6
        rfConfig.rxGain = [35]
        rfConfig.txGain = [35]
        rfConfig.rxCarrierFrequency = [2e9]
        rfConfig.txCarrierFrequency = [2e9]

        system = System()
        system.addUsrp(rfConfig=rfConfig, ip="192.168.189.132", usrpName="usrp1")
        system.addUsrp(rfConfig=rfConfig, ip="192.168.189.133", usrpName="usrp2")
        return system

    def createStreamingConfigs(
        self, txSignal: np.ndarray
    ) -> Tuple[Tuple[TxStreamingConfig, RxStreamingConfig], RxStreamingConfig]:
        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.1, samples=MimoSignal(signals=[txSignal])
        )
        rxStreamingConfig1 = RxStreamingConfig(
            receiveTimeOffset=0.1, noSamples=int(60e3)
        )
        rxStreamingConfig2 = RxStreamingConfig(
            receiveTimeOffset=0.1, noSamples=int(60e3)
        )

        return (txStreamingConfig1, rxStreamingConfig1), rxStreamingConfig2
