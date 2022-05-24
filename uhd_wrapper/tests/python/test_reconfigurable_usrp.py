import unittest
from unittest.mock import Mock, patch

import numpy as np

from uhd_wrapper.rpc_server.reconfigurable_usrp import ReconfigurableUsrp
from uhd_wrapper.usrp_pybinding import (
    Usrp,
    RfConfig,
    TxStreamingConfig,
    RxStreamingConfig,
)
from uhd_wrapper.utils.config import fillDummyRfConfig


class TestUsrpStarts(unittest.TestCase):
    def setUp(self) -> None:
        sleepPatcher = patch("time.sleep", return_value=None)
        _ = sleepPatcher.start()

        sysExitPatcher = patch("sys.exit", return_value=None)
        self.mockedSysExit = sysExitPatcher.start()

        usrpFactoryPatcher = patch(
            "uhd_wrapper.usrp_pybinding.createUsrp", return_value=Mock()
        )
        self.mockedUsrpFactoryFunction = usrpFactoryPatcher.start()

    def test_initCreatesUsrp(self) -> None:
        IP = "myIp"
        _ = ReconfigurableUsrp(IP)
        self.mockedUsrpFactoryFunction.assert_called_once_with(IP)

    def test_usrpCreatedAfterFirstFail(self) -> None:
        self.mockedUsrpFactoryFunction.side_effect = [RuntimeError(), Mock(), Mock()]
        _ = ReconfigurableUsrp("localhost")
        self.assertEqual(self.mockedUsrpFactoryFunction.call_count, 2)

    def test_usrpCreationIsOnlyAttemptedThreeTimes(self) -> None:
        self.mockedUsrpFactoryFunction.side_effect = [
            RuntimeError(),
            RuntimeError(),
            RuntimeError(),
            Mock(),
        ]
        _ = ReconfigurableUsrp("localhost")
        self.assertEqual(self.mockedUsrpFactoryFunction.call_count, 3)
        self.mockedSysExit.assert_called_once()
