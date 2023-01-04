from typing import Tuple, List, Optional
import unittest
import pytest
import os
import time

import matplotlib.pyplot as plt


import numpy as np

from uhd_wrapper.utils.config import (
    RfConfig,
    TxStreamingConfig,
    RxStreamingConfig,
    MimoSignal,
)
from usrp_client.system import System


def getIpUsrp1() -> str:
    envVariables = os.environ.keys()
    if "USRP1_IP" not in envVariables:
        raise RuntimeError("Environment variable USRP1_IP must be defined.")
    return os.environ["USRP1_IP"]


def getIpUsrp2() -> str:
    envVariables = os.environ.keys()
    if "USRP2_IP" not in envVariables:
        raise RuntimeError("Environment variable USRP2_IP must be defined.")
    return os.environ["USRP2_IP"]


def getUsrpIps() -> Tuple[str, str]:
    return (getIpUsrp1(), getIpUsrp2())


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
        *,
        txGain: float = 30,
        rxGain: float = 20,
        rxSampleRate: float = 12.288e6,
        txSampleRate: float = 12.288e6,
        txFc: float = 3.75e9,
        rxFc: float = 3.75e9,
        noRxAntennas: int,
        noTxAntennas: int,
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
        usrpIp = getIpUsrp1()

        self.system = System()
        self.system.addUsrp(rfConfig=self.rfConfig, ip=usrpIp, usrpName="usrp1")
        return self.system

    def propagateSignal(self, txSignals: List[np.ndarray],
                        system: Optional[System] = None) -> List[np.ndarray]:
        if system is None:
            system = self.connectUsrps()

        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0, samples=MimoSignal(signals=txSignals)
        )
        rxStreamingConfig1 = RxStreamingConfig(
            receiveTimeOffset=0.0, noSamples=int(60e3)
        )

        system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
        system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)

        system.execute()
        samplesSystem = system.collect()
        return samplesSystem["usrp1"][0].signals


@pytest.mark.hardware
class TestHardwareClocks(unittest.TestCase):
    def _createSystem(self, SetupClass: type) -> System:
        setup = SetupClass(noRxAntennas=1, noTxAntennas=1,
                           txSampleRate=245.76e6, rxSampleRate=245.76e6)

        return setup.connectUsrps()

    def test_singleUsrpResetFpgaTimes(self) -> None:
        system = self._createSystem(LocalTransmissionHardwareSetup)
        DELAY = 0.5

        system.resetFpgaTimes()
        fpgaTime1 = system.getCurrentFpgaTimes()[0]
        self.assertLess(fpgaTime1, 1.5)

        time.sleep(DELAY)
        fpgaTime2 = system.getCurrentFpgaTimes()[0]
        self.assertAlmostEqual(fpgaTime1 + DELAY, fpgaTime2, delta=0.1)

    def test_twoUsrpsAreSynchronized(self) -> None:
        system = self._createSystem(P2pHardwareSetup)

        system.resetFpgaTimes()
        fpgaTimes = system.getCurrentFpgaTimes()
        self.assertLess(abs(fpgaTimes[0] - fpgaTimes[1]), 0.05)


