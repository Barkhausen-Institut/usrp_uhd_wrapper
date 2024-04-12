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
    serializeComplexArray,
    deserializeComplexArray,
)
from uhd_wrapper.usrp_pybinding import (
    Usrp,
    RxStreamingConfig,
    TxStreamingConfig,
)
from uhd_wrapper.utils.config import RfConfig, MimoSignal
from uhd_wrapper.tests.python.utils import fillDummyRfConfig


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
        self.conf = fillDummyRfConfig(RfConfig())
        self.serializedRfConf = self.conf.serialize()

    def test_properRfConfigSerialization(self) -> None:
        serializedConf = self.conf.serialize()
        self.assertEqual(self.serializedRfConf, serializedConf)

    def test_properRfConfigDeSerialization(self) -> None:
        self.assertEqual(self.conf, RfConfig.deserialize(self.serializedRfConf))


class TestRfConfigCast(unittest.TestCase):
    def test_castFromBindingToConfig(self) -> None:
        from uhd_wrapper.usrp_pybinding import RfConfig as RfConfigBinding

        cBinding = fillDummyRfConfig(RfConfigBinding())

        c = RfConfigFromBinding(cBinding)
        self.assertEqual(cBinding.rxCarrierFrequency, c.rxCarrierFrequency)
        self.assertEqual(cBinding.txCarrierFrequency, c.txCarrierFrequency)
        self.assertEqual(cBinding.txSamplingRate, c.txSamplingRate)
        self.assertEqual(cBinding.rxSamplingRate, c.rxSamplingRate)
        self.assertEqual(cBinding.txAnalogFilterBw, c.txAnalogFilterBw)
        self.assertEqual(cBinding.rxAnalogFilterBw, c.rxAnalogFilterBw)
        self.assertEqual(cBinding.txGain, c.txGain)
        self.assertEqual(cBinding.rxGain, c.rxGain)

    def test_castConfigToBinding(self) -> None:
        from uhd_wrapper.utils.config import RfConfig

        cBinding = fillDummyRfConfig(RfConfig())

        c = RfConfigToBinding(cBinding)
        self.assertEqual(cBinding.rxCarrierFrequency, c.rxCarrierFrequency)
        self.assertEqual(cBinding.txCarrierFrequency, c.txCarrierFrequency)
        self.assertEqual(cBinding.txSamplingRate, c.txSamplingRate)
        self.assertEqual(cBinding.rxSamplingRate, c.rxSamplingRate)
        self.assertEqual(cBinding.txAnalogFilterBw, c.txAnalogFilterBw)
        self.assertEqual(cBinding.rxAnalogFilterBw, c.rxAnalogFilterBw)
        self.assertEqual(cBinding.txGain, c.txGain)
        self.assertEqual(cBinding.rxGain, c.rxGain)


class TestUsrpServer(unittest.TestCase):
    def setUp(self) -> None:
        self.usrpMock = Mock(spec=Usrp)
        self.usrpServer = UsrpServer(self.usrpMock)

    def test_mockThrowsExceptionIfCallMismatchesSpec(self) -> None:
        self.assertRaises(AttributeError, lambda: self.usrpMock.notImplemented())
        self.usrpMock.execute(3.0)

    def test_configureTxCalledWithCorrectArguments(self) -> None:
        TIME_OFFSET = 2.0
        signal = MimoSignal(signals=[np.array([2, 3]) + 1j * np.array([0, 1])])
        self.usrpServer.configureTx(
            TIME_OFFSET,
            signal.serialize(),
            18
        )
        self.usrpMock.setTxConfig.assert_called_once_with(
            TxStreamingConfig(sendTimeOffset=TIME_OFFSET, samples=signal.signals,
                              repetitions=18)
        )

    def test_configureRxCalledWithCorrectArguments(self) -> None:
        NO_SAMPLES = int(1e3)
        TIME_OFFSET = 2.0
        ANT = "A"
        REPs = 5
        PERIOD = 20000

        self.usrpServer.configureRx(TIME_OFFSET, NO_SAMPLES, ANT, REPs, PERIOD)
        self.usrpMock.setRxConfig.assert_called_once_with(
            RxStreamingConfig(receiveTimeOffset=TIME_OFFSET,
                              noSamples=NO_SAMPLES,
                              antennaPort=ANT,
                              numRepetitions=REPs,
                              repetitionPeriod=PERIOD)
        )

    def test_configureRfConfigCalledWithCorrectArguments(self) -> None:
        from uhd_wrapper.usrp_pybinding import RfConfig as RfConfigBinding
        from uhd_wrapper.utils.config import RfConfig

        c = fillDummyRfConfig(RfConfig())
        self.usrpServer.configureRfConfig(c.serialize())  # type: ignore

        self.usrpMock.setRfConfig.assert_called_once_with(
            fillDummyRfConfig(RfConfigBinding())
        )

    def test_getRfConfigReturnsSerializedVersion(self) -> None:
        from uhd_wrapper.usrp_pybinding import RfConfig as RfConfigBinding

        usrpRfConfig = fillDummyRfConfig(RfConfigBinding())
        c = RfConfigFromBinding(usrpRfConfig)

        self.usrpMock.getRfConfig.return_value = usrpRfConfig
        self.assertEqual(c.serialize(), self.usrpServer.getRfConfig())

    def test_collectGetsCalled(self) -> None:
        signal = MimoSignal(signals=[np.arange(10)])
        self.usrpMock.collect.return_value = [signal.signals]
        _ = self.usrpServer.collect()
        self.usrpMock.collect.assert_called_once()

    def test_collectReturnsSerializedVersion(self) -> None:
        signal = MimoSignal(signals=[np.arange(10)])
        self.usrpMock.collect.return_value = [signal.signals]

        self.assertListEqual([signal.serialize()], self.usrpServer.collect())

    def test_collectReturnsSerializedVersion_twoConfigs(self) -> None:
        signal = MimoSignal(signals=[np.arange(10)])
        self.usrpMock.collect.return_value = [signal.signals, signal.signals]

        self.assertListEqual(
            [signal.serialize(), signal.serialize()], self.usrpServer.collect()
        )
