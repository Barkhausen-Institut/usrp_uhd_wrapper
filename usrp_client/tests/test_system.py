import unittest
from unittest.mock import Mock, patch
from typing import List

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


class SystemMockFactory:
    def mockSystem(self, system: System, noMockUsrps: int) -> List[Mock]:
        mockUsrps = self.__createUsrpClients(noMockUsrps)
        self.__addClientsToSystem(system, mockUsrps)
        sleepPatcher = patch("time.sleep", return_value=None)
        _ = sleepPatcher.start()
        return mockUsrps

    def __createUsrpClients(self, noUsrpClients: int) -> List[Mock]:
        mockUsrps: List[Mock] = [Mock(spec=UsrpClient) for _ in range(noUsrpClients)]

        for mockedUsrpClient in mockUsrps:
            mockedUsrpClient.getCurrentFpgaTime.return_value = 3.0
        return mockUsrps

    def __addClientsToSystem(self, system: System, clients: List[Mock]) -> None:
        system.createUsrpClient = Mock()  # type: ignore
        system.createUsrpClient.side_effect = clients  # type: ignore
        for usrpIdx in range(len(clients)):  # type: ignore
            system.addUsrp(RfConfig(), f"localhost{usrpIdx+1}", f"usrp{usrpIdx+1}")


class TestStreamingConfiguration(unittest.TestCase, SystemMockFactory):
    @patch("time.sleep", return_value=None)
    def setUp(self, patched_sleep) -> None:
        self.system = System()
        self.mockUsrps = self.mockSystem(self.system, 2)

    def test_configureTxCallsFunctionInRpcClient(self) -> None:
        txStreamingConfig = TxStreamingConfig(
            sendTimeOffset=2.0, samples=[np.ones(int(2e3))]
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
        # add new usrp
        mockedUsrp = Mock(spec=UsrpClient)
        mockedUsrp.getCurrentFpgaTime.return_value = 3.0
        self.system.createUsrpClient.side_effect = [mockedUsrp]  # type: ignore
        self.system.addUsrp(RfConfig(), "localhost3", "usrp3")

        self.system.execute()
        self.mockUsrps[0].setTimeToZeroNextPps.assert_called_once()
        self.mockUsrps[1].setTimeToZeroNextPps.assert_called_once()
        mockedUsrp.setTimeToZeroNextPps.assert_called_once()

    def test_throwExceptionIfSyncIsInvalid(self) -> None:
        fpgaTimeUsrp1 = 3.0
        fpgaTimeUsrp2 = fpgaTimeUsrp1 + System.syncThresholdSec + 1.0
        self.mockUsrps[0].getCurrentFpgaTime.return_value = fpgaTimeUsrp1
        self.mockUsrps[1].getCurrentFpgaTime.return_value = fpgaTimeUsrp2
        self.assertRaises(ValueError, lambda: self.system.execute())


class TestTransceivingMultiDevice(unittest.TestCase, SystemMockFactory):
    def setUp(self) -> None:
        self.system = System()
        self.mockUsrps = self.mockSystem(self.system, 2)

    def test_collectCallsCollectFromUsrpClient(self) -> None:
        samplesUsrp1 = [np.ones(10)]
        samplesUsrp2 = [2 * np.ones(10)]

        self.mockUsrps[0].collect.return_value = samplesUsrp1
        self.mockUsrps[1].collect.return_value = samplesUsrp2
        samples = self.system.collect()
        npt.assert_array_equal(samples["usrp1"][0], samplesUsrp1[0])
        npt.assert_array_equal(samples["usrp2"][0], samplesUsrp2[0])

    def test_calculationBaseTime_validSynchronisation(self) -> None:
        FPGA_TIME_S_USRP1 = 0.3
        FPGA_TIME_S_USRP2 = 0.4
        BASE_TIME_OFFSET_SEC = 0.2

        System.baseTimeOffsetSec = BASE_TIME_OFFSET_SEC
        self.mockUsrps[0].getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP1
        self.mockUsrps[1].getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP2
        expectedBaseTime = FPGA_TIME_S_USRP2 + BASE_TIME_OFFSET_SEC
        self.system.execute()
        self.mockUsrps[0].execute.assert_called_once_with(expectedBaseTime)
        self.mockUsrps[1].execute.assert_called_once_with(expectedBaseTime)

    def test_calculationBaseTime_invalidSynchronisation(self) -> None:
        FPGA_TIME_S_USRP1 = 0.3
        FPGA_TIME_S_USRP2 = 1.5
        BASE_TIME_OFFSET_SEC = 0.2

        System.baseTimeOffsetSec = BASE_TIME_OFFSET_SEC
        self.mockUsrps[0].getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP1
        self.mockUsrps[1].getCurrentFpgaTime.return_value = FPGA_TIME_S_USRP2
        self.assertRaises(ValueError, lambda: self.system.execute())
