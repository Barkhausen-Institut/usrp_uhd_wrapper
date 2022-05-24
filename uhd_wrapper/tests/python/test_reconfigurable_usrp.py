import unittest
from unittest.mock import Mock, patch

from uhd_wrapper.rpc_server.reconfigurable_usrp import (
    ReconfigurableUsrp,
)
from uhd_wrapper.usrp_pybinding import Usrp, createUsrp


class TestReconfigurableUsrp(unittest.TestCase):
    @patch("uhd_wrapper.usrp_pybinding.createUsrp")
    def test_initCreatesUsrp(self, mockedUsrpFactoryFunction) -> None:
        IP = "myIp"
        _ = ReconfigurableUsrp(IP)
        mockedUsrpFactoryFunction.assert_called_once_with(IP)
