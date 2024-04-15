from typing import Tuple, List, Optional, Union
import unittest
import pytest
import os
import time
from collections import namedtuple
import logging

LOGGER = logging.getLogger(__name__)

import matplotlib.pyplot as plt  # noqa

import numpy as np
import numpy.testing as nt

from uhd_wrapper.utils.config import (
    RfConfig,
    TxStreamingConfig,
    RxStreamingConfig,
    MimoSignal,
)
from usrp_client import System, UsrpClient


IPandPort = namedtuple("IPandPort", "ip port")


def getIpUsrp1() -> IPandPort:
    envVariables = os.environ.keys()
    if "USRP1_IP" not in envVariables:
        raise RuntimeError("Environment variable USRP1_IP must be defined.")
    return IPandPort(ip=os.environ["USRP1_IP"],
                     port=os.environ.get("USRP1_PORT", 5555))


def getIpUsrp2() -> IPandPort:
    envVariables = os.environ.keys()
    if "USRP2_IP" not in envVariables:
        raise RuntimeError("Environment variable USRP2_IP must be defined.")
    return IPandPort(ip=os.environ["USRP2_IP"],
                     port=os.environ.get("USRP2_PORT", 5555))


def getUsrpIps() -> Tuple[IPandPort, IPandPort]:
    return (getIpUsrp1(), getIpUsrp2())


def skipIfFsNotSupported(Fs: Union[List[float], float],
                         dev: Union[List[UsrpClient], UsrpClient]) -> None:
    Fs = [Fs] if type(Fs) is float else Fs
    dev = [dev] if type(dev) is UsrpClient else dev

    # needed to satisfy mypy
    assert type(Fs) is list
    assert type(dev) is list

    for d in dev:
        for f in Fs:
            if f not in d.getSupportedSampleRates():
                pytest.skip(f"Samplerate {f/1e6}MHz not supported by device {d.ip}:{d.port}")


def skipIfAntennaCountNotAvailable(requiredAntennaCount: int,
                                   devices: Union[UsrpClient, List[UsrpClient]]) -> None:

    # ensure devices is a list
    devices = [devices] if type(devices) is UsrpClient else devices
    assert type(devices) is list   # needed to satisfy mypy

    for dev in devices:
        avail = dev.getNumAntennas()
        if avail < requiredAntennaCount:
            pytest.skip(f"{requiredAntennaCount} antennas needed, {avail} available.")


def createRandom(numSamples: int) -> np.ndarray:
    return 2 * (
        np.random.sample((numSamples,)) + 1j * np.random.sample((numSamples,))
    ) - (1 + 1j)


def padSignal(noZeroPads: int, signal: np.ndarray) -> np.ndarray:
    return np.hstack([np.zeros(noZeroPads), signal])


def findMultipleSignalStartsInFrame(frame: np.ndarray,
                                    txSignal: np.ndarray, numPeaks: int = 1) -> np.ndarray:
    import scipy.signal as S  # type: ignore
    correlation = abs(S.correlate(frame, txSignal, mode='valid'))
    return np.argsort(correlation)[-numPeaks:]


def findSignalStartInFrame(frame: np.ndarray, txSignal: np.ndarray) -> int:
    return findMultipleSignalStartsInFrame(frame, txSignal, numPeaks=1)[0]


