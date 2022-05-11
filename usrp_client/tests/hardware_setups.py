from typing import Tuple, List
import os

from uhd_wrapper.utils.config import (
    RfConfig,
)
from usrp_client.system import System


def getUsrpIps() -> Tuple[str, str]:
    envVariables = os.environ.keys()
    if "USRP1_IP" not in envVariables or "USRP2_IP" not in envVariables:
        raise RuntimeError("Environment variables USRP1_IP/USRP2_IP must be defined.")
    return (os.environ["USRP1_IP"], os.environ["USRP2_IP"])


class P2pHardwareSetup:
    def __init__(
        self,
        txGain: List[float],
        rxGain: List[float],
        rxSampleRate: float,
        txSampleRate: float,
        txFc: List[float],
        rxFc: List[float],
    ) -> None:
        self.rfConfig = RfConfig()
        self.rfConfig.rxAnalogFilterBw = 400e6
        self.rfConfig.txAnalogFilterBw = 400e6
        self.rfConfig.rxSamplingRate = rxSampleRate
        self.rfConfig.txSamplingRate = txSampleRate
        self.rfConfig.rxGain = rxGain
        self.rfConfig.txGain = txGain
        self.rfConfig.rxCarrierFrequency = rxFc
        self.rfConfig.txCarrierFrequency = txFc

    def connectUsrps(self) -> System:
        usrpIps = getUsrpIps()

        self.system = System()
        self.system.addUsrp(rfConfig=self.rfConfig, ip=usrpIps[0], usrpName="usrp1")
        self.system.addUsrp(rfConfig=self.rfConfig, ip=usrpIps[1], usrpName="usrp2")
        return self.system


class LocalTransmissionHardwareSetup:
    def __init__(
        self,
        txGain: List[float],
        rxGain: List[float],
        rxSampleRate: float,
        txSampleRate: float,
        txFc: List[float],
        rxFc: List[float],
    ) -> None:
        self.rfConfig = RfConfig()
        self.rfConfig.rxAnalogFilterBw = 400e6
        self.rfConfig.txAnalogFilterBw = 400e6
        self.rfConfig.rxSamplingRate = rxSampleRate
        self.rfConfig.txSamplingRate = txSampleRate
        self.rfConfig.rxGain = rxGain
        self.rfConfig.txGain = txGain
        self.rfConfig.rxCarrierFrequency = rxFc
        self.rfConfig.txCarrierFrequency = txFc

    def connectUsrps(self) -> System:
        usrpIps = getUsrpIps()

        self.system = System()
        self.system.addUsrp(rfConfig=self.rfConfig, ip=usrpIps[0], usrpName="usrp1")
        return self.system
