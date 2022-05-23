from typing import Tuple
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


def createRandom(noSamples: int) -> np.ndarray:
    return 2 * (
        np.random.sample((noSamples,)) + 1j * np.random.sample((noSamples,))
    ) - (1 + 1j)


def padSignal(noZeroPads: int, signal: np.ndarray) -> np.ndarray:
    return np.hstack([np.zeros(noZeroPads), signal])


def findSignalStartsInFrame(frame: np.ndarray, txSignal: np.ndarray) -> int:
    correlation = np.abs(np.correlate(frame, txSignal))
    return np.argsort(correlation)[-1]


class HardwareSetup:
    def __init__(
        self,
        txGain: float = 30,
        rxGain: float = 25,
        rxSampleRate: float = 12.288e6,
        txSampleRate: float = 12.288e6,
        txFc: float = 2e9,
        rxFc: float = 2e9,
        noRxAntennas: int = 4,
        noTxAntennas: int = 1,
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
        self.rfConfig.noRxAntennas = noRxAntennas
        self.rfConfig.noTxAntennas = noTxAntennas


class P2pHardwareSetup(HardwareSetup):
    def connectUsrps(self) -> System:
        usrpIps = getUsrpIps()
        self.system = System()
        self.system.addUsrp(rfConfig=self.rfConfig, ip=usrpIps[0], usrpName="usrp1")
        self.system.addUsrp(rfConfig=self.rfConfig, ip=usrpIps[1], usrpName="usrp2")
        return self.system


class LocalTransmissionHardwareSetup(HardwareSetup):
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

    def test_oneTxAntennaFourRxAntennas_localhost(self) -> None:
        setup = LocalTransmissionHardwareSetup()
        system = setup.connectUsrps()
        rxStreamingConfig1 = RxStreamingConfig(
            receiveTimeOffset=0.0, noSamples=int(60e3)
        )
        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0, samples=MimoSignal(signals=[self.randomSignal])
        )
        system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)
        system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
        system.execute()
        samplesSystem = system.collect()
        rxSamplesUsrpAnt1 = samplesSystem["usrp1"][0].signals[0]
        rxSamplesUsrpAnt2 = samplesSystem["usrp1"][0].signals[1]
        rxSamplesUsrpAnt3 = samplesSystem["usrp1"][0].signals[2]
        rxSamplesUsrpAnt4 = samplesSystem["usrp1"][0].signals[3]

        self.assertAlmostEqual(
            first=findSignalStartsInFrame(rxSamplesUsrpAnt1, self.randomSignal),
            second=findSignalStartsInFrame(rxSamplesUsrpAnt2, self.randomSignal),
            delta=1,
        )
        self.assertAlmostEqual(
            first=findSignalStartsInFrame(rxSamplesUsrpAnt1, self.randomSignal),
            second=findSignalStartsInFrame(rxSamplesUsrpAnt3, self.randomSignal),
            delta=1,
        )
        self.assertAlmostEqual(
            first=findSignalStartsInFrame(rxSamplesUsrpAnt1, self.randomSignal),
            second=findSignalStartsInFrame(rxSamplesUsrpAnt4, self.randomSignal),
            delta=1,
        )
        self.assertGreater(np.sum(np.abs(rxSamplesUsrpAnt1 - rxSamplesUsrpAnt2)), 1)
        self.assertGreater(np.sum(np.abs(rxSamplesUsrpAnt1 - rxSamplesUsrpAnt3)), 1)
        self.assertGreater(np.sum(np.abs(rxSamplesUsrpAnt1 - rxSamplesUsrpAnt4)), 1)

    def test_p2pTransmission(self) -> None:
        setup = P2pHardwareSetup()
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
            first=findSignalStartsInFrame(rxSamplesUsrp2, self.randomSignal),
            second=50,
            delta=10,
        )

    def test_localTransmission(self) -> None:
        setup = LocalTransmissionHardwareSetup()
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
            first=findSignalStartsInFrame(rxSamplesUsrp1, self.randomSignal),
            second=50,
            delta=10,
        )

    def test_jcas(self) -> None:
        setup = P2pHardwareSetup()
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
            first=findSignalStartsInFrame(rxSamplesUsrp1, self.randomSignal),
            second=50,
            delta=10,
        )
        self.assertAlmostEqual(
            first=findSignalStartsInFrame(rxSamplesUsrp2, self.randomSignal),
            second=50,
            delta=10,
        )


@pytest.mark.hardware_tx_mimo
class TestTxMimo(unittest.TestCase):
    def setUp(self) -> None:
        self.noSamples = int(20e3)
        self.randomSignal = (
            np.random.sample((self.noSamples,))
            + 1j * np.random.sample((self.noSamples,))
        ) - (0.5 + 0.5j)

    def test_fourTxAntennaOneRxAntenna_localhost(self) -> None:
        # create signal
        signalLength = 1000
        signalStarts = [0, int(10e3), int(20e3), int(30e3)]
        antTxSignals = [
            createRandom(signalLength),
            createRandom(signalLength),
            createRandom(signalLength),
            createRandom(signalLength),
        ]
        paddedAntTxSignals = []
        for antSignal, signalStart in zip(antTxSignals, signalStarts):
            s = np.zeros(int(50e3), dtype=np.complex64)
            s[signalStart + np.arange(antSignal.size)] = antSignal
            paddedAntTxSignals.append(s)

        # create setup
        setup = LocalTransmissionHardwareSetup(noTxAntennas=4, noRxAntennas=1)
        system = setup.connectUsrps()
        rxStreamingConfig1 = RxStreamingConfig(
            receiveTimeOffset=0.0, noSamples=int(60e3)
        )
        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0,
            samples=MimoSignal(signals=paddedAntTxSignals),
        )
        system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)
        system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
        system.execute()
        samplesSystem = system.collect()
        rxSamplesUsrpAnt1 = samplesSystem["usrp1"][0].signals[0]

        signalStartsInFrame = [
            findSignalStartsInFrame(rxSamplesUsrpAnt1, antTxSignals[0]),
            findSignalStartsInFrame(rxSamplesUsrpAnt1, antTxSignals[1]),
            findSignalStartsInFrame(rxSamplesUsrpAnt1, antTxSignals[2]),
            findSignalStartsInFrame(rxSamplesUsrpAnt1, antTxSignals[3]),
        ]

        for antIdx in range(1, 4):
            self.assertAlmostEqual(
                first=signalStartsInFrame[antIdx] - signalStartsInFrame[antIdx - 1],
                second=signalStarts[antIdx] - signalStarts[antIdx - 1],
                delta=0,
            )