class HardwareSetup:
    def __init__(
        self,
        *,
        txGain: float = 20,
        rxGain: float = 20,
        rxSampleRate: float = 1 / 4,
        txSampleRate: float = 1 / 4,
        txFc: float = 3.75e9,
        rxFc: float = 3.75e9,
        noRxStreams: int,
        noTxStreams: int,
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
        self.rfConfig.noRxStreams = noRxStreams
        self.rfConfig.noTxStreams = noTxStreams

    def _adjustSamplingRates(self, masterClockRate: float) -> None:
        def adjust(samplingRate: float) -> float:
            if samplingRate <= 1:
                if abs(np.round(1/samplingRate) - 1/samplingRate) > 0.01:
                    msg = f"Relative sampling rate {samplingRate} is not a valid relative rate"
                    raise RuntimeError(msg)
                result = samplingRate * masterClockRate
                LOGGER.info("Adjusting relative sampling rate " +
                            f"1/{1/samplingRate:.0f} to {result/1e6:.2f}MHz")
                return result
            else:
                return samplingRate

        self.rfConfig.txSamplingRate = adjust(self.rfConfig.txSamplingRate)
        self.rfConfig.rxSamplingRate = adjust(self.rfConfig.rxSamplingRate)


class P2pHardwareSetup(HardwareSetup):
    def connectUsrps(self) -> System:
        usrpIps = getUsrpIps()
        self.system = System()
        dev1 = self.system.newUsrp(ip=usrpIps[0].ip, usrpName="usrp1", port=usrpIps[0].port)
        dev2 = self.system.newUsrp(ip=usrpIps[1].ip, usrpName="usrp2", port=usrpIps[1].port)

        mc = dev1.getMasterClockRate()
        if mc != dev2.getMasterClockRate():
            raise RuntimeError("Devices with unequal clock rates not supported!")
        self._adjustSamplingRates(mc)

        skipIfFsNotSupported([self.rfConfig.rxSamplingRate, self.rfConfig.txSamplingRate],
                             [dev1, dev2])
        skipIfAntennaCountNotAvailable(
            max(self.rfConfig.noRxStreams, self.rfConfig.noTxStreams),
            [dev1, dev2])

        dev1.configureRfConfig(self.rfConfig)
        dev2.configureRfConfig(self.rfConfig)
        return self.system


class LocalTransmissionHardwareSetup(HardwareSetup):
    def connectUsrps(self) -> System:
        usrpIp = getIpUsrp1()

        self.system = System()
        device = self.system.newUsrp(ip=usrpIp.ip, usrpName="usrp1", port=usrpIp.port)
        self._adjustSamplingRates(device.getMasterClockRate())

        skipIfFsNotSupported([self.rfConfig.rxSamplingRate, self.rfConfig.txSamplingRate],
                             device)
        skipIfAntennaCountNotAvailable(
            max(self.rfConfig.noRxStreams, self.rfConfig.noTxStreams),
            device)

        device.configureRfConfig(self.rfConfig)
        return self.system

    def propagateSignal(self, txSignals: List[np.ndarray],
                        system: Optional[System] = None) -> List[np.ndarray]:
        if system is None:
            system = self.connectUsrps()

        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0, samples=MimoSignal(signals=txSignals)
        )
        rxStreamingConfig1 = RxStreamingConfig(
            receiveTimeOffset=0.0, numSamples=int(60e3)
        )

        system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
        system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)

        system.execute()
        samplesSystem = system.collect()
        return samplesSystem["usrp1"][0].signals


@pytest.mark.hardware
@pytest.mark.basic_hardware
class TestHardwareClocks(unittest.TestCase):
    def _createSystem(self, SetupClass: type) -> System:
        setup = SetupClass(noRxStreams=1, noTxStreams=1,
                           txSampleRate=1, rxSampleRate=1)

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

        system.synchronizeUsrps()
        fpgaTimes = system.getCurrentFpgaTimes()
        self.assertLess(abs(fpgaTimes[0] - fpgaTimes[1]), 0.05)


