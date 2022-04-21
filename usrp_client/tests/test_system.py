import unittest
from unittest.mock import Mock

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig


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


# class TestConfigurationTxRx(unittest.TestCase):
#    def setUp(self) -> None:
#        self.mockRpcClient1 = Mock()
#        self.mockRpcClient2 = Mock()
#        self.system = System()
#        self.system.addUsrp(RfConfig(), "localhost", "usrp1", self.mockRpcClient1)
#        self.system.addUsrp(RfConfig(), "localhost2", "usrp2", self.mockRpcClient2)
#
#    def test_configureTxCallsFunctionInRpcClient(self) -> None:
#        txStreamingConfig = TxStreamingConfig(
#            sendTimeOffset=2.0, samples=[np.ones(int(2e3))]
#        )
#        self.system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig)
#        self.mockRpcClient1.configureTx.assert_called_once_with(txStreamingConfig)
#        self.mockRpcClient2.configureTx.assert_not_called()
