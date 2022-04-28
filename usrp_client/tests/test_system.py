import unittest
from unittest.mock import Mock

import numpy as np
import numpy.testing as npt
from usrp_client.rpc_client import UsrpClient

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig, RxStreamingConfig


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


class TestStreamingConfiguration(unittest.TestCase):
    def setUp(self) -> None:
        self.system = System()
        self.mockUsrpClient1 = Mock(spec=UsrpClient)
        self.mockUsrpClient2 = Mock(spec=UsrpClient)
        self.mockUsrpClient1.getCurrentFpgaTime = Mock(return_value=3.0)
        self.mockUsrpClient2.getCurrentFpgaTime = Mock(return_value=3.0)

        self.system.createUsrpClient = Mock()  # type: ignore
        self.system.createUsrpClient.side_effect = [
            self.mockUsrpClient1,
            self.mockUsrpClient2,
        ]  # type: ignore

        self.system.addUsrp(RfConfig(), "localhost1", "usrp1")
        self.system.addUsrp(RfConfig(), "localhost2", "usrp2")

    def test_configureTxCallsFunctionInRpcClient(self) -> None:
        txStreamingConfig = TxStreamingConfig(
            sendTimeOffset=2.0, samples=[np.ones(int(2e3))]
        )
        self.system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig)
        self.mockUsrpClient1.configureTx.assert_called_once_with(txStreamingConfig)
        self.mockUsrpClient2.configureTx.assert_not_called()

    def test_configureRxCallsFunctionInRpcClient(self) -> None:
        rxStreamingConfig = RxStreamingConfig(
            receiveTimeOffset=2.0, noSamples=int(60e3)
        )
        self.system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig)
        self.mockUsrpClient1.configureRx.assert_not_called()
        self.mockUsrpClient2.configureRx.assert_called_once_with(rxStreamingConfig)


class TestMultiDeviceSync(unittest.TestCase):
    def setUp(self) -> None:
        self.system = System()
        self.mockUsrpClient1 = Mock(spec=UsrpClient)
        self.mockUsrpClient2 = Mock(spec=UsrpClient)
        self.mockUsrpClient3 = Mock(spec=UsrpClient)
        self.mockUsrpClient1.getCurrentFpgaTime = Mock(return_value=3.0)
        self.mockUsrpClient2.getCurrentFpgaTime = Mock(return_value=3.0)
        self.mockUsrpClient3.getCurrentFpgaTime = Mock(return_value=3.0)

        self.system.createUsrpClient = Mock()  # type: ignore
        self.system.createUsrpClient.side_effect = [
            self.mockUsrpClient1,
            self.mockUsrpClient2,
            self.mockUsrpClient3,
        ]  # type: ignore

        self.system.addUsrp(RfConfig(), "localhost1", "usrp1")
        self.system.addUsrp(RfConfig(), "localhost2", "usrp2")

    def test_synchronisationUponExecution(self) -> None:
        self.system.execute()
        self.mockUsrpClient1.setTimeToZeroNextPps.assert_called_once()
        self.mockUsrpClient2.setTimeToZeroNextPps.assert_called_once()

    def test_syncOnlyPerformedIfRequired(self) -> None:
        self.system.execute()
        self.mockUsrpClient1.setTimeToZeroNextPps.assert_called_once()
        self.mockUsrpClient2.setTimeToZeroNextPps.assert_called_once()

        self.mockUsrpClient1.reset_mock()
        self.mockUsrpClient2.reset_mock()
        self.system.execute()
        self.mockUsrpClient1.setTimeToZeroNextPps.assert_not_called()
        self.mockUsrpClient2.setTimeToZeroNextPps.assert_not_called()

    def test_reSyncIfNewUsrpAdded(self) -> None:
        self.system.execute()
        self.mockUsrpClient1.setTimeToZeroNextPps.assert_called_once()
        self.mockUsrpClient2.setTimeToZeroNextPps.assert_called_once()

        self.mockUsrpClient1.reset_mock()
        self.mockUsrpClient2.reset_mock()

        # add new usrp
        self.system.addUsrp(RfConfig(), "localhost3", "usrp3")
        self.system.execute()
        self.mockUsrpClient1.setTimeToZeroNextPps.assert_called_once()
        self.mockUsrpClient2.setTimeToZeroNextPps.assert_called_once()
        self.mockUsrpClient3.setTimeToZeroNextPps.assert_called_once()

    def test_throwExceptionIfSyncIsInvalid(self) -> None:
        fpgaTimeUsrp1 = 3.0
        fpgaTimeUsrp2 = fpgaTimeUsrp1 + System.syncThresholdSec + 1.0
        self.mockUsrpClient1.getCurrentFpgaTime.return_value = fpgaTimeUsrp1
        self.mockUsrpClient2.getCurrentFpgaTime.return_value = fpgaTimeUsrp2
        self.assertRaises(ValueError, lambda: self.system.execute())


