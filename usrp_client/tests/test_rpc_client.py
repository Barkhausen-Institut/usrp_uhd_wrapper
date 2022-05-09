import unittest
from unittest.mock import Mock

import numpy as np
import numpy.testing as npt

from usrp_client.rpc_client import UsrpClient
from uhd_wrapper.utils.config import (
    MimoSignal,
    RfConfig,
    TxStreamingConfig,
    RxStreamingConfig,
    fillDummyRfConfig,
)


class TestUsrpClient(unittest.TestCase):
    def setUp(self) -> None:
        self.masterClockRate = 400e6
        self.mockRpcClient = Mock()
        self.mockRpcClient.getMasterClockRate.return_value = self.masterClockRate
        self.usrpClient = UsrpClient(self.mockRpcClient)

    def test_configureRxSerializesCorrectly(self) -> None:
        rxConfig = RxStreamingConfig(receiveTimeOffset=1.0, noSamples=int(1e3))
        self.usrpClient.configureRx(rxConfig=rxConfig)
        self.mockRpcClient.configureRx.assert_called_with(
            rxConfig.receiveTimeOffset, rxConfig.noSamples
        )

    def test_configureTxSerializesCorrectly(self) -> None:
        signal = MimoSignal(signals=[np.arange(20)])
        txConfig = TxStreamingConfig(sendTimeOffset=3.0, samples=signal)
        self.usrpClient.configureTx(txConfig=txConfig)
        self.mockRpcClient.configureTx.assert_called_with(
            txConfig.sendTimeOffset, signal.serialize()
        )

    def test_executeGetsCalledWithBaseTime(self) -> None:
        BASE_TIME = 3.0
        self.usrpClient.execute(BASE_TIME)
        self.mockRpcClient.execute.assert_called_with(BASE_TIME)

    def test_collectReturnsDeserializedSamples(self) -> None:
        signal = MimoSignal(signals=[np.ones(10)])
        self.mockRpcClient.collect.return_value = [signal.serialize()]
        recvdSamples = self.usrpClient.collect()
        self.assertEqual(signal, recvdSamples[0])

    def test_collectReturnsDeserializedSamples_twoConfigs(self) -> None:
        signalConfig1 = MimoSignal(signals=[np.ones(10, dtype=np.complex64)])
        signalConfig2 = MimoSignal(signals=[2 * np.ones(10, dtype=np.complex64)])
        self.mockRpcClient.collect.return_value = [
            signalConfig1.serialize(),
            signalConfig2.serialize(),
        ]
        recvdSamples = self.usrpClient.collect()
        self.assertListEqual(recvdSamples, [signalConfig1, signalConfig2])

    def test_getRfConfigReturnsSerializedRfConfig(self) -> None:
        usrpRfConf = fillDummyRfConfig(RfConfig())

        self.mockRpcClient.getRfConfig.return_value = usrpRfConf.serialize()
        recvRfConfig = self.usrpClient.getRfConfig()

        self.assertEqual(recvRfConfig, usrpRfConf)

    def test_configureRfConfig_calledWithCorrectArguments(self) -> None:
        c = fillDummyRfConfig(RfConfig())

        self.usrpClient.configureRfConfig(rfConfig=c)
        self.mockRpcClient.configureRfConfig.assert_called_with(c.serialize())

    def test_setTimeToZeroPpsGetsCalled(self) -> None:
        self.usrpClient.setTimeToZeroNextPps()
        self.mockRpcClient.setTimeToZeroNextPps.assert_called_once()

    def test_getCurrentFpgaTimeGetsCalled(self) -> None:
        TIME = 3
        self.mockRpcClient.getCurrentFpgaTime.return_value = TIME
        self.assertAlmostEqual(self.usrpClient.getCurrentFpgaTime(), TIME)

    def test_getSystemTimeGetsCalled(self) -> None:
        TIME = 3
        self.mockRpcClient.getCurrentSystemTime.return_value = TIME
        self.assertAlmostEqual(self.usrpClient.getCurrentSystemTime(), TIME)

    def test_getMasterClockRate_functionGetsCalled(self) -> None:
        _ = self.usrpClient.getMasterClockRate()
        self.mockRpcClient.getMasterClockRate.assert_called_once()

    def test_supportedSamplingRates_queriesMasterClockRate(self) -> None:
        _ = self.usrpClient.getSupportedSamplingRates()
        self.mockRpcClient.getMasterClockRate.assert_called_once()

    def test_supportedSamplingRates(self) -> None:
        supportedDecimationRatios = np.array([1, 2])
        self.usrpClient.getSupportedDecimationRatios = (  # type: ignore
            lambda: supportedDecimationRatios
        )
        npt.assert_array_almost_equal(
            self.masterClockRate / supportedDecimationRatios,
            self.usrpClient.getSupportedSamplingRates(),
        )
