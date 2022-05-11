from typing import Tuple, List
import unittest
import pytest
import os

import numpy as np

from uhd_wrapper.utils.config import (
    RfConfig,
    TxStreamingConfig,
    RxStreamingConfig,
    MimoSignal,
)
from usrp_client.system import System


def getUsrpIps() -> Tuple[str, str]:
    envVariables = os.environ.keys()
    if "USRP1_IP" not in envVariables or "USRP2_IP" not in envVariables:
        raise RuntimeError("Environment variables USRP1_IP/USRP2_IP must be defined.")
    return (os.environ["USRP1_IP"], os.environ["USRP2_IP"])


class HardwareSetup:
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


class P2pHardwareSetup(HardwareSetup):
    def connectUsrps(self) -> System:
        usrpIps = getUsrpIps()
        self.system = System()
        self.system.addUsrp(rfConfig=self.rfConfig, ip=usrpIps[0], usrpName="usrp1")
        self.system.addUsrp(rfConfig=self.rfConfig, ip=usrpIps[1], usrpName="usrp2")
        return self.system


class LocalTransmission(HardwareSetup):
    def connectUsrps(self) -> System:
        usrpIps = getUsrpIps()

        self.system = System()
        self.system.addUsrp(rfConfig=self.rfConfig, ip=usrpIps[0], usrpName="usrp1")
        return self.system


@pytest.mark.hardware
class TestHardwareSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.noSamples = int(20e3)
        self.randomSignal = (
            np.random.sample((self.noSamples,))
            + 1j * np.random.sample((self.noSamples,))
        ) - (0.5 + 0.5j)

    def findSignalStartsInFrame(self, frame: np.ndarray, txSignal: np.ndarray) -> int:
        correlation = np.abs(np.correlate(frame, txSignal))
        return np.argsort(correlation)[-1]

    def test_p2pTransmission(self) -> None:
        setup = P2pHardwareSetup(
            txGain=[35],
            rxGain=[35],
            rxSampleRate=245.76e6,
            txSampleRate=245.76e6,
            txFc=[2e9],
            rxFc=[2e9],
        )
        system = setup.connectUsrps()
        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0, samples=MimoSignal(signals=[self.randomSignal])
        )
        rxStreamingConfig2 = RxStreamingConfig(
            receiveTimeOffset=0.0, noSamples=int(60e3)
        )
        system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
        system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)
        system.execute()
        samplesSystems = system.collect()
        rxSamplesUsrp2 = samplesSystems["usrp2"][0].signals[0]

        self.assertAlmostEqual(
            first=self.findSignalStartsInFrame(rxSamplesUsrp2, self.randomSignal),
            second=300,
            delta=10,
        )

    def test_localTransmission(self) -> None:
        setup = LocalTransmissionHardwareSetup(
            txGain=[35],
            rxGain=[35],
            rxSampleRate=245.76e6,
            txSampleRate=245.76e6,
            txFc=[2e9],
            rxFc=[2e9],
        )
        system = setup.connectUsrps()
        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0, samples=MimoSignal(signals=[self.randomSignal])
        )
        rxStreamingConfig1 = RxStreamingConfig(
            receiveTimeOffset=0.0, noSamples=int(60e3)
        )

        system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
        system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)

        system.execute()
        samplesSystem = system.collect()
        rxSamplesUsrp1 = samplesSystem["usrp1"][0].signals[0]

        self.assertAlmostEqual(
            first=self.findSignalStartsInFrame(rxSamplesUsrp1, self.randomSignal),
            second=300,
            delta=10,
        )

    def test_jcas(self) -> None:
        setup = P2pHardwareSetup(
            txGain=[35],
            rxGain=[35],
            rxSampleRate=245.76e6,
            txSampleRate=245.76e6,
            txFc=[2e9],
            rxFc=[2e9],
        )
        system = setup.connectUsrps()
        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.1, samples=MimoSignal(signals=[self.randomSignal])
        )
        rxStreamingConfig1 = RxStreamingConfig(
            receiveTimeOffset=0.1, noSamples=int(60e3)
        )
        rxStreamingConfig2 = RxStreamingConfig(
            receiveTimeOffset=0.1, noSamples=int(60e3)
        )
        system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
        system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)

        system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)

        system.execute()
        samplesSystem = system.collect()
        rxSamplesUsrp1 = samplesSystem["usrp1"][0].signals[0]
        rxSamplesUsrp2 = samplesSystem["usrp2"][0].signals[0]

        self.assertAlmostEqual(
            first=self.findSignalStartsInFrame(rxSamplesUsrp1, self.randomSignal),
            second=300,
            delta=10,
        )
        self.assertAlmostEqual(
            first=self.findSignalStartsInFrame(rxSamplesUsrp2, self.randomSignal),
            second=300,
            delta=10,
        )
