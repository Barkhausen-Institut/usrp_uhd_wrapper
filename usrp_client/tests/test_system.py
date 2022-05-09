import unittest
from unittest.mock import Mock, patch
from typing import List
import pytest

import numpy as np
import numpy.testing as npt
from usrp_client.rpc_client import UsrpClient

from usrp_client.system import System
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

        self.system.createUsrpClient = Mock()  # type: ignore
        self.system.createUsrpClient.return_value = self.mockUsrpClient  # type: ignore

    def test_usrpClientGetsCreated(self) -> None:
        IP = "localhost"
        self.system.addUsrp(RfConfig(), IP, "dummyName")
        self.system.createUsrpClient.assert_called_once_with(IP)  # type: ignore

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


class SystemMockFactory:
    def mockSystem(self, system: System, noMockUsrps: int) -> List[Mock]:
        self.__noUsrps = 0
        system.createUsrpClient = Mock()  # type: ignore
        system.createUsrpClient.side_effect = []  # type: ignore
        mockUsrps = [self.addUsrp(system) for _ in range(noMockUsrps)]
        sleepPatcher = patch("time.sleep", return_value=None)
        _ = sleepPatcher.start()
        return mockUsrps

    def addUsrp(self, system: System) -> Mock:
        self.__noUsrps += 1
        mockedUsrp = Mock(spec=UsrpClient)
        mockedUsrp = self.__mockFunctions(mockedUsrp)
        system.createUsrpClient.side_effect = list(  # type: ignore
            system.createUsrpClient.side_effect  # type: ignore
        ) + [mockedUsrp]
        system.addUsrp(
            RfConfig(), f"localhost{self.__noUsrps}", f"usrp{self.__noUsrps}"
        )
        return mockedUsrp

    def __mockFunctions(self, usrpClientMock: Mock) -> Mock:
        usrpClientMock.getCurrentFpgaTime.return_value = 3.0
        usrpClientMock.getRfConfig.return_value = RfConfig()
        usrpClientMock.getMasterClockRate.return_value = 400e6
        return usrpClientMock


class TestStreamingConfiguration(unittest.TestCase, SystemMockFactory):
    def setUp(self) -> None:
        self.system = System()
        self.mockUsrps = self.mockSystem(self.system, 2)

    def test_configureTxCallsFunctionInRpcClient(self) -> None:
        txStreamingConfig = TxStreamingConfig(
            sendTimeOffset=2.0, samples=MimoSignal(signals=[0.2 * np.ones(int(20e3))])
        )
        self.system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig)
        self.mockUsrps[0].configureTx.assert_called_once_with(txStreamingConfig)
        self.mockUsrps[1].configureTx.assert_not_called()

    def test_configureRxCallsFunctionInRpcClient(self) -> None:
        rxStreamingConfig = RxStreamingConfig(
            receiveTimeOffset=2.0, noSamples=int(60e3)
        )
        self.system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig)
        self.mockUsrps[0].configureRx.assert_not_called()
        self.mockUsrps[1].configureRx.assert_called_once_with(rxStreamingConfig)

    def test_getRfConfigCallsAtEachUsrpDevice(self) -> None:
        _ = self.system.getRfConfigs()
        self.mockUsrps[0].getRfConfig.assert_called_once()
        self.mockUsrps[1].getRfConfig.assert_called_once()

    def test_getRfConfigReturnsDictOfRfConfigs(self) -> None:
        rfConfigs = self.system.getRfConfigs()
        self.assertTrue(isinstance(rfConfigs["usrp1"], RfConfig))
        self.assertTrue(isinstance(rfConfigs["usrp1"], RfConfig))


