import unittest
from unittest.mock import Mock

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig


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
