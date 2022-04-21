import unittest
from unittest.mock import patch

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig


class TestAddingUsrp(unittest.TestCase):
    def setUp(self) -> None:
        self.system = System()
        self.patcherRpcClientConnection = patch("zerorpc.Client.connect")

    def test_clientConnects(self) -> None:
        self.mockRpcConnect = self.patcherRpcClientConnection.start()
        self.system.addUsrp(RfConfig(), "localhost", "testUsrp")
        self.mockRpcConnect.assert_called_once_with("tcp://localhost:5555")
        self.patcherRpcClientConnection.stop()

    def test_throwExceptionIfConnectionToUsrpAlreadyExists(self) -> None:
        self.system.addUsrp(RfConfig(), "localhost", "testName")
        self.assertRaises(
            ValueError, lambda: self.system.addUsrp(RfConfig(), "localhost", "testName")
        )
