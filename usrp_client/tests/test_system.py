import unittest
from unittest.mock import Mock
import time

import numpy as np
import numpy.testing as npt
from zerorpc.exceptions import RemoteError

from usrp_client.rpc_client import UsrpClient
from usrp_client.system import System, TimedFlag
from usrp_client.errors import RemoteUsrpError
from uhd_wrapper.utils.config import (
    MimoSignal,
    RfConfig,
    TxStreamingConfig,
    RxStreamingConfig,
)


class TestSystemInitialization(unittest.TestCase):
    def setUp(self) -> None:
        self.system = System()
        self.mockUsrpClient = Mock()

        self.system._createUsrpClient = Mock()  # type: ignore
        self.system._createUsrpClient.return_value = self.mockUsrpClient  # type: ignore

    def test_usrpClientGetsCreated(self) -> None:
        IP = "localhost"
        self.system.addUsrp(RfConfig(), IP, "dummyName")
        self.system._createUsrpClient.assert_called_once_with(IP)  # type: ignore

    def test_throwExceptionIfIpDuplicate_ip(self) -> None:
        self.system.addUsrp(RfConfig(), "localhost", "testName")
        self.assertRaises(
            ValueError,
            lambda: self.system.addUsrp(RfConfig(), "localhost", "testName2"),
        )

    def test_throwExceptionIfDuplicate_usrpName(self) -> None:
        self.system.addUsrp(RfConfig(), "localhost", "testName")
        self.assertRaises(
            ValueError,
            lambda: self.system.addUsrp(RfConfig(), "192.168.189.131", "testName"),
        )

    def test_rfConfigPassedToRpcClient(self) -> None:
        c = RfConfig()
        self.system.addUsrp(c, "localhost", "testusrp")
        self.mockUsrpClient.configureRfConfig.assert_called_once_with(c)

    def test_streamingConfigsAreReset(self) -> None:
        c = RfConfig()
        self.system.addUsrp(c, "localhost", "testusrp")
        self.mockUsrpClient.resetStreamingConfigs.assert_called_once()


class FakedTimeFlag(TimedFlag):
    def _startTimer(self) -> None:
        pass


class FakeSystem(System):
    def __init__(
        self,
        noUsrps: int,
        resyncFlag: TimedFlag = FakedTimeFlag(0.0),
        mockSyncValid: bool = True,
    ) -> None:
        super().__init__()
        self.__noUsrps = 0
        self._createUsrpClient = Mock(side_effect=[])  # type: ignore
        self._sleep = Mock(spec=System._sleep)  # type: ignore
        if mockSyncValid:
            self.synchronisationValid = Mock(return_value=True)  # type: ignore
        self._usrpsSynced = resyncFlag
        self.mockUsrps = [self.addNewUsrp() for _ in range(noUsrps)]

    synchronisationValid: Mock

    def addNewUsrp(self, usrpName: str = "") -> Mock:
        self.__noUsrps += 1
        mockedUsrp = Mock(spec=UsrpClient)
        mockedUsrp = self.__mockUsrpFunctions(mockedUsrp)
        if usrpName == "":
            usrpName = f"usrp{self.__noUsrps}"
        mockedUsrp.name = usrpName

        self._createUsrpClient.side_effect = list(  # type: ignore
            self._createUsrpClient.side_effect  # type: ignore
        ) + [mockedUsrp]
        super().addUsrp(RfConfig(), f"localhost{self.__noUsrps}", mockedUsrp.name)
        return mockedUsrp

    def __mockUsrpFunctions(self, usrpClientMock: Mock) -> Mock:
        usrpClientMock.getCurrentFpgaTime.return_value = 3.0
        usrpClientMock.getRfConfig.return_value = RfConfig()
        usrpClientMock.getMasterClockRate.return_value = 400e6
        return usrpClientMock


class TestStreamingConfiguration(unittest.TestCase):
    def setUp(self) -> None:
        self.system = FakeSystem(2)

    def test_configureTxCallsFunctionInRpcClient(self) -> None:
        txStreamingConfig = TxStreamingConfig(
            sendTimeOffset=2.0, samples=MimoSignal(signals=[0.2 * np.ones(int(20e3))])
        )
        self.system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig)
        self.system.mockUsrps[0].configureTx.assert_called_once_with(txStreamingConfig)
        self.system.mockUsrps[1].configureTx.assert_not_called()

    def test_configureRxCallsFunctionInRpcClient(self) -> None:
        rxStreamingConfig = RxStreamingConfig(
            receiveTimeOffset=2.0, noSamples=int(60e3)
        )
        self.system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig)
        self.system.mockUsrps[0].configureRx.assert_not_called()
        self.system.mockUsrps[1].configureRx.assert_called_once_with(rxStreamingConfig)

    def test_getRfConfigCallsAtEachUsrpDevice(self) -> None:
        _ = self.system.getRfConfigs()
        self.system.mockUsrps[0].getRfConfig.assert_called_once()
        self.system.mockUsrps[1].getRfConfig.assert_called_once()

    def test_getRfConfigReturnsDictOfRfConfigs(self) -> None:
        rfConfigs = self.system.getRfConfigs()
        self.assertTrue(isinstance(rfConfigs["usrp1"], RfConfig))
        self.assertTrue(isinstance(rfConfigs["usrp1"], RfConfig))

    def test_txSignalContainsClippedValues(self) -> None:
        txStreamingConfig = TxStreamingConfig(
            sendTimeOffset=2.0,
            samples=MimoSignal(
                signals=[0.1 * np.ones(int(20e3)), 1.1 * np.ones(int(20e3))]
            ),
        )
        self.assertRaises(
            ValueError,
            lambda: self.system.configureTx(
                usrpName="usrp1", txStreamingConfig=txStreamingConfig
            ),
        )

    def test_txSignalContainsValueThatAreExact1(self) -> None:
        txStreamingConfig = TxStreamingConfig(
            sendTimeOffset=2.0,
            samples=MimoSignal(
                signals=[0.1 * np.ones(int(20e3)), 1 * np.ones(int(20e3))]
            ),
        )
        self.system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig)