class TestTransceivingMultiDevice(unittest.TestCase):
    def setUp(self) -> None:
        self.system = System()
        self.mockUsrpClient1 = Mock(spec=UsrpClient)
        self.mockUsrpClient2 = Mock(spec=UsrpClient)
        self.mockUsrpClient1.getCurrentFpgaTime.return_value = 3.0
        self.mockUsrpClient2.getCurrentFpgaTime.return_value = 3.0

        self.system.createUsrpClient = Mock()  # type: ignore
        self.system.createUsrpClient.side_effect = [
            self.mockUsrpClient1,
            self.mockUsrpClient2,
        ]  # type: ignore

        self.system.addUsrp(RfConfig(), "localhost1", "usrp1")
        self.system.addUsrp(RfConfig(), "localhost2", "usrp2")

    def test_collectCallsCollectFromUsrpClient(self) -> None:
        samplesUsrp1 = [np.ones(10)]
        samplesUsrp2 = [2 * np.ones(10)]
        self.mockUsrpClient1.collect.return_value = samplesUsrp1
        self.mockUsrpClient2.collect.return_value = samplesUsrp2
        samples = self.system.collect()
        npt.assert_array_equal(samples[0][0], samplesUsrp1[0])
        npt.assert_array_equal(samples[1][0], samplesUsrp2[0])

    def test_calculationBaseTime_validSynchronisation(self) -> None:
        FPGA_TIME_S_USRP1 = 0.3
        FPGA_TIME_S_USRP2 = 0.5
        BASE_TIME_OFFSET_SEC = 0.2

        System.syncThresholdSec = (
            1  # increase to make sure that no assertion is raised...
        )
        System.baseTimeOffsetSec = BASE_TIME_OFFSET_SEC
        self.mockUsrpClient1.getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP1
        self.mockUsrpClient2.getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP2
        expectedBaseTime = FPGA_TIME_S_USRP2 + BASE_TIME_OFFSET_SEC
        self.system.execute()
        self.mockUsrpClient1.execute.assert_called_once_with(expectedBaseTime)
        self.mockUsrpClient2.execute.assert_called_once_with(expectedBaseTime)

    def test_calculationBaseTime_invalidSynchronisation(self) -> None:
        FPGA_TIME_S_USRP1 = 0.3
        FPGA_TIME_S_USRP2 = 0.5
        BASE_TIME_OFFSET_SEC = 0.2

        System.syncThresholdSec = (
            0.01  # decrease to make sure that assertion is raised...
        )
        System.baseTimeOffsetSec = BASE_TIME_OFFSET_SEC
        self.mockUsrpClient1.getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP1
        self.mockUsrpClient2.getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP2
        self.assertRaises(ValueError, lambda: self.system.execute())

    def test_calculationBaseTimeNarrowStreamingOffsets(self) -> None:
        FPGA_TIME_S_USRP1 = 0.3
        FPGA_TIME_S_USRP2 = 0.4

        self.mockUsrpClient1.getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP1
        self.mockUsrpClient2.getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP2
        self.assertRaises(ValueError, lambda: self.system.execute())
