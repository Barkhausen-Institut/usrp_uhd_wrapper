import unittest
from unittest.mock import Mock, patch

import numpy as np

from uhd_wrapper.rpc_server.reconfigurable_usrp import ReconfigurableUsrp
from uhd_wrapper.usrp_pybinding import Usrp, RfConfig, TxStreamingConfig
from uhd_wrapper.utils.config import fillDummyRfConfig


class TestUsrpStarts(unittest.TestCase):
    def setUp(self) -> None:
        sleepPatcher = patch("time.sleep", return_value=None)
        _ = sleepPatcher.start()
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


class TestFunctionsGetPassedThrough(unittest.TestCase):
    def setUp(self) -> None:
        self.mockedUsrpDevice = Mock(spec=Usrp)
        usrpFactoryPatcher = patch(
            "uhd_wrapper.usrp_pybinding.createUsrp", return_value=self.mockedUsrpDevice
        )
        self.mockedUsrpFactoryFunction = usrpFactoryPatcher.start()
        self.R = ReconfigurableUsrp("localhost")
        self.mockedUsrpDevice.reset_mock()
        self.mockedUsrpFactoryFunction.reset_mock()

    def test_rfConfigGetsPassedThrough(self) -> None:
        dummyRfConfig = fillDummyRfConfig(RfConfig())
        self.R.setRfConfig(dummyRfConfig)
        self.mockedUsrpDevice.setRfConfig.assert_called_once_with(dummyRfConfig)

    def test_txConfigGetsPassedThrough(self) -> None:
        dummyTxStreamingConfig = TxStreamingConfig(
            samples=[np.ones(10)], sendTimeOffset=3.0
        )
        self.R.setTxConfig(dummyTxStreamingConfig)
        self.mockedUsrpDevice.setTxConfig.assert_called_once_with(
            dummyTxStreamingConfig
        )