class TestMultiDeviceSync(unittest.TestCase):
    def setUp(self) -> None:
        self.system = FakeSystem(2)

    def test_synchronisationValidCheckedUponExecution(self) -> None:
        self.system.execute()
        self.system.synchronisationValid.assert_called_once()

    def test_syncOnlyPerformedIfNotAlreadySynced(self) -> None:
        self.system.execute()
        self.system.synchronisationValid.assert_called_once()
        self.system.synchronisationValid.reset_mock()
        self.system.execute()
        self.system.synchronisationValid.assert_not_called()

    def test_reSyncIfNewUsrpAdded(self) -> None:
        self.system.execute()
        self.system.synchronisationValid.assert_called_once()
        self.system.synchronisationValid.reset_mock()
        _ = self.system.addNewUsrp()

        self.system.synchronisationValid = Mock(side_effect=[False, True])  # type: ignore
        self.system.execute()
        self.assertEqual(self.system.synchronisationValid.call_count, 2)

    def test_threeTimesSyncRaisesError(self) -> None:
        self.system.synchronisationValid = Mock(return_value=False)  # type: ignore
        self.assertRaises(RuntimeError, lambda: self.system.execute())
        self.assertEqual(self.system.synchronisationValid.call_count, 4)

    def test_syncValidAfterSecondAttempt(self) -> None:
        self.system.synchronisationValid = Mock(  # type: ignore
            side_effect=[False, False, True]
        )
        self.system.execute()
        self.assertEqual(self.system.synchronisationValid.call_count, 3)

    def test_syncInvalidSetsPps(self) -> None:
        self.system.synchronisationValid = Mock(side_effect=[False, True])  # type: ignore
        self.system.execute()
        self.system.mockUsrps[0].setTimeToZeroNextPps.assert_called_once()
        self.system.mockUsrps[1].setTimeToZeroNextPps.assert_called_once()


class TestUsrpExceptionHandling(unittest.TestCase):
    def setUp(self) -> None:
        self.system = FakeSystem(1)

    def test_executeThrowsUsrpException_usrpNameFieldGetsSet(self) -> None:
        self.system.mockUsrps[0].execute.side_effect = RemoteError("", "foo", "")
        try:
            self.system.execute()
        except RemoteUsrpError as e:
            self.assertEqual(e.usrpName, self.system.mockUsrps[0].name)

    def test_collectThrowsUsrpException_usrpNameFieldGetsSet(self) -> None:
        self.system.mockUsrps[0].collect.side_effect = RemoteError("", "foo", "")
        try:
            self.system.collect()
        except RemoteUsrpError as e:
            self.assertEqual(e.usrpName, self.system.mockUsrps[0].name)

    def test_mismatchRfConfigThrowsUsrpException_usrpNameFieldGetsSet(self) -> None:
        self.system.mockUsrps[0].configureRfConfig.side_effect = RemoteError(
            "", "foo", ""
        )
        usrpName = "newUsrp"
        try:
            self.system.addNewUsrp(usrpName=usrpName)
        except RemoteUsrpError as e:
            self.assertEqual(e.usrpName, usrpName)


class TestSynchronisationValid(unittest.TestCase):
    def setUp(self) -> None:
        self.system = FakeSystem(2, mockSyncValid=False)

    def test_syncValidQueriesFpga(self) -> None:
        _ = self.system.synchronisationValid()
        self.system.mockUsrps[0].getCurrentFpgaTime.assert_called_once()
        self.system.mockUsrps[1].getCurrentFpgaTime.assert_called_once()

    def test_syncInvalidIfFpgaTimes_tooFarApart(self) -> None:
        self.system.mockUsrps[0].getCurrentFpgaTime.return_value = 3.0
        self.system.mockUsrps[0].getCurrentFpgaTime.return_value = (
            3.0 + System.syncThresholdSec + 1.0
        )
        self.assertFalse(self.system.synchronisationValid())

    def test_syncValidWhenFpgaTimesAreClose(self) -> None:
        self.system.mockUsrps[0].getCurrentFpgaTime.return_value = 3.0
        self.system.mockUsrps[0].getCurrentFpgaTime.return_value = (
            3.0 + System.syncThresholdSec - 0.1
        )
        self.assertTrue(self.system.synchronisationValid())


