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
        self.mockedUsrpDevice.collect.return_value = [[np.ones(int(10e3))]]
        usrpFactoryPatcher = patch(
            "uhd_wrapper.usrp_pybinding.createUsrp", return_value=self.mockedUsrpDevice
        )
        self.mockedUsrpFactoryFunction = usrpFactoryPatcher.start()
        self.R = ReconfigurableUsrp("localhost")
        self.mockedUsrpDevice.reset_mock()
        self.mockedUsrpFactoryFunction.reset_mock()

    def test_rfConfig(self) -> None:
        dummyRfConfig = fillDummyRfConfig(RfConfig())
        self.R.setRfConfig(dummyRfConfig)
        self.mockedUsrpDevice.setRfConfig.assert_called_once_with(dummyRfConfig)

    def test_txConfig(self) -> None:
        dummyTxStreamingConfig = TxStreamingConfig(
            samples=[np.ones(10)], sendTimeOffset=3.0
        )
        self.R.setTxConfig(dummyTxStreamingConfig)
        self.mockedUsrpDevice.setTxConfig.assert_called_once_with(
            dummyTxStreamingConfig
        )

    def test_rxConfig(self) -> None:
        dummyRxStreamingConfig = RxStreamingConfig(
            noSamples=int(1e3), receiveTimeOffset=3.0
        )
        self.R.setRxConfig(dummyRxStreamingConfig)
        self.mockedUsrpDevice.setRxConfig.assert_called_once_with(
            dummyRxStreamingConfig
        )

    def test_setTimeToZeroNextPpps(self) -> None:
        self.R.setTimeToZeroNextPps()
        self.mockedUsrpDevice.setTimeToZeroNextPps.assert_called_once()

    def test_getCurrentSystemTime(self) -> None:
        _ = self.R.getCurrentSystemTime()
        self.mockedUsrpDevice.getCurrentSystemTime.assert_called_once()

    def test_getCurrentFpgaTime(self) -> None:
        _ = self.R.getCurrentFpgaTime()
        self.mockedUsrpDevice.getCurrentFpgaTime.assert_called_once()

    def test_execute(self) -> None:
        baseTime = 1.0
        self.R.execute(baseTime)
        self.mockedUsrpDevice.execute.assert_called_once_with(baseTime)

    def test_collect(self) -> None:
        _ = self.R.collect()
        self.mockedUsrpDevice.collect.assert_called_once()

    def test_resetStreamingConfigs(self) -> None:
        self.R.resetStreamingConfigs()
        self.mockedUsrpDevice.resetStreamingConfigs.assert_called_once()

    def test_getMasterClockRate(self) -> None:
        _ = self.R.getMasterClockRate()
        self.mockedUsrpDevice.getMasterClockRate.assert_called_once()

    def test_getRfConfig(self) -> None:
        _ = self.R.getRfConfig()
        self.mockedUsrpDevice.getRfConfig.assert_called_once()
