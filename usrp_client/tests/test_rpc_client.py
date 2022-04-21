import unittest
from unittest.mock import Mock

import numpy as np
import numpy.testing as npt

from usrp_client.rpc_client import UsrpClient
from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig, RxStreamingConfig
from uhd_wrapper.utils.serialization import serializeComplexArray


class TestUsrpClient(unittest.TestCase):
    def setUp(self) -> None:
        self.mockRpcClient = Mock()
        self.usrpClient = UsrpClient(self.mockRpcClient)

    def test_configureRxSerializesCorrectly(self) -> None:
        rxConfig = RxStreamingConfig(receiveTimeOffset=1.0, noSamples=int(1e3))
        self.usrpClient.configureRx(rxConfig=rxConfig)
        self.mockRpcClient.configureRx.assert_called_with(
            rxConfig.receiveTimeOffset, rxConfig.noSamples
        )

    def test_configureTxSerializesCorrectly(self) -> None:
        txConfig = TxStreamingConfig(sendTimeOffset=3.0, samples=[np.arange(10)])
        self.usrpClient.configureTx(txConfig=txConfig)
        self.mockRpcClient.configureTx.assert_called_with(
            txConfig.sendTimeOffset, [serializeComplexArray(txConfig.samples[0])]
        )

    def test_executeGetsCalledWithBaseTime(self) -> None:
        BASE_TIME = 3.0
        self.usrpClient.execute(BASE_TIME)
        self.mockRpcClient.execute.assert_called_with(BASE_TIME)

    def test_collectReturnsDeserializedSamples(self) -> None:
        samplesDeserialized = [np.ones(10)]
        samplesSerialized = [serializeComplexArray(samplesDeserialized[0])]

        self.mockRpcClient.collect.return_value = samplesSerialized
        recvdSamples = self.usrpClient.collect()
        npt.assert_array_equal(recvdSamples[0], samplesDeserialized[0])

    def test_configureRfConfig_calledWithCorrectArguments(self) -> None:
        txGain = [50.0]
        rxGain = [30.0]
        txCarrierFrequency = [2e9]
        rxCarrierFrequency = [2e9]
        txAnalogFilterBw = 400e6
        rxAnalogFilterBw = 400e6
        txSamplingRate = 10e6
        rxSamplingRate = 10e6

        rfConfig = RfConfig(
            txGain=txGain,
            rxGain=rxGain,
            txCarrierFrequency=txCarrierFrequency,
            rxCarrierFrequency=rxCarrierFrequency,
            txAnalogFilterBw=txAnalogFilterBw,
            rxAnalogFilterBw=rxAnalogFilterBw,
            txSamplingRate=txSamplingRate,
            rxSamplingRate=rxSamplingRate,
        )
        self.usrpClient.configureRfConfig(rfConfig=rfConfig)
        self.mockRpcClient.configureRfConfig.assert_called_with(
            txGain,
            rxGain,
            txCarrierFrequency,
            rxCarrierFrequency,
            txAnalogFilterBw,
            rxAnalogFilterBw,
            txSamplingRate,
            rxSamplingRate,
        )

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