class TestMultiDeviceSync(unittest.TestCase, SystemMockFactory):
    def setUp(self) -> None:
        self.system = System()
        self.mockUsrps = self.mockSystem(self.system, 2)

    def test_synchronisationUponExecution(self) -> None:
        self.system.execute()
        self.mockUsrps[0].setTimeToZeroNextPps.assert_called_once()
        self.mockUsrps[1].setTimeToZeroNextPps.assert_called_once()

    def test_syncOnlyPerformedIfRequired(self) -> None:
        self.system.execute()
        self.mockUsrps[0].setTimeToZeroNextPps.assert_called_once()
        self.mockUsrps[1].setTimeToZeroNextPps.assert_called_once()

        self.mockUsrps[0].reset_mock()
        self.mockUsrps[1].reset_mock()
        self.system.execute()
        self.mockUsrps[0].setTimeToZeroNextPps.assert_not_called()
        self.mockUsrps[1].setTimeToZeroNextPps.assert_not_called()

    def test_reSyncIfNewUsrpAdded(self) -> None:
        self.system.execute()
        self.mockUsrps[0].setTimeToZeroNextPps.assert_called_once()
        self.mockUsrps[1].setTimeToZeroNextPps.assert_called_once()

        self.mockUsrps[0].reset_mock()
        self.mockUsrps[1].reset_mock()

        mockedUsrp = self.addUsrp(self.system)
        self.system.execute()
        self.mockUsrps[0].setTimeToZeroNextPps.assert_called_once()
        self.mockUsrps[1].setTimeToZeroNextPps.assert_called_once()
        mockedUsrp.setTimeToZeroNextPps.assert_called_once()

    def test_threeTimesSyncRaisesError(self) -> None:
        self.mockUsrps[0].getCurrentFpgaTime.side_effect = [1.0, 1.5, 2.0]
        self.mockUsrps[1].getCurrentFpgaTime.side_effect = [
            1.0 + System.syncThresholdSec + 1.0,
            1.0 + System.syncThresholdSec + 1.5,
            1.0 + System.syncThresholdSec + 2.0,
        ]

        self.assertRaises(RuntimeError, lambda: self.system.execute())
        self.assertEqual(self.mockUsrps[0].setTimeToZeroNextPps.call_count, 3)
        self.assertEqual(self.mockUsrps[1].setTimeToZeroNextPps.call_count, 3)

    def test_syncValidAfterSecondAttempt(self) -> None:
        self.mockUsrps[0].getCurrentFpgaTime.side_effect = [
            1.0,
            1.5,
            1.6,
        ]
        self.mockUsrps[1].getCurrentFpgaTime.side_effect = [
            1.0 + System.syncThresholdSec + 0.1,
            1.5 + System.syncThresholdSec,
            1.6 + 0.01,
        ]

        self.system.execute()
        self.assertEqual(self.mockUsrps[0].setTimeToZeroNextPps.call_count, 2)
        self.assertEqual(self.mockUsrps[1].setTimeToZeroNextPps.call_count, 2)


class TestTransceivingMultiDevice(unittest.TestCase, SystemMockFactory):
    def setUp(self) -> None:
        self.system = System()
        self.mockUsrps = self.mockSystem(self.system, 2)

    def test_collectCallsCollectFromUsrpClient(self) -> None:
        samplesUsrp1 = MimoSignal(signals=[0.5 * np.ones(10)])
        samplesUsrp2 = MimoSignal(signals=[0.1 * np.ones(10)])

        self.mockUsrps[0].collect.return_value = [samplesUsrp1]
        self.mockUsrps[1].collect.return_value = [samplesUsrp2]
        samples = self.system.collect()
        npt.assert_array_equal(samples["usrp1"][0], samplesUsrp1)
        npt.assert_array_equal(samples["usrp2"][0], samplesUsrp2)

    def test_calculationBaseTime_validSynchronisation(self) -> None:
        FPGA_TIME_S_USRP1 = 0.3
        FPGA_TIME_S_USRP2 = 0.4

        self.mockUsrps[0].getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP1
        self.mockUsrps[1].getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP2
        expectedBaseTime = FPGA_TIME_S_USRP2 + System.baseTimeOffsetSec
        self.system.execute()
        self.mockUsrps[0].execute.assert_called_once_with(expectedBaseTime)
        self.mockUsrps[1].execute.assert_called_once_with(expectedBaseTime)

    def test_calculationBaseTime_invalidSynchronisation(self) -> None:
        FPGA_TIME_S_USRP1 = 0.3
        FPGA_TIME_S_USRP2 = 1.5

        self.mockUsrps[0].getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP1
        self.mockUsrps[1].getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP2
        self.assertRaises(RuntimeError, lambda: self.system.execute())

    def test_getSamplingRates(self) -> None:
        supportedSamplingRates = np.array([200e6])
        self.mockUsrps[
            0
        ].getSupportedSamplingRates.return_value = supportedSamplingRates
        actualSamplingRates = self.system.getSupportedSamplingRates(usrpName="usrp1")

        npt.assert_array_equal(actualSamplingRates, supportedSamplingRates)

    def test_signalContainsClippedValues(self) -> None:
        self.mockUsrps[0].collect.return_value = [
            MimoSignal(signals=[np.ones(10, dtype=np.complex64)])
        ]

        self.assertRaises(ValueError, lambda: self.system.collect())

    def test_signalContainsTwoParts_oneContainsClippedValues_oneNot(self) -> None:
        self.mockUsrps[0].collect.return_value = [
            MimoSignal(
                signals=[
                    np.ones(10, dtype=np.complex64),
                    np.zeros(10, dtype=np.complex64),
                ]
            )
        ]

        self.assertRaises(ValueError, lambda: self.system.collect())


@pytest.mark.hardware
class TestHardwareFullFledged(unittest.TestCase):
    def test_dummy(self) -> None:
        self.assertTrue(1 == 1)
