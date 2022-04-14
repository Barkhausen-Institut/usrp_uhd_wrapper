import unittest
from unittest.mock import Mock
import sys
import os

sys.path.extend([os.path.join("build", "lib"), os.path.join("release_build", "lib")])

import numpy as np
import numpy.testing as npt

from server.rpc_server import (
    UsrpServer,
    serializeComplexArray,
    deserializeComplexArray,
)
from usrp_pybinding import Usrp


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
            sendTimeOffset=TIME_OFFSET,
            samples=[serializedSamples],
        )

        self.assertEqual(
            self.usrpMock.setTxConfig.call_args[0][0].sendTimeOffset, TIME_OFFSET
        )
        np.testing.assert_array_almost_equal(
            self.usrpMock.setTxConfig.call_args[0][0].samples[0],
            samples,
        )

    def test_configureRxCalledWithCorrectArguments(self) -> None:
        NO_SAMPLES = int(1e3)
        TIME_OFFSET = 2.0

        self.usrpServer.configureRx(receiveTimeOffset=TIME_OFFSET, noSamples=NO_SAMPLES)

        self.assertAlmostEqual(
            self.usrpMock.setRxConfig.call_args[0][0].receiveTimeOffset, TIME_OFFSET
        )
        self.assertAlmostEqual(
            self.usrpMock.setRxConfig.call_args[0][0].noSamples, NO_SAMPLES
        )

    def test_configureRfConfigCalledWithCorrectArguments(self) -> None:
        txGain = [50.0]
        rxGain = [30.0]
        txCarrierFrequency = [2e9]
        rxCarrierFrequency = [2e9]
        txAnalogFilterBw = 400e6
        rxAnalogFilterBw = 400e6
        txSamplingRate = 10e6
        rxSamplingRate = 10e6

        self.usrpServer.configureRfConfig(
            txGain=txGain,
            rxGain=rxGain,
            txCarrierFrequency=txCarrierFrequency,
            rxCarrierFrequency=rxCarrierFrequency,
            txAnalogFilterBw=txAnalogFilterBw,
            rxAnalogFilterBw=rxAnalogFilterBw,
            txSamplingRate=txSamplingRate,
            rxSamplingRate=rxSamplingRate,
        )

        self.assertListEqual(self.usrpMock.setRfConfig.call_args[0][0].txGain, txGain)
        self.assertListEqual(self.usrpMock.setRfConfig.call_args[0][0].rxGain, rxGain)
        self.assertListEqual(
            self.usrpMock.setRfConfig.call_args[0][0].txCarrierFrequency,
            txCarrierFrequency,
        )
        self.assertListEqual(
            self.usrpMock.setRfConfig.call_args[0][0].rxCarrierFrequency,
            rxCarrierFrequency,
        )
        self.assertAlmostEqual(
            self.usrpMock.setRfConfig.call_args[0][0].txAnalogFilterBw, txAnalogFilterBw
        )
        self.assertAlmostEqual(
            self.usrpMock.setRfConfig.call_args[0][0].rxAnalogFilterBw, rxAnalogFilterBw
        )
        self.assertAlmostEqual(
            self.usrpMock.setRfConfig.call_args[0][0].txSamplingRate, txSamplingRate
        )
        self.assertAlmostEqual(
            self.usrpMock.setRfConfig.call_args[0][0].rxSamplingRate, rxSamplingRate
        )

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
