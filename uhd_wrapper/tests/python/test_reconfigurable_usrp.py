import unittest
from unittest.mock import Mock, patch

from uhd_wrapper.rpc_server.reconfigurable_usrp import (
    ReconfigurableUsrp,
)
from uhd_wrapper.usrp_pybinding import Usrp, createUsrp


class TestReconfigurableUsrp(unittest.TestCase):
    def setUp(self) -> None:
        sleepPatcher = patch("time.sleep", return_value=None)
        _ = sleepPatcher.start()

    @patch("uhd_wrapper.usrp_pybinding.createUsrp")
    def test_initCreatesUsrp(self, mockedUsrpFactoryFunction) -> None:
        IP = "myIp"
        _ = ReconfigurableUsrp(IP)
        mockedUsrpFactoryFunction.assert_called_once_with(IP)

    @patch("uhd_wrapper.usrp_pybinding.createUsrp")
    def test_usrpCreatedAfterFirstFail(self, mockedUsrpFactoryFunction) -> None:
        mockedUsrpFactoryFunction.side_effect = [RuntimeError(), Mock(), Mock()]
        _ = ReconfigurableUsrp("localhost")
        self.assertEqual(mockedUsrpFactoryFunction.call_count, 2)
