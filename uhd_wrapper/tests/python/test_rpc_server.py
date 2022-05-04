import unittest
from unittest.mock import Mock

import numpy as np
import numpy.testing as npt

from uhd_wrapper.rpc_server.rpc_server import (
    RfConfigFromBinding,
    UsrpServer,
    RfConfigToBinding,
)
from uhd_wrapper.utils.serialization import (
    deserializeRfConfig,
    serializeComplexArray,
    deserializeComplexArray,
    serializeRfConfig,
)
from uhd_wrapper.usrp_pybinding import (
    Usrp,
    RxStreamingConfig,
    TxStreamingConfig,
)
from uhd_wrapper.utils.config import RfConfig


class TestSerializationComplexArr(unittest.TestCase):
    def test_oneDimensionalArray_complexValues(self) -> None:
        oneDimensionalArr = np.ones(3, dtype=np.complex64)
        real, imag = serializeComplexArray(oneDimensionalArr)

        self.assertListEqual(imag, np.imag(oneDimensionalArr).tolist())
        self.assertListEqual(real, np.real(oneDimensionalArr).tolist())

    def test_nonComplexArrayYieldsZeroImaginary(self) -> None:
        arr = np.ones(3)
        real, imag = serializeComplexArray(arr)

        self.assertListEqual(imag, np.imag(arr).tolist())
        self.assertListEqual(real, np.real(arr).tolist())

    def test_ndArrayShouldNotBeSupported(self) -> None:
        arr = np.ones((2, 3))
        self.assertRaises(ValueError, lambda: serializeComplexArray(arr))


class TestDeserializationComplexArr(unittest.TestCase):
    def test_properDeserialization(self) -> None:
        imagList = [1, 2, 3]
        realList = [4, 5, 6]

        expectedArr = np.array(realList) + 1j * np.array(imagList)
        deserializedArr = deserializeComplexArray((realList, imagList))
        npt.assert_array_almost_equal(deserializedArr, expectedArr)

    def test_noImagSamples_mismatch_noRealSamples(self) -> None:
        imagList = [0]
        realList = [1, 2]

        self.assertRaises(
            ValueError, lambda: deserializeComplexArray((realList, imagList))
        )


class TestSerializationRfConfig(unittest.TestCase):
    def setUp(self) -> None:
        self.conf = RfConfig()
        self.conf.txCarrierFrequency = [2e9]

        self.conf.txGain = [30]
        self.conf.txAnalogFilterBw = 200e6
        self.conf.txSamplingRate = 20e6

        self.conf.rxCarrierFrequency = [2e9]
        self.conf.rxGain = [40]
        self.conf.rxAnalogFilterBw = 100e6
        self.conf.rxSamplingRate = 30e6

        self.serializedRfConf = self.conf.to_json()  # type: ignore

    def test_properRfConfigSerialization(self) -> None:
        serializedConf = serializeRfConfig(self.conf)
        self.assertEqual(self.serializedRfConf, serializedConf)

    def test_properRfConfigDeSerialization(self) -> None:
        self.assertEqual(self.conf, deserializeRfConfig(self.serializedRfConf))


class TestRfConfigCast(unittest.TestCase):
    def test_castFromBindingToConfig(self) -> None:
        from uhd_wrapper.usrp_pybinding import RfConfig as RfConfigBinding

        cBinding = RfConfigBinding()
        cBinding.rxCarrierFrequency = [3e9]
        cBinding.txCarrierFrequency = [2e9]
        cBinding.txSamplingRate = 2e6
        cBinding.rxSamplingRate = 2e6
        cBinding.txGain = [30]
        cBinding.rxGain = [20]
        cBinding.txAnalogFilterBw = 400e6
        cBinding.rxAnalogFilterBw = 400e6

        c = RfConfigFromBinding(cBinding)
        self.assertListEqual(cBinding.rxCarrierFrequency, c.rxCarrierFrequency)
        self.assertListEqual(cBinding.txCarrierFrequency, c.txCarrierFrequency)
        self.assertEqual(cBinding.txSamplingRate, c.txSamplingRate)
        self.assertEqual(cBinding.rxSamplingRate, c.rxSamplingRate)
        self.assertEqual(cBinding.txAnalogFilterBw, c.txAnalogFilterBw)
        self.assertEqual(cBinding.rxAnalogFilterBw, c.rxAnalogFilterBw)
        self.assertListEqual(cBinding.txGain, c.txGain)
        self.assertListEqual(cBinding.rxGain, c.rxGain)

    def test_castConfigToBinding(self) -> None:
        from uhd_wrapper.utils.config import RfConfig

        cBinding = RfConfig()
        cBinding.rxCarrierFrequency = [3e9]
        cBinding.txCarrierFrequency = [2e9]
        cBinding.txSamplingRate = 2e6
        cBinding.rxSamplingRate = 2e6
        cBinding.txGain = [30]
        cBinding.rxGain = [20]
        cBinding.txAnalogFilterBw = 400e6
        cBinding.rxAnalogFilterBw = 400e6

        c = RfConfigToBinding(cBinding)
        self.assertListEqual(cBinding.rxCarrierFrequency, c.rxCarrierFrequency)
        self.assertListEqual(cBinding.txCarrierFrequency, c.txCarrierFrequency)
        self.assertEqual(cBinding.txSamplingRate, c.txSamplingRate)
        self.assertEqual(cBinding.rxSamplingRate, c.rxSamplingRate)
        self.assertEqual(cBinding.txAnalogFilterBw, c.txAnalogFilterBw)
        self.assertEqual(cBinding.rxAnalogFilterBw, c.rxAnalogFilterBw)
        self.assertListEqual(cBinding.txGain, c.txGain)
        self.assertListEqual(cBinding.rxGain, c.rxGain)


