import unittest
from unittest.mock import Mock, patch

from uhd_wrapper.rpc_server.reconfigurable_usrp import RestartingUsrp
from uhd_wrapper.usrp_pybinding import Usrp


class TestUsrpStarts(unittest.TestCase):
    def setUp(self) -> None:
        self.sleepPatcher = patch("time.sleep", return_value=None)
        _ = self.sleepPatcher.start()

        self.usrpMock = Mock(spec=Usrp)
        self.usrpFactoryPatcher = patch(
            "uhd_wrapper.usrp_pybinding.createUsrp", return_value=self.usrpMock
        )
        self.mockedUsrpFactoryFunction = self.usrpFactoryPatcher.start()

    def tearDown(self) -> None:
        self.sleepPatcher.stop()
        self.usrpFactoryPatcher.stop()

    def test_initCreatesUsrp(self) -> None:
        IP = "myIp"
        _ = RestartingUsrp(IP)
        self.mockedUsrpFactoryFunction.assert_called_once_with(IP)

    def test_usrpCreatedAfterFirstFail(self) -> None:
        self.mockedUsrpFactoryFunction.side_effect = [RuntimeError(), Mock(), Mock()]
        _ = RestartingUsrp("localhost")
        self.assertEqual(self.mockedUsrpFactoryFunction.call_count, 2)

    def test_usrpCreationIsOnlyAttemptedThreeTimes(self) -> None:
        self.mockedUsrpFactoryFunction.side_effect = [
            RuntimeError(),
            RuntimeError(),
            RuntimeError(),
            RuntimeError(),
            RuntimeError(),
            Mock(),
        ]
        self.assertRaises(RuntimeError, lambda: RestartingUsrp("localhost"))
        self.assertEqual(self.mockedUsrpFactoryFunction.call_count, 5)