@pytest.mark.hardware
class TestSampleRateSettings(unittest.TestCase):
    def setUp(self) -> None:
        self.transmitF = 0.05
        self.txSignal = np.exp(1j*2*np.pi*self.transmitF*np.arange(20e3))

    def _transmitAndGetRxPeakFrequency(self, rxRate: float, txRate: float) -> float:
        setup = LocalTransmissionHardwareSetup(
            noRxAntennas=1, noTxAntennas=1, txSampleRate=txRate, rxSampleRate=rxRate)

        rxSamples = setup.propagateSignal([self.txSignal])[0]

        N = len(rxSamples)
        spec = np.fft.fft(rxSamples)[:N//2]
        peak = np.argmax(spec).item() / N

        return peak

    def test_equalSampleRateTxRx(self) -> None:
        fPeak = self._transmitAndGetRxPeakFrequency(rxRate=245.76e6 / 2, txRate=245.76e6 / 2)

        self.assertAlmostEqual(fPeak, self.transmitF, delta=0.01)

    def test_HigherTxSampleRate(self) -> None:
        fPeak = self._transmitAndGetRxPeakFrequency(rxRate=245.76e6 / 4, txRate=245.76e6 / 2)

        self.assertAlmostEqual(fPeak, self.transmitF * 2, delta=0.01)

    def test_LowerTxSampleRate(self) -> None:
        fPeak = self._transmitAndGetRxPeakFrequency(rxRate=245.76e6 / 2, txRate=245.76e6 / 6)

        self.assertAlmostEqual(fPeak, self.transmitF / 3, delta=0.01)


@pytest.mark.hardware
class TestCarrierFrequencySettings(unittest.TestCase):
    def setUp(self) -> None:
        self.transmitF = 25e6
        self.R = 245.76e6 / 2
        self.Fc = 3.75e9

        self.txSignal = np.exp(1j*2*np.pi*self.transmitF/self.R*np.arange(20e3))

    def _transmitAndGetRxPeakFrequency(self, sampleRate: float,
                                       txCarrier: float, rxCarrier: float) -> float:
        setup = LocalTransmissionHardwareSetup(
            noRxAntennas=1, noTxAntennas=1,
            txFc=txCarrier, rxFc=rxCarrier,
            txSampleRate=sampleRate, rxSampleRate=sampleRate)

        rxSamples = setup.propagateSignal([self.txSignal])[0]

        N = len(rxSamples)
        spec = np.fft.fft(rxSamples)[:N//2]
        peak = np.argmax(spec).item() / N

        return peak * self.R

    def test_equalCarriers(self) -> None:
        fPeak = self._transmitAndGetRxPeakFrequency(
            sampleRate=self.R, txCarrier=self.Fc, rxCarrier=self.Fc)
        self.assertAlmostEqual(fPeak, self.transmitF, delta=10e3)

    def test_10MHzOffset(self) -> None:
        Fo = 10e6

        fPeak = self._transmitAndGetRxPeakFrequency(
            sampleRate=self.R, txCarrier=self.Fc, rxCarrier=self.Fc+Fo)
        self.assertAlmostEqual(fPeak, self.transmitF-Fo, delta=10e3)


@pytest.mark.hardware
class TestHardwareSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.noSamples = int(20e3)
        self.randomSignal = (
            np.random.sample((self.noSamples,))
            + 1j * np.random.sample((self.noSamples,))
        ) - (0.5 + 0.5j)
        # self.randomSignal *= np.linspace(0, 1, self.noSamples)

    def test_reUseSystemTenTimes_oneTxAntennaFourRxAntennas_localhost(self) -> None:
        setup = LocalTransmissionHardwareSetup(noRxAntennas=4, noTxAntennas=1)
        system = setup.connectUsrps()

        for _ in range(10):
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

            self.assertEqual(
                first=findSignalStartsInFrame(rxSamplesUsrpAnt1, self.randomSignal),
                second=findSignalStartsInFrame(rxSamplesUsrpAnt2, self.randomSignal),
            )
            self.assertEqual(
                first=findSignalStartsInFrame(rxSamplesUsrpAnt1, self.randomSignal),
                second=findSignalStartsInFrame(rxSamplesUsrpAnt3, self.randomSignal),
            )
            self.assertEqual(
                first=findSignalStartsInFrame(rxSamplesUsrpAnt1, self.randomSignal),
                second=findSignalStartsInFrame(rxSamplesUsrpAnt4, self.randomSignal),
            )
            self.assertGreater(np.sum(np.abs(rxSamplesUsrpAnt1 - rxSamplesUsrpAnt2)), 1)
            self.assertGreater(np.sum(np.abs(rxSamplesUsrpAnt1 - rxSamplesUsrpAnt3)), 1)
            self.assertGreater(np.sum(np.abs(rxSamplesUsrpAnt1 - rxSamplesUsrpAnt4)), 1)

    def test_p2pTransmission(self) -> None:
        setup = P2pHardwareSetup(noRxAntennas=1, noTxAntennas=1)
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
        setup = LocalTransmissionHardwareSetup(noRxAntennas=1, noTxAntennas=1)
        setup.rfConfig.rxSamplingRate = 245.76e6 / 1
        setup.rfConfig.txSamplingRate = 245.76e6 / 1

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

        plt.plot(abs(rxSamplesUsrp1))
        plt.show()

        self.assertAlmostEqual(
            first=findSignalStartsInFrame(rxSamplesUsrp1, self.randomSignal),
            second=268,
            delta=10,
        )

    def test_jcas(self) -> None:
        setup = P2pHardwareSetup(noRxAntennas=1, noTxAntennas=1)
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

    def test_reuseOfSystemTenTimes_4tx1rx_localhost(self) -> None:
        # create setup
        setup = LocalTransmissionHardwareSetup(noRxAntennas=1, noTxAntennas=4)
        system = setup.connectUsrps()

        # create signal
        for _ in range(10):
            signalLength = 5000
            signalStarts = [int(10e3), int(20e3), int(30e3), int(40e3)]
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

            # norm signal
            mvAvgFilter = np.convolve(
                np.ones(signalLength // 2, dtype=np.complex64),
                np.abs(rxSamplesUsrpAnt1) ** 2,
                "same",
            )
            rxSamplesUsrpAnt1 /= np.sqrt(mvAvgFilter)

            signalStartsInFrame = [
                findSignalStartsInFrame(rxSamplesUsrpAnt1, antTxSignals[0]),
                findSignalStartsInFrame(rxSamplesUsrpAnt1, antTxSignals[1]),
                findSignalStartsInFrame(rxSamplesUsrpAnt1, antTxSignals[2]),
                findSignalStartsInFrame(rxSamplesUsrpAnt1, antTxSignals[3]),
            ]

            for antIdx in range(1, 4):
                self.assertEqual(
                    first=signalStartsInFrame[antIdx] - signalStartsInFrame[antIdx - 1],
                    second=signalStarts[antIdx] - signalStarts[antIdx - 1],
                )