class TestSyncRecheck(unittest.TestCase):
    def setUp(self) -> None:
        self.syncTimeOut = 0.4
        self.sleepBeforeSyncTimeOut = 0.2
        self.sleepAfterSyncTimeOut = 0.2
        System.syncTimeOut = self.syncTimeOut
        self.system = FakeSystem(2, TimedFlag(resetTimeSec=self.syncTimeOut))

    def test_recheckSyncAfterSomeTime_syncValidAfterFirstAttempt(self) -> None:
        self.system.execute()
        time.sleep(self.syncTimeOut - self.sleepBeforeSyncTimeOut)
        self.system.synchronisationValid.assert_called_once()
        self.system.synchronisationValid.reset_mock()

        time.sleep(self.sleepBeforeSyncTimeOut + self.sleepAfterSyncTimeOut)
        self.system.synchronisationValid = Mock(side_effect=[False, True])  # type: ignore
        self.system.execute()
        self.assertEqual(self.system.synchronisationValid.call_count, 2)

    def test_recheckSyncAfterSomeTime_syncValidAfterSecondAttempt(self) -> None:
        self.system.execute()
        time.sleep(self.syncTimeOut - self.sleepBeforeSyncTimeOut)
        self.system.synchronisationValid.assert_called_once()
        self.system.synchronisationValid.reset_mock()

        time.sleep(self.sleepBeforeSyncTimeOut + self.sleepAfterSyncTimeOut)
        self.system.synchronisationValid = Mock(  # type: ignore
            side_effect=[False, False, True]
        )
        self.system.execute()
        self.assertEqual(self.system.synchronisationValid.call_count, 3)  # type: ignore

    def test_syncValidAfterResetSyncFlagTimerTimedOut(self) -> None:
        self.system.synchronisationValid = Mock(side_effect=[False, True])  # type: ignore
        self.system.execute()
        self.assertEqual(self.system.synchronisationValid.call_count, 2)

        time.sleep(self.syncTimeOut + self.sleepAfterSyncTimeOut)
        self.system.synchronisationValid = Mock(return_value=True)  # type: ignore
        self.system.execute()
        self.assertEqual(self.system.synchronisationValid.call_count, 1)


class TestTransceivingMultiDevice(unittest.TestCase):
    def setUp(self) -> None:
        self.system = FakeSystem(2)

    def test_collectCallsCollectFromUsrpClient(self) -> None:
        samplesUsrp1 = MimoSignal(signals=[0.5 * np.ones(10)])
        samplesUsrp2 = MimoSignal(signals=[0.1 * np.ones(10)])

        self.system.mockUsrps[0].collect.return_value = [samplesUsrp1]
        self.system.mockUsrps[1].collect.return_value = [samplesUsrp2]
        samples = self.system.collect()
        npt.assert_array_equal(samples["usrp1"][0], samplesUsrp1)
        npt.assert_array_equal(samples["usrp2"][0], samplesUsrp2)

    def test_calculationBaseTime_validSynchronisation(self) -> None:
        FPGA_TIME_S_USRP1 = 0.3
        FPGA_TIME_S_USRP2 = 0.4

        self.system.mockUsrps[0].getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP1
        self.system.mockUsrps[1].getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP2
        expectedBaseTime = FPGA_TIME_S_USRP2 + System.baseTimeOffsetSec
        self.system.execute()
        self.system.mockUsrps[0].execute.assert_called_once_with(expectedBaseTime)
        self.system.mockUsrps[1].execute.assert_called_once_with(expectedBaseTime)

    def test_getSamplingRates(self) -> None:
        supportedSamplingRates = np.array([200e6])
        self.system.mockUsrps[
            0
        ].getSupportedSamplingRates.return_value = supportedSamplingRates
        actualSamplingRates = self.system.getSupportedSamplingRates(usrpName="usrp1")

        npt.assert_array_equal(actualSamplingRates, supportedSamplingRates)

    def test_signalContainsClippedValues(self) -> None:
        self.system.mockUsrps[0].collect.return_value = [
            MimoSignal(signals=[np.ones(10, dtype=np.complex64)])
        ]

        self.assertRaises(ValueError, lambda: self.system.collect())

    def test_signalContainsTwoParts_oneContainsClippedValues_oneNot(self) -> None:
        self.system.mockUsrps[0].collect.return_value = [
            MimoSignal(
                signals=[
                    np.ones(10, dtype=np.complex64),
                    np.zeros(10, dtype=np.complex64),
                ]
            )
        ]

        self.assertRaises(ValueError, lambda: self.system.collect())
