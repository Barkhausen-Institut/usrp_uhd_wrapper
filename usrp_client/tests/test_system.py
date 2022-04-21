import unittest
from unittest.mock import Mock

import numpy as np

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig, RxStreamingConfig


class TestAddingUsrp(unittest.TestCase):
    def setUp(self) -> None:
        self.system = System()
        self.mockUsrpClient = Mock()

        self.system.createUsrpClient = Mock()  # type: ignore
        self.system.createUsrpClient.return_value = self.mockUsrpClient  # type: ignore

    def test_usrpClientGetsCreated(self) -> None:
        IP = "localhost"
        self.system.addUsrp(RfConfig(), IP, "dummyName")
        self.system.createUsrpClient.assert_called_once_with(IP)  # type: ignore

    def test_throwExceptionIfConnectionToUsrpAlreadyExists(self) -> None:
        self.system.addUsrp(RfConfig(), "localhost", "testName")
        self.assertRaises(
            ValueError,
            lambda: self.system.addUsrp(RfConfig(), "localhost", "testName"),
        )

    def test_rfConfigPassedToRpcClient(self) -> None:
        c = RfConfig()
        self.system.addUsrp(c, "localhost", "testusrp")
        self.mockUsrpClient.configureRfConfig.assert_called_once_with(c)


#    def test_usrpsRestartSynchronization_newUsrpAddedToSystem(self) -> None:
#        c = RfConfig()
#
#        self.system.addUsrp(c, "ip1", "usrp1", self.mockClients)
#        self.mockUsrpClient.setTimeToZeroNextPps.assert_called_once()
#
#        # reset mocks
#        self.mockUsrpClient.reset_mock()
#        mockZeroRpcClient2 = Mock(spec=zerorpc.Client)
#        mockUsrpClient2 = Mock(spec=UsrpClient)
#        self.system.addUsrp(c, "ip2", "usrp2", (mockZeroRpcClient2, mockUsrpClient2))
#        self.mockUsrpClient.setTimeToZeroNextPps.assert_called_once()
#        mockUsrpClient2.setTimeToZeroNextPps.assert_called_once()


class TestExecution(unittest.TestCase):
    def setUp(self) -> None:
        self.system = System()
        self.mockUsrpClient1 = Mock()
        self.mockUsrpClient2 = Mock()
        self.mockUsrpClient3 = Mock()

        self.system.createUsrpClient = Mock()  # type: ignore
        self.system.createUsrpClient.side_effect = [
            self.mockUsrpClient1,
            self.mockUsrpClient2,
            self.mockUsrpClient3,
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

    def test_executeCallsSynchronisation(self) -> None:
        self.system.execute()
        self.mockUsrpClient1.setTimeToZeroNextPps.assert_called_once()
        self.mockUsrpClient2.setTimeToZeroNextPps.assert_called_once()

    def test_syncOnlyOnce(self) -> None:
        self.system.execute()
        self.mockUsrpClient1.setTimeToZeroNextPps.assert_called_once()
        self.mockUsrpClient2.setTimeToZeroNextPps.assert_called_once()

        self.mockUsrpClient1.reset_mock()
        self.mockUsrpClient2.reset_mock()
        self.system.execute()
        self.mockUsrpClient1.setTimeToZeroNextPps.assert_not_called()
        self.mockUsrpClient2.setTimeToZeroNextPps.assert_not_called()

    def test_execute_reSyncIfUsrpAdded(self) -> None:
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