@pytest.mark.hardware
@pytest.mark.basic_hardware
class TestSampleRateSettings(unittest.TestCase):
    def setUp(self) -> None:
        self.transmitF = 0.05
        self.txSignal = np.exp(1j*2*np.pi*self.transmitF*np.arange(20e3))

    def _transmitAndGetRxPeakFrequency(self, rxRate: float, txRate: float) -> float:
        setup = LocalTransmissionHardwareSetup(
            noRxStreams=1, noTxStreams=1, txSampleRate=txRate, rxSampleRate=rxRate)

        rxSamples = setup.propagateSignal([self.txSignal])[0]

        N = len(rxSamples)
        spec = np.fft.fft(rxSamples)[:N//2]
        peak = np.argmax(spec).item() / N

        return peak

    def test_equalSampleRateTxRx(self) -> None:
        fPeak = self._transmitAndGetRxPeakFrequency(rxRate=1 / 2, txRate=1 / 2)

        self.assertAlmostEqual(fPeak, self.transmitF, delta=0.01)

    def test_HigherTxSampleRate(self) -> None:
        fPeak = self._transmitAndGetRxPeakFrequency(rxRate=0.25, txRate=0.5)

        self.assertAlmostEqual(fPeak, self.transmitF * 2, delta=0.01)

    def test_LowerTxSampleRate(self) -> None:
        fPeak = self._transmitAndGetRxPeakFrequency(rxRate=1 / 2, txRate=1 / 6)

        self.assertAlmostEqual(fPeak, self.transmitF / 3, delta=0.01)


@pytest.mark.hardware
@pytest.mark.basic_hardware
class TestSingleDevice(unittest.TestCase):
    def setUp(self) -> None:
        self.numSamples = 20000
        self.randomSignal = (
            np.random.sample((self.numSamples,))
            + 1j * np.random.sample((self.numSamples,))
        ) - (0.5 + 0.5j)

    def _getDevice(self, Fs: float) -> UsrpClient:
        setup = HardwareSetup(noRxStreams=1, noTxStreams=1,
                              txSampleRate=Fs, rxSampleRate=Fs)
        dev = UsrpClient(ip=getIpUsrp1().ip, port=getIpUsrp1().port)
        setup._adjustSamplingRates(dev.getMasterClockRate())
        skipIfFsNotSupported(setup.rfConfig.txSamplingRate, dev)

        dev.setSyncSource("internal")
        dev.configureRfConfig(setup.rfConfig)
        return dev

    def _executeNow(self, dev: UsrpClient,
                    txSamples: np.ndarray, noRxSamples: int) -> np.ndarray:
        dev.configureTx(TxStreamingConfig(sendTimeOffset=0.0,
                                          samples=MimoSignal(signals=[txSamples])))
        dev.configureRx(RxStreamingConfig(receiveTimeOffset=0.0,
                                          numSamples=noRxSamples))
        dev.executeImmediately()
        return dev.collect()[0].signals[0]

    def test_executeImmediate(self) -> None:
        dev = self._getDevice(Fs=1)
        rxSignal = [self._executeNow(dev, self.randomSignal, 30000)
                    for i in range(3)]

        peaks = [findSignalStartInFrame(rx, self.randomSignal)
                 for rx in rxSignal]
        self.assertLessEqual(max(peaks) - min(peaks), 2,
                             msg=f"Peaks {peaks} too far apart")

    def test_allowsOddTxRxSampleCount(self) -> None:
        dev = self._getDevice(Fs=1)
        signal = np.append(self.randomSignal, [0])
        rxSignal = [self._executeNow(dev, signal, 30001) for _ in range(2)]

        self.assertEqual(len(rxSignal[0]), 30001)
        self.assertAlmostEqual(findSignalStartInFrame(rxSignal[0], signal),
                               findSignalStartInFrame(rxSignal[1], signal),
                               delta=2)

    @pytest.mark.FS_400MHz
    def test_400MHzMIMO_ImmediateExecute(self) -> None:
        dev = self._getDevice(Fs=491.52e6)

        N = 10000
        OFF = 11000
        L = 100000
        signals = [np.random.sample((N,)) + 1j*np.random.sample((N,))-0.5-0.5j
                   for _ in range(4)]

        padded = [np.zeros((L,), dtype=complex) for _ in range(4)]
        for i in range(4):
            padded[i][OFF * i + np.arange(N)] = signals[i]

        dev.configureTx(TxStreamingConfig(sendTimeOffset=0.0,
                                          samples=MimoSignal(signals=padded)))
        dev.configureRx(RxStreamingConfig(receiveTimeOffset=0.0,
                                          numSamples=L))

        dev.executeImmediately()
        rxSignal = dev.collect()[0].signals

        for rx in range(4):
            for tx in range(4):
                peak = findSignalStartInFrame(rxSignal[rx], signals[tx])
                self.assertAlmostEqual(peak, 346 + OFF * tx, delta=5)


@pytest.mark.hardware
@pytest.mark.basic_hardware
class TestCarrierFrequencySettings(unittest.TestCase):
    def setUp(self) -> None:
        self.transmitF = 1/10
        self.R = 1 / 2
        self.Fc = 3.75e9

        self.txSignal = np.exp(1j*2*np.pi*self.transmitF*np.arange(20e3))

    def _transmitAndGetRxPeakFrequency(self, sampleRate: float, txCarrier: float,
                                       rxCarrier: float) -> Tuple[float, float]:
        setup = LocalTransmissionHardwareSetup(
            noRxStreams=1, noTxStreams=1,
            txFc=txCarrier, rxFc=rxCarrier,
            txSampleRate=sampleRate, rxSampleRate=sampleRate)

        rxSamples = setup.propagateSignal([self.txSignal])[0]

        N = len(rxSamples)
        spec = np.fft.fft(rxSamples)[:N//2]
        peak = np.argmax(spec).item() / N

        return peak, setup.rfConfig.txSamplingRate

    def test_equalCarriers(self) -> None:
        fPeak, realSampleRate = self._transmitAndGetRxPeakFrequency(
            sampleRate=self.R, txCarrier=self.Fc, rxCarrier=self.Fc)
        self.assertAlmostEqual(fPeak, self.transmitF, delta=1e-2)

    def test_10MHzOffset(self) -> None:
        Fo = 10e6

        fPeak, realSampleRate = self._transmitAndGetRxPeakFrequency(
            sampleRate=self.R, txCarrier=self.Fc, rxCarrier=self.Fc+Fo)
        self.assertAlmostEqual(fPeak, self.transmitF-Fo/realSampleRate, delta=1e-2)


@pytest.mark.hardware
class TestHardwareSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.numSamples = int(20e3)
        self.randomSignal = self.createRandom(self.numSamples)
        self.randomSignal2 = self.createRandom(self.numSamples)

    def createRandom(self, numSamples: int) -> np.ndarray:

        real = np.random.random(size=(numSamples,)) - 0.5
        imag = np.random.random(size=(numSamples,)) - 0.5
        return real + 1j*imag

    @pytest.mark.basic_hardware
    def test_allow2timesExecuteWithoutCrashing(self) -> None:
        setup = LocalTransmissionHardwareSetup(noRxStreams=1, noTxStreams=1)
        system = setup.connectUsrps()

        # Make sure, that if calling code crashes between calls to execute and collect, that
        # the usrp can cope with that.
        system.execute()
        system.execute()

    @pytest.mark.basic_hardware
    def test_doesNotCrashOnZeroLengthRxSignal(self) -> None:
        setup = LocalTransmissionHardwareSetup(noRxStreams=1, noTxStreams=1)
        system = setup.connectUsrps()

        system.configureRx(usrpName="usrp1", rxStreamingConfig=RxStreamingConfig(
            0.0, numSamples=0))

        system.execute()
        result = system.collect()
        self.assertEqual(len(result["usrp1"][0].signals[0]), 0)

    def test_2x2mimo_localhost(self) -> None:
        setup = LocalTransmissionHardwareSetup(
            noRxStreams=2, noTxStreams=2,
            txSampleRate=1 / 2, rxSampleRate=1 / 2)
        system = setup.connectUsrps()

        tx = np.zeros((2, 2*self.numSamples+2000), dtype=complex)
        tx[0, :self.numSamples] = self.randomSignal
        tx[1, self.numSamples+2000:] = self.randomSignal2

        txSignal = MimoSignal(signals=[tx[0, :], tx[1, :]])
        system.configureTx(
            usrpName="usrp1",
            txStreamingConfig=TxStreamingConfig(
                sendTimeOffset=0.0, samples=txSignal
            )
        )
        system.configureRx(
            usrpName="usrp1", rxStreamingConfig=RxStreamingConfig(
                receiveTimeOffset=0.0, numSamples=int(3*self.numSamples)
            )
        )
        system.execute()
        rxSamples = system.collect()["usrp1"][0]
        rx1 = rxSamples.signals[0]
        rx2 = rxSamples.signals[1]

        # plt.subplot(221); plt.plot(abs(rx1))
        # plt.subplot(222); plt.plot(abs(rx2))
        # plt.show()

        self.assertAlmostEqual(
            first=findSignalStartInFrame(rx1, self.randomSignal),
            second=findSignalStartInFrame(rx2, self.randomSignal),
            delta=1
        )
        self.assertAlmostEqual(
            first=findSignalStartInFrame(rx1, self.randomSignal2),
            second=findSignalStartInFrame(rx2, self.randomSignal2),
            delta=1
        )

        txDist = (findSignalStartInFrame(rx1, self.randomSignal2) -
                  findSignalStartInFrame(rx1, self.randomSignal))
        self.assertAlmostEqual(txDist, self.numSamples + 2000, delta=1)

    @pytest.mark.basic_hardware
    def test_offsetTxAndRxConfigs_localhost(self) -> None:
        Fs = 1/20
        setup = LocalTransmissionHardwareSetup(noRxStreams=1, noTxStreams=1,
                                               txSampleRate=Fs, rxSampleRate=Fs)
        system = setup.connectUsrps()

        samplesOffset = 20000
        realSampleRate = setup.rfConfig.txSamplingRate
        timeOffset = samplesOffset / realSampleRate

        txSignal = MimoSignal(signals=[self.randomSignal])
        system.configureTx(usrpName="usrp1", txStreamingConfig=TxStreamingConfig(
            samples=txSignal, sendTimeOffset=timeOffset))
        system.configureRx(usrpName="usrp1", rxStreamingConfig=RxStreamingConfig(
            receiveTimeOffset=0.0, numSamples=int(60e3)))

        system.execute()
        rxSignal = system.collect()["usrp1"][0].signals[0]

        # plt.plot(abs(rxSignal))
        # plt.show()

        peak = findSignalStartInFrame(rxSignal, self.randomSignal)
        self.assertAlmostEqual(peak, samplesOffset + 50, delta=10)

    @pytest.mark.basic_hardware
    def test_repeatTxSignals_localhost(self) -> None:
        Fs = 1
        setup = LocalTransmissionHardwareSetup(noRxStreams=1, noTxStreams=1,
                                               txSampleRate=Fs, rxSampleRate=Fs)

        system = setup.connectUsrps()
        txSamples = np.zeros(int(2**(np.ceil(np.log2(self.numSamples)))), dtype=complex)
        txSamples[:self.numSamples] = self.randomSignal

        txSignal = MimoSignal(signals=[txSamples])
        system.configureTx(usrpName="usrp1", txStreamingConfig=TxStreamingConfig(
            samples=txSignal, sendTimeOffset=0.0, numRepetitions=4))
        system.configureRx(usrpName="usrp1", rxStreamingConfig=RxStreamingConfig(
            receiveTimeOffset=0.0, numSamples=4*len(txSamples)))
        system.execute()
        rxSignal = system.collect()["usrp1"][0].signals[0]

        peaks = sorted(findMultipleSignalStartsInFrame(
            rxSignal, self.randomSignal, numPeaks=4))
        nt.assert_array_equal(np.diff(peaks), len(txSamples)*np.ones(3))

    @pytest.mark.basic_hardware
    def test_repeatRxBlocks_localhost(self) -> None:
        Fs = 1
        setup = LocalTransmissionHardwareSetup(noRxStreams=1, noTxStreams=1,
                                               txSampleRate=Fs, rxSampleRate=Fs)

        #  setup.rfConfig.txAntennaMapping=[2]
        # setup.rfConfig.rxAntennaMapping=[3]
        system = setup.connectUsrps()
        r1 = self.createRandom(2000)
        r2 = self.createRandom(2000)
        r3 = self.createRandom(2000)
        txSamples = np.zeros(3*4000, dtype=complex)
        txSamples[1000:3000] = r1
        txSamples[5000:7000] = r2
        txSamples[9000:11000] = r3

        system.configureTx(usrpName="usrp1", txStreamingConfig=TxStreamingConfig(
            samples=MimoSignal(signals=[txSamples]), sendTimeOffset=0.0))
        system.configureRx(usrpName="usrp1", rxStreamingConfig=RxStreamingConfig(
            receiveTimeOffset=0.0, numSamples=4000, numRepetitions=3, repetitionPeriod=4000,
            antennaPort="TX/RX"))
        system.execute()
        rxSignal = system.collect()["usrp1"]

        peaks = []
        for sig, ran in zip(rxSignal, [r1, r2, r3]):
            peaks.append(findSignalStartInFrame(sig.signals[0], ran))
        self.assertEqual(min(peaks), max(peaks))

    @pytest.mark.basic_hardware
    def test_multipleTxAndRxConfigs_localhost(self) -> None:
        Fs = 1/20
        setup = LocalTransmissionHardwareSetup(noRxStreams=1, noTxStreams=1,
                                               txSampleRate=Fs, rxSampleRate=Fs)
        system = setup.connectUsrps()

        samplesOffset = 20000
        realSampleRate = setup.rfConfig.txSamplingRate
        timeOffset = samplesOffset / realSampleRate

        txSignal = MimoSignal(signals=[self.randomSignal])
        system.configureTx(usrpName="usrp1", txStreamingConfig=TxStreamingConfig(
            samples=txSignal, sendTimeOffset=timeOffset))
        system.configureRx(usrpName="usrp1", rxStreamingConfig=RxStreamingConfig(
            receiveTimeOffset=0.0, numSamples=int(60e3)))

        system.configureTx(usrpName="usrp1", txStreamingConfig=TxStreamingConfig(
            samples=txSignal, sendTimeOffset=0.3))
        system.configureRx(usrpName="usrp1", rxStreamingConfig=RxStreamingConfig(
            receiveTimeOffset=0.3, numSamples=int(60e3)))

        system.execute()
        rx = system.collect()["usrp1"]
        rxSignal1 = rx[0].signals[0]
        rxSignal2 = rx[1].signals[0]

        delay = 50
        self.assertAlmostEqual(findSignalStartInFrame(rxSignal1, self.randomSignal),
                               samplesOffset + delay, delta=10)
        self.assertAlmostEqual(findSignalStartInFrame(rxSignal2, self.randomSignal),
                               delay, delta=10)

    def test_reUseSystem_oneTxAntennaFourRxAntennas_localhost(self) -> None:
        setup = LocalTransmissionHardwareSetup(noRxStreams=4, noTxStreams=1)
        system = setup.connectUsrps()

        for _ in range(3):
            rxStreamingConfig1 = RxStreamingConfig(
                receiveTimeOffset=0.0, numSamples=int(60e3)
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

            # plt.subplot(221); plt.plot(abs(rxSamplesUsrpAnt1))
            # plt.subplot(222); plt.plot(abs(rxSamplesUsrpAnt2))
            # plt.subplot(223); plt.plot(abs(rxSamplesUsrpAnt3))
            # plt.subplot(224); plt.plot(abs(rxSamplesUsrpAnt4))
            # plt.show()

            self.assertEqual(
                first=findSignalStartInFrame(rxSamplesUsrpAnt1, self.randomSignal),
                second=findSignalStartInFrame(rxSamplesUsrpAnt2, self.randomSignal),
            )
            self.assertEqual(
                first=findSignalStartInFrame(rxSamplesUsrpAnt1, self.randomSignal),
                second=findSignalStartInFrame(rxSamplesUsrpAnt3, self.randomSignal),
            )
            self.assertEqual(
                first=findSignalStartInFrame(rxSamplesUsrpAnt1, self.randomSignal),
                second=findSignalStartInFrame(rxSamplesUsrpAnt4, self.randomSignal),
            )
            self.assertGreater(np.sum(np.abs(rxSamplesUsrpAnt1 - rxSamplesUsrpAnt2)), 1)
            self.assertGreater(np.sum(np.abs(rxSamplesUsrpAnt1 - rxSamplesUsrpAnt3)), 1)
            self.assertGreater(np.sum(np.abs(rxSamplesUsrpAnt1 - rxSamplesUsrpAnt4)), 1)

    @pytest.mark.basic_hardware
    def test_p2pTransmission(self) -> None:
        setup = P2pHardwareSetup(noRxStreams=1, noTxStreams=1)
        system = setup.connectUsrps()
        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0, samples=MimoSignal(signals=[self.randomSignal])
        )
        rxStreamingConfig2 = RxStreamingConfig(
            receiveTimeOffset=0.0, numSamples=int(60e3)
        )

        peaks = []
        for _ in range(3):
            system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
            system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)
            system.execute()

            samplesSystems = system.collect()
            rxSamplesUsrp2 = samplesSystems["usrp2"][0].signals[0]
            peaks.append(findSignalStartInFrame(rxSamplesUsrp2, self.randomSignal))

        self.assertLess(max(peaks) - min(peaks), 4, msg=f"Peaks {peaks} are not equal")
        self.assertGreater(min(peaks), 20)

    def test_p2pWithPrecreatedUsrps(self) -> None:
        setup = P2pHardwareSetup(noRxStreams=1, noTxStreams=1)
        dev1 = UsrpClient(*getIpUsrp1())
        dev2 = UsrpClient(*getIpUsrp2())
        setup._adjustSamplingRates(dev1.getMasterClockRate())
        skipIfFsNotSupported([setup.rfConfig.rxSamplingRate, setup.rfConfig.txSamplingRate],
                             [dev1, dev2])

        dev1.configureRfConfig(setup.rfConfig)
        dev2.configureRfConfig(setup.rfConfig)

        system = System()
        system.addUsrp("usrp1", dev1)
        system.addUsrp("usrp2", dev2)

        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0, samples=MimoSignal(signals=[self.randomSignal])
        )
        rxStreamingConfig2 = RxStreamingConfig(
            receiveTimeOffset=0.0, numSamples=int(60e3)
        )
        peaks = []
        for _ in range(3):
            system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
            system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)
            system.execute()
            samplesSystems = system.collect()
            rxSamplesUsrp2 = samplesSystems["usrp2"][0].signals[0]
            peaks.append(findSignalStartInFrame(rxSamplesUsrp2, self.randomSignal))

        self.assertLess(max(peaks) - min(peaks), 4, msg=f"Peaks {peaks} are not equal")
        self.assertGreater(min(peaks), 20)

    @pytest.mark.basic_hardware
    def test_localTransmission(self) -> None:
        setup = LocalTransmissionHardwareSetup(noRxStreams=1, noTxStreams=1)
        setup.rfConfig.rxSamplingRate = 1
        setup.rfConfig.txSamplingRate = 1

        system = setup.connectUsrps()
        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.0, samples=MimoSignal(signals=[self.randomSignal])
        )
        rxStreamingConfig1 = RxStreamingConfig(
            receiveTimeOffset=0.0, numSamples=int(60e3)
        )

        rxSamples = []
        for _ in range(2):
            system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
            system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)

            system.execute()
            samplesSystem = system.collect()
            rxSamples.append(samplesSystem["usrp1"][0].signals[0])

        # plt.plot(abs(rxSamplesUsrp1))
        # plt.show()

        self.assertAlmostEqual(
            first=findSignalStartInFrame(rxSamples[0], self.randomSignal),
            second=findSignalStartInFrame(rxSamples[1], self.randomSignal),
            delta=2,
        )

    @pytest.mark.basic_hardware
    def test_longTxSignal_localhost(self) -> None:
        Fs = 1
        numFreqs = 50
        frequencies = (np.arange(numFreqs) + 1) / (4*numFreqs)
        numSamples = 200000
        sampsPerFreq = numSamples / numFreqs

        txSig = np.hstack([
            0.9*np.exp(1j*2*np.pi*f)**np.arange(sampsPerFreq)
            for f in frequencies
        ])

        setup = LocalTransmissionHardwareSetup(noRxStreams=1, noTxStreams=1,
                                               txSampleRate=Fs, rxSampleRate=Fs)
        system = setup.connectUsrps()
        txStreamingConfig = TxStreamingConfig(sendTimeOffset=0.0,
                                              samples=MimoSignal(signals=[txSig]))
        rxStreamingConfig = RxStreamingConfig(receiveTimeOffset=0.0,
                                              numSamples=numSamples+20000)

        system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig)
        system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig)

        system.execute()
        samplesRx = system.collect()["usrp1"][0].signals[0]
        samplesRx -= np.mean(samplesRx)  # remove DC component

        S = np.fft.fft(samplesRx)
        fIdx = (frequencies * len(S)).astype(int)
        SatF = abs(S[fIdx])
        self.assertTrue(np.all(SatF > 10*np.mean(abs(S))),
                        msg=f"{SatF=} not greater than {10*np.mean(abs(S))}")

        # plt.semilogy(abs(S), '-x')
        # plt.show()

    def test_jcas(self) -> None:
        setup = P2pHardwareSetup(noRxStreams=1, noTxStreams=1)
        system = setup.connectUsrps()
        txStreamingConfig1 = TxStreamingConfig(
            sendTimeOffset=0.1, samples=MimoSignal(signals=[self.randomSignal])
        )
        rxStreamingConfig1 = RxStreamingConfig(
            receiveTimeOffset=0.1, numSamples=int(60e3)
        )
        rxStreamingConfig2 = RxStreamingConfig(
            receiveTimeOffset=0.1, numSamples=int(60e3)
        )
        system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
        system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)

        system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)

        system.execute()
        samplesSystem = system.collect()
        rxSamplesUsrp1 = samplesSystem["usrp1"][0].signals[0]
        rxSamplesUsrp2 = samplesSystem["usrp2"][0].signals[0]

        self.assertAlmostEqual(
            first=findSignalStartInFrame(rxSamplesUsrp1, self.randomSignal),
            second=findSignalStartInFrame(rxSamplesUsrp2, self.randomSignal),
            delta=2)

    def test_reuseOfSystem_4tx1rx_localhost(self) -> None:
        # create setup
        setup = LocalTransmissionHardwareSetup(noRxStreams=1, noTxStreams=4)
        system = setup.connectUsrps()

        # create signal
        for _ in range(3):
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
                receiveTimeOffset=0.1, numSamples=int(60e3)
            )
            txStreamingConfig1 = TxStreamingConfig(
                sendTimeOffset=0.1,
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
                findSignalStartInFrame(rxSamplesUsrpAnt1, antTxSignals[0]),
                findSignalStartInFrame(rxSamplesUsrpAnt1, antTxSignals[1]),
                findSignalStartInFrame(rxSamplesUsrpAnt1, antTxSignals[2]),
                findSignalStartInFrame(rxSamplesUsrpAnt1, antTxSignals[3]),
            ]

            for antIdx in range(1, 4):
                self.assertEqual(
                    first=signalStartsInFrame[antIdx] - signalStartsInFrame[antIdx - 1],
                    second=signalStarts[antIdx] - signalStarts[antIdx - 1],
                )