class TestUsrpServer(unittest.TestCase):
    def setUp(self) -> None:
        self.usrpMock = Mock(spec=Usrp)
        self.usrpServer = UsrpServer(self.usrpMock)

    def test_mockThrowsExceptionIfCallMismatchesSpec(self) -> None:
        self.assertRaises(AttributeError, lambda: self.usrpMock.notImplemented())
        self.usrpMock.execute(3.0)

    def test_configureTxCalledWithCorrectArguments(self) -> None:
        TIME_OFFSET = 2.0
        samples = np.array([2, 3]) + 1j * np.array([0, 1])
        serializedSamples = serializeComplexArray(samples)
        self.usrpServer.configureTx(
            TIME_OFFSET,
            [serializedSamples],
        )
        self.usrpMock.setTxConfig.assert_called_once_with(
            TxStreamingConfig(sendTimeOffset=TIME_OFFSET, samples=[samples])
        )

    def test_configureRxCalledWithCorrectArguments(self) -> None:
        NO_SAMPLES = int(1e3)
        TIME_OFFSET = 2.0

        self.usrpServer.configureRx(TIME_OFFSET, NO_SAMPLES)
        self.usrpMock.setRxConfig.assert_called_once_with(
            RxStreamingConfig(receiveTimeOffset=TIME_OFFSET, noSamples=NO_SAMPLES)
        )

    def test_configureRfConfigCalledWithCorrectArguments(self) -> None:
        c = RfConfig()
        c.txGain = [50.0]
        c.rxGain = [30.0]
        c.txCarrierFrequency = [2e9]
        c.rxCarrierFrequency = [2e9]
        c.txAnalogFilterBw = 400e6
        c.rxAnalogFilterBw = 400e6
        c.txSamplingRate = 10e6
        c.rxSamplingRate = 10e6

        self.usrpServer.configureRfConfig(c.to_json())  # type: ignore

        self.usrpMock.setRfConfig.assert_called_once_with(
            RfConfig(
                txGain=c.txGain,
                rxGain=c.rxGain,
                txCarrierFrequency=c.txCarrierFrequency,
                rxCarrierFrequency=c.rxCarrierFrequency,
                txAnalogFilterBw=c.txAnalogFilterBw,
                rxAnalogFilterBw=c.rxAnalogFilterBw,
                txSamplingRate=c.txSamplingRate,
                rxSamplingRate=c.rxSamplingRate,
            )
        )

    def test_getRfConfigReturnsSerializedVersion(self) -> None:
        from uhd_wrapper.usrp_pybinding import RfConfig as RfConfigBinding

        usrpRfConfig = RfConfigBinding()
        usrpRfConfig.txCarrierFrequency = [2e9]

        usrpRfConfig.txGain = [30]
        usrpRfConfig.txAnalogFilterBw = 200e6
        usrpRfConfig.txSamplingRate = 20e6

        usrpRfConfig.rxCarrierFrequency = [2e9]
        usrpRfConfig.rxGain = [40]
        usrpRfConfig.rxAnalogFilterBw = 100e6
        usrpRfConfig.rxSamplingRate = 30e6
        self.usrpMock.getRfConfig.return_value = usrpRfConfig

        c = RfConfigFromBinding(usrpRfConfig)

        self.assertEqual(serializeRfConfig(c), self.usrpServer.getRfConfig())

    def test_executeGetsCalledWithCorrectArguments(self) -> None:
        BASE_TIME = 3.0

        self.usrpServer.execute(BASE_TIME)
        self.usrpMock.execute.assert_called_once_with(BASE_TIME)

    def test_settingTimeToZeroNextPps_getsCalled(self) -> None:
        self.usrpServer.setTimeToZeroNextPps()
        self.usrpMock.setTimeToZeroNextPps.assert_called_once()

    def test_collectGetsCalled(self) -> None:
        self.usrpMock.collect.return_value = [np.arange(10)]
        _ = self.usrpServer.collect()
        self.usrpMock.collect.assert_called_once()

    def test_collectReturnsSerializedVersion(self) -> None:
        receivedSamplesInFpga = np.arange(10)
        self.usrpMock.collect.return_value = [receivedSamplesInFpga]

        self.assertListEqual(
            [serializeComplexArray(receivedSamplesInFpga)], self.usrpServer.collect()
        )

    def test_usrpIsResetAtDestruction(self) -> None:
        del self.usrpServer
        self.usrpMock.reset.assert_called_once()

    def test_getCurrentFpgaTime_functionGetsCalled(self) -> None:
        TIME = 10
        self.usrpMock.getCurrentFpgaTime.return_value = TIME
        time = self.usrpServer.getCurrentFpgaTime()
        self.assertEqual(time, TIME)

    def test_getCurrentSystemTime_functionGetsCalled(self) -> None:
        TIME = 10
        self.usrpMock.getCurrentSystemTime.return_value = TIME
        time = self.usrpServer.getCurrentSystemTime()
        self.assertEqual(time, TIME)
