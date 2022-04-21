import unittest
from unittest.mock import Mock

import numpy as np

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig


class TestAddingUsrp(unittest.TestCase):
    def setUp(self) -> None:
        self.system = System()
        self.mockRpcClient = Mock()

    def test_clientConnects(self) -> None:
        self.system.addUsrp(RfConfig(), "localhost", "testUsrp", self.mockRpcClient)
        self.mockRpcClient.connect.assert_called_once_with("tcp://localhost:5555")

    def test_throwExceptionIfConnectionToUsrpAlreadyExists(self) -> None:
        self.system.addUsrp(RfConfig(), "localhost", "testName", self.mockRpcClient)
        self.assertRaises(
            ValueError,
            lambda: self.system.addUsrp(
                RfConfig(), "localhost", "testName", self.mockRpcClient
            ),
        )

    def test_rfConfigPassedToRpcClient(self) -> None:
        c = RfConfig()
        self.system.addUsrp(c, "localhost", "testusrp", self.mockRpcClient)
        self.mockRpcClient.configureRfConfig.assert_called_once_with(c)

    def test_usrpsRestartSynchronization_newUsrpAddedToSystem(self) -> None:
        c = RfConfig()

        self.system.addUsrp(c, "ip1", "usrp1", self.mockRpcClient)
        self.mockRpcClient.setTimeToZeroNextPps.assert_called_once()

        # reset mocks
        self.mockRpcClient.reset_mock()
        mockRpcClient2 = Mock()
        self.system.addUsrp(c, "ip2", "usrp2", mockRpcClient2)
        self.mockRpcClient.setTimeToZeroNextPps.assert_called_once()
        mockRpcClient2.setTimeToZeroNextPps.assert_called_once()


class TestConfigurationTxRx(unittest.TestCase):
    def setUp(self) -> None:
        self.mockRpcClient1 = Mock()
        self.mockRpcClient2 = Mock()
        self.system = System()
        self.system.addUsrp(RfConfig(), "localhost", "usrp1", self.mockRpcClient1)
        self.system.addUsrp(RfConfig(), "localhost2", "usrp2", self.mockRpcClient2)

    def test_configureTxCallsFunctionInRpcClient(self) -> None:
        txStreamingConfig = TxStreamingConfig(
            sendTimeOffset=2.0, samples=[np.ones(int(2e3))]
        )
        self.system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig)
        self.mockRpcClient1.configureTx.assert_called_once_with(txStreamingConfig)
        self.mockRpcClient2.configureTx.assert_not_called()
